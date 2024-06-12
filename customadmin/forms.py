from django import forms
from store.models import Product, ProductGallery, Variation

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'slug', 'description', 'price', 'images', 'stock', 'is_available', 'category']
        widgets = {
            'is_available': forms.CheckboxInput(),
        }

class ProductGalleryForm(forms.ModelForm):
    class Meta:
        model = ProductGallery
        fields = ['image']

class VariationForm(forms.ModelForm):
    class Meta:
        model = Variation
        fields = ['variation_category', 'variation_value', 'is_active']