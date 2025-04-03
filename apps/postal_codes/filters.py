import django_filters
from .models import ZipZone, RemoteArea


class ZipZoneFilter(django_filters.FilterSet):
    """邮编分区过滤器"""
    provider_id = django_filters.NumberFilter(lookup_expr='exact')
    origin_zip = django_filters.CharFilter(lookup_expr='exact')
    zone_number = django_filters.NumberFilter(lookup_expr='exact')
    dest_zip = django_filters.CharFilter(method='filter_dest_zip')

    class Meta:
        model = ZipZone
        fields = ['provider_id', 'origin_zip', 'zone_number']
    
    def filter_dest_zip(self, queryset, name, value):
        """按目的邮编过滤"""
        return queryset.filter(
            dest_zip_start__lte=value,
            dest_zip_end__gte=value
        )


class RemoteAreaFilter(django_filters.FilterSet):
    """偏远地区过滤器"""
    provider_id = django_filters.NumberFilter(lookup_expr='exact')
    origin_zip = django_filters.CharFilter(lookup_expr='exact')
    remote_level = django_filters.NumberFilter(lookup_expr='exact')
    zip_code = django_filters.CharFilter(lookup_expr='exact')

    class Meta:
        model = RemoteArea
        fields = ['provider_id', 'origin_zip', 'remote_level', 'zip_code'] 