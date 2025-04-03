<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="fuel-rate-form">
    <el-form-item label="服务商" prop="provider">
      <el-select v-model="form.provider" placeholder="请选择服务商">
        <el-option label="顺丰" value="SF" />
        <el-option label="圆通" value="YTO" />
        <el-option label="中通" value="ZTO" />
        <el-option label="韵达" value="YD" />
        <el-option label="申通" value="STO" />
      </el-select>
    </el-form-item>

    <el-form-item label="生效日期" prop="effective_date">
      <el-date-picker
        v-model="form.effective_date"
        type="date"
        placeholder="选择生效日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
    </el-form-item>

    <el-form-item label="失效日期" prop="expiry_date">
      <el-date-picker
        v-model="form.expiry_date"
        type="date"
        placeholder="选择失效日期（可选）"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
    </el-form-item>

    <el-form-item label="费率" prop="rate">
      <el-input-number v-model="form.rate" :precision="4" :step="0.001" :min="0" :max="1">
        <template #append>%</template>
      </el-input-number>
      <div class="form-tip">费率为小数，例如：0.1 表示 10%</div>
    </el-form-item>

    <el-form-item label="状态" prop="is_active">
      <el-switch
        v-model="form.is_active"
        :active-value="true"
        :inactive-value="false"
        active-text="启用"
        inactive-text="禁用"
      />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
      <el-button @click="handleReset">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import type { FormInstance, FormRules } from 'element-plus';
  import type { FuelRateCreateRequest } from '@/api/fuel';

  const emit = defineEmits<{
    (e: 'submit', data: FuelRateCreateRequest): void;
  }>();

  const formRef = ref<FormInstance>();
  const form = ref<FuelRateCreateRequest>({
    provider: '',
    rate: 0,
    effective_date: '',
    expiry_date: undefined,
    is_active: true,
  });

  const validateEffectiveDate = (rule: any, value: string, callback: any) => {
    if (!value) {
      callback(new Error('请选择生效日期'));
      return;
    }
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const effectiveDate = new Date(value);
    if (effectiveDate < today) {
      callback(new Error('生效日期不能早于今天'));
    } else {
      if (form.value.expiry_date) {
        const expiryDate = new Date(form.value.expiry_date);
        if (expiryDate <= effectiveDate) {
          callback(new Error('生效日期必须早于失效日期'));
          return;
        }
      }
      callback();
    }
  };

  const validateExpiryDate = (rule: any, value: string, callback: any) => {
    if (!value) {
      callback();
      return;
    }
    if (!form.value.effective_date) {
      callback(new Error('请先选择生效日期'));
      return;
    }
    const effectiveDate = new Date(form.value.effective_date);
    const expiryDate = new Date(value);
    if (expiryDate <= effectiveDate) {
      callback(new Error('失效日期必须晚于生效日期'));
    } else {
      callback();
    }
  };

  const rules: FormRules = {
    provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
    effective_date: [
      { required: true, message: '请选择生效日期', trigger: 'change' },
      { validator: validateEffectiveDate, trigger: 'change' },
    ],
    expiry_date: [{ validator: validateExpiryDate, trigger: 'change' }],
    rate: [
      { required: true, message: '请输入费率', trigger: 'blur' },
      { type: 'number', min: 0, max: 1, message: '费率必须在0-1之间', trigger: 'blur' },
    ],
    is_active: [{ required: true, message: '请选择状态', trigger: 'change' }],
  };

  const handleSubmit = async () => {
    if (!formRef.value) return;

    await formRef.value.validate(valid => {
      if (valid) {
        emit('submit', form.value);
      }
    });
  };

  const handleReset = () => {
    if (!formRef.value) return;
    formRef.value.resetFields();
  };

  const setFieldsValue = (values: Partial<FuelRateCreateRequest>) => {
    Object.assign(form.value, values);
  };

  defineExpose({
    setFieldsValue,
    resetFields: handleReset,
    submit: handleSubmit,
  });
</script>

<style scoped>
  .fuel-rate-form {
    max-width: 500px;
    margin: 0 auto;
    padding: 20px;
  }

  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
</style>
