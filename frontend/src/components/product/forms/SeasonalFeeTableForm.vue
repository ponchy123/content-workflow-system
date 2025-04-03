<template>
  <TableForm 
    title="旺季附加费" 
    description="管理特定时间段的旺季附加费"
    :uses-mock-data="usesMockData"
    :saving="saving"
    @save="handleSaveSeasonalFees"
  >
    <SeasonalFeeForm 
      :seasonalFees="seasonalFees" 
      :productId="productId"
      mode="list"
      @change="handleSeasonalFeeChange"
      @save="handleSaveSeasonalFees"
    />
  </TableForm>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Check } from '@element-plus/icons-vue';
import SeasonalFeeForm from './SeasonalFeeForm.vue';
import TableForm from './TableForm.vue';

const props = defineProps<{
  seasonalFees: any[];
  usesMockData: boolean;
  saving: boolean;
  productId: string;
}>();

const emit = defineEmits<{
  (e: 'save', seasonalFees: any[]): void;
  (e: 'change', seasonalFees: any[]): void;
}>();

// 处理保存旺季附加费
const handleSaveSeasonalFees = () => {
  emit('save', props.seasonalFees);
};

// 处理旺季附加费变更
const handleSeasonalFeeChange = (newSeasonalFees: any[]) => {
  emit('change', newSeasonalFees);
};
</script>

<style scoped>
.form-section {
  margin-bottom: 24px;
  padding: 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.section-header-with-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
}

.section-description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 0;
}
</style> 