<template>
  <base-rate-editor :title="title">
    <template #actions>
      <slot name="actions">
        <el-button v-if="hasSubmitButton" type="primary" :loading="loading" @click="handleSubmit">
          {{ submitText }}
        </el-button>
        <el-button v-if="hasCancelButton" @click="handleCancel">
          {{ cancelText }}
        </el-button>
      </slot>
    </template>

    <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
      <slot name="form-items">
        <el-form-item label="生效日期" prop="effectiveDate">
          <el-date-picker
            v-model="formData.effectiveDate"
            type="date"
            placeholder="选择生效日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item label="费率百分比" prop="rate">
          <el-input-number
            v-model="formData.rate"
            :min="0"
            :max="100"
            :precision="2"
            :step="0.1"
            :disabled="loading"
          />
          <div class="form-tip">输入0-100之间的数字，表示百分比</div>
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            placeholder="输入备注信息"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item>
          <div class="form-tip">燃油费率变更将影响所有使用该费率的计算</div>
        </el-form-item>
      </slot>
    </el-form>
  </base-rate-editor>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import type { FormRules } from 'element-plus';
  import { BaseRateEditor } from '@/components/common';

  interface FuelRateForm {
    effectiveDate: string;
    rate: number;
    remark: string;
  }

  interface Props {
    initialData?: Partial<FuelRateForm>;
    loading?: boolean;
    title?: string;
    hasSubmitButton?: boolean;
    hasCancelButton?: boolean;
    submitText?: string;
    cancelText?: string;
  }

  const props = withDefaults(defineProps<Props>(), {
    initialData: () => ({}),
    loading: false,
    title: '燃油费率设置',
    hasSubmitButton: true,
    hasCancelButton: true,
    submitText: '保存',
    cancelText: '取消',
  });

  const emit = defineEmits<{
    (e: 'submit', data: FuelRateForm): void;
    (e: 'cancel'): void;
  }>();

  const formRef = ref();
  const formData = ref<FuelRateForm>({
    effectiveDate: props.initialData.effectiveDate || '',
    rate: props.initialData.rate || 0,
    remark: props.initialData.remark || '',
  });

  const rules: FormRules = {
    effectiveDate: [{ required: true, message: '请选择生效日期', trigger: 'blur' }],
    rate: [
      { required: true, message: '请输入费率百分比', trigger: 'blur' },
      { type: 'number', min: 0, max: 100, message: '费率必须在0-100之间', trigger: 'blur' }
    ]
  };

  const handleSubmit = async () => {
    if (!formRef.value) return;

    try {
      await formRef.value.validate();
      emit('submit', formData.value);
    } catch (error) {
      // 表单验证失败
    }
  };

  const handleCancel = () => {
    emit('cancel');
  };
</script>
