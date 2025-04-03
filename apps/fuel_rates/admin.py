from django.contrib import admin
from django.utils import timezone
from .models import FuelRate, FuelRateHistory


@admin.register(FuelRate)
class FuelRateAdmin(admin.ModelAdmin):
    list_display = ['rate_id', 'provider', 'rate_value', 'effective_date', 'expiration_date', 'status', 'is_active', 'created_at']
    list_filter = ['provider', 'status', 'effective_date']
    search_fields = ['rate_id', 'provider__name']
    ordering = ['-effective_date', '-created_at']
    readonly_fields = ['rate_id', 'created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('rate_id', 'provider', 'rate_value', 'status')
        }),
        ('有效期', {
            'fields': ('effective_date', 'expiration_date')
        }),
        ('其他信息', {
            'fields': ('description', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active(self, obj):
        """
        判断费率是否在有效期内
        """
        now = timezone.now().date()
        return obj.effective_date <= now and (obj.expiration_date is None or obj.expiration_date > now)
    is_active.boolean = True
    is_active.short_description = '是否生效'

    def save_model(self, request, obj, form, change):
        """
        保存时自动创建历史记录
        """
        if change and 'rate_value' in form.changed_data:
            old_rate = FuelRate.objects.get(rate_id=obj.rate_id).rate_value
            super().save_model(request, obj, form, change)
            FuelRateHistory.objects.create(
                fuel_rate=obj,
                old_rate=old_rate,
                new_rate=obj.rate_value,
                change_type='MANUAL',
                change_reason='后台修改',
                operator=request.user
            )
        else:
            super().save_model(request, obj, form, change)
            if not change:  # 新建时创建历史记录
                FuelRateHistory.objects.create(
                    fuel_rate=obj,
                    old_rate=0,
                    new_rate=obj.rate_value,
                    change_type='MANUAL',
                    change_reason='后台新建',
                    operator=request.user
                )


@admin.register(FuelRateHistory)
class FuelRateHistoryAdmin(admin.ModelAdmin):
    list_display = ['fuel_rate', 'old_rate', 'new_rate', 'change_type', 'operator', 'created_at']
    list_filter = ['change_type', 'created_at', 'fuel_rate']
    search_fields = ['fuel_rate__rate_id', 'change_reason', 'operator__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('变更信息', {
            'fields': ('fuel_rate', 'old_rate', 'new_rate', 'change_type')
        }),
        ('操作信息', {
            'fields': ('operator', 'change_reason')
        }),
        ('其他信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """禁止手动添加历史记录"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁止修改历史记录"""
        return False
