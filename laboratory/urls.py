from django.urls import path
from . import views

urlpatterns = [
    path('', views.lab_requests_list, name='lab_requests_list'),
    path('request/<str:visit_id>/', views.request_lab_test, name='request_lab_test'),
    path('process/<str:request_id>/', views.process_lab_test, name='process_lab_test'),
    path('payment/<str:request_id>/', views.process_lab_payment, name='process_lab_payment'),  
    path('assign/<str:request_id>/', views.assign_lab_request, name='assign_lab_request'),
    path('result/<str:request_id>/', views.lab_result_detail, name='lab_result_detail'),  
]