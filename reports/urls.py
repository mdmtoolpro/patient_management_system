from django.urls import path
from . import views

urlpatterns = [
    path('financial/', views.financial_reports, name='financial_reports'),
    path('financial/export/', views.export_financial_report, name='export_financial_report'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]