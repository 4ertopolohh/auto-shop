from django.urls import path
from . import views
urlpatterns = [path('bootstrap/', views.bootstrap), path('products/', views.products), path('products/<slug:slug>/', views.products), path('delivery/', views.delivery_options), path('checkout/', views.checkout), path('orders/<uuid:order_id>/payment/', views.payment)]
