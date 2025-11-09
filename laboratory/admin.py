from django.contrib import admin
from .models import LabTestType, LabTestRequest, TestResult

@admin.register(LabTestType)
class LabTestTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'turnaround_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(LabTestRequest)
class LabTestRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'visit', 'test_type', 'requested_by', 'status', 'requested_at')
    list_filter = ('status', 'test_type', 'requested_at')
    search_fields = ('request_id', 'visit__visit_id', 'patient__first_name')
    readonly_fields = ('requested_at', 'payment_completed_at', 'started_at', 'completed_at', 'doctor_reviewed_at')

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('lab_request', 'performed_by', 'created_at')
    readonly_fields = ('created_at',)