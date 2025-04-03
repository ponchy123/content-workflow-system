# StatusBadge 状态徽章

用于展示状态、消息提醒等场景的徽章组件。

## 基础用法

```vue
<template>
  <status-badge value="5">
    <el-button>消息</el-button>
  </status-badge>
</template>
```

## 最大值

```vue
<template>
  <status-badge :value="100" :max="99">
    <el-button>消息</el-button>
  </status-badge>
</template>
```

## 小圆点

```vue
<template>
  <status-badge is-dot type="danger">
    <el-button>通知</el-button>
  </status-badge>
</template>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| value | 显示值 | string/number | - |
| max | 最大值，超过最大值会显示 '{max}+' | number | - |
| isDot | 是否显示小圆点 | boolean | false |
| hidden | 是否隐藏徽章 | boolean | false |
| type | 徽章类型 | 'primary'/'success'/'warning'/'danger'/'info' | '' |

## Slots

| 名称 | 说明 |
|------|------|
| default | 徽章包裹的内容 |

## 示例

### 不同类型

```vue
<template>
  <status-badge value="new" type="primary">
    <el-button>主要</el-button>
  </status-badge>
  <status-badge value="1" type="success">
    <el-button>成功</el-button>
  </status-badge>
  <status-badge value="2" type="warning">
    <el-button>警告</el-button>
  </status-badge>
  <status-badge value="3" type="danger">
    <el-button>危险</el-button>
  </status-badge>
  <status-badge value="4" type="info">
    <el-button>信息</el-button>
  </status-badge>
</template>
```

### 小圆点状态

```vue
<template>
  <status-badge is-dot type="primary">
    <el-button>主要</el-button>
  </status-badge>
  <status-badge is-dot type="success">
    <el-button>成功</el-button>
  </status-badge>
  <status-badge is-dot type="warning">
    <el-button>警告</el-button>
  </status-badge>
  <status-badge is-dot type="danger">
    <el-button>危险</el-button>
  </status-badge>
  <status-badge is-dot type="info">
    <el-button>信息</el-button>
  </status-badge>
</template>
```

### 动态控制

```vue
<template>
  <status-badge
    :value="count"
    :hidden="count === 0"
    type="danger"
  >
    <el-button>消息</el-button>
  </status-badge>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const count = ref(0);

setInterval(() => {
  count.value = Math.floor(Math.random() * 100);
}, 2000);
</script>
```

### 自定义样式

```vue
<template>
  <status-badge
    value="99+"
    type="primary"
    style="--status-badge-dot-size: 10px"
  >
    <el-button>自定义大小</el-button>
  </status-badge>
</template>
```

## CSS 变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| --status-badge-dot-size | 小圆点大小 | 8px |
| --status-badge-dot-right | 小圆点右侧位置 | 5px |
| --status-badge-dot-top | 小圆点顶部位置 | 5px |

## 注意事项

1. 徽章会根据内容自动调整位置
2. 当使用数字作为值时，建议设置 `max` 属性
3. 可以通过 CSS 变量自定义小圆点的大小和位置
4. 暗色主题下会自动调整样式 