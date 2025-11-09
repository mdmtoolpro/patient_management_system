from django.contrib import admin
from .models import FinancialReport, ReportSchedule

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_period', 'start_date', 'end_date', 'total_income', 'generated_by', 'created_at')
    list_filter = ('report_period', 'created_at')
    search_fields = ('title', 'generated_by__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_period', 'is_active', 'last_run', 'next_run')
    list_filter = ('report_period', 'is_active')
    readonly_fields = ('created_at',)