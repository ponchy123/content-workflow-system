<template>
  <el-dialog
    :title="dialogTitle"
    v-model="dialogVisible"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
      <el-form-item label="配置键" prop="key">
        <el-input v-model="formData.key" placeholder="请输入配置键" :disabled="!!configData" />
      </el-form-item>

      <el-form-item label="配置类型" prop="config_type">
        <el-select v-model="formData.config_type" placeholder="请选择配置类型">
          <el-option
            v-for="(label, value) in configTypes"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="配置值" prop="value">
        <config-value-editor
          v-model="formData.value"
          :type="valueType"
          :validation-rules="formData.validation_rules"
        />
      </el-form-item>

      <el-form-item label="验证规则" prop="validation_rules">
        <validation-rules-editor
          v-model="formData.validation_rules"
          @update:type="handleValidationTypeChange"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入配置描述"
        />
      </el-form-item>

      <el-form-item label="是否公开" prop="is_public">
        <el-switch v-model="formData.is_public" />
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading"> 确定 </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { ElMessage } from 'element-plus';
  import type { FormInstance } from 'element-plus';
  import ConfigValueEditor from './ConfigValueEditor.vue';
  import ValidationRulesEditor from './ValidationRulesEditor.vue';

  type ValidationType = 'string' | 'number' | 'boolean' | 'email' | 'array' | 'json';

  interface ValidationRule {
    type: ValidationType;
    max_length?: number;
    pattern?: string;
    min?: number;
    max?: number;
    max_items?: number;
    [key: string]: any;
  }

  interface ConfigData {
    id?: number;
    key: string;
    value: any;
    description: string;
    config_type: string;
    is_public: boolean;
    validation_rules: ValidationRule | null;
  }

  const props = defineProps({
    modelValue: {
      type: Boolean,
      required: true,
    },
    configData: {
      type: Object as () => ConfigData | null,
      default: null,
    },
    configTypes: {
      type: Object as () => Record<string, string>,
      required: true,
    },
  });

  const emit = defineEmits(['update:modelValue', 'success']);

  // 表单引用
  const formRef = ref<FormInstance>();
  const loading = ref(false);

  // 对话框标题
  const dialogTitle = computed(() => {
    return props.configData ? '编辑配置' : '新增配置';
  });

  // 对话框可见性
  const dialogVisible = computed({
    get: () => props.modelValue,
    set: val => emit('update:modelValue', val),
  });

  // 表单数据
  const formData = ref<ConfigData>({
    key: '',
    value: null,
    description: '',
    config_type: 'basic',
    is_public: false,
    validation_rules: null,
  });

  // 表单验证规则
  const rules = {
    key: [
      { required: true, message: '请输入配置键', trigger: 'blur' },
      {
        pattern: /^[a-z][a-z0-9_]*$/,
        message: '配置键只能包含小写字母、数字和下划线，且必须以字母开头',
        trigger: 'blur',
      },
    ],
    config_type: [{ required: true, message: '请选择配置类型', trigger: 'change' }],
    value: [{ required: true, message: '请输入配置值', trigger: 'blur' }],
    description: [{ required: true, message: '请输入配置描述', trigger: 'blur' }],
  };

  // 配置值类型
  const valueType = computed(() => {
    return formData.value.validation_rules?.type || 'text';
  });

  // 监听配置数据变化
  watch(
    () => props.configData,
    newVal => {
      if (newVal) {
        formData.value = { ...newVal };
      } else {
        formData.value = {
          key: '',
          value: null,
          description: '',
          config_type: 'basic',
          is_public: false,
          validation_rules: null,
        };
      }
    },
    { immediate: true },
  );

  // 处理验证规则类型变化
  const handleValidationTypeChange = (type: string) => {
    // 根据类型设置默认值
    switch (type) {
      case 'number':
        formData.value.value = 0;
        break;
      case 'boolean':
        formData.value.value = false;
        break;
      case 'array':
        formData.value.value = [];
        break;
      default:
        formData.value.value = '';
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    if (!formRef.value) return;

    try {
      await formRef.value.validate();

      loading.value = true;
      const url = props.configData
        ? `/api/system-configs/${props.configData.id}/`
        : '/api/system-configs/';

      const response = await fetch(url, {
        method: props.configData ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData.value),
      });

      if (!response.ok) {
        throw new Error('保存失败');
      }

      ElMessage.success(props.configData ? '更新成功' : '创建成功');
      emit('success');
      dialogVisible.value = false;
    } catch (error: any) {
      if (error.name === 'ValidationError') {
        // 表单验证错误，已经由 Element Plus 处理
        return;
      }
      console.error('保存配置失败:', error);
      ElMessage.error('保存失败');
    } finally {
      loading.value = false;
    }
  };
</script>

<style scoped>
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
</style>
