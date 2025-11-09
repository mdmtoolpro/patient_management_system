from django.db import models
from django.utils.translation import gettext_lazy as _
from patients.models import Patient
from billing.models import Payment
from users.models import User
from django.utils import timezone

class FinancialReport(models.Model):
    """Financial reports for the clinic"""
    REPORT_PERIOD_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'), 
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
        ('CUSTOM', 'Custom Range'),
    ]
    
    title = models.CharField(max_length=200)
    report_period = models.CharField(max_length=20, choices=REPORT_PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Financial data
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    registration_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lab_test_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pharmacy_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Statistics
    total_patients = models.IntegerField(default=0)
    new_patients = models.IntegerField(default=0)
    total_visits = models.IntegerField(default=0)
    total_lab_tests = models.IntegerField(default=0)
    total_prescriptions = models.IntegerField(default=0)
    
    # Report file
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_report_period_display()}"
    
    class Meta:
        ordering = ['-created_at']

class ReportSchedule(models.Model):
    """Schedule for automatic report generation"""
    name = models.CharField(max_length=100)
    report_period = models.CharField(max_length=20, choices=FinancialReport.REPORT_PERIOD_CHOICES)
    is_active = models.BooleanField(default=True)
    recipients = models.TextField(help_text="Comma-separated email addresses")
    
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name