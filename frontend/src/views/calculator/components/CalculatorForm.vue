<template>
  <div>
    <el-form
      ref="form"
      :model="formData"
      :rules="rules"
      label-width="120px"
      inline-message
      scrollToError
    >
      <!-- 地址信息 -->
      <el-form-item label="起始地" prop="fromAddress">
        <el-input
          v-model="formData.fromAddress"
          placeholder="请输入起始地邮编"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="目的地" prop="toAddress">
        <el-input
          v-model="formData.toAddress"
          placeholder="请输入目的地邮编"
          style="width: 100%"
        />
      </el-form-item>
      
      <!-- 重量信息 -->
      <el-form-item label="重量" prop="weight">
        <el-input-number
          v-model="formData.weight"
          :min="0.01"
          :max="999999"
          :precision="2"
          :step="0.1"
          style="width: 180px"
        />
        
        <el-select v-model="formData.weightUnit" style="width: 80px; margin-left: 10px">
          <el-option label="千克" value="kg" />
          <el-option label="磅" value="lb" />
        </el-select>
      </el-form-item>
      
      <!-- 尺寸信息 -->
      <el-form-item label="尺寸" prop="dimensions">
        <div style="display: flex; align-items: center; gap: 10px; width: 100%">
          <span>长:</span>
          <el-input-number
            v-model="formData.length"
            :min="0.1"
            :max="999999"
            :precision="2"
            :step="0.1"
            style="width: 120px"
          />
          
          <span>宽:</span>
          <el-input-number
            v-model="formData.width"
            :min="0.1"
            :max="999999"
            :precision="2"
            :step="0.1"
            style="width: 120px"
          />
          
          <span>高:</span>
          <el-input-number
            v-model="formData.height"
            :min="0.1"
            :max="999999"
            :precision="2"
            :step="0.1"
            style="width: 120px"
          />
          
          <el-select v-model="formData.dimensionUnit" style="width: 80px; margin-left: 10px">
            <el-option label="厘米" value="cm" />
            <el-option label="英寸" value="in" />
          </el-select>
        </div>
      </el-form-item>
      
      <!-- 数量信息 -->
      <el-form-item label="数量" prop="quantity">
        <el-input-number
          v-model="formData.quantity"
          :min="1"
          :max="9999"
          :precision="0"
          :step="1"
          style="width: 180px"
        />
      </el-form-item>
      
      <!-- 产品类型选择 -->
      <el-form-item label="产品类型" prop="productType">
        <el-select
          v-model="formData.productType"
          placeholder="请选择产品类型"
          style="width: 100%"
          :loading="productsLoading"
        >
          <el-option
            v-for="product in availableProducts"
            :key="product.product_id"
            :label="product.product_name"
            :value="product.product_id"
          />
        </el-select>
      </el-form-item>
      
      <!-- 其他选项 -->
      <el-form-item label="保价服务" prop="insuranceValue">
        <el-input-number
          v-model="formData.insuranceValue"
          :min="0"
          :max="999999"
          :precision="2"
          :step="10"
          placeholder="请输入货物申报价值"
          style="width: 180px"
        />
      </el-form-item>
      
      <el-form-item label="服务等级" prop="serviceLevel">
        <el-select
          v-model="formData.serviceLevel"
          placeholder="请选择服务等级"
          style="width: 180px"
        >
          <el-option
            v-for="option in serviceLevelsOptions"
            :key="option.code"
            :label="option.name"
            :value="option.code"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="危险品" prop="isDangerous">
        <el-switch v-model="formData.isDangerous" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, defineProps, defineEmits, defineExpose } from 'vue';
import { getProducts } from '@/api/calculator';
import type { FormItemRule } from 'element-plus';

// 定义产品接口
interface Product {
  product_id: string;
  product_name: string;
}

// 定义表单数据接口
interface FormData {
  fromAddress: string;
  toAddress: string;
  weight: number;
  weightUnit: string;
  length: number;
  width: number;
  height: number;
  dimensionUnit: string;
  quantity: number;
  productType: string;
  insuranceValue: number;
  serviceLevel: string;
  isDangerous: boolean;
  compareProducts: string[];
  [key: string]: any;
}

const props = defineProps({
  initFormData: {
    type: Object,
    default: () => ({})
  },
  availableProducts: {
    type: Array as () => Product[],
    default: () => []
  }
});

const emit = defineEmits(['update:form']);

// 表单引用
const form = ref();

// 表单数据
const formData = reactive<FormData>({
  fromAddress: '',
  toAddress: '',
  weight: 1,
  weightUnit: 'kg',
  length: 1,
  width: 1,
  height: 1,
  dimensionUnit: 'cm',
  quantity: 1,
  productType: '',
  insuranceValue: 0,
  serviceLevel: '',
  isDangerous: false,
  compareProducts: []
});

// 表单校验规则
const rules = {
  fromAddress: [
    { required: true, message: '请输入起始地邮编', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '请输入正确的6位数字邮政编码', trigger: 'blur' }
  ],
  toAddress: [
    { required: true, message: '请输入目的地邮编', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '请输入正确的6位数字邮政编码', trigger: 'blur' }
  ],
  weight: [
    { required: true, message: '请输入重量', trigger: 'blur' },
    { min: 0.01, message: '重量必须大于0', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { min: 1, message: '数量必须大于等于1', trigger: 'blur' }
  ],
  productType: [
    { required: true, message: '请选择产品类型', trigger: 'change' }
  ]
};

// 服务等级选项
const serviceLevelsOptions = ref([
  { code: 'standard', name: '标准服务' },
  { code: 'express', name: '快速服务' },
  { code: 'premium', name: '优先服务' }
]);

const productsLoading = ref(false);
const availableProducts = ref<Product[]>([]);

// 初始化产品列表
const fetchProducts = async () => {
  if (props.availableProducts && props.availableProducts.length > 0) {
    availableProducts.value = props.availableProducts;
    return;
  }
  
  productsLoading.value = true;
  try {
    const response = await getProducts();
    if (response?.data) {
      availableProducts.value = response.data.map((product: any) => ({
        product_id: product.product_id,
        product_name: product.product_name
      }));
      
      // 如果有可用产品，默认选择第一个
      if (availableProducts.value.length > 0) {
        formData.productType = availableProducts.value[0].product_id;
      }
    }
  } catch (error) {
    console.error('获取产品列表失败:', error);
  } finally {
    productsLoading.value = false;
  }
};

// 重置表单
const reset = () => {
  if (form.value) {
    form.value.resetFields();
  }
};

// 验证表单
const validate = () => {
  if (!form.value) return Promise.resolve(false);
  return new Promise<boolean>((resolve) => {
    form.value.validate((valid: boolean) => {
      resolve(valid);
    });
  });
};

// 明确类型的validateForm方法
const validateForm = async (): Promise<boolean> => {
  if (!form.value) return false;
  try {
    return await validate();
  } catch (error) {
    console.error('表单验证错误:', error);
    return false;
  }
};

// 设置表单数据
const setFormData = (data: any) => {
  Object.keys(data).forEach((key) => {
    if (key in formData) {
      formData[key] = data[key];
    }
  });
};

onMounted(() => {
  // 初始化表单数据
  if (props.initFormData) {
    setFormData(props.initFormData);
  }
  
  // 获取产品列表
  fetchProducts();
});

// 暴露组件方法和属性
defineExpose({
  form: formData,
  reset,
  validate,
  validateForm,
  setFormData,
  compareProducts: formData.compareProducts,
  setProductType: (type: string) => {
    formData.productType = type;
  },
  setProductSelectionMode: (mode: 'single' | 'compare') => {
    // 实现产品选择模式切换逻辑
    console.log('切换到模式:', mode);
  },
  setCompareProducts: (products: string[]) => {
    formData.compareProducts = products;
  }
});
</script>

<style scoped>
.el-form {
  max-width: 800px;
  margin: 0 auto;
}
</style> 