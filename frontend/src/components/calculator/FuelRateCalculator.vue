<template>
  <div class="fuel-rate-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3 class="card-title">燃油费率计算</h3>
          <div class="card-actions">
            <el-button type="primary" @click="calculate">
              <el-icon><Calculate /></el-icon>计算
            </el-button>
            <el-button @click="reset">
              <el-icon><Refresh /></el-icon>重置
            </el-button>
          </div>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="基础运费" required>
          <el-input-number
            v-model="form.baseFee"
            :min="0"
            :precision="2"
            :step="10"
            controls-position="right"
          />
          <span class="text-secondary ml-base">{{ currencyCode }}</span>
        </el-form-item>

        <el-form-item label="燃油费率">
          <el-input-number
            :model-value="currentRate ? currentRate.rate : 0"
            :disabled="true"
            :precision="2"
            controls-position="right"
          />
          <span class="text-secondary ml-base">%</span>
          <el-tooltip :content="rateDescription" placement="right">
            <el-icon class="tooltip-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </el-form-item>

        <el-form-item label="燃油附加费">
          <el-input-number
            v-model="fuelSurcharge"
            :disabled="true"
            :precision="2"
            controls-position="right"
          />
          <span class="text-secondary ml-base">{{ currencyCode }}</span>
        </el-form-item>
      </el-form>

      <div class="result-content mt-base">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="计算公式">
            燃油附加费 = 基础运费 × 燃油费率
          </el-descriptions-item>
          <el-descriptions-item label="计算明细">
            {{ form.baseFee }} × {{ currentRate ? currentRate.rate : 0 }}% = {{ fuelSurcharge }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 燃油费率信息 -->
      <el-descriptions :column="2" border>
        <el-descriptions-item label="当前燃油费率">
          {{ currentRate ? currentRate.rate.toFixed(2) + '%' : '暂无数据' }}
        </el-descriptions-item>
        <el-descriptions-item label="生效日期">
          {{ currentRate ? formatDate(currentRate.effectiveDate) : '暂无数据' }}
        </el-descriptions-item>
        <el-descriptions-item label="基准价格">
          {{ currentRate ? formatCurrency(currentRate.basePrice) : '暂无数据' }}
        </el-descriptions-item>
        <el-descriptions-item label="当前价格">
          {{ currentRate ? formatCurrency(currentRate.currentPrice) : '暂无数据' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 费率历史趋势图 -->
      <div class="rate-trend mt-4">
        <h4>费率历史趋势</h4>
        <div ref="chartRef" class="chart"></div>
      </div>

      <!-- 计算过程 -->
      <CalculationSteps v-if="calculation" :steps="calculation.steps" title="计算过程" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, watch, onUnmounted, computed } from 'vue';
  import * as echarts from 'echarts';
  import dayjs from 'dayjs';
  import CalculationSteps from './CalculationSteps.vue';
  import {
    ArrowRight as Calculate,
    RefreshRight as Refresh,
    InfoFilled,
  } from '@element-plus/icons-vue';
  import type { FuelRateForm } from '@/types/forms';

  interface FuelRate {
    rate: number;
    effectiveDate: string;
    basePrice: number;
    currentPrice: number;
  }

  interface CalculationStep {
    description: string;
    formula: string;
    result?: number;
  }

  interface Calculation {
    steps: CalculationStep[];
    total: number;
  }

  interface Props {
    productId: string;
    baseFee?: number;
    currency?: string;
  }

  const props = withDefaults(defineProps<Props>(), {
    baseFee: 0,
    currency: 'USD'
  });

  const emit = defineEmits<{
    (e: 'calculated', fuelSurcharge: number): void;
  }>();

  // 表单数据
  const form = ref<{ baseFee: number }>({
    baseFee: props.baseFee || 0,
  });

  // 当前燃油费率
  const currentRate = ref<FuelRate | null>(null);

  // 计算过程
  const calculation = ref<Calculation | null>(null);

  // 计算结果
  const fuelSurcharge = computed(() => {
    if (!currentRate.value || !form.value.baseFee) return 0;
    return form.value.baseFee * (currentRate.value.rate / 100);
  });

  // 费率说明
  const rateDescription = computed(() => {
    if (!currentRate.value) return '暂无费率数据';
    return `当前燃油费率为 ${currentRate.value.rate.toFixed(2)}%，生效日期 ${formatDate(currentRate.value.effectiveDate)}`;
  });

  // 使用props传入的货币代码或默认值USD
  const currencyCode = computed(() => props.currency || 'USD');

  // 图表相关
  const chartRef = ref<HTMLElement>();
  let chart: echarts.ECharts | null = null;

  // 重置
  const reset = () => {
    form.value.baseFee = 0;
    calculation.value = null;
  };

  // 获取燃油费率数据
  const fetchFuelRate = async () => {
    try {
      const response = await fetch(`/api/products/${props.productId}/fuel-rate`);
      currentRate.value = await response.json();
    } catch (error) {
      console.error('获取燃油费率数据失败:', error);
    }
  };

  // 获取燃油费率历史数据
  const fetchRateHistory = async () => {
    try {
      const response = await fetch(`/api/products/${props.productId}/fuel-rate/history`);
      const data = await response.json();
      updateChart(data);
    } catch (error) {
      console.error('获取燃油费率历史数据失败:', error);
    }
  };

  // 计算燃油附加费
  const calculate = async () => {
    try {
      const response = await fetch('/api/calculator/fuel-surcharge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          productId: props.productId,
          baseFee: form.value.baseFee,
        }),
      });

      const data = await response.json();
      calculation.value = data;
      emit('calculated', data.total);
    } catch (error) {
      console.error('计算燃油附加费失败:', error);
    }
  };

  // 更新图表
  const updateChart = (data: { date: string; rate: number }[]) => {
    if (!chartRef.value) return;

    if (!chart) {
      chart = echarts.init(chartRef.value);
    }

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const data = params[0];
          return `${data.name}<br/>费率: ${(data.value * 100).toFixed(2)}%`;
        },
      },
      xAxis: {
        type: 'category',
        data: data.map(item => formatDate(item.date)),
        axisLabel: {
          rotate: 45,
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => `${(value * 100).toFixed(2)}%`,
        },
      },
      series: [
        {
          name: '燃油费率',
          type: 'line',
          data: data.map(item => item.rate),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: {
            color: '#409EFF',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: 'rgba(64,158,255,0.3)',
              },
              {
                offset: 1,
                color: 'rgba(64,158,255,0.1)',
              },
            ]),
          },
        },
      ],
    };

    chart.setOption(option);
  };

  // 格式化日期
  const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD');
  };

  // 格式化货币
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: currencyCode.value,
    }).format(amount);
  };

  // 监听属性变化
  watch(
    () => [props.productId, form.value.baseFee],
    async ([newProductId, newBaseFee]) => {
      if (newProductId && newBaseFee) {
        await fetchFuelRate();
        await fetchRateHistory();
        await calculate();
      }
    },
    { immediate: true },
  );

  // 监听窗口大小变化
  onMounted(() => {
    window.addEventListener('resize', () => {
      chart?.resize();
    });
  });

  // 组件卸载时销毁图表
  onUnmounted(() => {
    chart?.dispose();
    window.removeEventListener('resize', () => {
      chart?.resize();
    });
  });
</script>

<style scoped>
  .fuel-rate-calculator {
    margin-bottom: var(--spacing-large);

    :deep(.el-form) {
      margin-bottom: var(--spacing-large);

      .el-form-item {
        margin-bottom: var(--spacing-base);

        &:last-child {
          margin-bottom: 0;
        }

        .el-form-item__label {
          color: var(--text-color-regular);
          font-weight: 500;
          line-height: 1.5;
        }

        .el-form-item__content {
          display: flex;
          align-items: center;
          gap: var(--spacing-base);
        }
      }

      .el-input-number {
        width: 160px;

        .el-input__wrapper {
          box-shadow: 0 0 0 1px var(--border-color) inset;

          &:hover {
            box-shadow: 0 0 0 1px var(--border-color-hover) inset;
          }

          &.is-focus {
            box-shadow: 0 0 0 1px var(--color-primary) inset;
          }
        }

        &.is-disabled .el-input__wrapper {
          box-shadow: 0 0 0 1px var(--border-color-light) inset;
          background-color: var(--fill-color-light);
        }
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-base);

      .card-title {
        margin: 0;
        font-size: var(--font-size-large);
        color: var(--text-color-primary);
        font-weight: 500;
      }

      .card-actions {
        display: flex;
        gap: var(--spacing-base);
      }
    }

    .text-secondary {
      color: var(--text-color-secondary);
      margin-left: var(--spacing-base);
    }

    .tooltip-icon {
      margin-left: var(--spacing-small);
      color: var(--text-color-info);
      cursor: help;
      transition: color var(--transition-duration);

      &:hover {
        color: var(--color-primary);
      }
    }

    .result-content {
      margin-top: var(--spacing-large);
      margin-bottom: var(--spacing-large);
    }

    :deep(.el-descriptions) {
      margin-bottom: var(--spacing-large);

      &:last-child {
        margin-bottom: 0;
      }

      .el-descriptions__label {
        background-color: var(--fill-color-light);
        color: var(--text-color-regular);
        font-weight: 500;
        width: 120px;
      }

      .el-descriptions__content {
        color: var(--text-color-primary);
      }

      .el-descriptions__cell {
        padding: var(--spacing-base);
      }
    }

    .rate-trend {
      margin-top: var(--spacing-large);
      padding-top: var(--spacing-large);
      border-top: 1px solid var(--border-color-light);

      h4 {
        margin: 0 0 var(--spacing-base);
        font-size: var(--font-size-base);
        color: var(--text-color-primary);
        font-weight: 500;
      }

      .chart {
        height: 300px;
        margin-top: var(--spacing-base);
      }
    }

    .calculation-process {
      margin-top: var(--spacing-large);
      padding-top: var(--spacing-large);
      border-top: 1px solid var(--border-color-light);

      h4 {
        margin: 0 0 var(--spacing-base);
        font-size: var(--font-size-base);
        color: var(--text-color-primary);
        font-weight: 500;
      }

      :deep(.el-steps) {
        --el-text-color-regular: var(--text-color-secondary);

        .el-step__title {
          font-size: var(--font-size-base);
          line-height: 1.5;
        }

        .el-step__description {
          font-size: var(--font-size-small);
          color: var(--text-color-secondary);
          margin-top: var(--spacing-extra-small);
        }

        .el-step__head {
          background-color: var(--bg-color);
        }

        .el-step__line {
          background-color: var(--border-color-light);
        }

        .el-step.is-success {
          .el-step__title,
          .el-step__description {
            color: var(--text-color-regular);
          }
        }
      }
    }

    .mt-base {
      margin-top: var(--spacing-base);
    }

    .mt-4 {
      margin-top: var(--spacing-large);
    }

    .ml-base {
      margin-left: var(--spacing-base);
    }
  }
</style>
