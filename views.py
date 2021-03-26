import json

from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404

from products.models import Product
from .models import Cart, CartItem
from .forms import EditCartForm


class CartView(View):
    """
    A view for displaying and editing anonymous
    and authenticated users' cart information.
    Edits the cart based on AJAX POST requests.
    """

    def get(self, request, *args, **kwargs):
        if "cart" in request.session and request.session["cart_len"] != 0:
            cart_info = get_cart_info(request)
            context = { "cart_info": cart_info }
            return render(request, 'cart/cart.html', context)
        else:
            # The cart is empty. Nothing to display.
            return render(request, 'cart/cart.html', {})

    def post(self, request, *args, **kwargs):
        if (request.POST.get('action') == 'edit'):
            new_quantity = int(request.POST.get('selection'))
            item_num = int(request.POST.get('item_num'))
        
            if new_quantity < 0 or new_quantity > 1000:
                raise Http404("The quantity submitted exceeds imposed limits...")

            edit_cart(request, item_num, new_quantity)
            product = Product.objects.get(product_id=request.session["cart"][item_num]["product_id"])
            product_price = float(product.product_price)
            context = {

                "action": "edit",
                "new_cart_summary": request.session["cart_summary"],
                "new_cart_len": request.session["cart_len"],

            }

            return HttpResponse(json.dumps(context), content_type="application/json")

        elif (request.POST.get('action') == 'delete'):
            item_num = int(request.POST.get('item_num'))

            delete_item(request, item_num)
            
            if request.session["cart_len"] == 0:
                clear_cart(request, True)

            return HttpResponse(json.dumps({"action": "delete"}), content_type="application/json")

        else:
            raise Http404("Invalid action...")


def sync_session_and_db_cart(request):
    """
    Sync cart session with database when user
    authenticates. Should only be called at login.
    """

    db_cart = Cart.objects.filter(user_id=request.user.user_id)

    if len(db_cart) == 0:
        if "cart" in request.session:
            db_cart = Cart.objects.create(user_id=request.user)
        else:
            return
    else:
        db_cart = db_cart[0]


    if "cart" in request.session:
        session_cart = request.session["cart"]

        for item in session_cart:
            product = Product.objects.get(product_id=item["product_id"])
            db_cart_item = CartItem.objects.filter(cart_id=db_cart.cart_id, product_id=product.product_id)

            if len(db_cart_item) != 0:
                db_cart_item = db_cart_item[0]
                db_cart_item.item_quantity = db_cart_item.item_quantity + item["quantity"]
                db_cart_item.save()

            else:
                CartItem.objects.create(cart_id=db_cart, \
                                        product_id=product, \
                                        item_quantity=item["quantity"])

        clear_cart(request, False)


    for item in CartItem.objects.filter(cart_id=db_cart.cart_id):
        add_to_cart(request, item.product_id.product_id, item.item_quantity, False)


def init_cart(request):
    """
    Initializes session cart variables and,
    if user is authenticated, the database.
    """

    request.session["cart"] = []
    request.session["cart_len"] = 0
    request.session["cart_summary"] = {
            
            "subtotal": 0,
            "shipping": 0,
            "sales_tax_estimate": 0,
            "order_total": 0,

    }

    if request.user.is_authenticated:
        if not Cart.objects.filter(user_id=request.user.user_id).exists():
            Cart.objects.create(user_id=request.user)


def add_to_cart(request, product_id, quantity, reflect_to_db):
    """
    Adds an item to the cart. If reflect_to_db
    is False, item is only added to session cart.
    """

    added = False
    product = Product.objects.get(product_id=product_id)

    if "cart" not in request.session:
        init_cart(request)

    if request.session["cart_len"] > 0:
        for item in request.session["cart"]:
            if item["product_id"] == product_id:
                item["quantity"] = item["quantity"] + quantity
                request.session["cart_len"] = request.session["cart_len"] + quantity
                summarize_cart_addition(request, product.product_price, quantity)

                if request.user.is_authenticated and reflect_to_db:
                    cart_id = Cart.objects.get(user_id=request.user.user_id).cart_id
                    cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product)
                    cart_item.item_quantity = cart_item.item_quantity + quantity
                    cart_item.save()

                added = True

                break

    if not added:
        request.session["cart"].append({"product_id": product_id,
                                        "quantity": quantity})
        request.session["cart_len"] = request.session["cart_len"] + quantity
        summarize_cart_addition(request, product.product_price, quantity)

        if request.user.is_authenticated and reflect_to_db:
            cart = Cart.objects.get(user_id=request.user.user_id)
            CartItem.objects.create(cart_id=cart, product_id=product, item_quantity=quantity)

    request.session.modified = True


def edit_cart(request, item_num, new_quantity):
    """
    Changes the quantity of item number
    item_num to new_quantity.
    """

    item = request.session["cart"][item_num]
    product = Product.objects.get(product_id=item["product_id"])

    old_quantity = item["quantity"]
    item["quantity"] = new_quantity

    if new_quantity < old_quantity:
        request.session["cart_len"] -= old_quantity - new_quantity
        adjust_cart_summary(request, product.product_price, old_quantity, new_quantity, True)
    elif new_quantity > old_quantity:
        request.session["cart_len"] += new_quantity - old_quantity
        adjust_cart_summary(request, product.product_price, old_quantity, new_quantity, False)

    request.session.modified = True

    if request.user.is_authenticated:
        cart_id = Cart.objects.get(user_id=request.user.user_id).cart_id
        cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product)
        cart_item.item_quantity = new_quantity
        cart_item.save()


def clear_cart(request, include_db):
    """
    Clears cart info from user session,
    If include_db is True, clears cart info
    from the database
    """

    del(request.session["cart"])
    del(request.session["cart_len"])
    del(request.session["cart_summary"])

    request.session.modified = True

    if include_db and request.user.is_authenticated:
        Cart.objects.get(user_id=request.user.user_id).delete()



def delete_item(request, item_num):
    """
    Deletes an item from the cart and removes
    its trace from the session and database.
    """

    product_id = request.session["cart"][item_num]["product_id"]
    product = Product.objects.get(product_id=product_id)

    edit_cart(request, item_num, new_quantity=0)

    del(request.session["cart"][item_num])

    if request.user.is_authenticated:
        cart_id = Cart.objects.get(user_id=request.user.user_id).cart_id
        CartItem.objects.get(cart_id=cart_id, product_id=product).delete()


def get_cart_info(request):
    """
    Returns an array of dictionaries with information
    pertaining to each item in the cart.
    """

    cart_info = []
    
    for i, item in enumerate(request.session["cart"]):
        product = Product.objects.get(product_id=item["product_id"])
        form = EditCartForm(initial={

            "new_item_quantity": item["quantity"],
            "new_item_quantity_input": item["quantity"]

        })

        form.fields['new_item_quantity'].widget.attrs['id'] = 'new-item-quantity' + '-' + str(i)
        form.fields['new_item_quantity_input'].widget.attrs['id'] = 'new-item-quantity-input' + '-' + str(i)


        cart_info.append({ 
            "number": i,
            "product": product,
            "item_quantity": item["quantity"],
            "form": form,
        })

    return cart_info


def summarize_cart_addition(request, product_price, quantity):
    """
    Adjusts cart details when an item is added.
    Will need to account for shipping / taxes.
    """

    request.session["cart_summary"]["subtotal"] += float(product_price * quantity)
    request.session["cart_summary"]["order_total"] = float(request.session["cart_summary"]["subtotal"] + \
                                                           request.session["cart_summary"]["shipping"] + \
                                                           request.session["cart_summary"]["sales_tax_estimate"])


def adjust_cart_summary(request, product_price, old_quantity, new_quantity, added):
    """
    Adjusts cart details when item quantity is changed.
    Will need to account for shipping / taxes.
    """

    if added == True:
        request.session["cart_summary"]["subtotal"] += float(product_price * (new_quantity - old_quantity))
    else:
        request.session["cart_summary"]["subtotal"] -= float(product_price * (old_quantity - new_quantity))

    request.session["cart_summary"]["order_total"] = float(request.session["cart_summary"]["subtotal"] + \
                                                           request.session["cart_summary"]["shipping"] + \
                                                           request.session["cart_summary"]["sales_tax_estimate"])


