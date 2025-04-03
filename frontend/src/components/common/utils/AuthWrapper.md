# AuthWrapper 权限包装器

用于包装需要权限控制的内容，支持单个权限、多个权限的组合判断。

## 基础用法

```vue
<template>
  <auth-wrapper permission="user:view">
    <el-button>查看用户</el-button>
  </auth-wrapper>
</template>
```

## 多个权限

```vue
<template>
  <auth-wrapper
    :permission="['user:add', 'user:edit']"
    mode="any"
  >
    <el-button>管理用户</el-button>
  </auth-wrapper>
</template>
```

## Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| permission | 权限标识，可以是单个权限或权限数组 | string/string[] | - |
| disabled | 是否禁用 | boolean | false |
| mode | 多个权限的判断模式，'all' 表示需要全部满足，'any' 表示满足任一个即可 | 'all'/'any' | 'all' |

## Slots

| 名称 | 说明 |
|------|------|
| default | 需要权限控制的内容 |
| fallback | 无权限时的替代内容 |

## 示例

### 基础权限控制

```vue
<template>
  <auth-wrapper permission="user:view">
    <el-button>查看详情</el-button>
  </auth-wrapper>
</template>
```

### 多权限控制

```vue
<template>
  <auth-wrapper
    :permission="['user:add', 'user:edit']"
    mode="all"
  >
    <el-button>编辑用户</el-button>
  </auth-wrapper>
</template>
```

### 自定义无权限展示

```vue
<template>
  <auth-wrapper permission="admin">
    <el-button type="primary">管理员操作</el-button>
    <template #fallback>
      <el-tooltip content="需要管理员权限">
        <el-button disabled>管理员操作</el-button>
      </el-tooltip>
    </template>
  </auth-wrapper>
</template>
```

### 禁用状态

```vue
<template>
  <auth-wrapper
    permission="user:edit"
    :disabled="isLoading"
  >
    <el-button>编辑</el-button>
  </auth-wrapper>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const isLoading = ref(false);
</script>
```

### 组合使用

```vue
<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>用户管理</span>
        <auth-wrapper
          :permission="['user:add', 'user:import']"
          mode="any"
        >
          <div class="header-actions">
            <auth-wrapper permission="user:add">
              <el-button type="primary">
                新增用户
              </el-button>
            </auth-wrapper>
            <auth-wrapper permission="user:import">
              <el-button>导入用户</el-button>
            </auth-wrapper>
          </div>
        </auth-wrapper>
      </div>
    </template>

    <el-table :data="users">
      <el-table-column label="操作">
        <template #default="{ row }">
          <auth-wrapper permission="user:edit">
            <el-button
              link
              type="primary"
              :disabled="row.status === 'locked'"
            >
              编辑
            </el-button>
          </auth-wrapper>
          <auth-wrapper permission="user:delete">
            <el-button
              link
              type="danger"
              :disabled="row.status === 'locked'"
            >
              删除
            </el-button>
          </auth-wrapper>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
```

### 与路由守卫配合

```typescript
// router.ts
import { usePermission } from '@/composables/usePermission';

router.beforeEach((to, from, next) => {
  const { checkPermission } = usePermission();
  
  if (to.meta.permission) {
    if (checkPermission(to.meta.permission)) {
      next();
    } else {
      next('/403');
    }
  } else {
    next();
  }
});
```

```vue
<!-- 页面组件 -->
<template>
  <auth-wrapper :permission="$route.meta.permission">
    <div class="page-content">
      <!-- 页面内容 -->
    </div>
    <template #fallback>
      <el-empty description="暂无访问权限" />
    </template>
  </auth-wrapper>
</template>
```

## 注意事项

1. 组件依赖 `usePermission` 组合式函数
2. 可以通过 `mode` 属性控制多权限的判断逻辑
3. 建议在按钮、操作等关键交互元素上使用
4. 可以配合路由守卫实现页面级的权限控制
5. 禁用状态会阻止所有交互事件 