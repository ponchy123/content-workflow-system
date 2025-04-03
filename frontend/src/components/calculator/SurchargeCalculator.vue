<template>
  <div class="surcharge-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>附加费计算器</h3>
        </div>
      </template>

      <!-- 附加费列表 -->
      <el-table :data="surcharges" border>
        <el-table-column prop="name" label="附加费名称" />
        <el-table-column prop="type" label="类型">
          <template #default="{ row }">
            {{ getSurchargeType(row.type) }}
          </template>
        </el-table-column>
        <el-table-column prop="rate" label="费率">
          <template #default="{ row }">
            {{ formatRate(row.rate, row.type) }}
          </template>
        </el-table-column>
        <el-table-column prop="condition" label="触发条件" />
        <el-table-column prop="amount" label="金额">
          <template #default="{ row }">
            {{ formatCurrency(row.amount) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 计算过程 -->
      <CalculationSteps v-if="calculation" :steps="calculation.steps" title="计算过程" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import { ElMessage } from 'element-plus';
  import CalculationSteps from './CalculationSteps.vue';

  type SurchargeType = 'fixed' | 'percentage' | 'per_kg' | 'per_shipment';

  interface Surcharge {
    name: string;
    type: SurchargeType;
    rate: number;
    condition: string;
    amount: number;
    [key: string]: any; // 支持Zone1, Zone2等键
  }

  interface CalculationStep {
    description: string;
    formula: string;
  }

  interface Calculation {
    steps: CalculationStep[];
    total: number;
  }

  interface Props {
    productId: string;
    weight: number;
    baseFee: number;
    zone: number;
    isRemoteArea: boolean;
    currency?: string;  // 添加货币属性
  }

  const props = defineProps<Props>();

  const emit = defineEmits<{
    (e: 'calculated', surcharges: number): void;
  }>();

  // 附加费数据
  const surcharges = ref<Surcharge[]>([]);

  // 计算过程
  const calculation = ref<Calculation | null>(null);

  // 获取附加费数据
  const fetchSurcharges = async () => {
    try {
      const response = await fetch(`/api/products/${props.productId}/surcharges`);
      if (!response.ok) {
        throw new Error('获取附加费数据失败');
      }
      surcharges.value = await response.json();
    } catch (error) {
      console.error('获取附加费数据失败:', error);
      ElMessage.error('获取附加费数据失败');
    }
  };

  // 计算附加费
  const calculate = async () => {
    try {
      const response = await fetch('/api/calculator/surcharges', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          productId: props.productId,
          weight: props.weight,
          baseFee: props.baseFee,
          zone: props.zone,
          isRemoteArea: props.isRemoteArea,
        }),
      });

      if (!response.ok) {
        throw new Error('计算附加费失败');
      }

      const data = await response.json();
      calculation.value = data;
      emit('calculated', data.total);
    } catch (error) {
      console.error('计算附加费失败:', error);
      ElMessage.error('计算附加费失败');
    }
  };

  // 获取附加费类型描述
  const getSurchargeType = (type: SurchargeType): string => {
    const types: Record<SurchargeType, string> = {
      fixed: '固定金额',
      percentage: '百分比',
      per_kg: '每公斤',
      per_shipment: '每票',
    };
    return types[type] || type;
  };

  // 格式化费率
  const formatRate = (rate: number, type: SurchargeType): string => {
    switch (type) {
      case 'percentage':
        return `${rate.toFixed(2)}%`;
      case 'fixed':
      case 'per_kg':
      case 'per_shipment':
        return formatCurrency(rate);
      default:
        return rate.toFixed(2);
    }
  };

  // 格式化货币
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: props.currency || 'USD',
    }).format(amount);
  };

  // 监听属性变化
  watch(
    () => [props.productId, props.weight, props.baseFee, props.zone, props.isRemoteArea],
    async ([newProductId, newWeight, newBaseFee, newZone, newIsRemoteArea]) => {
      if (newProductId && newWeight && newBaseFee && newZone !== undefined) {
        await fetchSurcharges();
        await calculate();
      }
    },
    { immediate: true },
  );
</script>

<style scoped>
  .surcharge-calculator {
    background-color: var(--bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);

    .calculator-header {
      padding: var(--spacing-base);
      border-bottom: 1px solid var(--border-color);

      .title {
        font-size: var(--font-size-large);
        font-weight: var(--font-weight-medium);
        color: var(--text-color-primary);
      }
    }

    .calculator-body {
      padding: var(--spacing-large);

      .surcharge-list {
        .surcharge-item {
          padding: var(--spacing-base);
          border: 1px solid var(--border-color);
          border-radius: var(--border-radius-base);
          margin-bottom: var(--spacing-base);

          .item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-base);

            .item-title {
              font-size: var(--font-size-medium);
              font-weight: var(--font-weight-medium);
              color: var(--text-color-primary);
            }

            .item-amount {
              font-size: var(--font-size-large);
              font-weight: var(--font-weight-bold);
              color: var(--color-primary);
            }
          }

          .item-description {
            color: var(--text-color-regular);
            margin-bottom: var(--spacing-base);
          }

          .item-conditions {
            padding: var(--spacing-base);
            background-color: var(--bg-color-light);
            border-radius: var(--border-radius-base);

            .condition-title {
              font-size: var(--font-size-small);
              font-weight: var(--font-weight-medium);
              color: var(--text-color-secondary);
              margin-bottom: var(--spacing-small);
            }

            .condition-list {
              display: flex;
              flex-wrap: wrap;
              gap: var(--spacing-small);

              .condition-tag {
                padding: var(--spacing-mini) var(--spacing-small);
                background-color: var(--bg-color);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-small);
                color: var(--text-color-regular);
                font-size: var(--font-size-small);
              }
            }
          }
        }
      }
    }

    .calculator-footer {
      padding: var(--spacing-base);
      border-top: 1px solid var(--border-color);
      background-color: var(--bg-color-light);
      display: flex;
      justify-content: space-between;
      align-items: center;

      .total-surcharge {
        .label {
          color: var(--text-color-regular);
          margin-right: var(--spacing-small);
        }

        .amount {
          font-size: var(--font-size-large);
          font-weight: var(--font-weight-bold);
          color: var(--color-primary);
        }
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--el-spacing-base);

      h3 {
        margin: 0;
        font-size: var(--el-font-size-large);
        color: var(--el-text-color-primary);
        font-weight: 500;
      }
    }

    .text-secondary {
      color: var(--el-text-color-secondary);
      margin-left: var(--el-spacing-base);
    }

    .tooltip-icon {
      margin-left: var(--el-spacing-small);
      color: var(--el-text-color-info);
      cursor: help;
      transition: color var(--el-transition-duration);

      &:hover {
        color: var(--el-color-primary);
      }
    }

    :deep(.el-table) {
      margin-top: var(--el-spacing-base);

      th {
        background-color: var(--el-fill-color-light);
        color: var(--el-text-color-primary);
        font-weight: 500;
      }

      td {
        color: var(--el-text-color-regular);
      }

      .el-table__cell {
        padding: var(--el-spacing-base);
      }

      .el-table__row:hover {
        td {
          background-color: var(--el-fill-color-light);
        }
      }
    }

    .calculation-process {
      margin-top: var(--el-spacing-large);
      padding-top: var(--el-spacing-large);
      border-top: 1px solid var(--el-border-color-light);

      h4 {
        margin: 0 0 var(--el-spacing-base);
        font-size: var(--el-font-size-base);
        color: var(--el-text-color-primary);
        font-weight: 500;
      }

      :deep(.el-steps) {
        --el-text-color-regular: var(--el-text-color-secondary);

        .el-step__title {
          font-size: var(--el-font-size-base);
          line-height: 1.5;
        }

        .el-step__description {
          font-size: var(--el-font-size-small);
          color: var(--el-text-color-secondary);
          margin-top: var(--el-spacing-extra-small);
        }

        .el-step__head {
          background-color: var(--el-bg-color);
        }

        .el-step__line {
          background-color: var(--el-border-color-light);
        }

        .el-step.is-success {
          .el-step__title,
          .el-step__description {
            color: var(--el-text-color-regular);
          }
        }
      }
    }

    .mt-base {
      margin-top: var(--el-spacing-base);
    }

    .mt-4 {
      margin-top: var(--el-spacing-large);
    }

    .ml-base {
      margin-left: var(--el-spacing-base);
    }
  }
</style>
