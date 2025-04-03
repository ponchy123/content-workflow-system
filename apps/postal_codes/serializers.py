from rest_framework import serializers
from .models import ZipZone, RemoteArea
from apps.core.serializers import ServiceProviderSerializer
from apps.core.models import ServiceProvider


class ZipZoneSerializer(serializers.ModelSerializer):
    """
    邮编分区序列化器
    """
    provider = ServiceProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        source='provider',
        queryset=ServiceProvider.objects.filter(is_deleted=False),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ZipZone
        fields = ['id', 'provider', 'provider_id', 'origin_zip', 'dest_zip_start', 'dest_zip_end', 
                 'zone_number', 'created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate(self, attrs):
        """检查目的邮编范围的有效性"""
        if attrs.get('dest_zip_start') and attrs.get('dest_zip_end'):
            if attrs['dest_zip_start'] > attrs['dest_zip_end']:
                raise serializers.ValidationError("目的邮编起始值不能大于结束值")
                
        if attrs.get('zone_number'):
            if attrs['zone_number'] < 1 or attrs['zone_number'] > 8:
                raise serializers.ValidationError("分区号必须在1-8之间")
        
        return attrs


class RemoteAreaSerializer(serializers.ModelSerializer):
    """
    偏远地区序列化器
    """
    provider = ServiceProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        source='provider',
        queryset=ServiceProvider.objects.filter(is_deleted=False),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = RemoteArea
        fields = ['id', 'provider', 'provider_id', 'origin_zip', 'zip_code', 'remote_level',
                 'created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted']
        read_only_fields = ['created_at', 'updated_at']
        
    def validate_remote_level(self, value):
        """验证偏远等级"""
        if not value:
            raise serializers.ValidationError("偏远等级不能为空")
        return value 