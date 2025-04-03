# ThemeSwitch 主题切换

用于切换应用的主题模式（浅色/深色）的开关组件。

## 基础用法

```vue
<template>
  <theme-switch />
</template>
```

## 自定义样式

```vue
<template>
  <theme-switch
    button-type="primary"
    size="small"
    :show-text="false"
  />
</template>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| buttonType | 按钮类型 | string | '' |
| size | 按钮尺寸 | 'large'/'default'/'small' | 'default' |
| showText | 是否显示文本 | boolean | true |

## 示例

### 基础切换

```vue
<template>
  <theme-switch />
</template>
```

### 不同尺寸

```vue
<template>
  <div class="demo-theme-switch">
    <theme-switch size="small" />
    <theme-switch size="default" />
    <theme-switch size="large" />
  </div>
</template>

<style>
.demo-theme-switch {
  display: flex;
  gap: 16px;
}
</style>
```

### 不同类型

```vue
<template>
  <div class="demo-theme-switch">
    <theme-switch />
    <theme-switch button-type="primary" />
    <theme-switch button-type="success" />
  </div>
</template>
```

### 仅图标

```vue
<template>
  <theme-switch :show-text="false" />
</template>
```

### 在导航栏中使用

```vue
<template>
  <el-header>
    <div class="header">
      <div class="logo">Logo</div>
      <div class="actions">
        <theme-switch
          button-type="text"
          :show-text="false"
        />
        <el-dropdown>
          <el-avatar>User</el-avatar>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>个人中心</el-dropdown-item>
              <el-dropdown-item>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </el-header>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
```

### 与其他设置组合

```vue
<template>
  <el-card class="settings-card">
    <template #header>
      <div class="settings-header">
        <span>显示设置</span>
      </div>
    </template>
    <div class="settings-content">
      <div class="settings-item">
        <span>主题模式</span>
        <theme-switch />
      </div>
      <div class="settings-item">
        <span>导航模式</span>
        <el-radio-group v-model="navMode">
          <el-radio-button value="side">
            侧边栏
          </el-radio-button>
          <el-radio-button value="top">
            顶部栏
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="settings-item">
        <span>主题色</span>
        <el-color-picker v-model="primaryColor" />
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const navMode = ref('side');
const primaryColor = ref('#409EFF');
</script>

<style scoped>
.settings-card {
  width: 100%;
  max-width: 600px;
}

.settings-header {
  font-weight: bold;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

## 注意事项

1. 组件依赖 `useTheme` 组合式函数
2. 主题切换会自动保存到本地存储
3. 切换主题时会触发相关样式变量的更新
4. 建议在应用的全局位置使用，如导航栏
5. 可以根据需要自定义按钮样式和文本显示 