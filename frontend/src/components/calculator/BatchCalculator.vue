<template>
  <div class="batch-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3 class="card-title">{{ title }}</h3>
          <div class="card-actions">
            <slot name="actions"></slot>
          </div>
        </div>
      </template>

      <!-- 上传区域 -->
      <slot name="upload-area"></slot>

      <!-- 验证错误展示 -->
      <div v-if="validationErrors?.length" class="validation-errors">
        <el-alert title="数据验证失败" type="error" :closable="false" show-icon>
          <template #default>
            <ul class="error-list">
              <li v-for="error in validationErrors" :key="error.row">
                第 {{ error.row }} 行: {{ error.message }}
              </li>
            </ul>
          </template>
        </el-alert>
      </div>

      <!-- 数据预览 -->
      <slot name="preview"></slot>

      <!-- 计算结果 -->
      <div v-if="result" class="result-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务状态">
            <el-tag :type="getTaskStatusType(result.status)">
              {{ getTaskStatusLabel(result.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(result.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="文件名称">
            {{ result.file_name }}
          </el-descriptions-item>
          <el-descriptions-item label="总记录数">
            {{ result.total_records }}
          </el-descriptions-item>
          <el-descriptions-item label="处理进度">
            <el-progress :percentage="calculateProgress" :status="progressStatus" />
          </el-descriptions-item>
          <el-descriptions-item label="处理结果">
            <div class="flex gap-base">
              <span class="text-success">成功: {{ result.success_records }}</span>
              <span class="text-danger">失败: {{ result.failed_records }}</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <slot name="result-details"></slot>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import type { BatchCalculationTask, BatchCalculationStatus } from '@/types/calculator';
  import { formatDateTime } from '@/utils/format';

  type ProgressStatus = '' | 'success' | 'exception' | 'warning';

  const props = defineProps<{
    title?: string;
    result?: BatchCalculationTask;
    validationErrors?: Array<{ row: number; message: string }>;
  }>();

  const calculateProgress = computed(() => {
    if (!props.result) return 0;
    return Math.round((props.result.processed_records / props.result.total_records) * 100);
  });

  const progressStatus = computed<ProgressStatus>(() => {
    if (!props.result) return '';
    if (props.result.status === 'completed') return 'success';
    if (props.result.status === 'failed') return 'exception';
    return 'warning';
  });

  const getTaskStatusType = (status: BatchCalculationStatus): 'success' | 'danger' | 'warning' | 'info' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'danger';
      case 'processing':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getTaskStatusLabel = (status: BatchCalculationStatus): string => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'processing':
        return '处理中';
      case 'pending':
        return '等待处理';
      default:
        return '未知状态';
    }
  };
</script>

<style scoped>
  .batch-calculator {
    width: 100%;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-title {
    margin: 0;
    font-size: var(--el-font-size-large);
    font-weight: 500;
  }

  .validation-errors {
    margin: var(--el-spacing-base) 0;
  }

  .error-list {
    margin: var(--el-spacing-small) 0 0;
    padding-left: var(--el-spacing-large);
  }

  .error-list li {
    color: var(--el-color-danger);
    margin: var(--el-spacing-extra-small) 0;
  }

  .result-content {
    margin-top: var(--el-spacing-base);
  }

  .flex {
    display: flex;
  }

  .gap-base {
    gap: var(--el-spacing-base);
  }

  .text-success {
    color: var(--el-color-success);
  }

  .text-danger {
    color: var(--el-color-danger);
  }
</style>
