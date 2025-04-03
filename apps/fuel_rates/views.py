from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import FuelRate, FuelRateHistory
from .serializers import FuelRateSerializer, FuelRateHistorySerializer
from apps.core.views import BaseViewSet
from apps.core.responses import APIResponse
from apps.core.decorators import db_connection_retry


class FuelRateViewSet(BaseViewSet):
    """
    燃油费率视图集
    
    list:
    获取燃油费率列表，默认只返回当前有效的费率
    
    create:
    创建新的燃油费率，自动生成费率ID
    
    retrieve:
    获取单个燃油费率详情
    
    update:
    更新燃油费率信息，同时创建变更历史记录
    
    partial_update:
    部分更新燃油费率信息
    
    destroy:
    删除燃油费率
    """
    queryset = FuelRate.objects.all()
    serializer_class = FuelRateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['provider_id', 'status']
    search_fields = ['provider__name', 'rate_id']
    ordering_fields = ['rate_value', 'effective_date', 'created_at']
    lookup_field = 'rate_id'
    model_name = '燃油费率'

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_queryset(self):
        queryset = super().get_queryset()
        # 处理有效期查询
        if self.request.query_params.get('current_only') == 'true':
            now = timezone.now().date()
            queryset = queryset.filter(
                Q(effective_date__lte=now) &
                (Q(expiration_date__gt=now) | Q(expiration_date=None)) &
                Q(status=True)
            )
        return queryset

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_create(self, serializer):
        """
        创建燃油费率时，同时创建历史记录
        """
        fuel_rate = serializer.save()
        FuelRateHistory.objects.create(
            fuel_rate=fuel_rate,
            old_rate=0,
            new_rate=fuel_rate.rate_value,
            operator=self.request.user,
            change_type='MANUAL',
            change_reason='初始创建'
        )

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_update(self, serializer):
        """
        更新燃油费率时，如果费率值变化，创建历史记录
        """
        instance = self.get_object()
        old_rate = instance.rate_value
        fuel_rate = serializer.save()
        
        # 只有费率值变化时才创建历史记录
        if old_rate != fuel_rate.rate_value:
            FuelRateHistory.objects.create(
                fuel_rate=fuel_rate,
                old_rate=old_rate,
                new_rate=fuel_rate.rate_value,
                operator=self.request.user,
                change_type='MANUAL',
                change_reason=self.request.data.get('change_reason', '费率更新')
            )

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_destroy(self, instance):
        """
        逻辑删除
        """
        instance.status = False
        instance.save()
        FuelRateHistory.objects.create(
            fuel_rate=instance,
            old_rate=instance.rate_value,
            new_rate=instance.rate_value,
            operator=self.request.user,
            change_type='MANUAL',
            change_reason='费率删除'
        )
        return self.success_response(message=f'{self.model_name}已删除')

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, rate_id=None):
        """
        切换燃油费率状态
        """
        fuel_rate = self.get_object()
        fuel_rate.status = not fuel_rate.status
        fuel_rate.save()
        
        FuelRateHistory.objects.create(
            fuel_rate=fuel_rate,
            old_rate=fuel_rate.rate_value,
            new_rate=fuel_rate.rate_value,
            operator=self.request.user,
            change_type='MANUAL',
            change_reason=f'状态切换为{"启用" if fuel_rate.status else "禁用"}'
        )
        
        return self.success_response(
            data={'status': fuel_rate.status},
            message=f'燃油费率状态已切换为{"启用" if fuel_rate.status else "禁用"}'
        )
        
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        获取当前有效的燃油费率
        """
        now = timezone.now().date()
        provider_id = request.query_params.get('provider_id')
        
        queryset = self.get_queryset().filter(
            Q(effective_date__lte=now) &
            (Q(expiration_date__gt=now) | Q(expiration_date=None)) &
            Q(status=True)
        )
        
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
            
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)


class FuelRateHistoryViewSet(BaseViewSet):
    """
    燃油费率历史记录视图集
    
    list:
    获取燃油费率历史记录列表
    
    retrieve:
    获取单个燃油费率历史记录详情
    """
    queryset = FuelRateHistory.objects.all().order_by('-created_at')
    serializer_class = FuelRateHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['fuel_rate_id', 'operator_id', 'change_type']
    search_fields = ['change_reason', 'operator__username']
    ordering_fields = ['created_at', 'updated_at']
    model_name = '燃油费率历史记录'

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_queryset(self):
        """
        根据燃油费率ID过滤历史记录
        """
        queryset = super().get_queryset()
        rate_id = self.request.query_params.get('rate_id')
        if rate_id:
            queryset = queryset.filter(fuel_rate_id=rate_id)
        return queryset
