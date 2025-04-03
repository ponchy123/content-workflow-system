<template>
  <div class="validation-rules-editor">
    <el-form :model="localRules" label-width="100px">
      <el-form-item label="值类型">
        <el-select v-model="localRules.type" placeholder="请选择值类型" @change="handleTypeChange">
          <el-option label="文本" value="string" />
          <el-option label="数字" value="number" />
          <el-option label="布尔" value="boolean" />
          <el-option label="邮箱" value="email" />
          <el-option label="数组" value="array" />
          <el-option label="JSON" value="json" />
        </el-select>
      </el-form-item>

      <!-- 文本类型规则 -->
      <template v-if="localRules.type === 'string'">
        <el-form-item label="最大长度">
          <el-input-number v-model="localRules.max_length" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="正则匹配">
          <el-input v-model="localRules.pattern" placeholder="请输入正则表达式" />
        </el-form-item>
      </template>

      <!-- 数字类型规则 -->
      <template v-if="localRules.type === 'number'">
        <el-form-item label="最小值">
          <el-input-number v-model="localRules.min" :precision="2" />
        </el-form-item>
        <el-form-item label="最大值">
          <el-input-number v-model="localRules.max" :precision="2" />
        </el-form-item>
      </template>

      <!-- 数组类型规则 -->
      <template v-if="localRules.type === 'array'">
        <el-form-item label="最大项数">
          <el-input-number v-model="localRules.max_items" :min="1" :max="100" />
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';

  interface ValidationRule {
    type: 'string' | 'number' | 'boolean' | 'email' | 'array' | 'json';
    max_length?: number;
    pattern?: string;
    min?: number;
    max?: number;
    max_items?: number;
  }

  const props = defineProps({
    modelValue: {
      type: Object as () => ValidationRule | null,
      default: null,
    },
  });

  const emit = defineEmits(['update:modelValue', 'update:type']);

  // 本地规则对象
  const localRules = ref<ValidationRule>({
    type: 'string',
    ...props.modelValue,
  });

  // 监听值变化
  watch(
    () => props.modelValue,
    newVal => {
      if (newVal) {
        localRules.value = { ...newVal };
      } else {
        localRules.value = { type: 'string' };
      }
    },
    { immediate: true },
  );

  // 监听本地规则变化
  watch(
    localRules,
    newVal => {
      emit('update:modelValue', { ...newVal });
    },
    { deep: true },
  );

  // 处理类型变化
  const handleTypeChange = (type: ValidationRule['type']) => {
    // 重置规则
    const newRules: ValidationRule = { type };

    // 根据类型添加默认规则
    switch (type) {
      case 'string':
        newRules.max_length = 100;
        break;
      case 'number':
        newRules.min = undefined;
        newRules.max = undefined;
        break;
      case 'array':
        newRules.max_items = 10;
        break;
    }

    localRules.value = newRules;
    emit('update:type', type);
  };
</script>

<style scoped>
  .validation-rules-editor {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 15px;
    background-color: #f8f9fa;
  }
</style>
