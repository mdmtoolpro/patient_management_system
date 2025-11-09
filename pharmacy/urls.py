from django.urls import path
from . import views

urlpatterns = [
    path('', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/<str:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    path('medicines/search/', views.medicine_search, name='medicine_search'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('dispense/<str:prescription_id>/', views.dispense_medicines, name='dispense_medicines'),
]