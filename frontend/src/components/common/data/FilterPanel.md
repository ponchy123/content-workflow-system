# FilterPanel 筛选面板

用于数据筛选的可折叠面板组件，支持多种输入类型和自定义字段。

## 基础用法

```vue
<template>
  <filter-panel
    v-model="filterData"
    :fields="fields"
    title="筛选条件"
    @change="handleFilterChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';

const filterData = ref({});

const fields = [
  {
    prop: 'keyword',
    label: '关键词',
    type: 'input',
    placeholder: '请输入关键词'
  },
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '全部', value: '' },
      { label: '启用', value: 1 },
      { label: '禁用', value: 0 }
    ]
  },
  {
    prop: 'date',
    label: '日期',
    type: 'daterange',
    startPlaceholder: '开始日期',
    endPlaceholder: '结束日期'
  }
];

const handleFilterChange = (field: string, value: any) => {
  console.log('字段变化:', field, value);
};
</script>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| modelValue | 筛选数据对象 | object | {} |
| fields | 筛选字段配置数组 | FilterField[] | [] |
| title | 面板标题 | string | - |
| labelWidth | 标签宽度 | string/number | 100 |
| labelPosition | 标签位置 | 'right'/'left'/'top' | 'right' |
| size | 组件尺寸 | 'large'/'default'/'small' | 'default' |
| gutter | 字段间距 | number | 20 |
| defaultSpan | 默认字段宽度 | number | 6 |
| collapsible | 是否可折叠 | boolean | true |
| clearable | 是否可清空 | boolean | true |

## FilterField 配置

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| prop | 字段属性名 | string | - |
| label | 字段标签 | string | - |
| type | 字段类型 | 'input'/'select'/'date'/'daterange'/string | - |
| placeholder | 占位文本 | string | - |
| startPlaceholder | 范围选择起始占位文本 | string | - |
| endPlaceholder | 范围选择结束占位文本 | string | - |
| options | 选择器选项 | { label: string; value: any; disabled?: boolean }[] | - |
| component | 自定义组件名称 | string | - |
| props | 组件属性 | object | - |
| rules | 验证规则 | object[] | - |
| span | 字段宽度 | number | - |
| xs/sm/md/lg/xl | 响应式宽度 | number | - |

## Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| update:modelValue | 筛选数据更新 | (value: object) |
| change | 字段值变化 | (field: string, value: any) |
| clear | 清空筛选时触发 | - |

## Slots

| 名称 | 说明 | 作用域参数 |
|------|------|------------|
| title | 自定义标题 | - |
| footer | 自定义底部 | - |
| field-[prop] | 自定义字段内容 | { field, model } |

## Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| validate | 验证表单 | - |
| resetFields | 重置表单 | - |
| clearValidate | 清除验证信息 | (props?: string/string[]) |

## 示例

### 基础筛选

```vue
<filter-panel
  v-model="filterData"
  :fields="[
    {
      prop: 'keyword',
      label: '关键词',
      type: 'input'
    },
    {
      prop: 'status',
      label: '状态',
      type: 'select',
      options: statusOptions
    }
  ]"
/>
```

### 日期范围筛选

```vue
<filter-panel
  v-model="filterData"
  :fields="[
    {
      prop: 'dateRange',
      label: '日期范围',
      type: 'daterange',
      startPlaceholder: '开始日期',
      endPlaceholder: '结束日期',
      props: {
        valueFormat: 'YYYY-MM-DD'
      }
    }
  ]"
/>
```

### 自定义组件

```vue
<filter-panel
  v-model="filterData"
  :fields="[
    {
      prop: 'region',
      label: '地区',
      component: 'region-selector',
      props: {
        multiple: true
      }
    }
  ]"
>
  <template #field-custom="{ field, model }">
    <div>自定义字段内容</div>
  </template>
</filter-panel>
```

### 响应式布局

```vue
<filter-panel
  v-model="filterData"
  :fields="[
    {
      prop: 'name',
      label: '名称',
      type: 'input',
      span: 8,
      xs: 24,
      sm: 12,
      md: 8,
      lg: 6
    }
  ]"
/>
``` 