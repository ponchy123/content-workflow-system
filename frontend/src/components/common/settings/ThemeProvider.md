# ThemeProvider 主题提供者

用于提供主题变量和样式的容器组件，支持浅色/深色主题切换。

## 基础用法

```vue
<template>
  <theme-provider>
    <app />
  </theme-provider>
</template>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| enableTransition | 是否启用主题切换过渡动画 | boolean | true |

## 示例

### 基础使用

```vue
<!-- App.vue -->
<template>
  <theme-provider>
    <el-config-provider>
      <router-view />
    </el-config-provider>
  </theme-provider>
</template>
```

### 禁用过渡动画

```vue
<template>
  <theme-provider :enable-transition="false">
    <app />
  </theme-provider>
</template>
```

### 与主题切换组件配合

```vue
<template>
  <theme-provider>
    <el-container>
      <el-header>
        <div class="header">
          <h1>My App</h1>
          <theme-switch />
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </theme-provider>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}
</style>
```

### 自定义主题变量

```vue
<template>
  <theme-provider>
    <div class="custom-theme">
      <router-view />
    </div>
  </theme-provider>
</template>

<style>
.custom-theme {
  /* 浅色主题变量 */
  .theme-light & {
    --custom-color: #f5f5f5;
    --custom-text: #333333;
  }

  /* 深色主题变量 */
  .theme-dark & {
    --custom-color: #1f1f1f;
    --custom-text: #ffffff;
  }
}
</style>
```

### 嵌套使用

```vue
<template>
  <theme-provider>
    <div class="app">
      <el-container>
        <el-aside>
          <!-- 侧边栏使用独立主题 -->
          <theme-provider :enable-transition="false">
            <div class="sidebar">
              <el-menu mode="vertical">
                <!-- 菜单内容 -->
              </el-menu>
            </div>
          </theme-provider>
        </el-aside>
        <el-container>
          <el-header>
            <theme-switch />
          </el-header>
          <el-main>
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </theme-provider>
</template>

<style scoped>
.sidebar {
  height: 100%;
  background-color: var(--el-bg-color-overlay);
}
</style>
```

### 主题预览

```vue
<template>
  <div class="theme-preview">
    <theme-provider>
      <div class="preview-item">
        <h3>当前主题</h3>
        <preview-content />
      </div>
    </theme-provider>
    <theme-provider class="theme-light">
      <div class="preview-item">
        <h3>浅色主题</h3>
        <preview-content />
      </div>
    </theme-provider>
    <theme-provider class="theme-dark">
      <div class="preview-item">
        <h3>深色主题</h3>
        <preview-content />
      </div>
    </theme-provider>
  </div>
</template>

<script setup lang="ts">
// 预览内容组件
const PreviewContent = defineComponent({
  template: `
    <div class="content">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>卡片标题</span>
            <el-button type="text">操作</el-button>
          </div>
        </template>
        <div class="card-content">
          <el-input placeholder="请输入内容" />
          <el-button type="primary">主要按钮</el-button>
          <el-button>默认按钮</el-button>
        </div>
      </template>
    </el-card>
  `
});
</script>

<style scoped>
.theme-preview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  padding: 24px;
}

.preview-item {
  padding: 16px;
  border-radius: 8px;
  background-color: var(--el-bg-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
```

## CSS 变量

### 浅色主题

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| --el-bg-color | 背景色 | #ffffff |
| --el-bg-color-overlay | 遮罩背景色 | #ffffff |
| --el-text-color-primary | 主要文字颜色 | #303133 |
| --el-text-color-regular | 常规文字颜色 | #606266 |
| --el-text-color-secondary | 次要文字颜色 | #909399 |
| --el-text-color-placeholder | 占位符文字颜色 | #a8abb2 |
| --el-border-color-base | 基础边框颜色 | #dcdfe6 |
| --el-border-color-light | 浅色边框颜色 | #e4e7ed |
| --el-border-color-lighter | 更浅边框颜色 | #ebeef5 |
| --el-border-color-extra-light | 特别浅边框颜色 | #f2f6fc |
| --el-fill-color-base | 基础填充色 | #f0f2f5 |
| --el-fill-color-light | 浅色填充色 | #f5f7fa |
| --el-fill-color-lighter | 更浅填充色 | #fafafa |
| --el-fill-color-extra-light | 特别浅填充色 | #fafcff |
| --el-fill-color-blank | 空白填充色 | #ffffff |
| --el-mask-color | 遮罩颜色 | rgba(255, 255, 255, 0.9) |
| --el-box-shadow | 基础阴影 | 0 2px 12px 0 rgba(0, 0, 0, 0.1) |
| --el-box-shadow-light | 浅色阴影 | 0 2px 12px 0 rgba(0, 0, 0, 0.1) |
| --el-box-shadow-lighter | 更浅阴影 | 0 2px 12px 0 rgba(0, 0, 0, 0.1) |
| --el-box-shadow-dark | 深色阴影 | 0 2px 16px 0 rgba(0, 0, 0, 0.2) |

### 深色主题

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| --el-bg-color | 背景色 | #141414 |
| --el-bg-color-overlay | 遮罩背景色 | #1d1e1f |
| --el-text-color-primary | 主要文字颜色 | #ffffff |
| --el-text-color-regular | 常规文字颜色 | #e5eaf3 |
| --el-text-color-secondary | 次要文字颜色 | #a3a6ad |
| --el-text-color-placeholder | 占位符文字颜色 | #8d9095 |
| --el-border-color-base | 基础边框颜色 | #434343 |
| --el-border-color-light | 浅色边框颜色 | #363637 |
| --el-border-color-lighter | 更浅边框颜色 | #2e2e2f |
| --el-border-color-extra-light | 特别浅边框颜色 | #242424 |
| --el-fill-color-base | 基础填充色 | #262727 |
| --el-fill-color-light | 浅色填充色 | #1d1d1d |
| --el-fill-color-lighter | 更浅填充色 | #1d1d1d |
| --el-fill-color-extra-light | 特别浅填充色 | #191919 |
| --el-fill-color-blank | 空白填充色 | transparent |
| --el-mask-color | 遮罩颜色 | rgba(0, 0, 0, 0.9) |
| --el-box-shadow | 基础阴影 | 0 2px 12px 0 rgba(0, 0, 0, 0.3) |
| --el-box-shadow-light | 浅色阴影 | 0 2px 12px 0 rgba(0, 0, 0, 0.3) |
| --el-box-shadow-lighter | 更浅阴影 | 0 2px 12px 0 rgba(0, 0, 0, 0.3) |
| --el-box-shadow-dark | 深色阴影 | 0 2px 16px 0 rgba(0, 0, 0, 0.4) |

## 注意事项

1. 组件依赖 `useTheme` 组合式函数
2. 建议在应用根节点使用
3. 支持嵌套使用，实现局部主题
4. CSS 变量会自动应用到子组件
5. 过渡动画可能会影响性能，可以根据需要禁用 