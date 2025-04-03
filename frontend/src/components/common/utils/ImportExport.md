# ImportExport 导入导出

用于数据导入导出的组合组件，支持模板下载、文件导入、字段选择导出等功能。

## 基础用法

```vue
<template>
  <import-export
    :export-fields="exportFields"
    @template-download="handleTemplateDownload"
    @export="handleExport"
  />
</template>

<script setup lang="ts">
const exportFields = [
  { label: '姓名', value: 'name' },
  { label: '年龄', value: 'age' },
  { label: '邮箱', value: 'email' }
];

const handleTemplateDownload = () => {
  window.open('/api/template/download');
};

const handleExport = (fields: string[], form: any) => {
  console.log('导出字段:', fields);
  console.log('导出条件:', form);
};
</script>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| showImport | 是否显示导入按钮 | boolean | true |
| showExport | 是否显示导出按钮 | boolean | true |
| importText | 导入按钮文本 | string | '导入' |
| exportText | 导出按钮文本 | string | '导出' |
| importButtonType | 导入按钮类型 | string | 'primary' |
| exportButtonType | 导出按钮类型 | string | 'primary' |
| importIcon | 导入按钮图标 | string | 'Upload' |
| exportIcon | 导出按钮图标 | string | 'Download' |
| size | 按钮尺寸 | 'large'/'default'/'small' | 'default' |
| importDialogTitle | 导入对话框标题 | string | '导入数据' |
| exportDialogTitle | 导出对话框标题 | string | '导出数据' |
| dialogWidth | 对话框宽度 | string/number | '600px' |
| showFieldSelect | 是否显示字段选择 | boolean | true |
| fieldSelectLabel | 字段选择标签 | string | '导出字段' |
| exportFields | 可导出字段配置 | ExportField[] | [] |
| importProps | 导入组件的属性 | object | {} |

## Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| template-download | 点击下载模板时触发 | - |
| before-upload | 上传文件之前的钩子 | (file: File) |
| import-progress | 文件上传时的钩子 | (evt: any, file: any) |
| import-success | 文件上传成功时的钩子 | (response: any, file: any) |
| import-error | 文件上传失败时的钩子 | (error: Error, file: any) |
| export | 点击确认导出时触发 | (fields: string[], form: any) |

## Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| openImport | 打开导入对话框 | - |
| openExport | 打开导出对话框 | - |
| closeImport | 关闭导入对话框 | - |
| closeExport | 关闭导出对话框 | - |

## Slots

| 名称 | 说明 | 作用域参数 |
|------|------|------------|
| export-form | 自定义导出表单内容 | { form: any } |

## 示例

### 自定义按钮

```vue
<template>
  <import-export
    import-text="批量导入"
    export-text="批量导出"
    import-button-type="success"
    export-button-type="warning"
    import-icon="Plus"
    export-icon="Download"
    size="small"
  />
</template>
```

### 自定义导出表单

```vue
<template>
  <import-export
    :export-fields="exportFields"
    @export="handleExport"
  >
    <template #export-form="{ form }">
      <el-form-item label="开始日期">
        <el-date-picker
          v-model="form.startDate"
          type="date"
          placeholder="选择开始日期"
        />
      </el-form-item>
      <el-form-item label="结束日期">
        <el-date-picker
          v-model="form.endDate"
          type="date"
          placeholder="选择结束日期"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="form.status" placeholder="选择状态">
          <el-option label="全部" value="" />
          <el-option label="启用" value="1" />
          <el-option label="禁用" value="0" />
        </el-select>
      </el-form-item>
    </template>
  </import-export>
</template>

<script setup lang="ts">
const exportFields = [
  { label: '订单号', value: 'orderNo' },
  { label: '商品名称', value: 'productName' },
  { label: '订单金额', value: 'amount' },
  { label: '下单时间', value: 'createTime' },
  { label: '订单状态', value: 'status' }
];

const handleExport = (fields: string[], form: any) => {
  // 处理导出请求
  const params = {
    fields,
    startDate: form.startDate,
    endDate: form.endDate,
    status: form.status
  };
  console.log('导出参数:', params);
};
</script>
```

### 完整示例

```vue
<template>
  <import-export
    ref="importExportRef"
    :import-props="{
      action: '/api/import',
      headers: { Authorization: 'Bearer token' },
      accept: '.xlsx,.xls',
      tip: '只能上传 Excel 文件'
    }"
    :export-fields="exportFields"
    @template-download="handleTemplateDownload"
    @before-upload="handleBeforeUpload"
    @import-success="handleImportSuccess"
    @import-error="handleImportError"
    @export="handleExport"
  >
    <template #export-form="{ form }">
      <el-form-item
        label="关键词"
        prop="keyword"
      >
        <el-input
          v-model="form.keyword"
          placeholder="请输入关键词"
        />
      </el-form-item>
    </template>
  </import-export>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { UploadFile } from 'element-plus';

const importExportRef = ref();

const exportFields = [
  { label: '用户ID', value: 'userId' },
  { label: '用户名', value: 'username' },
  { label: '手机号', value: 'mobile' },
  { label: '注册时间', value: 'registerTime' }
];

const handleTemplateDownload = () => {
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

const handleImportSuccess = (response: any) => {
  ElMessage.success(`成功导入 ${response.successCount} 条数据`);
};

const handleImportError = (error: Error) => {
  ElMessage.error(error.message || '导入失败');
};

const handleExport = async (fields: string[], form: any) => {
  try {
    const response = await fetch('/api/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fields,
        keyword: form.keyword
      })
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '导出数据.xlsx';
    link.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    ElMessage.error('导出失败');
  }
};
</script>
```

## 注意事项

1. 导入功能基于 `ImportTemplateHelper` 组件实现
2. 导出功能支持字段选择和自定义条件
3. 可以通过 `ref` 调用组件方法控制对话框
4. 建议在导出大量数据时显示加载状态
5. 可以通过 `importProps` 配置导入组件的详细属性 