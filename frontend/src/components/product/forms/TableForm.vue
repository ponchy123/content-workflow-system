<template>
  <div class="form-section">
    <div class="section-header-with-actions">
      <div class="section-header">
        <h2>{{ title }}</h2>
        <p class="section-description">{{ description }}</p>
      </div>
      <el-button type="primary" @click="handleSave" :loading="saving">
        <el-icon><Check /></el-icon>保存
      </el-button>
    </div>
    <div class="mock-data-notice" v-if="usesMockData">
      <el-alert
        title="当前显示的是模拟数据"
        type="warning"
        :closable="false"
        description="由于API返回数据为空或发生错误，系统生成了模拟数据用于展示。您可以编辑这些数据，但保存时可能会发生错误。"
      />
    </div>
    
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { Check } from '@element-plus/icons-vue';

const props = defineProps<{
  title: string;
  description: string;
  usesMockData: boolean;
  saving: boolean;
}>();

const emit = defineEmits<{
  (e: 'save'): void;
}>();

// 处理保存
const handleSave = () => {
  emit('save');
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