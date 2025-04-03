<template>
  <TableForm 
    title="基本信息" 
    description="管理产品的基本配置信息"
    :uses-mock-data="usesMockData"
    :saving="saving"
    @save="handleSave"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="product-form">
      <el-form-item label="产品代码" prop="code">
        <el-input v-model="form.code" disabled />
        <div class="form-item-tip">产品代码创建后不可修改</div>
      </el-form-item>
      
      <el-form-item label="产品名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入产品名称" />
      </el-form-item>
      
      <el-form-item label="服务商" prop="provider_id">
        <el-select v-model="form.provider_id" placeholder="请选择服务商">
          <el-option 
            v-for="provider in providers"
            :key="provider.id"
            :label="provider.name"
            :value="provider.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="国家" prop="country">
        <el-input v-model="form.country" placeholder="请输入国家" />
      </el-form-item>
      
      <el-form-item label="体积重系数" prop="dim_factor">
        <div class="dim-factor-input">
          <el-input-number 
            v-model="form.dim_factor" 
            :precision="2"
            :step="0.01"
            :min="0"
          />
          <el-select 
            v-model="form.dim_factor_unit" 
            placeholder="选择单位"
            style="width: 120px; margin-left: 8px;"
          >
            <el-option
              v-for="option in dimFactorUnitOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
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
      
      <el-form-item label="失效日期" prop="expiration_date">
        <el-date-picker
          v-model="form.expiration_date"
          type="date"
          placeholder="选择失效日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      
      <el-form-item label="币种" prop="currency_code">
        <el-select v-model="form.currency_code" placeholder="请选择币种">
          <el-option label="USD" value="USD" />
          <el-option label="CNY" value="CNY" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="状态" prop="status">
        <el-switch
          v-model="form.status"
          :active-value="1"
          :inactive-value="0"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>
      
      <el-form-item label="启用开始日期" prop="enabled_start_date">
        <el-date-picker
          v-model="form.enabled_start_date"
          type="date"
          placeholder="选择启用开始日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      
      <el-form-item label="启用结束日期" prop="enabled_end_date">
        <el-date-picker
          v-model="form.enabled_end_date"
          type="date"
          placeholder="选择启用结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请输入产品描述"
        />
      </el-form-item>
    </el-form>
  </TableForm>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { Check } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage } from 'element-plus';
import TableForm from './TableForm.vue';

const props = defineProps<{
  formData: any;
  providers: any[];
  usesMockData: boolean;
  saving: boolean;
  dimFactorUnitOptions: { label: string; value: string }[];
}>();

const emit = defineEmits<{
  (e: 'save', formData: any): void;
}>();

const formRef = ref<FormInstance>();
const form = reactive({ ...props.formData });

// 表单验证规则
const rules = reactive<FormRules>({
  name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  provider_id: [
    { required: true, message: '请选择服务商', trigger: 'change' }
  ],
  country: [
    { required: true, message: '请输入国家', trigger: 'blur' }
  ],
  dim_factor: [
    { required: true, message: '请输入体积重系数', trigger: 'blur' }
  ],
  effective_date: [
    { required: true, message: '请选择生效日期', trigger: 'change' }
  ],
  expiration_date: [
    { required: true, message: '请选择失效日期', trigger: 'change' }
  ],
  currency_code: [
    { required: true, message: '请选择币种', trigger: 'change' }
  ]
});

// 保存表单
const handleSave = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate((valid, fields) => {
    if (valid) {
      emit('save', form);
    } else {
      ElMessage.error('请检查表单填写是否正确');
    }
  });
};
</script>

<style scoped>
.form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dim-factor-input {
  display: flex;
  align-items: center;
}

.product-form {
  margin-top: 20px;
}
</style> 