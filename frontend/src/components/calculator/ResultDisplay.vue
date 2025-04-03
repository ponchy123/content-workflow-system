<template>
  <div class="result-display">
    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <span>计算结果</span>
          <el-button type="primary" link @click="handleSave">保存</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="基础运费">{{ formatCurrency(result.baseCharge) }}</el-descriptions-item>
        <el-descriptions-item label="燃油附加费">{{ formatCurrency(result.fuelSurcharge) }}</el-descriptions-item>
        <el-descriptions-item label="总费用">
          <span class="total-charge">{{ formatCurrency(result.totalCharge) }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <div class="details-section" v-if="result.details">
        <h4>费用明细</h4>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="重量费用">
            {{ formatCurrency(result.details.weightCharge) }}
          </el-descriptions-item>
          <el-descriptions-item label="距离费用">
            {{ formatCurrency(result.details.distanceCharge) }}
          </el-descriptions-item>
          <el-descriptions-item label="区域费用">
            {{ formatCurrency(result.details.zoneCharge) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="result.details.volumeCharge" label="体积费用">
            {{ formatCurrency(result.details.volumeCharge) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="result.details.additionalCharges?.length" class="additional-charges">
          <h4>附加费用</h4>
          <el-table :data="result.details.additionalCharges" border stripe>
            <el-table-column prop="name" label="费用名称" />
            <el-table-column prop="type" label="费用类型" />
            <el-table-column prop="amount" label="金额">
              <template #default="{ row }">
                {{ formatCurrency(row.amount) }}
              </template>
            </el-table-column>
            <el-table-column v-if="showDescription" prop="description" label="说明" show-overflow-tooltip />
          </el-table>
        </div>
      </div>

      <div class="actions">
        <el-button type="primary" @click="handleSave">保存结果</el-button>
        <el-button @click="handlePrint">打印</el-button>
        <el-button @click="handleExport">导出</el-button>
      </div>
    </el-card>

    <el-empty v-else description="暂无计算结果" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElMessage } from 'element-plus';
import type { CalculationResult, CalculationRequest, CalculationHistory } from '@/types/calculator';
import { saveCalculationResult } from '@/api/calculator/index';
import { formatCurrency as formatCurrencyUtil } from '@/utils/format';

interface Props {
  result?: CalculationResult | CalculationHistory;
  showDescription?: boolean;
  allowSave?: boolean;
  allowPrint?: boolean;
  allowExport?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showDescription: false,
  allowSave: true,
  allowPrint: true,
  allowExport: true
});

const emit = defineEmits<{
  (e: 'save', result: CalculationResult): void;
  (e: 'print', result: CalculationResult): void;
  (e: 'export', result: CalculationResult): void;
}>();

// 添加统一的货币格式化函数
const formatCurrency = (amount: number): string => {
  if (!props.result) return formatCurrencyUtil(amount);
  
  // 使用结果中的货币信息
  const currency = props.result.currency || 'USD';
  return formatCurrencyUtil(amount, currency);
};

// 处理保存结果
const handleSave = async () => {
  if (!props.result) return;
  
  try {
    if ('request' in props.result) {
      await saveCalculationResult(props.result.request);
    } else {
      ElMessage.error('无法保存结果：缺少原始请求数据');
      return;
    }
    emit('save', props.result);
    ElMessage.success('保存成功');
  } catch (error) {
    ElMessage.error('保存失败');
  }
};

// 处理打印
const handlePrint = () => {
  if (!props.result) return;
  emit('print', props.result);
  window.print();
};

// 处理导出
const handleExport = () => {
  if (!props.result) return;
  emit('export', props.result);
};

// 计算总附加费用
const totalAdditionalCharges = computed((): number => {
  if (!props.result?.details.additionalCharges?.length) return 0;
  return props.result.details.additionalCharges.reduce((sum, charge) => sum + charge.amount, 0);
});
</script>

<style scoped>
.result-display {
  width: 100%;
}

.result-card {
  margin-bottom: var(--el-spacing-large);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-charge {
  font-size: var(--el-font-size-large);
  font-weight: bold;
  color: var(--el-color-danger);
}

.details-section {
  margin-top: var(--el-spacing-large);
}

.details-section h4 {
  margin: var(--el-spacing-base) 0;
  color: var(--el-text-color-primary);
}

.additional-charges {
  margin-top: var(--el-spacing-large);
}

.actions {
  margin-top: var(--el-spacing-large);
  display: flex;
  gap: var(--el-spacing-base);
  justify-content: flex-end;
}

@media print {
  .actions {
    display: none;
  }
}
</style>
