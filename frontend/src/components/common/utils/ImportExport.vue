<template>
  <div class="import-export">
    <!-- 导入导出按钮组 -->
    <div class="import-export__actions">
      <!-- 导入按钮 -->
      <el-button
        v-if="showImport"
        :type="importButtonType"
        :icon="importIcon"
        :size="size"
        @click="handleImportClick"
      >
        {{ importText }}
      </el-button>

      <!-- 导出按钮 -->
      <el-button
        v-if="showExport"
        :type="exportButtonType"
        :icon="exportIcon"
        :size="size"
        :loading="exporting"
        @click="handleExportClick"
      >
        {{ exportText }}
      </el-button>
    </div>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="importVisible"
      :title="importDialogTitle"
      :width="dialogWidth"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <import-template-helper
        ref="importRef"
        v-bind="importProps"
        @download="handleTemplateDownload"
        @before-upload="handleBeforeUpload"
        @progress="handleProgress"
        @success="handleSuccess"
        @error="handleError"
      />
    </el-dialog>

    <!-- 导出对话框 -->
    <el-dialog
      v-model="exportVisible"
      :title="exportDialogTitle"
      :width="dialogWidth"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="exportFormRef" :model="exportForm" label-width="100px" @submit.prevent>
        <!-- 导出字段选择 -->
        <el-form-item v-if="showFieldSelect" :label="fieldSelectLabel">
          <el-checkbox-group v-model="selectedFields">
            <el-checkbox v-for="field in exportFields" :key="field.value" :label="field.value">
              {{ field.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 导出条件 -->
        <slot name="export-form" :form="exportForm" />
      </el-form>

      <template #footer>
        <el-button @click="exportVisible = false"> 取消 </el-button>
        <el-button type="primary" :loading="exporting" @click="handleExport"> 确认导出 </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import type { FormInstance } from 'element-plus';
  import ImportTemplateHelper from './ImportTemplateHelper.vue';

  interface ExportField {
    label: string;
    value: string;
  }

  interface Props {
    showImport?: boolean;
    showExport?: boolean;
    importText?: string;
    exportText?: string;
    importButtonType?: '' | 'text' | 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger';
    exportButtonType?: '' | 'text' | 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger';
    importIcon?: string;
    exportIcon?: string;
    size?: 'large' | 'default' | 'small';
    importDialogTitle?: string;
    exportDialogTitle?: string;
    dialogWidth?: string | number;
    showFieldSelect?: boolean;
    fieldSelectLabel?: string;
    exportFields?: ExportField[];
    importProps: { action: string } & Record<string, any>;
  }

  const props = withDefaults(defineProps<Props>(), {
    showImport: true,
    showExport: true,
    importText: '导入',
    exportText: '导出',
    importButtonType: 'primary',
    exportButtonType: 'primary',
    importIcon: 'Upload',
    exportIcon: 'Download',
    size: 'default',
    importDialogTitle: '导入数据',
    exportDialogTitle: '导出数据',
    dialogWidth: '600px',
    showFieldSelect: true,
    fieldSelectLabel: '导出字段',
    exportFields: () => [],
    importProps: () => ({ action: '/api/import' }),
  });

  const emit = defineEmits<{
    (e: 'template-download'): void;
    (e: 'before-upload', file: File): void | boolean | Promise<File>;
    (e: 'import-progress', evt: any, file: any): void;
    (e: 'import-success', response: any, file: any): void;
    (e: 'import-error', error: Error, file: any): void;
    (e: 'export', fields: string[], form: any): void;
  }>();

  const importRef = ref();
  const exportFormRef = ref<FormInstance>();
  const importVisible = ref(false);
  const exportVisible = ref(false);
  const exporting = ref(false);
  const exportForm = ref<Record<string, any>>({});
  const selectedFields = ref<string[]>([]);

  // 处理导入点击
  const handleImportClick = () => {
    importVisible.value = true;
  };

  // 处理导出点击
  const handleExportClick = () => {
    exportVisible.value = true;
    selectedFields.value = props.exportFields.map(field => field.value);
  };

  // 处理模板下载
  const handleTemplateDownload = () => {
    emit('template-download');
  };

  // 处理上传前
  const handleBeforeUpload = (file: File) => {
    return emit('before-upload', file);
  };

  // 处理上传进度
  const handleProgress = (evt: any, file: any) => {
    emit('import-progress', evt, file);
  };

  // 处理上传成功
  const handleSuccess = (response: any, file: any) => {
    emit('import-success', response, file);
    importVisible.value = false;
  };

  // 处理上传失败
  const handleError = (error: Error, file: any) => {
    emit('import-error', error, file);
  };

  // 处理导出
  const handleExport = async () => {
    try {
      exporting.value = true;
      await emit('export', selectedFields.value, exportForm.value);
      exportVisible.value = false;
    } finally {
      exporting.value = false;
    }
  };

  // 对外暴露方法
  defineExpose({
    openImport: () => (importVisible.value = true),
    openExport: () => (exportVisible.value = true),
    closeImport: () => (importVisible.value = false),
    closeExport: () => (exportVisible.value = false),
  });
</script>

<style>
  .import-export {
    display: inline-block;
  }

  .import-export__actions {
    display: flex;
    gap: var(--spacing-sm);
  }
</style>
