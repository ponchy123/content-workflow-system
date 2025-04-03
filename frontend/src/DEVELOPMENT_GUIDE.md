# 前端开发规范指南

本文档旨在提供前端开发规范，确保代码一致性、可维护性和可扩展性。

## 目录

1. [CSS变量命名规范](#css变量命名规范)
2. [组件开发指南](#组件开发指南)
3. [视图和组件职责划分](#视图和组件职责划分)
4. [代码重用策略](#代码重用策略)
5. [错误修复和报告](#错误修复和报告)

## CSS变量命名规范

### 变量命名约定

我们的项目使用两种CSS变量命名格式，但推荐使用完整形式：

1. **完整形式**（推荐）:
   - `--spacing-small`
   - `--spacing-base`
   - `--spacing-large`
   - `--spacing-extra-large`

2. **简写形式**（通过别名支持）:
   - `--spacing-sm`
   - `--spacing-md`
   - `--spacing-lg`
   - `--spacing-xl`

为了确保项目的一致性，请遵循以下原则：

- 在新组件中优先使用完整形式变量
- 在同一组件中保持变量命名风格一致
- 避免直接使用Element Plus变量（`--el-*`），除非必要

### 变量使用示例

```css
/* 推荐 */
.my-component {
  padding: var(--spacing-base);
  margin-bottom: var(--spacing-large);
  color: var(--text-color-primary);
}

/* 不推荐 - 混合使用不同命名风格 */
.my-component {
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-large);
  color: var(--el-text-color-primary); /* 使用了Element Plus变量 */
}
```

## 组件开发指南

### 组件结构

组件应当遵循以下结构：

```
src/
├── components/           # 可复用组件
│   ├── common/           # 通用基础组件
│   │   ├── form/         # 表单相关组件
│   │   ├── data/         # 数据展示组件
│   │   └── ...
│   ├── module1/          # 模块相关组件
│   └── module2/
├── views/                # 页面级组件 
│   ├── module1/
│   └── module2/
└── layouts/              # 布局模板
```

### 组件设计原则

1. **单一职责**：每个组件应该只专注于一个功能
2. **可组合性**：组件应该可以灵活组合使用
3. **自包含**：组件应当尽可能少依赖外部状态
4. **接口清晰**：提供清晰的API和文档

### 基础组件使用

我们已经创建了一系列通用基础组件，请优先使用它们：

```vue
<template>
  <!-- 使用基础组件 -->
  <base-rate-editor :title="编辑费率">
    <!-- 自定义内容 -->
  </base-rate-editor>
</template>

<script setup>
import { BaseRateEditor } from '@/components/common';
</script>
```

## 视图和组件职责划分

### 视图组件职责

视图组件（`views/`目录下）应该专注于：

- 页面布局
- 数据获取和状态管理
- 用户交互处理
- 业务逻辑编排

### 可复用组件职责

可复用组件（`components/`目录下）应该专注于：

- UI展示
- 用户输入处理
- 数据验证
- 通用交互逻辑

## 代码重用策略

### 组件复用

1. **检查现有组件**：在创建新组件前，检查是否已有类似组件
2. **提取共同逻辑**：对于多处出现的相似代码，提取为公共组件
3. **使用组合模式**：通过组合小组件构建复杂功能

### 代码共享方式

1. **基础组件**：通用UI组件
2. **高阶组件**：封装共享逻辑
3. **Composables**：可复用的组合式函数
4. **Mixins**：共享功能（不推荐，优先使用组合式API）

## 错误修复和报告

### 错误报告格式

报告错误时，请提供以下信息：

1. 错误发生的环境（浏览器、设备等）
2. 复现步骤
3. 预期行为与实际行为
4. 错误截图或日志

### 修复步骤

1. 定位问题根源
2. 制定修复方案
3. 编写测试用例
4. 实施修复
5. 验证修复效果

## 总结

遵循这些规范可以帮助我们创建高质量、一致且可维护的前端代码。如有任何疑问或建议，请联系项目负责人。

---

## 附录：常用CSS变量参考

### 间距变量
```css
--spacing-mini: 4px;
--spacing-small: 8px;
--spacing-base: 16px;
--spacing-large: 24px;
--spacing-extra-large: 32px;
```

### 颜色变量
```css
--color-primary: #409EFF;
--color-success: #67C23A;
--color-warning: #E6A23C;
--color-danger: #F56C6C;
--text-color-primary: #303133;
--text-color-regular: #606266;
--text-color-secondary: #909399;
--border-color: #DCDFE6;
--bg-color: #FFFFFF;
```

### 字体变量
```css
--font-size-small: 12px;
--font-size-base: 14px;
--font-size-medium: 16px;
--font-size-large: 18px;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-bold: 700;
``` 