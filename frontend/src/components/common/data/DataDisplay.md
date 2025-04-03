# DataDisplay 数据展示组件

`DataDisplay` 组件是一个灵活的数据展示组件，支持表格、列表和卡片三种展示模式，并提供了加载状态、错误处理、分页和排序等功能。

## 功能特性

- 支持三种展示模式：表格、列表、卡片
- 统一的加载和错误状态处理
- 内置分页功能
- 支持数据排序
- 自定义渲染支持
- 响应式设计
- 主题定制

## 代码示例

### 基础表格模式

```vue
<template>
  <data-display
    :data="tableData"
    :columns="columns"
    :loading="loading"
    @sort-change="handleSortChange"
  />
</template>

<script setup lang="ts">
const columns = [
  { prop: 'date', label: '日期', sortable: true },
  { prop: 'name', label: '姓名' },
  { prop: 'address', label: '地址' }
];

const tableData = [
  {
    date: '2024-01-01',
    name: '张三',
    address: '北京市朝阳区'
  },
  // ...更多数据
];
</script>
```

### 列表模式

```vue
<template>
  <data-display
    display-mode="list"
    :data="listData"
    :columns="columns"
  >
    <template #list-item="{ item }">
      <div class="custom-list-item">
        <h3>{{ item.name }}</h3>
        <p>{{ item.description }}</p>
      </div>
    </template>
  </data-display>
</template>
```

### 卡片模式

```vue
<template>
  <data-display
    display-mode="card"
    :data="cardData"
    :columns="columns"
  >
    <template #card="{ item }">
      <div class="custom-card">
        <img :src="item.image" :alt="item.name">
        <h4>{{ item.name }}</h4>
        <p>{{ item.description }}</p>
      </div>
    </template>
  </data-display>
</template>
```

### 错误处理

```vue
<template>
  <data-display
    :data="[]"
    :columns="columns"
    :error="true"
    error-message="数据加载失败"
    @retry="handleRetry"
  />
</template>

<script setup lang="ts">
const handleRetry = () => {
  // 重新加载数据
  loadData();
};
</script>
```

### 自定义列渲染

```vue
<template>
  <data-display
    :data="tableData"
    :columns="columns"
  >
    <template #column-status="{ value }">
      <el-tag :type="getTagType(value)">
        {{ value }}
      </el-tag>
    </template>
    
    <template #column-actions="{ row }">
      <el-button @click="handleEdit(row)">编辑</el-button>
    </template>
  </data-display>
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| data | array | - | 要展示的数据数组（必填） |
| columns | Column[] | - | 列配置数组（必填） |
| displayMode | 'table' \| 'list' \| 'card' | 'table' | 展示模式 |
| loading | boolean | false | 是否显示加载状态 |
| error | boolean | false | 是否显示错误状态 |
| errorMessage | string | '' | 错误提示信息 |
| emptyText | string | '暂无数据' | 空数据提示文本 |
| showPagination | boolean | true | 是否显示分页 |
| currentPage | number | 1 | 当前页码 |
| pageSize | number | 10 | 每页显示条数 |
| pageSizes | number[] | [10, 20, 50, 100] | 可选的每页条数 |
| total | number | 0 | 数据总条数 |
| paginationLayout | string | 'total, sizes, prev, pager, next, jumper' | 分页组件布局 |
| tableProps | object | {} | 传递给 el-table 的属性 |
| itemKey | string \| function | 'id' | 数据项的唯一标识 |

### Column 类型定义

```typescript
interface Column {
  prop: string;        // 数据字段名
  label: string;       // 列标题
  sortable?: boolean;  // 是否可排序
  width?: number | string; // 列宽度
  [key: string]: any; // 其他 el-table-column 支持的属性
}
```

## Events

| 事件名 | 参数 | 说明 |
|-------|------|------|
| update:currentPage | (page: number) | 当前页改变时触发 |
| update:pageSize | (size: number) | 每页条数改变时触发 |
| sort-change | ({ prop: string, order: string }) | 排序条件改变时触发 |
| retry | - | 点击重试按钮时触发 |

## Slots

| 插槽名 | 作用域参数 | 说明 |
|-------|------------|------|
| empty | - | 自定义空数据展示 |
| column-[prop] | { row, column, value } | 自定义列渲染 |
| list-item | { item, index } | 自定义列表项渲染 |
| card | { item, index } | 自定义卡片渲染 |
| table-append | - | 表格追加内容 |

## 样式定制

组件使用 CSS 变量进行样式定制，主要变量包括：

```css
:root {
  --data-display-padding: 16px;
  --data-display-item-padding: 12px;
  --border-width-base: 1px;
  --border-style-base: solid;
  --border-color-base: #dcdfe6;
  --border-radius-base: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
}
```

## 最佳实践

1. 展示模式选择：
   - 表格模式：适合结构化数据展示，特别是需要排序和比较的场景
   - 列表模式：适合简单的数据展示，或需要更灵活布局的场景
   - 卡片模式：适合图文混合展示，或需要网格布局的场景

2. 性能优化：
   - 合理设置每页显示条数
   - 使用服务端分页处理大量数据
   - 避免在卡片模式下同时显示过多数据

3. 自定义渲染：
   - 使用具名插槽自定义特定列的渲染
   - 保持渲染函数的简洁和高效
   - 注意作用域插槽参数的使用

4. 错误处理：
   - 提供清晰的错误提示
   - 实现重试机制
   - 保持用户界面的可用性

## 注意事项

1. 数据格式：
   - 确保数据项具有唯一标识
   - 数据结构与列定义匹配
   - 处理可能的空值或异常值

2. 响应式考虑：
   - 在不同屏幕尺寸下测试
   - 调整列的显示优先级
   - 确保移动端的可用性

3. 性能优化：
   - 避免频繁切换展示模式
   - 合理使用分页和懒加载
   - 优化自定义渲染的性能

4. 可访问性：
   - 提供键盘导航支持
   - 确保足够的颜色对比度
   - 添加适当的 ARIA 属性