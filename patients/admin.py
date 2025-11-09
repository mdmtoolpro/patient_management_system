from django.contrib import admin
from .models import Patient, Visit, MedicalExamination

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'first_name', 'last_name', 'phone', 'gender', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('patient_id', 'first_name', 'last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('visit_id', 'patient', 'assigned_doctor', 'status', 'registration_time')
    list_filter = ('status', 'assigned_doctor', 'registration_time')
    search_fields = ('visit_id', 'patient__patient_id', 'patient__first_name')
    readonly_fields = ('registration_time', 'doctor_assigned_time', 'lab_request_time', 'lab_completion_time', 'prescription_time', 'completion_time')

@admin.register(MedicalExamination)
class MedicalExaminationAdmin(admin.ModelAdmin):
    list_display = ('visit', 'blood_pressure', 'temperature', 'created_by', 'created_at')
    readonly_fields = ('created_at',)