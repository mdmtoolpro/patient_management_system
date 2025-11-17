from django.db import models
from django.utils.translation import gettext_lazy as _
from patients.models import Patient, Visit
from users.models import User

class Medicine(models.Model):
    class Category(models.TextChoices):
        TABLET = 'TABLET', _('Tablet')
        CAPSULE = 'CAPSULE', _('Capsule')
        SYRUP = 'SYRUP', _('Syrup')
        INJECTION = 'INJECTION', _('Injection')
        OINTMENT = 'OINTMENT', _('Ointment')
        DROPS = 'DROPS', _('Drops')
        OTHER = 'OTHER', _('Other')
    
    medicine_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    manufacturer = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Stock management
    quantity_in_stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Medical information
    dosage_form = models.CharField(max_length=50, blank=True)
    strength = models.CharField(max_length=50, blank=True)
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        UNDER_REVIEW = 'UNDER_REVIEW', _('Under Review')
        READY = 'READY', _('Ready')
        DISPENSED = 'DISPENSED', _('Dispensed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    prescription_id = models.CharField(max_length=20, unique=True)
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='prescription')
    prescribed_by = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': User.Role.DOCTOR})
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    dosage = models.CharField(max_length=100)  # e.g., "500mg twice daily"
    duration = models.CharField(max_length=50)  # e.g., "7 days"
    instructions = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['prescription', 'medicine']

class DispenseCart(models.Model):
    pharmacist = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': User.Role.PHARMACIST},
        related_name='dispense_carts'
    )
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE)
    items = models.ManyToManyField(PrescriptionItem, through='CartItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.prescription.prescription_id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['pharmacist', 'prescription'],
                condition=models.Q(is_active=True),
                name='unique_active_cart_per_pharmacist_prescription'
            )
        ]

class CartItem(models.Model):
    cart = models.ForeignKey(DispenseCart, on_delete=models.CASCADE)
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE)
    quantity_to_dispense = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.prescription_item.medicine.name} in cart"

    class Meta:
        unique_together = ['cart', 'prescription_item']