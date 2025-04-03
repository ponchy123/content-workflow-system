# ErrorBoundary 错误边界

用于捕获和展示组件渲染过程中的错误，提供友好的错误提示和重试功能。

## 基础用法

```vue
<template>
  <error-boundary>
    <my-component />
  </error-boundary>
</template>
```

## 自定义错误展示

```vue
<template>
  <error-boundary
    title="加载失败"
    description="组件加载过程中发生错误，请稍后重试"
    :show-details="true"
    @error="handleError"
    @retry="handleRetry"
  >
    <my-component />
  </error-boundary>
</template>

<script setup lang="ts">
const handleError = (error: Error) => {
  console.error('组件错误:', error);
};

const handleRetry = () => {
  console.log('重试加载组件');
};
</script>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| title | 错误标题 | string | '组件渲染错误' |
| description | 错误描述 | string | error.message |
| showDetails | 是否显示错误详情 | boolean | false |
| onError | 错误发生时的回调 | (error: Error) => void | - |
| onRetry | 点击重试时的回调 | () => void | - |

## Slots

| 名称 | 说明 | 作用域参数 |
|------|------|------------|
| default | 需要错误保护的内容 | - |
| icon | 自定义错误图标 | - |
| title | 自定义错误标题 | { error: Error } |
| description | 自定义错误描述 | { error: Error } |
| actions | 自定义操作按钮 | { retry: () => void } |

## 示例

### 基础错误捕获

```vue
<template>
  <error-boundary>
    <component-with-error />
  </error-boundary>
</template>
```

### 自定义错误展示

```vue
<template>
  <error-boundary>
    <template #icon>
      <el-icon :size="48" color="var(--el-color-warning)">
        <info-filled />
      </el-icon>
    </template>
    <template #title="{ error }">
      <span>{{ error.name }}</span>
    </template>
    <template #description="{ error }">
      <p>{{ error.message }}</p>
      <p>请检查组件配置是否正确</p>
    </template>
    <template #actions="{ retry }">
      <el-button @click="retry">重新加载</el-button>
      <el-button type="primary" @click="handleCustomAction">
        其他操作
      </el-button>
    </template>
    <component-with-error />
  </error-boundary>
</template>
```

### 显示错误详情

```vue
<template>
  <error-boundary
    :show-details="true"
    title="组件错误"
    description="渲染过程中发生错误"
  >
    <component-with-error />
  </error-boundary>
</template>
```

### 错误处理

```vue
<template>
  <error-boundary
    @error="handleError"
    @retry="handleRetry"
  >
    <component-with-error />
  </error-boundary>
</template>

<script setup lang="ts">
const handleError = (error: Error) => {
  // 错误上报
  reportError(error);
};

const handleRetry = () => {
  // 重新加载数据
  reloadData();
};
</script>
```

### 嵌套使用

```vue
<template>
  <error-boundary>
    <div class="container">
      <error-boundary>
        <component-a />
      </error-boundary>
      <error-boundary>
        <component-b />
      </error-boundary>
    </div>
  </error-boundary>
</template>
```

## 注意事项

1. 错误边界只能捕获后代组件渲染和生命周期中的错误
2. 不能捕获以下类型的错误：
   - 事件处理器中的错误
   - 异步代码中的错误
   - 服务端渲染中的错误
3. 建议在路由组件和关键业务组件外层使用错误边界
4. 可以嵌套使用错误边界，实现更细粒度的错误处理 