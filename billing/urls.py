from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('lab/<str:request_id>/', views.process_lab_payment, name='process_lab_payment'),
    path('medicine/<str:prescription_id>/', views.process_medicine_payment, name='process_medicine_payment'),
    path('pending-medicine/', views.pending_medicine_payments, name='pending_medicine_payments'),
    path('<str:payment_id>/', views.payment_detail, name='payment_detail'),  
]