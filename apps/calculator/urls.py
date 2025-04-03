from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CalculationView,
    BatchCalculationView,
    ProductComparisonView,
    BatchCalculationTaskViewSet,
    CalculatorViewSet,
    calculation_history,
    calculation_detail,
    BatchCalculatorView
)

router = DefaultRouter()
router.register(r'batch-tasks', BatchCalculationTaskViewSet, basename='batchcalculationtask')
router.register(r'new-calculator', CalculatorViewSet, basename='new-calculator')

urlpatterns = [
    path('calculate/', CalculationView.as_view(), name='calculation-calculate-single'),
    path('calculate-batch/', BatchCalculationView.as_view(), name='calculation-calculate-batch'),
    path('compare-products/', ProductComparisonView.as_view(), name='calculation-compare-products'),
    path('history/', calculation_history, name='calculation-history'),
    path('detail/<str:request_id>/', calculation_detail, name='calculation-detail'),
    path('batch/<str:task_id>/', BatchCalculatorView.as_view(), name='calculation-batch-progress'),
    path('batch/', BatchCalculatorView.as_view(), name='calculation-batch-create'),
    path('', include(router.urls)),
]
