import os
from django.conf import settings

# 线程和进程池配置
OPTIMAL_THREAD_COUNT = min(32, os.cpu_count() * 2)
MAX_WORKERS = getattr(settings, 'MAX_WORKERS', OPTIMAL_THREAD_COUNT)

# 缓存配置
CACHE_KEY_PREFIX = 'freight_calc'
CACHE_TTL = getattr(settings, 'CALCULATION_CACHE_TTL', 3600)  # 默认1小时
LOCAL_CACHE_SIZE = getattr(settings, 'LOCAL_CACHE_SIZE', 1000)
CACHE_WARM_SAMPLE_SIZE = getattr(settings, 'CACHE_WARM_SAMPLE_SIZE', 100)

# 批量处理配置
BATCH_CHUNK_SIZE = getattr(settings, 'BATCH_CHUNK_SIZE', 5000)
MAX_BATCH_RECORDS = getattr(settings, 'MAX_BATCH_RECORDS', 100000)
BULK_INSERT_SIZE = getattr(settings, 'BULK_INSERT_SIZE', 1000)
PROCESSING_TIMEOUT = getattr(settings, 'BATCH_PROCESSING_TIMEOUT', 7200)
OPTIMAL_CHUNK_SIZE = getattr(settings, 'OPTIMAL_CHUNK_SIZE', 1000)
MAX_BATCH_SIZE = getattr(settings, 'MAX_BATCH_CALCULATION_SIZE', 100)

# 业务限制
MIN_WEIGHT = '0.01'
MAX_WEIGHT = '999999.99' 