<template>
  <div class="import-template-helper">
    <!-- 模板下载 -->
    <div class="import-template-helper__download">
      <el-button
        :type="downloadButtonType"
        :icon="downloadIcon"
        :size="size"
        @click="handleDownload"
      >
        {{ downloadText }}
      </el-button>
    </div>

    <!-- 文件上传 -->
    <div class="import-template-helper__upload">
      <el-upload
        ref="uploadRef"
        v-bind="uploadProps"
        :action="action"
        :headers="headers"
        :data="data"
        :multiple="multiple"
        :accept="accept"
        :limit="limit"
        :auto-upload="autoUpload"
        :show-file-list="showFileList"
        :drag="drag"
        :disabled="disabled"
        :on-exceed="handleExceed"
        :before-upload="handleBeforeUpload"
        :on-progress="handleProgress"
        :on-success="handleSuccess"
        :on-error="handleError"
        :on-change="handleChange"
        :on-remove="handleRemove"
      >
        <template v-if="drag">
          <el-icon class="el-icon--upload">
            <upload-filled />
          </el-icon>
          <div class="el-upload__text">将文件拖到此处或<em>点击上传</em></div>
        </template>
        <template v-else>
          <el-button :type="uploadButtonType" :icon="uploadIcon" :size="size" :loading="loading">
            {{ uploadText }}
          </el-button>
        </template>
        <template v-if="tip" #tip>
          <div class="el-upload__tip">
            {{ tip }}
          </div>
        </template>
      </el-upload>
    </div>

    <!-- 导入进度 -->
    <div v-if="showProgress" class="import-template-helper__progress">
      <el-progress
        :percentage="progress"
        :status="progressStatus"
        :text-inside="true"
        :stroke-width="18"
      />
    </div>

    <!-- 导入结果 -->
    <div v-if="showResult" class="import-template-helper__result">
      <el-alert
        :title="resultTitle"
        :type="resultType"
        :description="resultDescription"
        :closable="false"
        show-icon
      />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import { UploadFilled } from '@element-plus/icons-vue';
  import type {
    UploadInstance,
    UploadProps,
    UploadUserFile,
    UploadRawFile,
  } from 'element-plus';

  interface Props {
    action: string;
    headers?: Record<string, string>;
    data?: Record<string, any>;
    multiple?: boolean;
    accept?: string;
    limit?: number;
    autoUpload?: boolean;
    showFileList?: boolean;
    drag?: boolean;
    disabled?: boolean;
    size?: 'large' | 'default' | 'small';
    downloadText?: string;
    downloadButtonType?: '' | 'text' | 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger';
    downloadIcon?: string;
    uploadText?: string;
    uploadButtonType?: '' | 'text' | 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger';
    uploadIcon?: string;
    tip?: string;
    uploadProps?: Partial<UploadProps>;
  }

  const props = withDefaults(defineProps<Props>(), {
    headers: () => ({}),
    data: () => ({}),
    multiple: false,
    accept: '.xlsx,.xls',
    limit: 1,
    autoUpload: true,
    showFileList: true,
    drag: false,
    disabled: false,
    size: 'default',
    downloadText: '下载模板',
    downloadButtonType: 'primary',
    downloadIcon: 'Download',
    uploadText: '上传文件',
    uploadButtonType: 'primary',
    uploadIcon: 'Upload',
    uploadProps: () => ({}),
  });

  const emit = defineEmits<{
    (e: 'download'): void;
    (e: 'exceed', files: File[], uploadFiles: UploadUserFile[]): void;
    (e: 'before-upload', file: UploadRawFile): void | boolean | Promise<void | Blob | File | null | undefined>;
    (e: 'progress', evt: ProgressEvent, file: UploadUserFile): void;
    (e: 'success', response: any, file: UploadUserFile): void;
    (e: 'error', error: Error, file: UploadUserFile): void;
    (e: 'change', file: UploadUserFile, uploadFiles: UploadUserFile[]): void;
    (e: 'remove', file: UploadUserFile, uploadFiles: UploadUserFile[]): void;
  }>();

  type UploadRef = UploadInstance & {
    clearFiles: (files?: UploadUserFile[]) => void;
    abort: (file: UploadUserFile) => void;
    handleStart: (file: UploadUserFile) => void;
    handleRemove: (file: UploadUserFile) => void;
  };

  const uploadRef = ref<UploadRef>();
  const loading = ref(false);
  const progress = ref(0);
  const showProgress = ref(false);
  const showResult = ref(false);
  const resultType = ref<'success' | 'warning' | 'error'>('success');
  const resultTitle = ref('');
  const resultDescription = ref('');

  // 计算进度状态
  const progressStatus = computed(() => {
    if (progress.value === 100) return 'success';
    return '';
  });

  // 处理下载
  const handleDownload = () => {
    emit('download');
  };

  // 处理超出限制
  const handleExceed = (files: File[], uploadFiles: UploadUserFile[]) => {
    emit('exceed', files, uploadFiles);
  };

  // 处理上传前
  const handleBeforeUpload = (file: UploadRawFile) => {
    loading.value = true;
    showProgress.value = true;
    showResult.value = false;
    progress.value = 0;
    return emit('before-upload', file);
  };

  // 处理上传进度
  const handleProgress = (evt: ProgressEvent, file: UploadUserFile) => {
    progress.value = Math.round(evt.loaded / evt.total * 100);
    emit('progress', evt, file);
  };

  // 处理上传成功
  const handleSuccess = (response: any, file: UploadUserFile) => {
    loading.value = false;
    showResult.value = true;
    resultType.value = 'success';
    resultTitle.value = '导入成功';
    resultDescription.value = `成功导入 ${response.successCount || 0} 条数据`;
    emit('success', response, file);
  };

  // 处理上传失败
  const handleError = (error: Error, file: UploadUserFile) => {
    loading.value = false;
    showResult.value = true;
    resultType.value = 'error';
    resultTitle.value = '导入失败';
    resultDescription.value = error.message || '文件上传失败，请重试';
    emit('error', error, file);
  };

  // 处理文件状态改变
  const handleChange = (file: UploadUserFile, uploadFiles: UploadUserFile[]) => {
    emit('change', file, uploadFiles);
  };

  // 处理移除文件
  const handleRemove = (file: UploadUserFile, uploadFiles: UploadUserFile[]) => {
    showProgress.value = false;
    showResult.value = false;
    emit('remove', file, uploadFiles);
  };

  // 对外暴露方法
  defineExpose({
    submit: () => uploadRef.value?.submit(),
    clearFiles: (files?: UploadUserFile[]) => uploadRef.value?.clearFiles(files),
    abort: (file: UploadUserFile) => uploadRef.value?.abort(file),
    handleStart: (file: UploadUserFile) => uploadRef.value?.handleStart(file),
    handleRemove: (file: UploadUserFile) => uploadRef.value?.handleRemove(file),
  });
</script>

<style>
  .import-template-helper {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .import-template-helper__download {
    display: flex;
    justify-content: flex-end;
  }

  .import-template-helper__upload {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .import-template-helper__progress {
    margin-top: var(--spacing-sm);
  }

  .import-template-helper__result {
    margin-top: var(--spacing-sm);
  }

  /* 拖拽上传样式 */
  .el-upload-dragger {
    width: 100%;
    height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
  }

  .el-upload-dragger .el-icon--upload {
    font-size: 48px;
    color: var(--el-text-color-secondary);
    margin-bottom: var(--spacing-sm);
  }

  .el-upload-dragger .el-upload__text {
    color: var(--el-text-color-regular);
    font-size: var(--font-size-base);
  }

  .el-upload-dragger .el-upload__text em {
    color: var(--el-color-primary);
    font-style: normal;
  }

  /* 暗色主题 */
  .dark .el-upload-dragger {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-darker);
  }
</style>
