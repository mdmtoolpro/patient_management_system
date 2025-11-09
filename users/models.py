from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrator')
        DOCTOR = 'DOCTOR', _('Doctor')
        NURSE = 'NURSE', _('Nurse')
        LAB_TECH = 'LAB_TECH', _('Lab Technician')
        RECEPTIONIST = 'RECEPTIONIST', _('Receptionist')
        PHARMACIST = 'PHARMACIST', _('Pharmacist')
        CASHIER = 'CASHIER', _('Cashier')
    
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RECEPTIONIST)
    phone_number = models.CharField(max_length=15, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR
    
    @property
    def is_nurse(self):
        return self.role == self.Role.NURSE
    
    @property
    def is_lab_tech(self):
        return self.role == self.Role.LAB_TECH
    
    @property
    def is_receptionist(self):
        return self.role == self.Role.RECEPTIONIST
    
    @property
    def is_pharmacist(self):
        return self.role == self.Role.PHARMACIST
    
    @property
    def is_cashier(self):
        return self.role == self.Role.CASHIER
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

class StaffProfile(models.Model):
    """Extended profile for staff members"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    
    # Professional Information
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    
    # Employment Information
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Documents
    profile_picture = models.ImageField(upload_to='staff_profiles/', null=True, blank=True)
    id_document = models.FileField(upload_to='staff_documents/', null=True, blank=True)
    cv_document = models.FileField(upload_to='staff_documents/', null=True, blank=True)
    
    # Additional Information
    bio = models.TextField(blank=True)
    qualifications = models.TextField(blank=True)
    experience_years = models.IntegerField(default=0)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile - {self.user.get_full_name()}"
    
    class Meta:
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"

class Role(models.Model):
    """System roles with specific permissions"""
    name = models.CharField(max_length=20, choices=User.Role.choices, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField('auth.Permission', blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"