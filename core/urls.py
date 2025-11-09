from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Change to plural "accounts" to match Django's default expectation
    path('accounts/login/', views.custom_login, name='custom_login'),
    path('accounts/logout/', views.custom_logout, name='custom_logout'),
    path('accounts/signup/', views.custom_signup, name='custom_signup'),
    
    # Other URLs
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]