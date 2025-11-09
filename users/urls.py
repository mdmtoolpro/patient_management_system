from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('staff/', views.staff_list, name='staff_list'),
]