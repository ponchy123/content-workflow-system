import { ref, computed, watch, onUnmounted, shallowRef, reactive } from 'vue';
import type {
  CalculationRequest,
  CalculationResult,
  BatchCalculationRequest,
  BatchCalculationResponse,
  BatchCalculationTask,
  ValidationResult,
  BatchCalculationItem,
  ValidationError,
} from '@/types/calculator';
import {
  calculateFreight,
  getProductTypes,
  getServiceLevels,
  calculateBatch,
  getBatchTaskStatus,
  cancelBatchTask,
} from '@/api/calculator';
import { handleError, BusinessError } from '@/utils/logger/error-handler';
import { logger } from '@/utils/logger';
import { useRequest } from '@/composables/useRequest';
import { ElMessage, ElNotification } from 'element-plus';
import type { ValidationRule } from '@/utils/validation';
import { createTaskProgressWebSocket, type TaskProgress } from '@/api/calculator/websocket';
import type { Ref } from 'vue';

// 性能监控配置
const PERFORMANCE_CONFIG = {
  SLOW_CALCULATION_THRESHOLD: 5000, // 慢计算阈值（毫秒）
  MEMORY_WARNING_THRESHOLD: 50000, // 内存警告阈值（条目数）
  BATCH_SIZE: 1000, // 批处理大小
  CACHE_TTL: 1800000, // 缓存有效期（30分钟）
  CACHE_MAX_SIZE: 1000, // 缓存最大条目数
  DEBOUNCE_DELAY: 300, // 防抖延迟（毫秒）
  THROTTLE_DELAY: 1000, // 节流延迟（毫秒）
  AUTO_RETRY_COUNT: 3, // 自动重试次数
  PROGRESS_UPDATE_INTERVAL: 500, // 进度更新间隔（毫秒）
};

// WebSocket 重连配置
const WS_CONFIG = {
  MAX_RECONNECT_ATTEMPTS: 3,
  RECONNECT_INTERVAL: 1000,
  CONNECTION_TIMEOUT: 5000,
  HEARTBEAT_INTERVAL: 30000,
};

// 数据验证规则
const VALIDATION_RULES = {
  MIN_WEIGHT: 0.1,
  MAX_WEIGHT: 1000,
  MIN_VOLUME: 0.001,
  MAX_VOLUME: 100,
  MAX_QUANTITY: 1000,
  POSTCODE_PATTERN: /^\d{6}$/,
  MAX_NOTE_LENGTH: 200,
};

// 缓存管理器
class CacheManager<T> {
  private cache = new Map<string, { data: T; timestamp: number }>();

  set(key: string, value: T) {
    if (this.cache.size >= PERFORMANCE_CONFIG.CACHE_MAX_SIZE) {
      // 删除最旧的缓存
      const oldestKey = Array.from(this.cache.entries()).sort(
        ([, a], [, b]) => a.timestamp - b.timestamp,
      )[0][0];
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, { data: value, timestamp: Date.now() });
  }

  get(key: string): T | null {
    const item = this.cache.get(key);
    if (!item) return null;
    if (Date.now() - item.timestamp > PERFORMANCE_CONFIG.CACHE_TTL) {
      this.cache.delete(key);
      return null;
    }
    return item.data;
  }

  clear() {
    this.cache.clear();
  }
}

// 内存使用监控
interface ExtendedPerformance extends Performance {
  memory?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

// 性能监控器
class PerformanceMonitor {
  private metrics = {
    calculationTime: 0,
    memoryUsage: 0,
    batchSize: 0,
    errorCount: 0,
    retryCount: 0,
    startTimeStamp: 0,
  };

  start() {
    this.metrics.startTimeStamp = performance.now();
  }

  end() {
    this.metrics.calculationTime = performance.now() - this.metrics.startTimeStamp;
    if (this.metrics.calculationTime > PERFORMANCE_CONFIG.SLOW_CALCULATION_THRESHOLD) {
      logger.warn('计算耗时过长', this.metrics);
    }
  }

  updateMetrics(metrics: Partial<typeof this.metrics>) {
    Object.assign(this.metrics, metrics);
  }

  getMetrics() {
    return { ...this.metrics };
  }

  getMemoryUsage() {
    try {
      const extendedPerf = performance as ExtendedPerformance;
      if (extendedPerf.memory) {
        return extendedPerf.memory.usedJSHeapSize;
      }
    } catch {
      // 忽略错误
    }
    return 0;
  }
}

// 定义表单选项接口
interface FormOptions<T> {
  initialValues: T;
  rules?: Record<string, any[]>;
  validateOnChange?: boolean;
}

// 定义表单返回接口
interface FormReturn<T> {
  values: T;
  formRef: Ref<any>;
  validate: () => Promise<boolean>;
}

// 修改useForm函数定义
const useForm = <T>(options: FormOptions<T>): FormReturn<T> => {
  // 实现简化版useForm，适配接口
  const values = reactive({ ...options.initialValues } as object) as T;
  const formRef = ref<any>(null);
  
  const validate = async (): Promise<boolean> => {
    if (formRef.value && typeof formRef.value.validate === 'function') {
      return formRef.value.validate();
    }
    return true;
  };
  
  return {
    values,
    formRef,
    validate
  };
};

export function useCalculator() {
  const loading = ref(false);
  const result = ref<CalculationResult | null>(null);

  // 表单验证规则
  const rules: Record<string, ValidationRule[]> = {
    fromAddress: [
      { required: true, message: '请输入起始地邮编' },
      { pattern: VALIDATION_RULES.POSTCODE_PATTERN, message: '邮编格式不正确' },
    ],
    toAddress: [
      { required: true, message: '请输入目的地邮编' },
      { pattern: VALIDATION_RULES.POSTCODE_PATTERN, message: '邮编格式不正确' },
    ],
    weight: [
      { required: true, message: '请输入重量' },
      {
        validator: (value: number) =>
          value >= VALIDATION_RULES.MIN_WEIGHT && value <= VALIDATION_RULES.MAX_WEIGHT,
        message: `重量必须在 ${VALIDATION_RULES.MIN_WEIGHT}kg 到 ${VALIDATION_RULES.MAX_WEIGHT}kg 之间`,
      },
    ],
    volume: [
      {
        validator: (value?: number) =>
          !value || (value >= VALIDATION_RULES.MIN_VOLUME && value <= VALIDATION_RULES.MAX_VOLUME),
        message: `体积必须在 ${VALIDATION_RULES.MIN_VOLUME}m³ 到 ${VALIDATION_RULES.MAX_VOLUME}m³ 之间`,
      },
    ],
    quantity: [
      {
        validator: (value: number) => value > 0 && value <= VALIDATION_RULES.MAX_QUANTITY,
        message: `数量必须在 1 到 ${VALIDATION_RULES.MAX_QUANTITY} 之间`,
      },
    ],
    productType: [{ required: true, message: '请选择产品类型' }],
    serviceLevel: [{ required: true, message: '请选择服务等级' }],
    note: [
      {
        validator: (value?: string) => !value || value.length <= VALIDATION_RULES.MAX_NOTE_LENGTH,
        message: `备注不能超过 ${VALIDATION_RULES.MAX_NOTE_LENGTH} 个字符`,
      },
    ],
  };

  // 使用 useForm 处理表单
  const form = useForm<CalculationRequest>({
    initialValues: {
      fromAddress: '',
      toAddress: '',
      weight: 1,
      volume: 0,
      quantity: 1,
      productType: '',
      note: '',
    },
    rules,
    validateOnChange: true,
  });

  // 定义产品类型和服务等级类型
  type ProductType = { id: number; name: string; code: string; };
  type ServiceLevel = { id: number; name: string; code: string; };

  // 创建自定义的处理函数
  const useProductTypes = () => {
    const data = ref<ProductType[]>([]);
    const loading = ref(true);
    
    getProductTypes().then(result => {
      data.value = result as ProductType[];
      loading.value = false;
    }).catch(error => {
      logger.error('获取产品类型失败', error);
      ElMessage.error('获取产品类型失败，请稍后重试');
      loading.value = false;
    });
    
    return { data, loading };
  };
  
  const useServiceLevels = () => {
    const data = ref<ServiceLevel[]>([]);
    const loading = ref(true);
    
    getServiceLevels().then(result => {
      data.value = result as ServiceLevel[];
      loading.value = false;
    }).catch(error => {
      logger.error('获取服务等级失败', error);
      ElMessage.error('获取服务等级失败，请稍后重试');
      loading.value = false;
    });
    
    return { data, loading };
  };

  // 使用自定义钩子获取数据
  const { data: productTypes, loading: loadingProductTypes } = useProductTypes();
  const { data: serviceLevels, loading: loadingServiceLevels } = useServiceLevels();

  // 计算运费
  const calculate = async () => {
    try {
      loading.value = true;

      // 表单验证
      const isValid = await form.validate();
      if (!isValid) {
        throw new Error('表单验证失败');
      }

      logger.info('开始计算运费', form.values);
      result.value = await calculateFreight(form.values);
      logger.info('运费计算完成', result.value);

      ElMessage.success('运费计算成功');
      return result.value;
    } catch (error) {
      logger.error('计算运费失败', error);
      handleError(error);
      ElMessage.error('计算运费失败，请检查输入并重试');
      throw error;
    } finally {
      loading.value = false;
    }
  };

  // 计算体积重量（带缓存的计算属性）
  const calculateVolumetricWeight = computed(
    () => (length: number, width: number, height: number) => {
      return (length * width * height) / 6000;
    },
  );

  // 计算计费重量（带缓存的计算属性）
  const getChargeableWeight = computed(() => (actualWeight: number, volumetricWeight: number) => {
    return Math.max(actualWeight, volumetricWeight);
  });

  return {
    loading,
    loadingProductTypes,
    loadingServiceLevels,
    result,
    productTypes,
    serviceLevels,
    form,
    calculate,
    calculateVolumetricWeight,
    getChargeableWeight,
  };
}

// 批量计算功能
export function useBatchCalculator() {
  const loading = ref(false);
  const progress = ref(0);
  const taskId = ref<string>('');
  const results = shallowRef<BatchCalculationItem[]>([]);
  const error = ref<Error | null>(null);
  const status = ref<BatchCalculationTask['status']>('pending');
  const validationResult = ref<ValidationResult | null>(null);
  const wsConnected = ref(false);
  const taskWs = ref<ReturnType<typeof createTaskProgressWebSocket> | null>(null);
  const reconnectAttempts = ref(0);
  const pollingEnabled = ref(false);
  const pollingInterval = ref<number | null>(null);
  const lastProgressUpdate = ref<number>(0);
  const processingTime = ref<number>(0);
  const estimatedTimeRemaining = ref<number>(0);

  // 性能监控和缓存
  const performanceMonitor = new PerformanceMonitor();
  const resultCache = new CacheManager<CalculationResult[]>();
  const requestCache = new CacheManager<BatchCalculationResponse>();

  // 防抖和节流
  const debounce = <T extends (...args: any[]) => any>(
    fn: T,
    delay: number,
  ): ((...args: Parameters<T>) => Promise<ReturnType<T>>) => {
    let timeoutId: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      return new Promise(resolve => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          resolve(fn(...args));
        }, delay);
      });
    };
  };

  const throttle = <T extends (...args: any[]) => any>(
    fn: T,
    delay: number,
  ): ((...args: Parameters<T>) => void) => {
    let lastCall = 0;
    return (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCall >= delay) {
        fn(...args);
        lastCall = now;
      }
    };
  };

  // 更新进度信息
  const updateProgress = throttle((currentProgress: number, total: number) => {
    const now = Date.now();
    const timeDiff = now - lastProgressUpdate.value;

    if (timeDiff > 0 && currentProgress > 0) {
      const progressDiff = currentProgress - progress.value;
      const progressRate = progressDiff / timeDiff;

      if (progressRate > 0) {
        const remainingProgress = total - currentProgress;
        estimatedTimeRemaining.value = remainingProgress / progressRate;
      }
    }

    progress.value = currentProgress;
    lastProgressUpdate.value = now;
    const metrics = performanceMonitor.getMetrics();
    processingTime.value = now - metrics.startTimeStamp;
  }, PERFORMANCE_CONFIG.PROGRESS_UPDATE_INTERVAL);

  // 用户反馈增强
  const showFeedback = (type: 'success' | 'warning' | 'error', title: string, message: string) => {
    ElNotification({
      type,
      title,
      message,
      duration: type === 'error' ? 0 : 5000,
    });
  };

  // 错误重试处理
  const retryOperation = async <T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000,
  ): Promise<T> => {
    let lastError: Error | null = null;
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await operation();
      } catch (err) {
        lastError = err as Error;
        logger.warn(`操作失败，第 ${i + 1} 次重试`, err);
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
    throw lastError;
  };

  // 批量处理大数据
  const processBatchData = async (data: BatchCalculationRequest): Promise<CalculationResult[]> => {
    const batchSize = PERFORMANCE_CONFIG.BATCH_SIZE;
    const totalItems = data.items.length;

    if (totalItems > PERFORMANCE_CONFIG.MEMORY_WARNING_THRESHOLD) {
      showFeedback('warning', '性能警告', '数据量较大，处理可能需要较长时间');
    }

    const batches: BatchCalculationRequest[] = [];
    for (let i = 0; i < totalItems; i += batchSize) {
      batches.push({
        items: data.items.slice(i, i + batchSize),
      });
    }

    const processedResults: CalculationResult[] = [];
    for (const batch of batches) {
      const batchResponse = await retryOperation(() => calculateBatch(batch), 3, 1000);
      if (batchResponse.results) {
        processedResults.push(...batchResponse.results);
      }
    }

    return processedResults;
  };

  // 验证批量计算数据
  const validateBatchData = (data: BatchCalculationRequest): ValidationResult => {
    performanceMonitor.start();
    const result = validateBatchDataInternal(data);
    performanceMonitor.end();
    return result;
  };

  // 内部验证函数
  const validateBatchDataInternal = (data: BatchCalculationRequest): ValidationResult => {
    const errors: ValidationError[] = [];
    const warnings: ValidationError[] = [];

    data.items.forEach((item, index) => {
      // 验证必填字段
      if (!item.fromAddress || !item.toAddress || !item.weight) {
        errors.push({
          row: index + 1,
          field: !item.fromAddress ? 'fromAddress' : !item.toAddress ? 'toAddress' : 'weight',
          message: '必填字段不能为空',
          type: 'error',
        });
      }

      // 验证邮编格式
      if (item.fromAddress && !VALIDATION_RULES.POSTCODE_PATTERN.test(item.fromAddress)) {
        errors.push({
          row: index + 1,
          field: 'fromAddress',
          message: '起始地邮编格式不正确',
          type: 'error',
        });
      }
      if (item.toAddress && !VALIDATION_RULES.POSTCODE_PATTERN.test(item.toAddress)) {
        errors.push({
          row: index + 1,
          field: 'toAddress',
          message: '目的地邮编格式不正确',
          type: 'error',
        });
      }

      // 验证数值范围
      if (item.weight < VALIDATION_RULES.MIN_WEIGHT || item.weight > VALIDATION_RULES.MAX_WEIGHT) {
        errors.push({
          row: index + 1,
          field: 'weight',
          message: `重量必须在 ${VALIDATION_RULES.MIN_WEIGHT}kg 到 ${VALIDATION_RULES.MAX_WEIGHT}kg 之间`,
          type: 'error',
        });
      }

      if (
        item.volume !== undefined &&
        (item.volume < VALIDATION_RULES.MIN_VOLUME || item.volume > VALIDATION_RULES.MAX_VOLUME)
      ) {
        warnings.push({
          row: index + 1,
          field: 'volume',
          message: `体积必须在 ${VALIDATION_RULES.MIN_VOLUME}m³ 到 ${VALIDATION_RULES.MAX_VOLUME}m³ 之间`,
          type: 'warning',
        });
      }

      if (item.quantity > VALIDATION_RULES.MAX_QUANTITY) {
        warnings.push({
          row: index + 1,
          field: 'quantity',
          message: `数量不能超过 ${VALIDATION_RULES.MAX_QUANTITY}`,
          type: 'warning',
        });
      }
    });

    return {
      isValid: errors.length === 0,
      data: data.items.map(item => ({
        ...item,
        ruleId: '', // 初始化为空字符串，将在计算时更新
        success: false,
        message: '',
      })) as BatchCalculationItem[],
      errors,
      warnings,
    };
  };

  // 启动轮询
  const startPolling = async () => {
    if (!taskId.value || pollingInterval.value) return;

    const poll = async () => {
      try {
        const response = await getBatchTaskStatus(taskId.value);
        handleTaskProgress(response);

        if (response.status === 'completed' || response.status === 'failed') {
          stopPolling();
        }
      } catch (err) {
        logger.error('获取任务状态失败', err);
        handleError(err);
      }
    };

    pollingEnabled.value = true;
    pollingInterval.value = window.setInterval(poll, 2000);
  };

  // 停止轮询
  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value);
      pollingInterval.value = null;
    }
    pollingEnabled.value = false;
  };

  // 优化的任务进度处理
  const handleTaskProgress = (response: BatchCalculationResponse) => {
    const currentProgress = response.progress || 0;
    updateProgress(currentProgress, response.totalItems || 100);
    status.value = response.status;

    // 性能监控
    const currentMemoryUsage = performanceMonitor.getMemoryUsage();
    performanceMonitor.updateMetrics({
      memoryUsage: currentMemoryUsage,
      batchSize: response.totalItems || 0,
      errorCount: response.errorMessages.length,
    });

    if (response.results?.length) {
      const cacheKey = `results_${taskId.value}`;
      const cachedResults = resultCache.get(cacheKey);

      if (!cachedResults) {
        resultCache.set(cacheKey, response.results);
        // 使用 requestAnimationFrame 优化视图更新
        requestAnimationFrame(() => {
          results.value = convertToCalculationItems(response.results!);
        });
      }
    }

    // 状态处理和用户反馈
    if (response.status === 'completed') {
      const metrics = performanceMonitor.getMetrics();
      showFeedback(
        'success',
        '计算完成',
        [
          `成功处理 ${results.value.length} 条数据`,
          `处理时间: ${(metrics.calculationTime / 1000).toFixed(2)}秒`,
          `内存使用: ${(metrics.memoryUsage / (1024 * 1024)).toFixed(2)}MB`,
        ].join('\n'),
      );
      cleanup();
    } else if (response.status === 'failed') {
      error.value = new Error(response.error || '批量计算失败');
      showFeedback(
        'error',
        '计算失败',
        [
          response.error || '批量计算失败',
          `错误数量: ${response.errorMessages.length}`,
          ...response.errorMessages,
        ].join('\n'),
      );
      cleanup();
    }
  };

  // 转换计算结果为计算项
  const convertToCalculationItems = (results: CalculationResult[]): BatchCalculationItem[] => {
    return results.map((result, index) => {
      // 创建一个符合BatchCalculationItem类型的对象
      const item: BatchCalculationItem = {
        id: index + 1, // 使用索引作为数字ID
        ruleId: result.requestId || crypto.randomUUID().toString(),
        fromAddress: '',
        toAddress: '',
        weight: 0,
        quantity: 1,
        productType: '',
        success: true,
        basePrice: result.baseCharge,
        fuelSurcharge: result.fuelSurcharge,
        otherFees: 0,
        totalPrice: result.totalCharge,
        message: result.error || ''
      };
      return item;
    });
  };

  // 重连 WebSocket
  const reconnectWebSocket = async (itemCount: number) => {
    if (reconnectAttempts.value >= WS_CONFIG.MAX_RECONNECT_ATTEMPTS) {
      logger.warn('WebSocket重连次数超过限制，切换到轮询模式');
      startPolling();
      return;
    }

    reconnectAttempts.value++;
    const delay = WS_CONFIG.RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts.value - 1);

    await new Promise(resolve => setTimeout(resolve, delay));

    try {
      const ws = createTaskProgressWebSocket(taskId.value);
      taskWs.value = ws;

      // 等待连接建立
      await Promise.race([
        new Promise<void>(resolve => {
          const checkConnection = () => {
            if (ws.progress.value.status !== 'pending') {
              wsConnected.value = true;
              resolve();
            } else {
              setTimeout(checkConnection, 100);
            }
          };
          checkConnection();
        }),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('WebSocket连接超时')), WS_CONFIG.CONNECTION_TIMEOUT),
        ),
      ]);

      setupWebSocketHandlers(ws, itemCount);
    } catch (err) {
      logger.error('WebSocket重连失败', err);
      reconnectWebSocket(itemCount);
    }
  };

  // 设置 WebSocket 处理器
  const setupWebSocketHandlers = (
    ws: ReturnType<typeof createTaskProgressWebSocket>,
    itemCount: number,
  ) => {
    // 监听进度变化
    watch(
      () => ws.progress.value,
      (newProgress: TaskProgress) => {
        handleTaskProgress({
          taskId: taskId.value,
          status: newProgress.status,
          progress: newProgress.progress,
          results: newProgress.result,
          error: newProgress.message,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          totalItems: itemCount,
          processedItems: Math.floor(((newProgress.progress || 0) * itemCount) / 100),
          errorMessages: newProgress.message ? [newProgress.message] : [],
        });
      },
      { immediate: true },
    );
  };

  // 开始批量计算
  const startBatchCalculation = async (
    data: BatchCalculationRequest,
  ): Promise<BatchCalculationResponse> => {
    performanceMonitor.start();
    try {
      loading.value = true;
      status.value = 'pending';
      progress.value = 0;
      error.value = null;
      results.value = [];
      reconnectAttempts.value = 0;

      // 检查缓存
      const cacheKey = JSON.stringify(data);
      const cachedResponse = requestCache.get(cacheKey);
      if (cachedResponse) {
        showFeedback('success', '使用缓存', '使用缓存数据快速响应');
        results.value = convertToCalculationItems(cachedResponse.results || []);
        return cachedResponse;
      }

      // 数据验证
      const validation = validateBatchData(data);
      validationResult.value = validation;

      if (!validation.isValid) {
        throw new BusinessError('数据验证失败', { details: validation });
      }

      // 大数据处理
      if (data.items.length > PERFORMANCE_CONFIG.BATCH_SIZE) {
        const processedResults = await processBatchData(data);
        const response: BatchCalculationResponse = {
          taskId: '',
          status: 'completed',
          results: processedResults,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          totalItems: processedResults.length,
          processedItems: processedResults.length,
          errorMessages: [],
        };
        results.value = convertToCalculationItems(processedResults);
        requestCache.set(cacheKey, response);
        return response;
      }

      logger.info('开始批量计算', data);
      const response = await retryOperation(() => calculateBatch(data), 3, 1000);
      taskId.value = response.taskId;

      // WebSocket 连接处理
      try {
        const ws = createTaskProgressWebSocket(response.taskId);
        taskWs.value = ws;
        await Promise.race([
          new Promise<void>(resolve => {
            const checkConnection = () => {
              if (ws.progress.value.status !== 'pending') {
                wsConnected.value = true;
                resolve();
              } else {
                setTimeout(checkConnection, 100);
              }
            };
            checkConnection();
          }),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('WebSocket连接超时')), WS_CONFIG.CONNECTION_TIMEOUT),
          ),
        ]);

        setupWebSocketHandlers(ws, data.items.length);
      } catch (err) {
        logger.warn('WebSocket连接失败，切换到轮询模式', err);
        startPolling();
      }

      return response;
    } catch (err) {
      logger.error('批量计算失败', err);
      handleError(err);
      error.value = err as Error;
      status.value = 'failed';
      showFeedback('error', '计算失败', '批量计算失败，请重试');
      throw err;
    } finally {
      loading.value = false;
      performanceMonitor.end();
      const metrics = performanceMonitor.getMetrics();
      logger.info('批量计算性能指标', metrics);
    }
  };

  // 取消批量计算
  const cancelCalculation = async () => {
    if (!taskId.value) return;

    try {
      await cancelBatchTask(taskId.value);
      status.value = 'failed';
      cleanup();
      ElMessage.info('已取消批量计算');
    } catch (err) {
      logger.error('取消批量计算失败', err);
      handleError(err);
      ElMessage.error('取消批量计算失败');
      throw err;
    }
  };

  // 清理资源
  const cleanup = () => {
    if (taskWs.value) {
      taskWs.value.disconnect();
      taskWs.value = null;
    }
    stopPolling();
    wsConnected.value = false;
    taskId.value = '';
    progress.value = 0;
    status.value = 'pending';
    error.value = null;
    results.value = [];
    validationResult.value = null;
    reconnectAttempts.value = 0;

    // 清理过期缓存
    if (Math.random() < 0.1) {
      // 10% 的概率执行缓存清理
      resultCache.clear();
      requestCache.clear();
    }
  };

  // 优化的统计信息计算
  const statistics = computed(() => {
    const total = results.value.length;
    const success = results.value.filter(r => r.success).length;
    const failed = total - success;

    // 使用 reduce 的优化版本，避免多次遍历
    const { totalPrice, minPrice, maxPrice } = results.value.reduce(
      (acc, r) => {
        const price = r.totalPrice || 0;
        return {
          totalPrice: acc.totalPrice + price,
          minPrice: Math.min(acc.minPrice, price),
          maxPrice: Math.max(acc.maxPrice, price),
        };
      },
      { totalPrice: 0, minPrice: Infinity, maxPrice: -Infinity },
    );

    const averagePrice = total > 0 ? totalPrice / total : 0;
    const metrics = performanceMonitor.getMetrics();

    return {
      total,
      success,
      failed,
      totalPrice,
      averagePrice,
      minPrice: minPrice === Infinity ? 0 : minPrice,
      maxPrice: maxPrice === -Infinity ? 0 : maxPrice,
      progress: progress.value,
      successRate: total > 0 ? ((success / total) * 100).toFixed(1) + '%' : '0%',
      processingTime: processingTime.value,
      estimatedTimeRemaining: estimatedTimeRemaining.value,
      performance: {
        calculationTime: metrics.calculationTime,
        memoryUsage: metrics.memoryUsage,
        errorCount: metrics.errorCount,
        retryCount: metrics.retryCount,
        batchSize: metrics.batchSize,
      },
    };
  });

  // 组件卸载时清理资源
  onUnmounted(() => {
    cleanup();
  });

  return {
    loading,
    progress,
    status,
    results,
    error,
    validationResult,
    statistics,
    wsConnected,
    startBatchCalculation: debounce(startBatchCalculation, PERFORMANCE_CONFIG.DEBOUNCE_DELAY),
    cancelCalculation,
    cleanup,
  };
}
