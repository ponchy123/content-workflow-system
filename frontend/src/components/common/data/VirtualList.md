# VirtualList 虚拟列表

用于高效渲染大量数据的虚拟滚动列表组件。通过只渲染可视区域内的数据项来提升性能。

## 基础用法

```vue
<template>
  <virtual-list
    :data="items"
    :height="400"
    :item-height="50"
    item-key="id"
  >
    <template #default="{ item }">
      <div class="item">{{ item.name }}</div>
    </template>
  </virtual-list>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const items = ref(Array.from({ length: 10000 }, (_, i) => ({
  id: i,
  name: `Item ${i}`
})));
</script>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 要渲染的数据数组 | array | [] |
| height | 容器的高度(px) | number | 400 |
| itemHeight | 每个列表项的高度(px) | number | 50 |
| itemKey | 用于 v-for 的 key | string | 'id' |
| bufferSize | 上下缓冲区大小(项数) | number | 5 |

## Slots

| 名称 | 说明 | 作用域参数 |
|------|------|------------|
| default | 列表项的内容 | { item: any } |

## 注意事项

1. 每个列表项必须是固定高度
2. 建议设置合适的 bufferSize 来平衡性能和滚动体验
3. 确保提供的 itemKey 在数据中是唯一的
4. 列表项的样式应该通过 slot 内容来定义

## 性能优化

1. 使用 CSS transform 进行位移，避免重排
2. 只渲染可视区域内的数据，减少 DOM 节点数量
3. 使用 computed 属性缓存计算结果
4. 使用 will-change 提示浏览器优化渲染

## 示例

### 基础列表

```vue
<virtual-list
  :data="items"
  :height="400"
  :item-height="50"
>
  <template #default="{ item }">
    <div class="item">{{ item.name }}</div>
  </template>
</virtual-list>
```

### 自定义列表项

```vue
<virtual-list
  :data="users"
  :height="600"
  :item-height="80"
  item-key="userId"
>
  <template #default="{ item }">
    <div class="user-card">
      <img :src="item.avatar" class="avatar">
      <div class="info">
        <h3>{{ item.name }}</h3>
        <p>{{ item.email }}</p>
      </div>
    </div>
  </template>
</virtual-list>
```

### 与其他组件结合

```vue
<virtual-list
  :data="tableData"
  :height="500"
  :item-height="60"
>
  <template #default="{ item }">
    <el-row class="table-row">
      <el-col :span="8">{{ item.name }}</el-col>
      <el-col :span="8">{{ item.date }}</el-col>
      <el-col :span="8">
        <status-tag :status="item.status" />
      </el-col>
    </el-row>
  </template>
</virtual-list>
```