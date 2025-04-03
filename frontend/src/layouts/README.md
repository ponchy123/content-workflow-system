# 布局目录结构说明

## 目录结构

```
frontend/src/layouts/
├── default.vue    # 默认布局（带侧边栏的主布局）
├── admin.vue      # 管理后台布局
└── auth.vue       # 认证页面布局
```

## 布局说明

### 1. 默认布局 (default.vue)

主要用于系统的主要功能页面，包含：
- 顶部导航栏
- 侧边菜单栏
- 主内容区域
- 面包屑导航
- 用户菜单

使用场景：
- 运费计算
- 批量计算
- 产品比较
- 计算历史等

### 2. 管理后台布局 (admin.vue)

用于系统管理和配置页面，包含：
- 顶部导航栏
- 可折叠侧边栏
- 主内容区域
- 权限控制
- 系统菜单

使用场景：
- 用户管理
- 角色权限
- 系统配置
- 日志查看等

### 3. 认证布局 (auth.vue)

用于登录、注册等认证页面，特点：
- 居中布局
- 简洁设计
- 响应式适配
- 品牌展示

使用场景：
- 登录页面
- 注册页面
- 密码重置
- 验证页面等

## 使用规范

### 1. 布局组件

- 使用 common/layout 中的组件
- 保持布局结构统一
- 支持响应式设计
- 遵循主题定制

### 2. 路由配置

```typescript
// router/index.ts
const routes = [
  {
    path: '/',
    component: () => import('@/layouts/default.vue'),
    children: [
      {
        path: 'calculator',
        component: () => import('@/views/calculator/single.vue')
      }
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/admin.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: 'users',
        component: () => import('@/views/admin/users.vue')
      }
    ]
  },
  {
    path: '/auth',
    component: () => import('@/layouts/auth.vue'),
    children: [
      {
        path: 'login',
        component: () => import('@/views/auth/login.vue')
      }
    ]
  }
]
```

### 3. 布局组件

```vue
<!-- layouts/default.vue -->
<template>
  <div class="layout-default">
    <app-header />
    <el-container>
      <app-sidebar />
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>
```

### 4. 样式规范

- 使用 CSS 变量定义布局尺寸
- 支持响应式设计
- 使用 BEM 命名规范
- 支持主题切换

```css
.layout-default {
  --header-height: 60px;
  --sidebar-width: 240px;
  --sidebar-collapsed-width: 64px;
  
  min-height: 100vh;
}
```

## 最佳实践

1. **布局选择**
   - 根据页面类型选择合适的布局
   - 保持布局风格统一
   - 考虑响应式需求

2. **组件复用**
   - 使用通用布局组件
   - 避免重复实现
   - 保持一致的用户体验

3. **主题支持**
   - 使用 CSS 变量
   - 支持明暗主题
   - 提供平滑切换

4. **性能优化**
   - 路由懒加载
   - 组件按需加载
   - 合理使用缓存

## 常见问题

1. **如何选择布局？**
   - 默认布局：主要功能页面
   - 管理布局：系统管理页面
   - 认证布局：登录注册页面

2. **如何处理响应式？**
   - 使用 Element Plus 的栅格系统
   - 定义断点处理逻辑
   - 提供移动端适配

3. **如何处理权限？**
   - 在路由配置中定义
   - 使用路由守卫
   - 结合权限组件 