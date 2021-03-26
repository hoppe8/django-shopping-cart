var url = $('#selection-form').attr('action');

document.getElementById("selection-form").addEventListener("change", function(event) {

   var target_id = event.target.id;
   var item = event.target.parentElement;
   var value = event.target.value;
   var item_num;
   var action = "edit";

   if (value === ""){
      return;
   }
   else if (value === "0"){
      action = "delete";
   }
   else if (Number(value) > 1000){
      event.target.value = 1000;
      value = 1000;
   }


   if (target_id.slice(0,17) === "new-item-quantity"){
      
      if (item.id.slice(0,13) === "item-dropdown"){
	 item_num = item.id.slice(14);
      }
      else {
         item_num = item.id.slice(11);
      }

      if (item.id.slice(0,13) === "item-dropdown" && value > 10) {
	 var change_element = document.getElementById("item-input-" + item_num);
	 item.classList.add("d-none");
	 change_element.classList.remove("d-none");
	 change_element.firstChild.select();
 
	 // changes need not be reflected to server
	 return;
      }
      else if (item.id.slice(0,10) === "item-input" && value < 11) {
	 var change_element = document.getElementById("item-dropdown-" + item_num);
	 change_element.firstChild.value = value;
	 change_element.classList.remove("d-none");
	 item.classList.add("d-none");
      }

      $.ajax({
         type: "POST",
         url: url,
         data: { 
            'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val(),
            selection: value,
            item_num: item_num,
	    action: action,
         },
         dataType: "json",
         success: function(result) {
	    if (result.action === "edit"){
               document.getElementById("subtotal").innerText = "$" +
			    result.new_cart_summary.subtotal.toFixed(2);
               document.getElementById("shipping").innerText = "$" +
			    result.new_cart_summary.shipping.toFixed(2);
               document.getElementById("sales-tax-estimate").innerText = "$" +
			    result.new_cart_summary.sales_tax_estimate.toFixed(2);
               document.getElementById("order-total").innerText = "$" +
			    result.new_cart_summary.order_total.toFixed(2);
	       document.getElementById("cart-len").innerText = "Cart (" +
			    result.new_cart_len + ")";
	    }
	    else if (result.action === "delete") {
	       location.reload(true);
	    }
         },
         error: function(result) {
            alert('error');
         }
      });

   }

});


