# 样式目录结构说明

## 目录结构

```
frontend/src/styles/
├── variables/           # CSS变量定义
│   ├── colors.css      # 颜色变量
│   ├── spacing.css     # 间距变量
│   ├── typography.css  # 字体排版变量
│   ├── layout.css      # 布局相关变量
│   ├── card.css        # 卡片组件变量
│   ├── form.css        # 表单组件变量
│   └── index.css       # 变量统一导出
├── theme/              # 主题相关
│   ├── index.ts        # 主题功能导出
│   ├── types.ts        # 主题类型定义
│   ├── themes.ts       # 主题配置定义
│   ├── presets.ts      # 预设主题配置
│   └── utils.ts        # 主题工具函数
└── base.css           # 基础样式
```

## 文件说明

### variables 目录

1. **colors.css**
   - 定义系统颜色变量
   - 包含主色、辅助色、文字颜色等
   - 支持明暗主题切换

2. **spacing.css**
   - 定义间距变量
   - 包含内边距、外边距等
   - 统一间距使用规范

3. **typography.css**
   - 定义字体排版变量
   - 包含字体大小、行高、字重等
   - 确保文字样式一致性

4. **layout.css**
   - 定义布局相关变量
   - 包含容器宽度、间距等
   - 支持响应式布局

5. **card.css**
   - 定义卡片组件变量
   - 包含边框、阴影、圆角等
   - 统一卡片样式规范

6. **form.css**
   - 定义表单组件变量
   - 包含输入框、按钮等样式
   - 确保表单元素一致性

7. **index.css**
   - 统一导出所有变量
   - 管理变量依赖关系
   - 提供变量使用文档

### theme 目录

1. **index.ts**
   - 导出主题相关功能
   - 提供主题切换接口
   - 初始化主题配置

2. **types.ts**
   - 定义主题相关类型
   - 包含主题配置接口
   - TypeScript 类型支持

3. **themes.ts**
   - 定义具体主题配置
   - 包含明暗主题变量
   - 支持主题扩展

4. **presets.ts**
   - 预设主题配置
   - 默认主题定义
   - 主题模板

5. **utils.ts**
   - 主题工具函数
   - 主题切换逻辑
   - 主题相关辅助方法

### base.css

- 定义全局基础样式
- 样式重置和初始化
- 通用样式类定义

## 使用规范

### 1. CSS变量命名

- 使用 `--` 前缀
- 使用 kebab-case 命名法
- 按功能进行分类
- 提供清晰的注释说明

示例：
```css
/* 主要颜色 */
--color-primary: #409EFF;
--color-success: #67C23A;
--color-warning: #E6A23C;
--color-danger: #F56C6C;
--color-info: #909399;

/* 文字颜色 */
--text-color-primary: #303133;
--text-color-regular: #606266;
--text-color-secondary: #909399;

/* 边框颜色 */
--border-color-base: #DCDFE6;
--border-color-light: #E4E7ED;
--border-color-lighter: #EBEEF5;

/* 背景颜色 */
--bg-color-base: #F5F7FA;
--bg-color-light: #F5F7FA;
--bg-color-lighter: #FAFAFA;
```

### 2. 主题配置

- 在 theme 目录下定义主题变量
- 使用 CSS 变量实现主题切换
- 支持浅色/深色主题
- 提供主题切换过渡效果

### 3. 基础样式

- 在 base.css 中定义全局基础样式
- 包含样式重置和通用样式类
- 避免过度的全局样式
- 使用 CSS 变量引用

### 4. 响应式设计

- 使用相对单位（rem, em）
- 定义断点变量
- 使用媒体查询适配不同屏幕
- 移动优先的设计理念

### 5. 组件样式

- 组件样式使用 scoped
- 引用全局 CSS 变量
- 遵循 BEM 命名规范
- 支持主题切换

### 6. 性能优化

- 避免深层嵌套选择器
- 合理使用选择器
- 避免重复定义
- 压缩生产环境 CSS

## 使用示例

### 1. 在组件中使用变量

```vue
<style scoped>
.my-component {
  color: var(--text-color-primary);
  background-color: var(--bg-color-base);
  padding: var(--spacing-md);
  border-radius: var(--border-radius-base);
  box-shadow: var(--box-shadow-light);
}
</style>
```

### 2. 主题适配

```vue
<style>
.my-component {
  /* 浅色主题 */
  .theme-light & {
    background-color: var(--bg-color-light);
    color: var(--text-color-primary);
  }

  /* 深色主题 */
  .theme-dark & {
    background-color: var(--bg-color-dark);
    color: var(--text-color-light);
  }
}
</style>
```

### 3. 响应式设计

```vue
<style scoped>
.my-component {
  padding: var(--spacing-md);

  @media (max-width: 768px) {
    padding: var(--spacing-sm);
  }

  @media (max-width: 480px) {
    padding: var(--spacing-xs);
  }
}
</style>
```

## 最佳实践

1. **变量使用**
   - 始终使用 CSS 变量而不是硬编码值
   - 在 variables 目录下集中管理变量
   - 提供清晰的变量命名和注释

2. **主题支持**
   - 使用 ThemeProvider 组件包装应用
   - 通过 CSS 变量切换主题
   - 提供平滑的主题切换过渡

3. **样式作用域**
   - 组件样式使用 scoped
   - 全局样式放在 base.css
   - 避免样式污染

4. **响应式设计**
   - 使用 CSS Grid 和 Flexbox
   - 定义标准断点
   - 使用相对单位

5. **性能考虑**
   - 避免过度嵌套
   - 合理使用选择器
   - 按需加载样式

## 常见问题

1. **如何添加新的变量？**
   - 在对应的变量文件中添加
   - 更新变量文档
   - 确保命名规范

2. **如何处理主题切换？**
   - 使用 CSS 变量
   - 在 theme 目录下定义
   - 使用 ThemeProvider

3. **如何处理响应式？**
   - 使用预定义断点
   - 移动优先设计
   - 使用相对单位

## 样式开发规范

### CSS变量命名规范

1. **核心变量命名标准**
   - 使用 `--变量类型-变量名称` 的命名方式
   - 例如：`--spacing-base`, `--color-primary`
   
2. **标准命名与简写**
   - 项目对间距变量同时支持两种命名方式：
     - 完整版：`--spacing-small`, `--spacing-medium`, `--spacing-large`
     - 简写版：`--spacing-sm`, `--spacing-md`, `--spacing-lg`
   - 两种均可使用，但同一组件内应保持一致
   - 简写版是通过原始变量引用实现，确保更新统一性

3. **组件内样式规范**
   - 所有组件样式使用 `<style scoped>` 确保样式隔离
   - 共享样式应放在全局样式文件中
   - 避免在组件内硬编码色值，应使用CSS变量

4. **避免重复定义**
   - 当需要使用样式变量时，应先检查是否已有定义
   - 复用现有变量而非创建新的近似变量 