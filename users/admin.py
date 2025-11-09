from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StaffProfile, Role

class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name_plural = 'Staff Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (StaffProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    fieldsets = UserAdmin.fieldsets + (
        ('Clinic Information', {
            'fields': ('role', 'phone_number', 'license_number', 'specialization')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Clinic Information', {
            'fields': ('role', 'phone_number', 'license_number', 'specialization')
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'hire_date', 'experience_years')
    list_filter = ('department', 'hire_date')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(User, CustomUserAdmin)