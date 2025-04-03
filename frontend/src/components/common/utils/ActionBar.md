# ActionBar 操作栏组件

`ActionBar` 是一个用于展示操作按钮的组件，支持主要操作、次要操作和更多操作的分组展示，并提供权限控制和响应式布局。

## 功能特性

- 主要操作和次要操作分组
- 更多操作下拉菜单
- 权限控制支持
- 图标支持
- 响应式布局
- 垂直布局选项

## 代码示例

### 基础用法

```vue
<template>
  <action-bar
    :primary-actions="primaryActions"
    :secondary-actions="secondaryActions"
    @action="handleAction"
  />
</template>

<script setup lang="ts">
const primaryActions = [
  {
    key: 'add',
    label: '新增',
    type: 'primary',
    icon: 'Plus',
    permission: 'data:create'
  },
  {
    key: 'import',
    label: '导入',
    icon: 'Upload',
    permission: 'data:import'
  }
];

const secondaryActions = [
  {
    key: 'export',
    label: '导出',
    icon: 'Download',
    permission: 'data:export'
  }
];

const handleAction = (key: string) => {
  console.log('Action clicked:', key);
};
</script>
```

### 带更多操作

```vue
<template>
  <action-bar
    :primary-actions="primaryActions"
    :secondary-actions="secondaryActions"
    :more-actions="moreActions"
    @action="handleAction"
  />
</template>

<script setup lang="ts">
const moreActions = [
  {
    key: 'settings',
    label: '设置',
    icon: 'Setting',
    permission: 'settings:view'
  },
  {
    key: 'help',
    label: '帮助',
    icon: 'QuestionFilled'
  }
];
</script>
```

### 垂直布局

```vue
<template>
  <action-bar
    :primary-actions="primaryActions"
    :secondary-actions="secondaryActions"
    vertical
  />
</template>
```

### 自定义按钮属性

```vue
<template>
  <action-bar
    :primary-actions="[{
      key: 'submit',
      label: '提交',
      type: 'primary',
      loading: isSubmitting,
      props: {
        'auto-insert-space': true,
        round: true
      }
    }]"
  />
</template>
```

### 带权限控制

```vue
<template>
  <action-bar
    :primary-actions="[{
      key: 'delete',
      label: '删除',
      type: 'danger',
      permission: 'data:delete',
      disabled: !selectedItems.length
    }]"
  />
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| primaryActions | Action[] | [] | 主要操作按钮配置 |
| secondaryActions | Action[] | [] | 次要操作按钮配置 |
| moreActions | Action[] | [] | 更多操作下拉菜单配置 |
| vertical | boolean | false | 是否垂直布局 |
| size | 'large' \| 'default' \| 'small' | 'default' | 按钮尺寸 |

### Action 类型定义

```typescript
interface Action {
  key: string;        // 操作唯一标识
  label: string;      // 操作文本
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'; // 按钮类型
  icon?: string;      // 图标名称
  permission?: string; // 权限标识
  disabled?: boolean; // 是否禁用
  loading?: boolean;  // 是否加载中
  props?: Record<string, any>; // 其他按钮属性
  handler?: () => void; // 点击处理函数
}
```

## Events

| 事件名 | 参数 | 说明 |
|-------|------|------|
| action | (key: string) | 点击操作按钮时触发 |

## 样式定制

组件使用 CSS 变量进行样式定制，主要变量包括：

```css
:root {
  --action-bar-gap: var(--spacing-md);
  --action-bar-button-gap: var(--spacing-sm);
  --action-icon-margin: var(--spacing-xs);
  --action-button-min-width: 120px;
}
```

## 最佳实践

1. 操作分组：
   - 主要操作放在 `primaryActions` 中
   - 次要操作放在 `secondaryActions` 中
   - 不常用操作放在 `moreActions` 中

2. 权限控制：
   - 为每个操作设置合适的权限标识
   - 使用 `disabled` 控制操作状态
   - 处理无权限时的显示逻辑

3. 响应式设计：
   - 在移动端自动切换为垂直布局
   - 控制按钮最小宽度
   - 合理使用图标

4. 交互设计：
   - 为重要操作添加确认提示
   - 使用 `loading` 状态反馈
   - 提供操作快捷键

## 注意事项

1. 性能优化：
   - 避免过多操作按钮
   - 合理使用计算属性
   - 控制重渲染

2. 权限处理：
   - 正确配置权限标识
   - 处理权限变化
   - 提供无权限提示

3. 响应式布局：
   - 测试不同屏幕尺寸
   - 确保按钮可点击区域
   - 优化移动端体验

4. 主题适配：
   - 支持明暗主题
   - 保持视觉一致性
   - 确保足够的对比度