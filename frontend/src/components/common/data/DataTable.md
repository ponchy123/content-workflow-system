# DataTable 数据表格组件

`DataTable` 是一个功能丰富的数据表格组件，基于 Element Plus 的 `el-table` 组件扩展，提供了更多开箱即用的功能。

## 功能特性

- 多种展示模式：表格、列表、卡片
- 内置加载状态和错误处理
- 支持分页和排序
- 自定义列渲染
- 支持选择和操作列
- 响应式设计

## 代码示例

### 基础用法

```vue
<template>
  <data-table
    :data="tableData"
    :columns="columns"
    :loading="loading"
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
  }
  // ... 更多数据
];
</script>
```

### 带工具栏和操作列

```vue
<template>
  <data-table
    :data="tableData"
    :columns="columns"
  >
    <template #toolbar>
      <el-button type="primary" @click="handleAdd">
        新增
      </el-button>
      <el-button @click="handleExport">
        导出
      </el-button>
    </template>

    <template #actions="{ row }">
      <el-button type="text" @click="handleEdit(row)">
        编辑
      </el-button>
      <el-button type="text" @click="handleDelete(row)">
        删除
      </el-button>
    </template>
  </data-table>
</template>
```

### 自定义列渲染

```vue
<template>
  <data-table
    :data="tableData"
    :columns="columns"
    :status-map="statusMap"
  >
    <!-- 金额列 -->
    <template #column-amount="{ value }">
      {{ formatCurrency(value) }}
    </template>

    <!-- 日期列 -->
    <template #column-date="{ value }">
      {{ formatDate(value, 'YYYY-MM-DD HH:mm:ss') }}
    </template>

    <!-- 状态列 -->
    <template #column-status="{ value }">
      <status-tag :type="value.type" :text="value.text" />
    </template>
  </data-table>
</template>

<script setup lang="ts">
const statusMap = {
  pending: { type: 'warning', text: '待处理' },
  processing: { type: 'primary', text: '处理中' },
  completed: { type: 'success', text: '已完成' },
  failed: { type: 'danger', text: '失败' }
};
</script>
```

### 可选择表格

```vue
<template>
  <data-table
    :data="tableData"
    :columns="columns"
    :selectable="true"
    @selection-change="handleSelectionChange"
  >
    <template #toolbar>
      <el-button
        type="danger"
        :disabled="!selectedRows.length"
        @click="handleBatchDelete"
      >
        批量删除
      </el-button>
    </template>
  </data-table>
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| data | array | - | 表格数据（必填） |
| columns | Column[] | - | 列配置（必填） |
| loading | boolean | false | 加载状态 |
| error | boolean | false | 错误状态 |
| errorMessage | string | '' | 错误提示信息 |
| emptyText | string | '暂无数据' | 空数据提示文本 |
| selectable | boolean | false | 是否可选择 |
| showIndex | boolean | false | 是否显示序号列 |
| indexLabel | string | '序号' | 序号列标题 |
| showPagination | boolean | true | 是否显示分页 |
| currentPage | number | 1 | 当前页码 |
| pageSize | number | 10 | 每页显示条数 |
| pageSizes | number[] | [10, 20, 50, 100] | 可选的每页条数 |
| total | number | 0 | 数据总条数 |
| paginationLayout | string | 'total, sizes, prev, pager, next, jumper' | 分页组件布局 |
| actionsLabel | string | '操作' | 操作列标题 |
| actionsWidth | string \| number | 150 | 操作列宽度 |
| actionsFixed | boolean \| 'left' \| 'right' | 'right' | 操作列固定方向 |
| statusMap | object | {} | 状态映射配置 |

### Column 类型定义

```typescript
interface Column {
  prop: string;        // 数据字段名
  label: string;       // 列标题
  type?: 'text' | 'currency' | 'date' | 'status'; // 列类型
  format?: string;     // 日期格式化模式
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
| selection-change | (selection: any[]) | 选择项改变时触发 |
| retry | - | 点击重试按钮时触发 |

## Slots

| 插槽名 | 作用域参数 | 说明 |
|-------|------------|------|
| toolbar | - | 工具栏内容 |
| empty | - | 空数据展示 |
| column-[prop] | { row, column, value } | 自定义列渲染 |
| actions | { row, $index } | 操作列内容 |

## 方法

| 方法名 | 参数 | 说明 |
|-------|------|------|
| clearSelection | - | 清空选择 |
| toggleRowSelection | (row, selected?) | 切换行选择状态 |
| toggleAllSelection | - | 切换全选状态 |
| toggleRowExpansion | (row, expanded?) | 切换行展开状态 |
| setCurrentRow | (row) | 设置当前行 |
| clearSort | - | 清空排序 |
| clearFilter | (columnKeys?) | 清空过滤器 |
| doLayout | - | 重新布局表格 |
| sort | (prop, order) | 手动排序 |

## 样式定制

组件使用 CSS 变量进行样式定制，主要变量包括：

```css
:root {
  --table-toolbar-height: 48px;
  --table-pagination-height: 48px;
  --table-header-bg-color: var(--bg-color-light);
  --table-border-color: var(--border-color);
  --table-row-hover-bg-color: var(--bg-color-light);
}
```

## 最佳实践

1. 列配置：
   - 合理设置列宽度
   - 使用适当的列类型
   - 考虑响应式显示

2. 分页处理：
   - 合理设置每页条数
   - 使用服务端分页处理大量数据
   - 保持分页状态同步

3. 自定义渲染：
   - 使用合适的列类型
   - 保持渲染函数简洁
   - 注意性能优化

4. 工具栏设计：
   - 放置常用操作
   - 保持布局整洁
   - 考虑移动端显示

## 注意事项

1. 性能优化：
   - 避免过多列
   - 合理使用固定列
   - 控制数据量

2. 响应式处理：
   - 在小屏幕上隐藏次要列
   - 调整操作列布局
   - 优化工具栏显示

3. 数据处理：
   - 处理空值和异常值
   - 注意数据类型转换
   - 保持数据格式一致

4. 状态管理：
   - 同步分页状态
   - 处理选择状态
   - 保持排序状态 