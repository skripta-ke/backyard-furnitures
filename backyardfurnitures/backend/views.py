from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import models


from .models import (
    Product, Category, Material, ProductImage, ProductVariant,
    Customer, Order, OrderItem, Inventory, Warehouse,
    ProductReview, Supplier, Promotion, Wishlist, WishlistItem,
    Cart, CartItem
)

def signupview(request):
    return render(request,'backend/auth/login.html')

def homeview(request):
    return render(request,'backend/hero.html')


from .forms import *

# Dashboard Views
class DashboardView( ListView):
    """Main dashboard view for the system"""
    template_name = 'backend/dashboard.html'
    permission_required = 'backend.view_product'
    model = Product
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        context['total_orders'] = Order.objects.count()
        context['recent_orders'] = Order.objects.all().order_by('-created_at')[:5]
        context['low_stock_items'] = (
            Inventory.objects
            .filter(quantity__lte=models.F('reorder_point'))
            .select_related('product', 'warehouse')
            .order_by('product__name')
        )
        return context


# Product Views
class ProductListView( ListView):
    """List all products"""
    model = Product
    template_name = 'backend/products/list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Filter by search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query)
            )
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by material
        material_id = self.request.GET.get('material')
        if material_id:
            queryset = queryset.filter(material_id=material_id)
            
        # Sort options
        sort = self.request.GET.get('sort', 'name')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['materials'] = Material.objects.all()
        return context


class ProductDetailView( DetailView):
    """Show product details"""
    model = Product
    template_name = 'backend/products/detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['images'] = product.images.all()
        context['variants'] = product.variants.all()
        context['inventory'] = (
            Inventory.objects
            .filter(product=product)
            .select_related('warehouse')
        )
        context['reviews'] = product.reviews.select_related('customer__user').all()
        context['avg_rating'] = (
            product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        )
        return context


class ProductCreateView( CreateView):
    """Create a new product"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/products/form.html'
    permission_required = 'backend.add_product'
    
    def get_success_url(self):
        messages.success(self.request, 'Product created successfully!')
        return reverse_lazy('product_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Product'
        context['button_text'] = 'Create Product'
        return context


class ProductUpdateView( UpdateView):
    """Update an existing product"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/products/form.html'
    permission_required = 'backend.change_product'
    
    def get_success_url(self):
        messages.success(self.request, 'Product updated successfully!')
        return reverse_lazy('product_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Product'
        context['button_text'] = 'Update Product'
        return context


class ProductDeleteView( DeleteView):
    """Delete a product"""
    model = Product
    template_name = 'backend/products/confirm_delete.html'
    permission_required = 'backend.delete_product'
    success_url = reverse_lazy('product_list')
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        messages.success(request, f'Product "{product.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Category Views
class CategoryListView( ListView):
    """List all categories"""
    model = Category
    template_name = 'backend/categories/list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(product_count=Count('products'))


class CategoryDetailView( DetailView):
    """Show category details and its products"""
    model = Category
    template_name = 'backend/categories/detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['products'] = Product.objects.filter(category=category)
        return context


class CategoryCreateView( CreateView):
    """Create a new category"""
    model = Category
    form_class = CategoryForm
    template_name = 'backend/categories/form.html'
    permission_required = 'backend.add_category'
    success_url = reverse_lazy('category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Category'
        context['button_text'] = 'Create Category'
        return context


class CategoryUpdateView( UpdateView):
    """Update an existing category"""
    model = Category
    form_class = CategoryForm
    template_name = 'backend/categories/form.html'
    permission_required = 'backend.change_category'
    
    def get_success_url(self):
        return reverse_lazy('category_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Category'
        context['button_text'] = 'Update Category'
        return context


class CategoryDeleteView( DeleteView):
    """Delete a category"""
    model = Category
    template_name = 'backend/categories/confirm_delete.html'
    permission_required = 'backend.delete_category'
    success_url = reverse_lazy('category_list')


# Inventory Views
class InventoryListView( ListView):
    """List inventory across all warehouses"""
    model = Inventory
    template_name = 'backend/inventory/list.html'
    context_object_name = 'inventory_items'
    permission_required = 'backend.view_inventory'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Inventory.objects.select_related('product', 'warehouse')
        
        # Filter by warehouse
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Filter by stock status
        stock_status = self.request.GET.get('status')
        if stock_status == 'low':
            queryset = queryset.filter(quantity__lte=models.F('reorder_point'))
        elif stock_status == 'out':
            queryset = queryset.filter(quantity=0)
        
        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(product__sku__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.all()
        return context


class InventoryUpdateView( UpdateView):
    """Update inventory quantity"""
    model = Inventory
    form_class = InventoryForm
    template_name = 'backend/inventory/form.html'
    permission_required = 'backend.change_inventory'
    success_url = reverse_lazy('inventory_list')



def adjust_inventory(request, pk):
    """Add or subtract from inventory"""
    inventory = get_object_or_404(Inventory, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        quantity = int(request.POST.get('quantity', 0))
        
        if action == 'add':
            inventory.quantity += quantity
            inventory.last_restock_date = timezone.now().date()
            messages.success(request, f'Added {quantity} items to inventory.')
        elif action == 'subtract':
            if quantity > inventory.quantity:
                messages.error(request, 'Cannot remove more than available quantity.')
            else:
                inventory.quantity -= quantity
                messages.success(request, f'Removed {quantity} items from inventory.')
        
        inventory.save()
        return redirect('inventory_detail', pk=inventory.pk)
    
    return render(request, 'backend/inventory/adjust.html', {
        'inventory': inventory
    })


# Order Views
class OrderListView( ListView):
    """List all orders"""
    model = Order
    template_name = 'backend/orders/list.html'
    context_object_name = 'orders'
    permission_required = 'backend.view_order'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Order.objects.select_related('customer__user')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        
        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer__user__first_name__icontains=search) |
                Q(customer__user__last_name__icontains=search) |
                Q(customer__user__email__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class OrderDetailView( DetailView):
    """Show order details"""
    model = Order
    template_name = 'backend/orders/detail.html'
    context_object_name = 'order'
    permission_required = 'backend.view_order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['items'] = order.items.select_related('product').all()
        context['status_history'] = order.status_history.all().order_by('-timestamp')
        return context


class OrderCreateView( CreateView):
    """Create a new order"""
    model = Order
    form_class = OrderForm
    template_name = 'backend/orders/form.html'
    permission_required = 'backend.add_order'
    
    def get_success_url(self):
        return reverse('order_items', kwargs={'order_id': self.object.id})


class OrderUpdateView( UpdateView):
    """Update order details"""
    model = Order
    form_class = OrderForm
    template_name = 'backend/orders/form.html'
    permission_required = 'backend.change_order'
    
    def get_success_url(self):
        return reverse('order_detail', kwargs={'pk': self.object.pk})



def update_order_status(request, pk):
    """Update the status of an order"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status != order.status:
            order.status = new_status
            order.save()
            
            # Create status history entry
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user
            )
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
        
        return redirect('order_detail', pk=order.pk)
    
    return render(request, 'backend/orders/update_status.html', {
        'order': order
    })


# Customer Views
class CustomerListView( ListView):
    """List all customers"""
    model = Customer
    template_name = 'backend/customers/list.html'
    context_object_name = 'customers'
    permission_required = 'backend.view_customer'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Customer.objects.select_related('user')
        
        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(phone__icontains=search)
            )
            
        return queryset.order_by('user__last_name', 'user__first_name')


class CustomerDetailView( DetailView):
    """Show customer details, orders, and reviews"""
    model = Customer
    template_name = 'backend/customers/detail.html'
    context_object_name = 'customer'
    permission_required = 'backend.view_customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        context['orders'] = Order.objects.filter(customer=customer).order_by('-created_at')
        context['reviews'] = ProductReview.objects.filter(customer=customer).select_related('product')
        context['addresses'] = customer.addresses.all()
        
        # Order statistics
        order_count = context['orders'].count()
        context['order_count'] = order_count
        
        if order_count > 0:
            context['total_spent'] = context['orders'].aggregate(Sum('total'))['total__sum']
            context['avg_order_value'] = context['total_spent'] / order_count
        
        return context


# Frontend Views (for customers)
def home(request):
    """Homepage view showing featured products"""
    featured_products = Product.objects.filter(featured=True, is_active=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    current_promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )[:3]
    
    return render(request, 'backend/frontend/home.html', {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'promotions': current_promotions,
    })


def shop(request):
    """Product listing page with filters"""
    products = Product.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Filter by material
    material_id = request.GET.get('material')
    if material_id:
        products = products.filter(material_id=material_id)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
        
    # Sort options
    sort = request.GET.get('sort', 'default')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'popular':
        products = products.annotate(order_count=Count('orderitem')).order_by('-order_count')
    elif sort == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    categories = Category.objects.filter(is_active=True)
    materials = Material.objects.all()
    
    return render(request, 'backend/frontend/shop.html', {
        'products': products,
        'categories': categories,
        'materials': materials,
    })


def product_detail(request, slug):
    """Product detail page for customers"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get related products (same category)
    related_products = (
        Product.objects
        .filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .order_by('?')[:4]
    )
    
    # Check if product is in user's wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            wishlists = Wishlist.objects.filter(customer=customer)
            if WishlistItem.objects.filter(wishlist__in=wishlists, product=product).exists():
                in_wishlist = True
        except Customer.DoesNotExist:
            pass
    
    # Reviews with pagination
    reviews = product.reviews.select_related('customer__user').order_by('-created_at')
    review_paginator = Paginator(reviews, 5)
    review_page = request.GET.get('review_page')
    reviews = review_paginator.get_page(review_page)
    
    # Review form for authenticated users
    review_form = None
    if request.user.is_authenticated:
        review_form = ProductReviewForm()
    
    return render(request, 'backend/frontend/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
        'review_form': review_form,
    })



def add_to_cart(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))
        variant_id = request.POST.get('variant')
        
        # Get or create cart
        try:
            customer = Customer.objects.get(user=request.user)
            cart, created = Cart.objects.get_or_create(customer=customer)
        except Customer.DoesNotExist:
            messages.error(request, 'Customer profile not found.')
            return redirect('product_detail', slug=product.slug)
        
        # Get variant if specified
        variant = None
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        
        # Check inventory
        try:
            inventory = Inventory.objects.filter(product=product).first()
            if inventory and inventory.available_quantity < quantity:
                messages.error(request, f'Sorry, only {inventory.available_quantity} items available.')
                return redirect('product_detail', slug=product.slug)
        except Inventory.DoesNotExist:
            pass
        
        # Add to cart or update quantity
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f'Added {quantity} {product.name} to your cart.')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('cart')
    
    return redirect('shop')



def cart(request):
    """View shopping cart"""
    try:
        customer = Customer.objects.get(user=request.user)
        cart = Cart.objects.filter(customer=customer).first()
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('shop')
    
    if not cart:
        cart = Cart.objects.create(customer=customer)
    
    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
    
    # Calculate totals
    subtotal = sum(item.product.sale_price * item.quantity if item.product.sale_price 
                   else item.product.price * item.quantity for item in cart_items)
    
    # Get applicable promotions
    active_promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
        minimum_order_value__lte=subtotal
    )
    
    # Find best discount
    best_discount = 0
    best_promotion = None
    
    for promotion in active_promotions:
        if promotion.discount_type == 'percentage':
            discount = subtotal * (promotion.discount_value / 100)
        else:
            discount = promotion.discount_value
            
        if discount > best_discount:
            best_discount = discount
            best_promotion = promotion
    
    # Calculate final totals
    discount = best_discount
    shipping = 0  # Simplified - would normally calculate based on location, weight, etc.
    tax = subtotal * 0.07  # Simplified tax calculation (7%)
    total = subtotal - discount + shipping + tax
    
    return render(request, 'backend/frontend/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'promotion': best_promotion,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    })



def checkout(request):
    """Checkout process"""
    try:
        customer = Customer.objects.get(user=request.user)
        cart = Cart.objects.filter(customer=customer).first()
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('shop')
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    
    # Get customer addresses
    addresses = customer.addresses.all()
    
    if request.method == 'POST':
        # Process checkout form submission
        shipping_address_id = request.POST.get('shipping_address')
        billing_address_id = request.POST.get('billing_address')
        payment_method = request.POST.get('payment_method')
        shipping_method = request.POST.get('shipping_method')
        
        # Validate form data
        if not all([shipping_address_id, billing_address_id, payment_method, shipping_method]):
            messages.error(request, 'Please fill all required fields.')
            return redirect('checkout')
        
        # Get addresses
        shipping_address = get_object_or_404(Address, id=shipping_address_id)
        billing_address = get_object_or_404(Address, id=billing_address_id)
        
        # Calculate totals (simplified)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        subtotal = sum(item.product.sale_price * item.quantity if item.product.sale_price 
                      else item.product.price * item.quantity for item in cart_items)
        
        shipping_cost = 0
        if shipping_method == 'standard':
            shipping_cost = 10
        elif shipping_method == 'express':
            shipping_cost = 25
            
        tax = subtotal * 0.07  # 7% tax
        total = subtotal + shipping_cost + tax
        
        # Create order
        order = Order.objects.create(
            customer=customer,
            shipping_address=shipping_address,
            billing_address=billing_address,
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            subtotal=subtotal,
            tax=tax,
            total=total,
            payment_method=payment_method,
        )
        
        # Create order items
        for cart_item in cart_items:
            price = cart_item.product.sale_price if cart_item.product.sale_price else cart_item.product.price
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=price,
                total=price * cart_item.quantity
            )
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, f'Order placed successfully! Your order number is {order.order_number}')
        return redirect('order_confirmation', order_id=order.id)
    
    return render(request, 'backend/frontend/checkout.html', {
        'customer': customer,
        'addresses': addresses,
    })



def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    order_items = order.items.all().select_related('product')
    
    return render(request, 'backend/frontend/order_confirmation.html', {
        'order': order,
        'order_items': order_items,
    })



def my_account(request):
    """Customer account dashboard"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('home')
    
    orders = Order.objects.filter(customer=customer).order_by('-created_at')[:5]
    addresses = customer.addresses.all()
    wishlists = Wishlist.objects.filter(customer=customer)
    
    return render(request, 'backend/frontend/my_account.html', {
        'customer': customer,
        'orders': orders,
        'addresses': addresses,
        'wishlists': wishlists,
    })



def my_orders(request):
    """List customer orders"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('home')
    
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    return render(request, 'backend/frontend/my_orders.html', {
        'orders': orders,
    })


