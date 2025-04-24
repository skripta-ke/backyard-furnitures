from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Address, Category, Material, Product, ProductImage, ProductVariant,
    Customer, Order, OrderItem, Supplier, ProductReview, Promotion,
    Wishlist, WishlistItem, Cart, CartItem
)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('phone', 'birth_date', 'is_subscribed_to_newsletter')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'is_default')


class CustomerAddressForm(forms.Form):
    address_type = forms.ChoiceField(choices=[
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
        ('both', 'Both Billing & Shipping')
    ])
    address = forms.ModelChoiceField(queryset=None)
    
    def __init__(self, customer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter addresses by customer
        from .models import CustomerAddress
        existing_addresses = CustomerAddress.objects.filter(customer=customer).values_list('address', flat=True)
        self.fields['address'].queryset = Address.objects.filter(id__in=existing_addresses)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'parent', 'image', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude current category from parent choices to prevent circular references
        if self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(pk=self.instance.pk)


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('name', 'description', 'weather_resistance_rating', 'maintenance_level', 'is_eco_friendly')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'description', 'category', 'material', 'price', 'sale_price', 
                 'weight', 'width', 'height', 'depth', 'assembly_required', 
                 'weather_resistant', 'sku', 'is_active', 'featured', 'warranty_months')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ('image', 'alt_text', 'is_primary', 'display_order')


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ('color', 'color_code', 'price_adjustment', 'image')
        widgets = {
            'color_code': forms.TextInput(attrs={'type': 'color'}),
        }


class ProductImageFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        primary_count = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_primary', False):
                    primary_count += 1
        
        if primary_count > 1:
            raise forms.ValidationError("Only one image can be set as primary.")
        elif self.total_form_count() > 0 and primary_count == 0:
            raise forms.ValidationError("At least one image must be set as primary.")


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('name', 'contact_person', 'address', 'phone', 'email', 
                 'website', 'account_number', 'is_active', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


# class ProductSupplierForm(forms.ModelForm):
#     class Meta:
#         model = Supplier
#         fields = ('supplier', 'supplier_sku', 'cost', 'lead_time_days', 'is_primary')


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'shipping_method', 'tracking_number', 'notes', 'payment_status')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ('product', 'variant', 'quantity', 'price')


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ('rating', 'title', 'comment')
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


class ReviewImageForm(forms.Form):
    images = forms.ImageField()


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ('name', 'description', 'discount_type', 'discount_value', 'code', 
                 'start_date', 'end_date', 'is_active', 'minimum_order_value', 
                 'usage_limit')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class PromotionCategoryForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )


class PromotionProductForm(forms.Form):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )


class WishlistForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ('name', 'is_public')


class WishlistItemForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ('product', 'variant', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ('product', 'variant', 'quantity')


class CheckoutForm(forms.Form):
    # Customer information
    email = forms.EmailField()
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    phone = forms.CharField(max_length=20)
    
    # Shipping address
    shipping_address_line1 = forms.CharField(max_length=100)
    shipping_address_line2 = forms.CharField(max_length=100, required=False)
    shipping_city = forms.CharField(max_length=50)
    shipping_state = forms.CharField(max_length=50)
    shipping_postal_code = forms.CharField(max_length=20)
    shipping_country = forms.CharField(max_length=50)
    
    # Billing address
    same_as_shipping = forms.BooleanField(required=False, initial=True)
    billing_address_line1 = forms.CharField(max_length=100, required=False)
    billing_address_line2 = forms.CharField(max_length=100, required=False)
    billing_city = forms.CharField(max_length=50, required=False)
    billing_state = forms.CharField(max_length=50, required=False)
    billing_postal_code = forms.CharField(max_length=20, required=False)
    billing_country = forms.CharField(max_length=50, required=False)
    
    # Shipping method
    shipping_method = forms.ChoiceField(choices=[
        ('standard', 'Standard Delivery (3-5 business days)'),
        ('express', 'Express Delivery (1-2 business days)'),
        ('nextday', 'Next Day Delivery'),
    ])
    
    # Payment information
    payment_method = forms.ChoiceField(choices=[
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ])
    
    # Order notes
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    # Promotional code
    promo_code = forms.CharField(max_length=50, required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        same_as_shipping = cleaned_data.get('same_as_shipping')
        
        if not same_as_shipping:
            # Validate billing address fields if not same as shipping
            required_billing_fields = [
                'billing_address_line1', 'billing_city', 'billing_state', 
                'billing_postal_code', 'billing_country'
            ]
            
            for field in required_billing_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required when billing address is different')
        
        return cleaned_data


class ProductSearchForm(forms.Form):
    query = forms.CharField(required=False, label='Search')
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories"
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        required=False,
        empty_label="All Materials"
    )
    weather_resistant = forms.BooleanField(required=False)
    assembly_required = forms.BooleanField(required=False)
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Default'),
            ('price_asc', 'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('name_asc', 'Name: A to Z'),
            ('name_desc', 'Name: Z to A'),
            ('newest', 'Newest First'),
        ]
    )


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)


class InventoryForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(is_active=True))
    warehouse = forms.ModelChoiceField(queryset=None)  # Will be set in __init__
    adjustment_type = forms.ChoiceField(choices=[
        ('add', 'Add Stock'),
        ('remove', 'Remove Stock'),
        ('set', 'Set Exact Quantity'),
    ])
    quantity = forms.IntegerField(min_value=1)
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, **kwargs):
        from .models import Warehouse
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)