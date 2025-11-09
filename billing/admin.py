from django.contrib import admin
from .models import Payment, Invoice, InvoiceItem

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'patient', 'payment_type', 'payment_method', 'amount', 'status', 'processed_by', 'created_at')
    list_filter = ('payment_type', 'payment_method', 'status', 'created_at')
    search_fields = ('payment_id', 'patient__patient_id', 'receipt_number')
    readonly_fields = ('created_at', 'completed_at')
    
    # Prevent deletion of completed payments
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == Payment.Status.COMPLETED:
            return False
        return super().has_delete_permission(request, obj)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('total_price',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'patient', 'total_amount', 'final_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('invoice_number', 'patient__patient_id')
    inlines = [InvoiceItemInline]
    readonly_fields = ('created_at',)
    
    # Soft delete protection
    def has_delete_permission(self, request, obj=None):
        return False