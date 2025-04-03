from django.contrib import admin
from .models import ZipZone, RemoteArea


@admin.register(ZipZone)
class ZipZoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider', 'origin_zip', 'dest_zip_start', 'dest_zip_end', 'zone_number']
    list_filter = ['zone_number', 'provider']
    search_fields = ['origin_zip', 'dest_zip_start', 'dest_zip_end']
    ordering = ['zone_number', 'origin_zip']


@admin.register(RemoteArea)
class RemoteAreaAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider', 'origin_zip', 'zip_code', 'remote_level']
    list_filter = ['remote_level', 'provider']
    search_fields = ['origin_zip', 'zip_code']
    ordering = ['remote_level', 'origin_zip'] 