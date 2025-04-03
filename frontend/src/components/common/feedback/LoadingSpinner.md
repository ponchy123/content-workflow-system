# LoadingSpinner 加载动画

用于展示加载状态的动画组件，支持全屏加载、自定义大小和文本。

## 基础用法

```vue
<template>
  <loading-spinner text="加载中..." />
</template>
```

## 全屏加载

```vue
<template>
  <loading-spinner
    fullscreen
    text="正在处理，请稍候..."
  />
</template>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| loading | 是否显示加载动画 | boolean | true |
| fullscreen | 是否全屏显示 | boolean | false |
| transparent | 是否使用透明背景 | boolean | false |
| text | 加载提示文本 | string | - |
| background | 背景遮罩颜色 | string | rgba(255, 255, 255, 0.9) |
| size | 加载图标大小 | 'small'/'default'/'large' | 'default' |

## Slots

| 名称 | 说明 |
|------|------|
| icon | 自定义加载图标 |
| text | 自定义加载文本 |

## 示例

### 不同尺寸

```vue
<template>
  <loading-spinner size="small" text="小尺寸" />
  <loading-spinner size="default" text="默认尺寸" />
  <loading-spinner size="large" text="大尺寸" />
</template>
```

### 自定义图标

```vue
<template>
  <loading-spinner>
    <template #icon>
      <el-icon class="custom-icon">
        <loading />
      </el-icon>
    </template>
  </loading-spinner>
</template>
```

### 透明背景

```vue
<template>
  <loading-spinner transparent text="透明背景" />
</template>
```

### 自定义背景色

```vue
<template>
  <loading-spinner
    background="rgba(0, 0, 0, 0.7)"
    text="自定义背景"
  />
</template>
```

### 在容器内使用

```vue
<template>
  <div class="container" style="position: relative; height: 200px;">
    <loading-spinner text="加载中..." />
  </div>
</template>
```

### 动态控制

```vue
<template>
  <div>
    <el-button @click="startLoading">开始加载</el-button>
    <loading-spinner
      :loading="isLoading"
      text="处理中..."
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const isLoading = ref(false);

const startLoading = () => {
  isLoading.value = true;
  setTimeout(() => {
    isLoading.value = false;
  }, 3000);
};
</script>
```

## 注意事项

1. 全屏模式下会自动添加 `z-index: 9999`
2. 使用透明背景时，确保背景色对比度足够
3. 在容器内使用时，容器需要设置 `position: relative`
4. 建议配合 `v-loading` 指令使用，实现更便捷的加载控制 