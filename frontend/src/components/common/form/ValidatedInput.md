# ValidatedInput 验证输入组件

`ValidatedInput` 是一个带验证功能的输入框组件，基于 Element Plus 的 `el-input` 组件扩展，提供了实时验证、错误提示等功能。

## 功能特性

- 实时输入验证
- 自定义验证规则
- 错误状态展示
- 支持必填验证
- 支持前后置内容
- 支持所有 el-input 的特性

## 代码示例

### 基础用法

```vue
<template>
  <validated-input
    v-model="value"
    placeholder="请输入内容"
    :required="true"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';

const value = ref('');
</script>
```

### 自定义验证规则

```vue
<template>
  <validated-input
    v-model="phone"
    placeholder="请输入手机号"
    :validator="validatePhone"
    @valid="handleValid"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';

const phone = ref('');

const validatePhone = (value: string) => {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return {
    valid: phoneRegex.test(value),
    message: '请输入正确的手机号码'
  };
};

const handleValid = (isValid: boolean) => {
  console.log('验证结果:', isValid);
};
</script>
```

### 带标签的输入框

```vue
<template>
  <validated-input
    v-model="username"
    label="用户名"
    placeholder="请输入用户名"
    :required="true"
  />
</template>
```

### 前后置内容

```vue
<template>
  <validated-input v-model="website" placeholder="请输入网址">
    <template #prepend>http://</template>
    <template #append>.com</template>
  </validated-input>
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| modelValue | string | - | 输入框的值（必填） |
| name | string | '' | 输入框名称 |
| placeholder | string | '' | 占位文本 |
| label | string | '' | 输入框标签 |
| disabled | boolean | false | 是否禁用 |
| required | boolean | true | 是否必填 |
| validator | function | - | 自定义验证函数 |
| validateOnInput | boolean | true | 是否在输入时验证 |
| validateOnBlur | boolean | true | 是否在失去焦点时验证 |

### validator 函数类型定义

```typescript
interface ValidationResult {
  valid: boolean;
  message?: string;
}

type ValidatorFunction = (value: string) => ValidationResult;
```

## Events

| 事件名 | 参数 | 说明 |
|-------|------|------|
| update:modelValue | (value: string) | 输入值更新时触发 |
| change | (value: string) | 值变化时触发 |
| valid | (isValid: boolean) | 验证结果变化时触发 |
| blur | (value: string) | 失去焦点时触发 |

## Slots

| 插槽名 | 说明 |
|-------|------|
| prepend | 输入框前置内容 |
| append | 输入框后置内容 |

## 样式定制

组件使用 CSS 变量进行样式定制，主要变量包括：

```css
:root {
  --form-item-margin-bottom: 18px;
  --form-control-width: 100%;
  --form-error-color: #f56c6c;
  --form-error-font-size: 12px;
  --form-error-margin-top: 4px;
}
```

## 最佳实践

1. 验证规则设计：
   - 根据业务需求选择合适的验证时机
   - 提供清晰的错误提示信息
   - 避免过于复杂的验证逻辑

2. 错误处理：
   - 及时反馈验证结果
   - 错误提示要简洁明了
   - 提供修正建议

3. 用户体验：
   - 适时进行验证，避免打扰用户输入
   - 保持验证反馈的一致性
   - 合理使用必填标记

4. 表单集成：
   - 与表单验证系统配合使用
   - 统一管理验证状态
   - 支持表单级别的验证

## 注意事项

1. 性能考虑：
   - 避免在验证函数中进行复杂计算
   - 合理使用防抖处理
   - 避免频繁的状态更新

2. 可访问性：
   - 提供适当的 aria 标签
   - 确保键盘可访问性
   - 保持错误提示的可读性

3. 验证时机：
   - 输入时验证：适用于即时反馈
   - 失焦时验证：适用于完整性验证
   - 提交时验证：适用于最终确认

4. 集成注意：
   - 确保与表单验证框架的兼容性
   - 处理好异步验证场景
   - 注意验证状态的同步 