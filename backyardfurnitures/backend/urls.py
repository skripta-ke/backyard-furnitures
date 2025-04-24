from django.urls import path
from . import views

urlpatterns = [
    # Authentication and Home Views
    path('signup/', views.signupview, name='signup'),
    path('', views.homeview, name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Inventory URLs
    path('inventory/', views.InventoryListView.as_view(), name='inventory_list'),
    path('inventory/<int:pk>/update/', views.InventoryUpdateView.as_view(), name='inventory_update'),
    path('inventory/<int:pk>/adjust/', views.adjust_inventory, name='adjust_inventory'),
    
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/status/', views.update_order_status, name='update_order_status'),
    
    # Customer URLs
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    
    # Frontend URLs
    path('shop/', views.shop, name='shop'),
    path('shop/product/<str:slug>/', views.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Customer account URLs
    path('my-account/', views.my_account, name='my_account'),
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # Additional URL for order items (referenced in OrderCreateView success_url)
    path('orders/<int:order_id>/items/', views.OrderCreateView.as_view(), name='order_items'),
]