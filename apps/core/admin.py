from django.contrib import admin
from .models import ServiceProvider, SystemConfig


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'contact_phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'code', 'contact_person']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'status')
        }),
        ('联系信息', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('API配置', {
            'fields': ('api_key', 'api_secret', 'config'),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'description', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['key', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('key', 'value', 'description', 'is_public')
        }),
        ('其他信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 