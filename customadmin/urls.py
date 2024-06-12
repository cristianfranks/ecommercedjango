from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='admin_login'),
    path('productos', views.admin_productos, name='admin_productos'),
    path('create/', views.product_create, name='product_create'),
    path('update/<int:pk>/', views.product_update, name='product_update'),
    path('delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('ordenes', views.admin_orders, name='admin_orders'),
    path('complete_order/<int:pk>/', views.complete_order, name='complete_order'),
    path('product_gallery_delete/<int:pk>/', views.product_gallery_delete, name='product_gallery_delete'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard', views.dashboard, name='admin_dashboard'),
    path('order/<int:order_id>/', views.view_order, name='view_order'),

    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/download/', views.download_orders_excel, name='download_orders_excel'),

]
