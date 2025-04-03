# SearchInput 搜索输入组件

`SearchInput` 是一个基于 `ValidatedInput` 的搜索输入框组件，提供了搜索按钮、加载状态、防抖处理等功能。

## 功能特性

- 搜索按钮集成
- 加载状态展示
- 防抖处理
- 验证功能继承
- 自动触发搜索
- 支持自定义验证

## 代码示例

### 基础用法

```vue
<template>
  <search-input
    v-model="searchText"
    placeholder="请输入搜索关键词"
    @search="handleSearch"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';

const searchText = ref('');

const handleSearch = (value: string) => {
  console.log('搜索:', value);
};
</script>
```

### 带验证的搜索

```vue
<template>
  <search-input
    v-model="keyword"
    placeholder="请输入商品编号"
    :validator="validateProductCode"
    :min-search-length="6"
    @search="handleSearch"
    @valid="handleValid"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';

const keyword = ref('');

const validateProductCode = (value: string) => {
  const codeRegex = /^[A-Z]{2}\d{4}$/;
  return {
    valid: codeRegex.test(value),
    message: '请输入正确的商品编号（如：AB1234）'
  };
};

const handleSearch = (value: string) => {
  // 执行搜索
};

const handleValid = (isValid: boolean) => {
  console.log('验证结果:', isValid);
};
</script>
```

### 自动搜索

```vue
<template>
  <search-input
    v-model="query"
    placeholder="输入即可搜索"
    :search-on-valid="true"
    :debounce-time="500"
    @search="handleSearch"
  />
</template>
```

### 失焦时搜索

```vue
<template>
  <search-input
    v-model="query"
    placeholder="失去焦点时搜索"
    :search-on-blur="true"
    @search="handleSearch"
  />
</template>
```

## Props

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| modelValue | string | - | 输入框的值（必填） |
| name | string | '' | 输入框名称 |
| placeholder | string | '搜索...' | 占位文本 |
| label | string | '' | 输入框标签 |
| disabled | boolean | false | 是否禁用 |
| required | boolean | false | 是否必填 |
| validator | function | - | 自定义验证函数 |
| minSearchLength | number | 1 | 最小搜索长度 |
| searchOnBlur | boolean | false | 是否在失去焦点时搜索 |
| searchOnValid | boolean | false | 是否在验证通过时搜索 |
| debounceTime | number | 300 | 防抖延迟时间（毫秒） |

## Events

| 事件名 | 参数 | 说明 |
|-------|------|------|
| update:modelValue | (value: string) | 输入值更新时触发 |
| change | (value: string) | 值变化时触发 |
| search | (value: string) | 执行搜索时触发 |
| valid | (isValid: boolean) | 验证结果变化时触发 |

## Methods

| 方法名 | 参数 | 返回值 | 说明 |
|-------|------|--------|------|
| search | - | void | 手动触发搜索 |
| reset | - | void | 重置输入框状态 |

## 样式定制

组件继承了 `ValidatedInput` 的样式变量，并添加了以下变量：

```css
:root {
  --form-button-padding: 12px;
}
```

## 最佳实践

1. 搜索触发时机：
   - 即时搜索：适用于快速过滤场景
   - 按钮触发：适用于需要精确搜索的场景
   - 失焦搜索：适用于表单集成场景

2. 防抖处理：
   - 设置合适的防抖时间
   - 考虑用户输入速度
   - 平衡实时性和性能

3. 验证规则：
   - 根据业务需求设置最小搜索长度
   - 添加适当的输入限制
   - 提供清晰的错误提示

4. 用户体验：
   - 显示加载状态反馈
   - 保持搜索按钮状态同步
   - 提供清空输入的功能

## 注意事项

1. 性能优化：
   - 合理使用防抖
   - 避免不必要的搜索请求
   - 优化验证逻辑

2. 状态管理：
   - 处理好加载状态
   - 管理好禁用状态
   - 保持搜索按钮状态同步

3. 错误处理：
   - 处理搜索失败情况
   - 提供重试机制
   - 显示友好的错误提示

4. 集成建议：
   - 与后端接口协调
   - 处理好异步搜索
   - 考虑批量搜索场景 