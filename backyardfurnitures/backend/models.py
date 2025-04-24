from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(TimeStampedModel):
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.state} {self.postal_code}"

    class Meta:
        verbose_name_plural = "Addresses"


class Category(TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Material(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weather_resistance_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rating from 1-10 on weather resistance"
    )
    MAINTENANCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    maintenance_level = models.CharField(max_length=10, choices=MAINTENANCE_CHOICES)
    is_eco_friendly = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=7, decimal_places=2, help_text="Weight in kg")
    
    # Dimensions
    width = models.DecimalField(max_digits=7, decimal_places=2, help_text="Width in cm")
    height = models.DecimalField(max_digits=7, decimal_places=2, help_text="Height in cm")
    depth = models.DecimalField(max_digits=7, decimal_places=2, help_text="Depth in cm")
    
    assembly_required = models.BooleanField(default=True)
    weather_resistant = models.BooleanField(default=True)
    sku = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    warranty_months = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price


class ProductImage(TimeStampedModel):
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=1)

    def __str__(self):
        return f"Image for {self.product.name}"

    class Meta:
        ordering = ['display_order']


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50)
    color_code = models.CharField(max_length=10, help_text="Hex color code")
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='variants/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.color}"


class Customer(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    is_subscribed_to_newsletter = models.BooleanField(default=False)
    loyalty_points = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class CustomerAddress(TimeStampedModel):
    """Model linking customers with their addresses"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=20, choices=[
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
        ('both', 'Both Billing & Shipping')
    ])

    def __str__(self):
        return f"{self.customer}'s {self.get_address_type_display()} address"

    class Meta:
        verbose_name_plural = "Customer Addresses"


class Warehouse(TimeStampedModel):
    name = models.CharField(max_length=100)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    manager = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Inventory(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0, help_text="Items in customer carts or being processed")
    reorder_point = models.IntegerField(default=5)
    last_restock_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} at {self.warehouse.name}"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    @property
    def needs_restock(self):
        return self.available_quantity <= self.reorder_point

    class Meta:
        verbose_name_plural = "Inventories"


class Order(TimeStampedModel):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipping_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='billing_orders')
    shipping_method = models.CharField(max_length=50)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment info
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    total = models.DecimalField(max_digits=10, decimal_places=2)  # Price * quantity

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.order.order_number}"


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ProductSupplier(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='suppliers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    supplier_sku = models.CharField(max_length=50, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.IntegerField(default=7)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.product.name} from {self.supplier.name}"


class ProductReview(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Review for {self.product.name} by {self.customer}"
    
    class Meta:
        unique_together = ['product', 'customer']


class ReviewImage(TimeStampedModel):
   
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')
    
    def __str__(self):
        return f"Image for review #{self.review.id}"


class Promotion(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    discount_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.IntegerField(default=0, help_text="0 for unlimited")
    used_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and 
                (self.usage_limit == 0 or self.used_count < self.usage_limit))


class PromotionCategory(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.promotion.name} - {self.category.name}"
    
    class Meta:
        unique_together = ['promotion', 'category']


class PromotionProduct(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.promotion.name} - {self.product.name}"
    
    class Meta:
        unique_together = ['promotion', 'product']


class Wishlist(TimeStampedModel):
    """Model for customer wishlists"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='wishlists')
    name = models.CharField(max_length=100, default="My Wishlist")
    is_public = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.customer}'s {self.name}"


class WishlistItem(TimeStampedModel):
    """Model for individual items in a wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.product.name} in {self.wishlist}"

    class Meta:
        unique_together = ['wishlist', 'product', 'variant']


class Cart(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)  # For anonymous users
    
    def __str__(self):
        if self.customer:
            return f"Cart for {self.customer}"
        return f"Anonymous Cart {self.session_key}"


class CartItem(TimeStampedModel):

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart}"

    class Meta:
        unique_together = ['cart', 'product', 'variant']