# StatusTag 状态标签组件

`StatusTag` 是一个用于展示状态信息的标签组件，基于 Element Plus 的 `el-tag` 组件扩展，提供了更多预设状态样式和图标支持。

## 功能特性

- 预设状态样式
- 图标支持
- 多种显示效果
- 响应式设计
- 主题适配

## 代码示例

### 基础用法

```vue
<template>
  <status-tag type="success" text="成功" />
  <status-tag type="warning" text="警告" />
  <status-tag type="danger" text="错误" />
  <status-tag type="info" text="信息" />
</template>
```

### 带图标

```vue
<template>
  <status-tag
    type="success"
    text="已完成"
    icon="Check"
  />
  <status-tag
    type="processing"
    text="处理中"
    icon="Loading"
  />
  <status-tag
    type="warning"
    text="待处理"
    icon="Warning"
  />
</template>
```

### 不同效果

```vue
<template>
  <status-tag
    type="success"
    text="成功"
    effect="dark"
  />
  <status-tag
    type="warning"
    text="警告"
    effect="plain"
  />
</template>
```

### 不同尺寸

```vue
<template>
  <status-tag
    type="success"
    text="大尺寸"
    size="large"
  />
  <status-tag
    type="warning"
    text="默认尺寸"
  />
  <status-tag
    type="info"
    text="小尺寸"
    size="small"
  />
</template>
```

### 自定义状态

```vue
<template>
  <status-tag
    type="processing"
    text="处理中"
    icon="Loading"
  />
  <status-tag
    type="pending"
    text="待处理"
    icon="Clock"
  />
  <status-tag
    type="cancelled"
    text="已取消"
    icon="Close"
  />
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| type | string | '' | 状态类型 |
| text | string | - | 状态文本（必填） |
| icon | string | - | 图标名称 |
| effect | 'light' \| 'dark' \| 'plain' | 'light' | 显示效果 |
| size | 'large' \| 'default' \| 'small' | 'small' | 标签尺寸 |

### 预设状态类型

- `''`（默认）：普通状态
- `'success'`：成功状态
- `'warning'`：警告状态
- `'danger'`：危险状态
- `'info'`：信息状态
- `'processing'`：处理中状态
- `'pending'`：待处理状态
- `'completed'`：已完成状态
- `'failed'`：失败状态
- `'cancelled'`：已取消状态

## 样式定制

组件使用 CSS 变量进行样式定制，主要变量包括：

```css
.status-tag {
  /* 基础样式 */
  --status-tag-height: 24px;
  --status-tag-padding: 0 var(--spacing-sm);
  --status-tag-font-size: var(--font-size-small);
  --status-tag-font-weight: var(--font-weight-medium);
  --status-tag-border-radius: var(--border-radius-base);

  /* 图标样式 */
  --status-tag-icon-size: 14px;
  --status-tag-icon-margin: var(--spacing-xs);

  /* 状态颜色 */
  --status-tag-processing-color: var(--color-primary);
  --status-tag-pending-color: var(--color-warning);
  --status-tag-completed-color: var(--color-success);
  --status-tag-failed-color: var(--color-danger);
  --status-tag-cancelled-color: var(--color-info);
}
```

## 最佳实践

1. 状态选择：
   - 使用合适的状态类型
   - 保持状态文本简洁
   - 适当使用图标

2. 显示效果：
   - 根据场景选择合适的效果
   - 保持视觉层级
   - 确保可读性

3. 响应式设计：
   - 在小屏幕上使用合适的尺寸
   - 控制文本长度
   - 保持图标比例

4. 主题适配：
   - 支持明暗主题
   - 使用预设状态颜色
   - 保持颜色一致性

## 注意事项

1. 可访问性：
   - 确保足够的对比度
   - 提供合适的文本描述
   - 考虑色盲用户

2. 性能优化：
   - 使用按需加载图标
   - 避免频繁更新
   - 控制重渲染

3. 状态管理：
   - 正确处理状态变化
   - 提供过渡动画
   - 处理边界情况

4. 样式定制：
   - 使用 CSS 变量
   - 保持主题一致性
   - 避免样式冲突 