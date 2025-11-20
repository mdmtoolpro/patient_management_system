from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from users.models import User

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        LAB_REQUEST = 'LAB_REQUEST', _('Lab Test Request')
        LAB_RESULT = 'LAB_RESULT', _('Lab Result Ready')
        PRESCRIPTION = 'PRESCRIPTION', _('New Prescription')
        PAYMENT = 'PAYMENT', _('Payment Required')
        SYSTEM = 'SYSTEM', _('System Notification')
        PATIENT_ASSIGNMENT = 'PATIENT_ASSIGNMENT', _('Patient Assignment')  # New type
        CONSULTATION_READY = 'CONSULTATION_READY', _('Consultation Ready')  # New type
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_object_id = models.CharField(max_length=20, blank=True)
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient}"

class SystemConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key

# Import here to avoid circular imports
def create_lab_notification(sender, instance, created, **kwargs):
    if created:
        from users.models import User
        # Notify lab technicians
        lab_techs = User.objects.filter(role=User.Role.LAB_TECH, is_active=True)
        for tech in lab_techs:
            Notification.objects.create(
                recipient=tech,
                notification_type=Notification.NotificationType.LAB_REQUEST,
                title='New Lab Test Request',
                message=f'New {instance.test_type.name} requested for {instance.visit.patient}',
                related_object_id=instance.request_id
            )

def create_lab_result_notification(sender, instance, created, **kwargs):
    if created:
        # Notify the requesting doctor
        Notification.objects.create(
            recipient=instance.lab_request.requested_by,
            notification_type=Notification.NotificationType.LAB_RESULT,
            title='Lab Test Results Ready',
            message=f'Results for {instance.lab_request.test_type.name} are ready',
            related_object_id=instance.lab_request.request_id
        )

def create_prescription_notification(sender, instance, created, **kwargs):
    if created:
        from users.models import User
        # Notify pharmacists
        pharmacists = User.objects.filter(role=User.Role.PHARMACIST, is_active=True)
        for pharmacist in pharmacists:
            Notification.objects.create(
                recipient=pharmacist,
                notification_type=Notification.NotificationType.PRESCRIPTION,
                title='New Prescription',
                message=f'New prescription for {instance.visit.patient}',
                related_object_id=instance.prescription_id
            )

# We'll connect these signals in apps.py to avoid circular imports