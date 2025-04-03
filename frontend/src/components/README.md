# 组件目录结构说明

## 目录结构

```
frontend/src/components/
├── common/                # 通用组件
│   ├── data/             # 数据展示相关组件
│   │   ├── DataTable     # 数据表格
│   │   ├── DataDisplay   # 数据展示
│   │   ├── DataManager   # 数据管理
│   │   ├── VirtualList   # 虚拟列表
│   │   └── FilterPanel   # 筛选面板
│   ├── form/             # 表单相关组件
│   │   ├── FormGroup     # 表单分组
│   │   ├── SearchInput   # 搜索输入框
│   │   ├── ValidatedInput # 带验证的输入框
│   │   ├── UnitInput     # 单位输入框
│   │   └── DateRangePicker # 日期范围选择器
│   ├── layout/           # 布局相关组件
│   │   ├── FormCard      # 表单卡片
│   │   ├── AppHeader     # 应用头部
│   │   └── AppSidebar    # 应用侧边栏
│   ├── feedback/         # 反馈相关组件
│   │   ├── StatusTag     # 状态标签
│   │   ├── StatusBadge   # 状态徽章
│   │   ├── LoadingSpinner # 加载动画
│   │   └── ErrorBoundary # 错误边界
│   ├── utils/            # 工具类组件
│   │   ├── ImportTemplateHelper # 导入模板助手
│   │   ├── ImportExport  # 导入导出
│   │   ├── AuthWrapper   # 权限包装器
│   │   └── ActionBar     # 操作栏
│   └── settings/         # 设置相关组件
│       ├── ThemeSwitch   # 主题切换
│       ├── ThemeProvider # 主题提供者
│       └── LanguageSwitch # 语言切换
├── calculator/           # 运费计算相关组件
├── postal/              # 邮编管理相关组件
├── product/             # 产品管理相关组件
├── notification/        # 通知相关组件
├── fuel-rate/          # 燃油费率相关组件
├── system/             # 系统管理相关组件
└── report/             # 报表相关组件

```

## 使用规范

### 1. 组件分类

- **通用组件**：放在 `common` 目录下，可被其他组件复用
- **业务组件**：按功能模块划分，放在对应的目录下
- **布局组件**：用于页面布局的组件，放在 `common/layout` 目录下

### 2. 组件命名

- 使用 PascalCase 命名组件文件和组件名
- 通用组件使用功能描述性名称（如 DataTable）
- 业务组件使用业务描述性名称（如 ProductList）

### 3. 样式规范

- 使用 `styles/variables` 中定义的变量
- 避免在组件中硬编码样式值
- 使用 BEM 命名规范编写样式
- 支持暗色主题适配

### 4. 组件文档

每个组件都应包含以下文档：
- 组件说明（.md文件）
- Props 定义及说明
- Events 定义及说明
- Slots 定义及说明
- 使用示例

### 5. TypeScript 支持

- 使用 TypeScript 编写组件
- 为 Props 和 Events 定义类型接口
- 导出组件的类型定义

### 6. 组件复用原则

- 优先使用 common 目录下的通用组件
- 避免在业务模块中重复实现类似功能
- 提取可复用的逻辑到 composables

### 7. 性能优化

- 合理使用 computed 和 watch
- 大数据列表使用虚拟滚动
- 按需加载组件
- 避免不必要的重渲染

### 8. 测试要求

- 编写单元测试
- 测试文件与组件文件同目录
- 覆盖主要功能和边界情况

### 9. 代码提交

- 遵循项目的 Git 提交规范
- 提供清晰的提交信息
- 确保代码通过 lint 检查

### 10. 组件通信

- 优先使用 props 和 events
- 复杂状态使用 Pinia 管理
- 避免过度使用全局状态

## 开发流程

1. **新增组件**
   - 在对应目录创建组件文件
   - 创建组件文档
   - 编写单元测试
   - 在 index.ts 中导出组件

2. **修改组件**
   - 更新组件文档
   - 更新单元测试
   - 确保向后兼容

3. **删除组件**
   - 确认组件未被使用
   - 移除相关文档和测试
   - 从 index.ts 中移除导出

## 常见问题

1. **如何选择组件位置？**
   - 如果是通用功能，放在 common 目录
   - 如果是特定业务，放在对应业务模块目录

2. **何时创建新的通用组件？**
   - 当功能在多个地方重复使用
   - 当逻辑足够通用和独立

3. **如何处理组件间的样式冲突？**
   - 使用 scoped 样式
   - 遵循 BEM 命名规范
   - 使用 CSS 变量控制主题

## 概述
本目录包含了应用程序中所有可复用的 Vue 组件。每个子目录都必须包含一个 index.ts 文件，用于统一导出该目录下的组件。

### 目录索引文件（index.ts）
每个子目录下的 index.ts 文件用于：
- 统一导出组件，提供简洁的导入方式
- 控制组件的可见性
- 便于后期维护和重构
- 提供 TypeScript 类型支持

#### index.ts 规范
1. 文件位置
   - 每个组件子目录必须包含 index.ts 文件
   - index.ts 文件应位于目录根级别

2. 导出规范
   ```typescript
   // 正确的导出方式
   export { default as ComponentName } from './ComponentName.vue';
   
   // 批量导出示例
   export { default as ComponentA } from './ComponentA.vue';
   export { default as ComponentB } from './ComponentB.vue';
   ```

3. 导入规范
   ```typescript
   // 推荐的导入方式
   import { ComponentA, ComponentB } from '@/components/module-name';
   
   // 不推荐的导入方式
   import ComponentA from '@/components/module-name/ComponentA.vue';
   ```

4. 注意事项
   - 确保组件文件正确导出了 default
   - 导出名称应与组件文件名保持一致（PascalCase）
   - 避免在 index.ts 中添加业务逻辑
   - 保持导出项的字母顺序

#### 目录结构示例
```
components/
├── module-name/
│   ├── ComponentA.vue
│   ├── ComponentB.vue
│   └── index.ts  // 导出该目录下的所有组件
└── README.md
```

使用示例：
```typescript
// 推荐的导入方式
import { NotificationList, NotificationIcon } from '@/components/notification';

// 不推荐直接导入具体文件
import NotificationList from '@/components/notification/NotificationList.vue';
```

## 开发规范

1. 保持组件职责单一，功能聚焦
2. 使用 props 和 events 进行组件通信
3. 在组件文件中编写 API 文档
4. 遵循 Vue 3 组合式 API 模式
5. 保持命名规范一致性

### 命名规范
- 组件文件使用 PascalCase 命名法
- 组件名应该体现其功能（如 Form、Table、List 等前缀）
- 保持命名的一致性和可读性

### 组件开发指南
1. 组件设计原则
   - 遵循单一职责原则
   - 保持组件的可复用性
   - 合理划分组件粒度

2. 性能优化
   - 合理使用计算属性和监听器
   - 适当使用组件懒加载
   - 避免不必要的组件渲染

3. 文档规范
   - 注明组件的用途和功能
   - 说明 props 和 events 的使用方法
   - 提供使用示例

4. 代码质量
   - 编写单元测试
   - 做好错误处理
   - 保持代码整洁

### 组件导出规范
1. 组件文件规范
   - 确保每个 .vue 文件都有 default 导出
   - 组件名称应与文件名一致
   - 使用 TypeScript 定义组件属性和事件

2. 组件定义方式
   ```vue
   <!-- 方式一：使用 <script setup> + defineOptions -->
   <script setup lang="ts">
   import { defineOptions } from 'vue';
   
   defineOptions({
     name: 'ComponentName'
   });
   </script>

   <!-- 方式二：使用传统的组件定义方式 -->
   <script lang="ts">
   import { defineComponent } from 'vue';
   
   export default defineComponent({
     name: 'ComponentName',
     // ... 其他选项
   });
   </script>
   ```

3. index.ts 文件规范
   - 每个组件目录必须包含 index.ts
   - 所有对外暴露的组件都要在 index.ts 中导出
   - 导出语句要简洁清晰
   - 按字母顺序组织导出语句
   ```typescript
   // index.ts 示例
   export { default as ComponentA } from './ComponentA.vue';
   export { default as ComponentB } from './ComponentB.vue';
   ```

4. 导入使用规范
   - 总是通过 index.ts 导入组件
   - 使用命名导入而不是默认导入
   - 避免直接导入 .vue 文件
   ```typescript
   // 正确的导入方式
   import { ComponentA, ComponentB } from '@/components/module-name';
   
   // 错误的导入方式
   import ComponentA from '@/components/module-name/ComponentA.vue';
   ```

5. 组件导出检查清单
   - [ ] 组件是否有正确的 name 属性
   - [ ] 组件是否正确导出（default export）
   - [ ] index.ts 是否包含所有需要导出的组件
   - [ ] 导入方式是否符合规范
   - [ ] TypeScript 类型是否正确

6. 常见问题解决
   - 如果出现 "module has no default export" 错误：
     - 检查组件是否正确使用 defineComponent 或 defineOptions
     - 确保组件文件有 default 导出
   - 如果出现组件名称相关警告：
     - 确保组件名称与文件名匹配
     - 检查 name 属性是否正确设置

### 组件导出示例
```
components/
├── module-name/
│   ├── ComponentA.vue
│   ├── ComponentB.vue
│   └── index.ts  // 导出该目录下的所有组件
└── README.md
```

使用示例：
```typescript
// 推荐的导入方式
import { NotificationList, NotificationIcon } from '@/components/notification';

// 不推荐直接导入具体文件
import NotificationList from '@/components/notification/NotificationList.vue';
``` 