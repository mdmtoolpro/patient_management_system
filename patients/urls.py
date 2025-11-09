from django.urls import path
from . import views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('register/', views.register_patient, name='register_patient'),
    path('<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('<str:patient_id>/visit/create/', views.create_visit, name='create_visit'),
    path('visit/<str:visit_id>/', views.visit_detail, name='visit_detail'),
]