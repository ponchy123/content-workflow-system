from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Surcharge, PeakSeasonSurcharge, BaseFee
from simple_history.admin import SimpleHistoryAdmin


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    list_display = ['product_id', 'product_name', 'provider_name', 'country', 'currency', 'status', 'created_at']
    list_filter = ['provider_name', 'country', 'status', 'effective_date', 'expiration_date']
    search_fields = ['product_name', 'provider_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['product_id', 'product_name', 'provider_name', 'description']
        }),
        ('计量单位', {
            'fields': ['dim_factor', 'dim_factor_unit', 'weight_unit', 'dim_unit']
        }),
        ('区域设置', {
            'fields': ['country', 'currency']
        }),
        ('有效期', {
            'fields': ['effective_date', 'expiration_date']
        }),
        ('状态', {
            'fields': ['status', 'enabled_start_date', 'enabled_end_date']
        }),
        ('系统信息', {
            'fields': ['created_at', 'updated_at', 'created_by', 'updated_by'],
            'classes': ['collapse']
        })
    ]


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    list_display = ['product', 'surcharge_type', 'sub_type', 'created_at']
    list_filter = ['product', 'surcharge_type']
    search_fields = ['product__product_name', 'surcharge_type']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(PeakSeasonSurcharge)
class PeakSeasonSurchargeAdmin(admin.ModelAdmin):
    list_display = ['product', 'surcharge_type', 'start_date', 'end_date', 'fee_amount', 'is_active_now', 'created_at']
    list_filter = ['product', 'surcharge_type']
    search_fields = ['product__product_name', 'surcharge_type']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def is_active_now(self, obj):
        """判断当前日期是否在附加费的生效期内"""
        from django.utils import timezone
        current_date = timezone.now().date()
        is_active = obj.start_date <= current_date <= obj.end_date and obj.fee_amount > 0
        return is_active
    
    is_active_now.short_description = '当前是否生效'
    is_active_now.boolean = True


@admin.register(BaseFee)
class BaseFeeAdmin(admin.ModelAdmin):
    list_display = ['product', 'weight', 'weight_unit', 'fee_type', 'created_at']
    list_filter = ['product', 'weight_unit', 'fee_type']
    search_fields = ['product__product_name', 'weight', 'fee_type']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by'] 