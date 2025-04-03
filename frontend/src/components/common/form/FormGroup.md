# FormGroup 表单分组组件

`FormGroup` 组件用于对表单内容进行分组展示，支持标题、描述、可折叠功能和错误状态展示。

## 功能特性

- 支持标题和描述文本
- 可选的折叠功能
- 支持必填标记
- 错误状态展示
- 自定义额外内容和页脚
- 响应式设计
- 主题定制

## 代码示例

### 基础用法

```vue
<template>
  <form-group
    title="基本信息"
    description="请填写用户的基本信息"
  >
    <el-form>
      <el-form-item label="姓名">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="年龄">
        <el-input-number v-model="form.age" />
      </el-form-item>
    </el-form>
  </form-group>
</template>
```

### 可折叠分组

```vue
<template>
  <form-group
    title="高级设置"
    description="可选的高级配置项"
    :collapsible="true"
    :default-collapsed="true"
    @collapse="handleCollapse"
  >
    <el-form>
      <!-- 表单内容 -->
    </el-form>
  </form-group>
</template>

<script setup lang="ts">
const handleCollapse = (collapsed: boolean) => {
  console.log('分组已', collapsed ? '折叠' : '展开');
};
</script>
```

### 错误状态

```vue
<template>
  <form-group
    title="支付信息"
    :has-error="true"
    error-message="请完善支付信息"
  >
    <el-form>
      <!-- 表单内容 -->
    </el-form>
  </form-group>
</template>
```

### 自定义额外内容

```vue
<template>
  <form-group title="订单信息">
    <template #extra>
      <el-button type="primary" size="small">
        添加商品
      </el-button>
    </template>

    <el-form>
      <!-- 表单内容 -->
    </el-form>

    <template #footer>
      <div class="d-flex justify-content-end">
        <el-button type="primary">
          保存
        </el-button>
      </div>
    </template>
  </form-group>
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| title | string | - | 分组标题（必填） |
| description | string | '' | 分组描述文本 |
| collapsible | boolean | false | 是否可折叠 |
| defaultCollapsed | boolean | false | 默认是否折叠 |
| required | boolean | false | 是否显示必填标记 |
| hasError | boolean | false | 是否显示错误状态 |
| errorMessage | string | '' | 错误提示信息 |

## Events

| 事件名 | 参数 | 说明 |
|-------|------|------|
| collapse | (collapsed: boolean) | 折叠状态改变时触发 |

## Slots

| 插槽名 | 说明 |
|-------|------|
| default | 分组的主要内容 |
| extra | 标题栏右侧的额外内容 |
| footer | 分组底部内容 |

## 样式定制

组件使用 CSS 变量进行样式定制，主要变量包括：

```css
:root {
  --form-group-margin-bottom: 24px;
  --form-group-padding: 16px;
  --border-width-base: 1px;
  --border-style-base: solid;
  --border-color-base: #dcdfe6;
  --border-radius-base: 4px;
  --form-error-color: #f56c6c;
  --form-error-bg-color: #fef0f0;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --transition-duration: 0.3s;
}
```

## 最佳实践

1. 合理分组：
   - 将相关的表单项放在同一个分组中
   - 避免一个分组内包含过多表单项
   - 使用清晰的标题和描述

2. 折叠功能：
   - 对于可选或高级配置项使用折叠功能
   - 默认展开必填项分组
   - 保持折叠状态的一致性

3. 错误处理：
   - 在表单验证失败时显示错误状态
   - 提供清晰的错误提示信息
   - 考虑使用醒目的视觉提示

4. 响应式设计：
   - 在小屏幕上自动调整布局
   - 确保内容在各种屏幕尺寸下都清晰可读
   - 适当使用间距和留白

## 注意事项

1. 性能考虑：
   - 折叠时使用 v-show 而不是 v-if，避免不必要的重渲染
   - 合理使用计算属性和缓存

2. 可访问性：
   - 提供键盘导航支持
   - 使用语义化的HTML结构
   - 确保颜色对比度符合WCAG标准

3. 兼容性：
   - 检查CSS变量的浏览器兼容性
   - 提供合适的降级方案
   - 测试不同设备和平台 