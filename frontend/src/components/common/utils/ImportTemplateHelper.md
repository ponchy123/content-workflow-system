# ImportTemplateHelper 导入模板助手

用于文件导入场景的辅助组件，支持模板下载、文件上传、进度展示等功能。

## 基础用法

```vue
<template>
  <import-template-helper
    action="/api/import"
    @download="handleDownload"
    @success="handleSuccess"
  />
</template>

<script setup lang="ts">
const handleDownload = () => {
  // 处理模板下载
  window.open('/api/template/download');
};

const handleSuccess = (response: any) => {
  console.log('导入成功:', response);
};
</script>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| action | 上传的地址 | string | - |
| headers | 设置上传的请求头部 | object | {} |
| data | 上传时附带的额外参数 | object | {} |
| multiple | 是否支持多选文件 | boolean | false |
| accept | 接受上传的文件类型 | string | .xlsx,.xls |
| limit | 最大允许上传个数 | number | 1 |
| autoUpload | 是否在选取文件后立即进行上传 | boolean | true |
| showFileList | 是否显示已上传文件列表 | boolean | true |
| drag | 是否启用拖拽上传 | boolean | false |
| disabled | 是否禁用 | boolean | false |
| size | 组件尺寸 | 'large'/'default'/'small' | 'default' |
| downloadText | 下载按钮文本 | string | '下载模板' |
| downloadButtonType | 下载按钮类型 | string | 'primary' |
| downloadIcon | 下载按钮图标 | string | 'Download' |
| uploadText | 上传按钮文本 | string | '上传文件' |
| uploadButtonType | 上传按钮类型 | string | 'primary' |
| uploadIcon | 上传按钮图标 | string | 'Upload' |
| tip | 上传提示文本 | string | - |
| uploadProps | 上传组件的额外属性 | object | {} |

## Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| download | 点击下载模板时触发 | - |
| exceed | 文件超出个数限制时触发 | (files: File[], uploadFiles: UploadFile[]) |
| before-upload | 上传文件之前的钩子 | (file: File) |
| progress | 文件上传时的钩子 | (evt: any, file: UploadFile) |
| success | 文件上传成功时的钩子 | (response: any, file: UploadFile) |
| error | 文件上传失败时的钩子 | (error: Error, file: UploadFile) |
| change | 文件状态改变时的钩子 | (file: UploadFile, uploadFiles: UploadFile[]) |
| remove | 文件列表移除文件时的钩子 | (file: UploadFile, uploadFiles: UploadFile[]) |

## Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| submit | 手动上传文件 | - |
| clearFiles | 清空已上传的文件列表 | (files?: UploadFile[]) |
| abort | 取消上传请求 | (file: UploadFile) |
| handleStart | 手动选择文件 | (file: UploadFile) |
| handleRemove | 手动移除文件 | (file: UploadFile) |

## 示例

### 拖拽上传

```vue
<template>
  <import-template-helper
    action="/api/import"
    drag
    tip="只能上传 xlsx/xls 文件，且不超过 10MB"
  />
</template>
```

### 自定义按钮

```vue
<template>
  <import-template-helper
    action="/api/import"
    download-text="获取导入模板"
    download-button-type="success"
    upload-text="批量导入"
    upload-button-type="warning"
  />
</template>
```

### 手动上传

```vue
<template>
  <import-template-helper
    ref="importRef"
    action="/api/import"
    :auto-upload="false"
  >
    <template #tip>
      <el-button @click="submitUpload">
        开始上传
      </el-button>
    </template>
  </import-template-helper>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const importRef = ref();

const submitUpload = () => {
  importRef.value?.submit();
};
</script>
```

### 完整示例

```vue
<template>
  <import-template-helper
    action="/api/import"
    :headers="headers"
    :data="{ type: 'users' }"
    :limit="5"
    :multiple="true"
    drag
    tip="支持批量上传，单个文件不超过 10MB"
    @download="handleDownload"
    @before-upload="handleBeforeUpload"
    @success="handleSuccess"
    @error="handleError"
  />
</template>

<script setup lang="ts">
import type { UploadFile } from 'element-plus';

const headers = {
  Authorization: 'Bearer token'
};

const handleDownload = () => {
  window.open('/api/template/users');
};

const handleBeforeUpload = (file: File) => {
  const isExcel = /\.(xlsx|xls)$/.test(file.name);
  const isLt10M = file.size / 1024 / 1024 < 10;

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件！');
    return false;
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！');
    return false;
  }
  return true;
};

const handleSuccess = (response: any, file: UploadFile) => {
  ElMessage.success(`成功导入 ${response.successCount} 条数据`);
};

const handleError = (error: Error) => {
  ElMessage.error(error.message || '导入失败');
};
</script>
```

## 注意事项

1. 组件内置了上传进度和结果展示
2. 支持自定义上传按钮和下载按钮的样式
3. 可以通过 `uploadProps` 传递更多的 `el-upload` 属性
4. 建议设置合适的文件类型和大小限制
5. 可以使用 `ref` 调用组件方法实现更灵活的控制 