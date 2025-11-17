from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from patients.models import Patient, Visit
from laboratory.models import LabTestRequest
from pharmacy.models import Prescription

class Payment(models.Model):
    class PaymentType(models.TextChoices):
        REGISTRATION = 'REGISTRATION', _('Registration Fee')
        LAB_TEST = 'LAB_TEST', _('Lab Test')
        MEDICINE = 'MEDICINE', _('Medicine')
        CONSULTATION = 'CONSULTATION', _('Consultation')
        OTHER = 'OTHER', _('Other')
    
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Cash')
        CARD = 'CARD', _('Card')
        MOBILE = 'MOBILE', _('Mobile Money')
        INSURANCE = 'INSURANCE', _('Insurance')
        PENDING = 'PENDING', _('Pending')
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
    
    payment_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, null=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Related objects
    lab_request = models.ForeignKey(LabTestRequest, on_delete=models.PROTECT, null=True, blank=True)
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT, null=True, blank=True)
    
    # System fields
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role__in': [User.Role.CASHIER, User.Role.RECEPTIONIST]})
    notes = models.TextField(blank=True)
    
    # Audit fields - NO ONE CAN DELETE PAYMENTS
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True)

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment tracking
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    
    # Soft delete protection
    is_active = models.BooleanField(default=True)

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Reference to original items
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, null=True, blank=True)
    lab_request = models.ForeignKey(LabTestRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['invoice', 'payment']),
        ]