from django.contrib import admin
from .models import Medicine, Prescription, PrescriptionItem, DispenseCart, CartItem

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('medicine_id', 'name', 'generic_name', 'category', 'quantity_in_stock', 'unit_price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('medicine_id', 'name', 'generic_name')
    readonly_fields = ('created_at',)

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1
    readonly_fields = ('total_price',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_id', 'visit', 'prescribed_by', 'status', 'total_cost', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('prescription_id', 'visit__visit_id')
    inlines = [PrescriptionItemInline]
    readonly_fields = ('created_at', 'reviewed_at', 'dispensed_at')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('subtotal',)

@admin.register(DispenseCart)
class DispenseCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'pharmacist', 'prescription', 'total_amount', 'is_active', 'created_at')
    inlines = [CartItemInline]
    readonly_fields = ('created_at',)