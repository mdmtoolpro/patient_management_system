from django.db import models
from django.utils.translation import gettext_lazy as _
from patients.models import Patient, Visit
from users.models import User

class LabTestType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    turnaround_time = models.IntegerField(help_text="Hours")  # Added turnaround time
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class LabTestRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', _('Requested')
        PAYMENT_PENDING = 'PAYMENT_PENDING', _('Payment Pending')
        PAYMENT_COMPLETED = 'PAYMENT_COMPLETED', _('Payment Completed')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    request_id = models.CharField(max_length=20, unique=True)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='lab_requests')
    test_type = models.ForeignKey(LabTestType, on_delete=models.PROTECT)
    
    # Fixed: Added unique related_name to avoid clash
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        limit_choices_to={'role': User.Role.DOCTOR},
        related_name='requested_lab_tests'  # Unique related_name
    )
    
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        limit_choices_to={'role': User.Role.LAB_TECH}, 
        null=True, 
        blank=True,
        related_name='assigned_lab_tests'  # Unique related_name
    )
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    doctor_notes = models.TextField(blank=True)
    lab_notes = models.TextField(blank=True)
    
    # Results
    result_value = models.CharField(max_length=100, blank=True)
    normal_range = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    is_abnormal = models.BooleanField(default=False)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    doctor_reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.request_id} - {self.test_type.name}"

class TestResult(models.Model):
    lab_request = models.OneToOneField(LabTestRequest, on_delete=models.CASCADE, related_name='result')
    result_data = models.TextField(blank=True)  
    findings = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    
    # Fixed: Added unique related_name
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        limit_choices_to={'role': User.Role.LAB_TECH},
        related_name='performed_tests'  # Unique related_name
    )
    
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='verified_tests'  # Unique related_name
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Results for {self.lab_request.request_id}"