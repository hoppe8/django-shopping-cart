from django import forms
from django.forms.widgets import Select


class AddToCartForm(forms.Form):
    product_choices = forms.ChoiceField(choices=[], \
            widget=forms.Select(attrs={"class": "form-control custom-select"}))

    item_quantity = forms.IntegerField(min_value=1, max_value=1000, 
            widget=forms.NumberInput(attrs={"class": "form-control", "required": "required"}))


class EditCartForm(forms.Form):
    new_item_quantity = forms.ChoiceField(choices=[(1, '1'),
                                                   (2, '2'),
                                                   (3, '3'),
                                                   (4, '4'),
                                                   (5, '5'),
                                                   (6, '6'),
                                                   (7, '7'),
                                                   (8, '8'),
                                                   (9, '9'),
                                                   (10, '10'),
                                                   (11, '11+'),],
                                                   widget=forms.Select(attrs= \
                                                           {"class": "form-control custom-select", \
                                                           "style": "width:60px"}))

    new_item_quantity_input = forms.IntegerField(min_value=0, max_value=1000,
            widget=forms.NumberInput(attrs={"class": "form-control", "style": "width:60px"}))

