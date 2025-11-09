from django.contrib import admin
from .models import Notification, SystemConfig  # Remove ClinicSettings if it's here

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title')
    readonly_fields = ('created_at', 'read_at')

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_active', 'created_at')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')

