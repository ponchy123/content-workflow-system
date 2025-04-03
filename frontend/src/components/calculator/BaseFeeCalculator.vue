<template>
  <div class="base-fee-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3 class="card-title">基础运费计算</h3>
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
        <el-form-item label="实际重量" required>
          <el-input-number
            v-model="form.actualWeight"
            :min="0"
            :precision="2"
            :step="0.1"
            controls-position="right"
          />
          <span class="text-secondary ml-base">{{ weightUnit }}</span>
        </el-form-item>

        <el-form-item label="包裹尺寸" required>
          <div class="flex gap-base items-center">
            <el-input-number
              v-model="form.length"
              :min="0"
              :precision="2"
              :step="0.1"
              controls-position="right"
              placeholder="长"
            />
            <span>×</span>
            <el-input-number
              v-model="form.width"
              :min="0"
              :precision="2"
              :step="0.1"
              controls-position="right"
              placeholder="宽"
            />
            <span>×</span>
            <el-input-number
              v-model="form.height"
              :min="0"
              :precision="2"
              :step="0.1"
              controls-position="right"
              placeholder="高"
            />
            <span class="text-secondary">{{ dimUnit }}</span>
          </div>
        </el-form-item>

        <el-form-item label="体积重">
          <el-input-number v-model="volumetricWeight" :disabled="true" controls-position="right" />
          <span class="text-secondary ml-base">{{ weightUnit }}</span>
          <el-tooltip content="体积重 = (长 × 宽 × 高) / 系数" placement="right">
            <el-icon class="tooltip-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </el-form-item>

        <el-form-item label="计费重量">
          <el-input-number v-model="chargeableWeight" :disabled="true" controls-position="right" />
          <span class="text-secondary ml-base">{{ weightUnit }}</span>
          <el-tooltip content="计费重量 = max(实际重量, 体积重)" placement="right">
            <el-icon class="tooltip-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </el-form-item>

        <el-form-item label="基础运费">
          <el-input-number
            v-model="baseFee"
            :disabled="true"
            :precision="2"
            controls-position="right"
          />
          <span class="text-secondary ml-base">{{ currencyCode }}</span>
        </el-form-item>
      </el-form>

      <!-- 重量分段计价表 -->
      <el-table :data="weightBands" border>
        <el-table-column prop="start" label="起始重量(kg)">
          <template #default="{ row }">
            {{ row.start.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="end" label="结束重量(kg)">
          <template #default="{ row }">
            {{ row.end === Infinity ? '无限' : row.end.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="price" label="单价">
          <template #default="{ row }">
            {{ formatCurrency(row.price) }}
          </template>
        </el-table-column>
        <el-table-column prop="type" label="计价方式">
          <template #default="{ row }">
            {{ row.type === 'per_kg' ? '每公斤' : '每票' }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 计算过程 -->
      <CalculationSteps v-if="calculation" :steps="calculation.steps" title="计算过程" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watch, reactive } from 'vue';
  import {
    Position as Calculate,
    Refresh,
    InfoFilled
  } from '@element-plus/icons-vue';
  import { CalculationSteps } from '@/components/calculator';
  import { ElMessage } from 'element-plus';
  import type { WeightUnit, DimensionUnit, CalculationResult } from '@/types/calculator';

  interface WeightBand {
    start: number;
    end: number;
    price: number;
    type: 'per_kg' | 'per_shipment';
  }

  interface CalculationStep {
    description: string;
    formula: string;
  }

  interface Calculation {
    steps: CalculationStep[];
    total: number;
  }

  interface BaseFeeForm {
    actualWeight: number;
    length: number;
    width: number;
    height: number;
    weightUnit: WeightUnit;
    dimensionUnit: DimensionUnit;
  }

  interface Props {
    weightUnit?: WeightUnit;
    dimensionUnit?: DimensionUnit;
    dimFactor?: number;
    minWeight?: number;
    maxWeight?: number;
    minDimension?: number;
    maxDimension?: number;
    productId?: string;
    zone?: string;
  }

  const props = withDefaults(defineProps<Props>(), {
    weightUnit: 'KG',
    dimensionUnit: 'CM',
    dimFactor: 5000,
    minWeight: 0.1,
    maxWeight: 999999,
    minDimension: 0,
    maxDimension: 999999,
    productId: '',
    zone: ''
  });

  const emit = defineEmits<{
    (e: 'calculate', result: CalculationResult): void;
    (e: 'reset'): void;
  }>();

  const form = reactive<BaseFeeForm>({
    actualWeight: 0,
    length: 0,
    width: 0,
    height: 0,
    weightUnit: props.weightUnit,
    dimensionUnit: props.dimensionUnit
  });

  // 重量分段数据
  const weightBands = ref<WeightBand[]>([]);

  // 计算过程
  const calculation = ref<Calculation | null>(null);

  // 计算体积重
  const volumetricWeight = computed((): number => {
    const { length, width, height } = form;
    if (!length || !width || !height) return 0;
    
    // 转换单位（如果需要）
    const factor = form.dimensionUnit === 'IN' ? 2.54 : 1; // 英寸转厘米
    const volumeInCm = length * width * height * Math.pow(factor, 3);
    
    return volumeInCm / props.dimFactor;
  });

  // 计算计费重量
  const chargeableWeight = computed((): number => {
    const actualWeight = form.weightUnit === 'LB' ? form.actualWeight * 0.453592 : form.actualWeight;
    return Math.max(actualWeight, volumetricWeight.value);
  });

  // 计算基础运费
  const baseFee = ref(0);

  // 单位
  const weightUnit = 'KG';
  const dimUnit = 'CM';
  const currencyCode = 'CNY';

  // 获取重量分段数据
  const fetchWeightBands = async () => {
    try {
      const response = await fetch(
        `/api/products/${props.productId}/weight-bands?zone=${props.zone}`,
      );
      weightBands.value = await response.json();
    } catch (error) {
      console.error('获取重量分段数据失败:', error);
    }
  };

  // 验证表单
  const validateForm = (): boolean => {
    if (!form.actualWeight || form.actualWeight < props.minWeight) {
      ElMessage.error(`实际重量必须大于${props.minWeight}${form.weightUnit}`);
      return false;
    }

    if (form.actualWeight > props.maxWeight) {
      ElMessage.error(`实际重量不能超过${props.maxWeight}${form.weightUnit}`);
      return false;
    }

    const dimensions = [form.length, form.width, form.height];
    if (dimensions.some(d => !d || d < props.minDimension)) {
      ElMessage.error(`尺寸必须大于${props.minDimension}${form.dimensionUnit}`);
      return false;
    }

    if (dimensions.some(d => d > props.maxDimension)) {
      ElMessage.error(`尺寸不能超过${props.maxDimension}${form.dimensionUnit}`);
      return false;
    }

    return true;
  };

  // 计算费用
  const calculate = async () => {
    if (!validateForm()) return;

    try {
      const currentWeight = chargeableWeight.value;
      const band = weightBands.value.find(b => currentWeight >= b.start && currentWeight <= b.end);
      
      if (!band) {
        ElMessage.error('未找到匹配的重量段');
        return;
      }

      const fee = band.type === 'per_kg' ? currentWeight * band.price : band.price;
      baseFee.value = fee;

      calculation.value = {
        steps: [
          {
            description: '计算体积重',
            formula: `${form.length} × ${form.width} × ${form.height} ÷ ${props.dimFactor} = ${volumetricWeight.value.toFixed(2)}${weightUnit}`
          },
          {
            description: '确定计费重量',
            formula: `max(${form.actualWeight}, ${volumetricWeight.value.toFixed(2)}) = ${chargeableWeight.value.toFixed(2)}${weightUnit}`
          },
          {
            description: '计算基础运费',
            formula: band.type === 'per_kg'
              ? `${chargeableWeight.value.toFixed(2)} × ${band.price} = ${fee.toFixed(2)}${currencyCode}`
              : `${band.price}${currencyCode} (固定费率)`
          }
        ],
        total: fee
      };

      emit('calculate', {
        requestId: Date.now().toString(),
        baseCharge: parseFloat(fee.toFixed(2)),
        fuelSurcharge: 0,
        totalCharge: parseFloat(fee.toFixed(2)),
        currency: 'CNY',
        details: {
          weightCharge: parseFloat(fee.toFixed(2)),
          distanceCharge: 0,
          zoneCharge: 0,
          additionalCharges: []
        }
      });
    } catch (error) {
      console.error('计算失败:', error);
      ElMessage.error('计算失败，请重试');
    }
  };

  // 重置表单
  const reset = () => {
    Object.assign(form, {
      actualWeight: 0,
      length: 0,
      width: 0,
      height: 0,
      weightUnit: props.weightUnit,
      dimensionUnit: props.dimensionUnit
    });
    calculation.value = null;
    baseFee.value = 0;
    emit('reset');
  };

  // 格式化货币
  const formatCurrency = (value: number): string => {
    return `${value.toFixed(2)} ${currencyCode}`;
  };

  // 监听属性变化
  watch(
    () => [props.productId, props.zone],
    async ([newProductId, newZone]) => {
      if (newProductId && newZone) {
        await fetchWeightBands();
        await calculate();
      }
    },
    { immediate: true },
  );

  // 暴露给父组件的方法
  defineExpose({
    reset,
    calculate,
    form
  });
</script>

<style scoped>
  .calculator {
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

      .form-section {
        margin-bottom: var(--spacing-large);

        .section-title {
          font-size: var(--font-size-medium);
          font-weight: var(--font-weight-medium);
          color: var(--text-color-primary);
          margin-bottom: var(--spacing-base);
        }

        .form-row {
          display: flex;
          gap: var(--spacing-base);
          margin-bottom: var(--spacing-base);

          .form-item {
            flex: 1;
            min-width: 0;
          }
        }
      }
    }

    .calculator-footer {
      padding: var(--spacing-base);
      border-top: 1px solid var(--border-color);
      background-color: var(--bg-color-light);
      display: flex;
      justify-content: flex-end;
      gap: var(--spacing-base);
    }

    .result-section {
      margin-top: var(--spacing-large);
      padding: var(--spacing-base);
      background-color: var(--bg-color-light);
      border-radius: var(--border-radius-base);

      .result-title {
        font-size: var(--font-size-medium);
        font-weight: var(--font-weight-medium);
        color: var(--text-color-primary);
        margin-bottom: var(--spacing-base);
      }

      .result-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-small) 0;

        .item-label {
          color: var(--text-color-regular);
        }

        .item-value {
          font-weight: var(--font-weight-medium);
          color: var(--text-color-primary);

          &.highlight {
            color: var(--color-primary);
            font-size: var(--font-size-large);
          }
        }
      }
    }
  }
</style>
