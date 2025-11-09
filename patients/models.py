from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Basic Information
    patient_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    emergency_contact = models.CharField(max_length=100, blank=True)
    
    # Medical Information
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    
    # System Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='registered_patients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient_id} - {self.first_name} {self.last_name}"

class Visit(models.Model):
    class Status(models.TextChoices):
        REGISTERED = 'REGISTERED', _('Registered')
        WITH_DOCTOR = 'WITH_DOCTOR', _('With Doctor')
        LAB_REQUESTED = 'LAB_REQUESTED', _('Lab Test Requested')
        LAB_IN_PROGRESS = 'LAB_IN_PROGRESS', _('Lab Test in Progress')
        LAB_COMPLETED = 'LAB_COMPLETED', _('Lab Test Completed')
        WITH_DOCTOR_REVIEW = 'WITH_DOCTOR_REVIEW', _('Doctor Reviewing Results')
        PRESCRIPTION_READY = 'PRESCRIPTION_READY', _('Prescription Ready')
        MEDICINE_DISPENSED = 'MEDICINE_DISPENSED', _('Medicine Dispensed')
        COMPLETED = 'COMPLETED', _('Completed')
    
    visit_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    assigned_doctor = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': User.Role.DOCTOR})
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED)
    symptoms = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)
    
    # Timestamps for tracking workflow
    registration_time = models.DateTimeField(auto_now_add=True)
    doctor_assigned_time = models.DateTimeField(null=True, blank=True)
    lab_request_time = models.DateTimeField(null=True, blank=True)
    lab_completion_time = models.DateTimeField(null=True, blank=True)
    prescription_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class MedicalExamination(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='examination')
    blood_pressure = models.CharField(max_length=20, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    examination_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)