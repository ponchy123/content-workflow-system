<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    :label-position="labelPosition"
    :label-width="labelWidth"
    class="calculator-form"
    @submit.prevent="handleSubmit"
  >
    <!-- 基本信息 -->
    <div class="form-section">
      <div class="form-section-title">基本信息</div>
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item :label="fromLabel" prop="fromAddress">
            <slot name="from-address">
              <postal-code-input
                v-model="form.fromAddress"
                :placeholder="fromPlaceholder"
                @result="handleFromAddressResult"
              />
            </slot>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="toLabel" prop="toAddress">
            <slot name="to-address">
              <postal-code-input
                v-model="form.toAddress"
                :placeholder="toPlaceholder"
                @result="handleToAddressResult"
              />
            </slot>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 包裹信息 -->
    <div class="form-section">
      <div class="form-section-title">包裹信息</div>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="重量" prop="weight" class="compact-form-item">
            <unit-input
              v-model="form.weight"
              v-model:unit="form.weightUnit"
              name="weight"
              :min="0.1"
              :max="1000"
              :step="0.1"
              :precision="2"
              :show-unit-select="true"
              :units="[
                { label: 'KG', value: 'KG' },
                { label: 'LB', value: 'LB' },
                { label: 'OZ', value: 'OZ' },
              ]"
              @change="handleWeightChange"
            />
            <slot name="weight-info"></slot>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="长度" prop="length" class="compact-form-item">
            <unit-input
              v-model="form.length"
              v-model:unit="form.dimensionUnit"
              name="length"
              :min="1"
              :precision="1"
              :show-unit-select="true"
              :units="[
                { label: 'CM', value: 'CM' },
                { label: 'IN', value: 'IN' },
              ]"
              @change="handleDimensionChange"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="宽度" prop="width" class="compact-form-item">
            <unit-input
              v-model="form.width"
              v-model:unit="form.dimensionUnit"
              name="width"
              :min="1"
              :precision="1"
              :show-unit-select="true"
              :units="[
                { label: 'CM', value: 'CM' },
                { label: 'IN', value: 'IN' },
              ]"
              @change="handleDimensionChange"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="高度" prop="height" class="compact-form-item">
            <unit-input
              v-model="form.height"
              v-model:unit="form.dimensionUnit"
              name="height"
              :min="1"
              :precision="1"
              :show-unit-select="true"
              :units="[
                { label: 'CM', value: 'CM' },
                { label: 'IN', value: 'IN' },
              ]"
              @change="handleDimensionChange"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 服务选项 -->
    <template v-if="showServices">
      <div class="form-section">
        <div class="form-section-title">服务选项</div>
        <slot name="service-options">
          <!-- 产品选择模式 -->
          <el-row :gutter="24" class="product-selection-row">
            <el-col :span="24">
              <el-form-item label="产品选择模式" class="compact-form-item">
                <el-radio-group v-model="productSelectionMode" @change="handleProductSelectionModeChange">
                  <el-radio :value="'single'">单产品</el-radio>
                  <el-radio :value="'compare'">多产品比较</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- 住宅地址选项 -->
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="住宅地址" class="compact-form-item">
                <el-switch v-model="form.isResidential"></el-switch>
                <span class="option-hint" style="margin-left: 10px; font-size: 12px; color: #999;">选择此项将应用住宅地址附加费</span>
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- 产品类型选择 -->
          <el-row :gutter="24">
            <el-col :span="24" v-if="productSelectionMode === 'single'">
              <el-form-item label="产品类型" prop="productType" class="compact-form-item">
                <el-select 
                  v-model="form.productType" 
                  placeholder="请选择产品类型"
                  filterable
                >
                  <template v-if="Array.isArray(props.productTypes) && props.productTypes.length > 0">
                    <el-option
                      v-for="item in props.productTypes"
                      :key="typeof item === 'string' ? item : item.code"
                      :label="typeof item === 'string' ? item : item.name"
                      :value="typeof item === 'string' ? item : item.code"
                    >
                      <div class="product-option" v-if="typeof item !== 'string'">
                        <span>{{ item.name }}</span>
                        <span class="product-code">{{ item.code }}</span>
                      </div>
                      <div v-else>{{ item }}</div>
                    </el-option>
                  </template>
                  <el-option v-else value="" disabled>没有可用产品</el-option>
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="24" v-else>
              <el-form-item label="比较产品" prop="compareProducts" class="compact-form-item">
                <el-select 
                  v-model="compareProducts" 
                  placeholder="请选择要比较的产品"
                  filterable
                  multiple
                >
                  <template v-if="Array.isArray(props.productTypes) && props.productTypes.length > 0">
                    <el-option
                      v-for="item in props.productTypes"
                      :key="typeof item === 'string' ? item : item.code"
                      :label="typeof item === 'string' ? item : item.name"
                      :value="typeof item === 'string' ? item : item.code"
                    >
                      <div class="product-option" v-if="typeof item !== 'string'">
                        <span>{{ item.name }}</span>
                        <span class="product-code">{{ item.code }}</span>
                      </div>
                      <div v-else>{{ item }}</div>
                    </el-option>
                  </template>
                  <el-option v-else value="" disabled>没有可用产品</el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </slot>
      </div>
    </template>

    <slot name="form-footer"></slot>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage } from 'element-plus';
import PostalCodeInput from '@/components/postal/PostalCodeInput.vue';
import UnitInput from '@/components/common/form/UnitInput.vue';
import type {
  CalculationRequest,
  WeightUnit,
  DimensionUnit
} from '@/types/calculator';
import type { PostalSearchResult } from '@/types/postal';

interface Props {
  labelPosition?: 'top' | 'left' | 'right';
  labelWidth?: string | number;
  fromLabel?: string;
  toLabel?: string;
  fromPlaceholder?: string;
  toPlaceholder?: string;
  showDimensions?: boolean;
  showNote?: boolean;
  showServices?: boolean;
  productTypes?: Array<string | { code: string; name: string }>;
  serviceLevel?: string;
}

interface FormData extends CalculationRequest {
  weightUnit: WeightUnit;
  dimensionUnit: DimensionUnit;
  length?: number;
  width?: number;
  height?: number;
  isResidential: boolean;
}

interface UnitChangeEvent {
  value: string | number;
  unit: string;
  target?: { name: string };
}

const props = withDefaults(defineProps<Props>(), {
  labelPosition: 'right',
  labelWidth: 100,
  fromLabel: '发件地址',
  toLabel: '收件地址',
  fromPlaceholder: '请输入发件地邮编',
  toPlaceholder: '请输入收件地邮编',
  showDimensions: true,
  showNote: true,
  showServices: true,
  productTypes: () => [],
  serviceLevel: ''
});

const emit = defineEmits<{
  (e: 'submit', form: CalculationRequest): void;
  (e: 'reset'): void;
  (e: 'from-address-change', address: string): void;
  (e: 'to-address-change', address: string): void;
  (e: 'weight-change', value: { weight: number; unit: string }): void;
  (
    e: 'dimension-change',
    value: { length: number; width: number; height: number; unit: string },
  ): void;
  (e: 'product-selection-mode-change', mode: 'single' | 'compare'): void;
  (e: 'compare-products-change', products: string[]): void;
}>();

const formRef = ref<FormInstance>();
const form = reactive<FormData>({
  fromAddress: '',
  toAddress: '',
  weight: 0,
  volume: 0,
  quantity: 1,
  productType: '',
  note: '',
  weightUnit: 'KG',
  dimensionUnit: 'CM',
  length: 0,
  width: 0,
  height: 0,
  isResidential: false
});

// 产品选择模式
const productSelectionMode = ref<'single' | 'compare'>('single');
const compareProducts = ref<string[]>([]);

// 表单验证规则
const rules = reactive<FormRules>({
  fromAddress: [
    { required: true, message: '请输入起始地邮编', trigger: 'blur' },
    { pattern: /^\d+$/, message: '请输入数字邮政编码', trigger: 'blur' }
  ],
  toAddress: [
    { required: true, message: '请输入目的地邮编', trigger: 'blur' },
    { pattern: /^\d+$/, message: '请输入数字邮政编码', trigger: 'blur' }
  ],
  weight: [
    { required: true, message: '请输入重量', trigger: 'blur' },
    { type: 'number', min: 0.1, message: '重量必须大于0.1', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '数量必须大于0', trigger: 'blur' }
  ],
  productType: [
    { required: true, message: '请选择产品类型', trigger: 'change' }
  ]
});

// 监听产品类型变化
watch(() => props.productTypes, (newTypes) => {
  console.log('接收到新的产品类型列表:', newTypes);
}, { deep: true });

// 监听表单中产品类型变化
watch(() => form.productType, (newType) => {
  console.log('产品类型变更为:', newType);
}, { immediate: true });

// 计算体积
const calculateVolume = () => {
  if (form.length && form.width && form.height) {
    form.volume = (form.length * form.width * form.height) / 1000000; // 转换为立方米
  }
};

// 监听尺寸变化
watch([() => form.length, () => form.width, () => form.height], calculateVolume);

// 处理地址变更
const handleFromAddressResult = (result: PostalSearchResult) => {
  form.fromAddress = result.postal_code;
  emit('from-address-change', result.postal_code);
};

const handleToAddressResult = (result: PostalSearchResult) => {
  form.toAddress = result.postal_code;
  emit('to-address-change', result.postal_code);
};

// 处理重量变化
const handleWeightChange = (event: UnitChangeEvent) => {
  form.weight = Number(event.value);
  form.weightUnit = event.unit as WeightUnit;
  emit('weight-change', { weight: Number(event.value), unit: event.unit });
};

// 处理尺寸变化
const handleDimensionChange = (event: UnitChangeEvent) => {
  const value = Number(event.value);
  const { unit } = event;
  
  if (event.target?.name === 'length') {
    form.length = value;
  } else if (event.target?.name === 'width') {
    form.width = value;
  } else if (event.target?.name === 'height') {
    form.height = value;
  }
  
  form.dimensionUnit = unit as DimensionUnit;
  
  if (form.length && form.width && form.height) {
    emit('dimension-change', {
      length: form.length,
      width: form.width,
      height: form.height,
      unit: form.dimensionUnit
    });
  }
};

// 处理产品选择模式变化
const handleProductSelectionModeChange = (mode: any) => {
  // 确保传入的值是有效的模式
  const validMode = (typeof mode === 'string' && (mode === 'single' || mode === 'compare')) 
    ? mode as 'single' | 'compare'
    : 'single';
  
  // 如果切换到多产品比较模式，初始化已选产品
  if (validMode === 'compare' && form.productType && compareProducts.value.length === 0) {
    compareProducts.value = [form.productType];
  }
  emit('product-selection-mode-change', validMode);
};

// 监听多产品选择变化
watch(compareProducts, (newProducts) => {
  console.log('比较产品列表变化:', newProducts);
  emit('compare-products-change', newProducts);
}, { deep: true });

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    const request: CalculationRequest = {
      fromAddress: form.fromAddress,
      toAddress: form.toAddress,
      weight: form.weight,
      volume: form.volume,
      quantity: form.quantity,
      productType: form.productType,
      note: form.note,
      isResidential: form.isResidential
    };
    emit('submit', request);
  } catch (error) {
    ElMessage.error('请检查表单填写是否正确');
  }
};

// 重置表单
const resetForm = () => {
  if (!formRef.value) return;
  formRef.value.resetFields();
  emit('reset');
};

defineExpose({
  form,
  formRef,
  resetForm,
  validate: async () => {
    if (!formRef.value) return false;
    return formRef.value.validate();
  },
  setProductType: (productType: string) => {
    console.log('通过方法设置产品类型:', productType);
    form.productType = productType;
  },
  productSelectionMode,
  compareProducts,
  setCompareProducts: (products: string[]) => {
    compareProducts.value = products;
  },
  setProductSelectionMode: (mode: 'single' | 'compare') => {
    productSelectionMode.value = mode;
  }
});
</script>

<style>
  /* 表单基础样式 */
  .calculator-form {
    margin-bottom: 20px;
    background-color: #fff;
    border-radius: 4px;
  }

  .form-section {
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ebeef5;
  }

  .form-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }

  .form-section-title {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ebeef5;
  }

  /* 调整表单项间距 */
  .compact-form-item {
    margin-bottom: 15px;
  }

  /* 产品选择行样式 */
  .product-selection-row {
    margin-bottom: 10px;
  }

  /* 产品选项样式 */
  .product-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  .product-code {
    color: #909399;
    font-size: 0.85em;
  }

  /* 选项提示文本 */
  .option-hint {
    font-size: 12px;
    color: #909399;
    margin-left: 8px;
  }

  /* 标签靠近输入框的样式 */
  .calculator-form :deep(.el-form-item__label) {
    padding-right: 8px; /* 减少标签与输入框的距离 */
  }

  /* 紧凑型表单项样式 */
  .compact-form-item {
    margin-bottom: 18px; /* 减少表单项之间的垂直间距 */
  }

  /* 表单区块样式 */
  .form-section {
    margin-bottom: 18px;
  }

  /* 表单区块标题 */
  .form-section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--el-text-color-primary);
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-light);
  }
  
  .unit-display {
    padding: 0 12px;
    height: var(--form-control-height);
    line-height: var(--form-control-height);
    border-left: 1px solid var(--el-border-color);
    background-color: var(--el-fill-color-light);
    color: var(--el-text-color-regular);
    white-space: nowrap;
    font-size: 14px;
  }

  /* 暗色主题适配 */
  .dark .unit-display {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-darker);
  }

  /* 添加响应式布局 */
  @media screen and (max-width: 768px) {
    .calculator-form {
      padding: 12px;
    }
    
    .calculator-form :deep(.el-form-item) {
      margin-bottom: 12px;
    }
    
    .calculator-form :deep(.el-form-item__label) {
      width: 100% !important;
      text-align: left;
      padding-bottom: 4px;
    }
  }
</style>
