<template>
  <TableForm 
    title="附加费" 
    description="管理各种附加费，包括处理费、超大尺寸费等"
    :uses-mock-data="usesMockData"
    :saving="saving"
    @save="handleSurchargesSave"
  >
    <SurchargeForm 
      :surcharges="surcharges" 
      :productId="productId"
      mode="list"
      @change="handleSurchargeChange"
      @save="handleSurchargesSave"
    />
  </TableForm>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Check } from '@element-plus/icons-vue';
import SurchargeForm from './SurchargeForm.vue';
import TableForm from './TableForm.vue';

const props = defineProps<{
  surcharges: any[];
  availableZones: any[];
  usesMockData: boolean;
  saving: boolean;
  productId: string;
}>();

const emit = defineEmits<{
  (e: 'save', surcharges: any[]): void;
  (e: 'change', surcharges: any[]): void;
}>();

// 处理保存附加费
const handleSurchargesSave = () => {
  emit('save', props.surcharges);
};

// 处理附加费变更
const handleSurchargeChange = (newSurcharges: any[]) => {
  emit('change', newSurcharges);
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