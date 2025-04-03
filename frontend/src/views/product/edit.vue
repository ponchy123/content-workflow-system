<template>
  <div class="page-container">
    <div class="page-header">
      <el-page-header :icon="ArrowLeft" @back="goBack" content="编辑产品" />
    </div>
    
    <!-- 表单容器 -->
    <div class="form-container">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <!-- 表单内容 -->
      <div v-else>
        <!-- 基本信息表单 -->
        <BasicInfoForm 
          :formData="product"
          :providers="[]"
          :uses-mock-data="usesMockData"
          :saving="saving"
          :dimFactorUnitOptions="[
            {label: 'kg/cm³', value: 'kg/cm³'},
            {label: 'lb/in³', value: 'lb/in³'}
          ]"
          @save="saveProductBasicInfo"
        />
        
        <!-- 基础费用表单 -->
        <BaseFeeTableForm
          :base-fee-list="baseFees"
          :available-zones="availableZones"
          :uses-mock-data="usesMockData"
          :saving="saving"
          :product-id="productId"
          @save="saveBaseFees"
          @add="addBaseFee"
          @check="checkBaseFeeData"
          @reload="reloadBaseFeeData"
          @remove="removeBaseFee"
          @update="updateBaseFee"
        />
        
        <!-- 附加费表单 -->
        <SurchargeTableForm
          :surcharges="surcharges"
          :available-zones="availableZones"
          :uses-mock-data="usesMockData"
          :saving="saving"
          :product-id="productId"
          @save="saveSurcharges"
          @change="handleSurchargeChange"
        />
        
        <!-- 季节性费用表单 -->
        <SeasonalFeeTableForm
          :seasonal-fees="seasonalFees"
          :uses-mock-data="usesMockData"
          :saving="saving"
          :product-id="productId"
          @save="saveSeasonalFees"
          @change="handleSeasonalFeeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowLeft } from '@element-plus/icons-vue';
import { 
  getProduct, 
  updateProduct, 
  getProductBaseFees as getBaseFees, 
  getSurcharges, 
  getSeasonalFees
} from '@/api/products';

// 自定义保存函数
import { axiosInstance } from '@/api/core/request';

// 导入组件
import { 
  BasicInfoForm,
  BaseFeeTableForm,
  SurchargeTableForm,
  SeasonalFeeTableForm
} from '@/components/product';

// 路由相关
const router = useRouter();
const route = useRoute();
const productId = route.params.id as string;

// 状态管理
const loading = ref(true);
const saving = ref(false);
const usesMockData = ref(false);

// 产品数据
const product = reactive({
  id: '',
  code: '',
  name: '',
  provider: '',
  country: '',
  dim_factor: 0,
  effective_date: '',
  expiration_date: '',
  currency: 'CNY',
  status: 'ACTIVE',
  description: ''
});

// 费用数据
const baseFees = ref<any[]>([]);
const surcharges = ref<any[]>([]);
const seasonalFees = ref<any[]>([]);

// 可用区间
const availableZones = ref(['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5']);

// 返回上一页
const goBack = () => {
  router.push('/product/list');
};

// 加载产品数据
const loadProductData = async () => {
  try {
    loading.value = true;
    const response = await getProduct(productId);
    const data = response.data;
    
    // 更新产品基本信息
    Object.assign(product, data);
    
    await Promise.all([
      loadBaseFees(),
      loadSurcharges(),
      loadSeasonalFees()
    ]);
    
    loading.value = false;
  } catch (error) {
    console.error('加载产品数据失败', error);
    ElMessage.error('加载产品数据失败');
    loading.value = false;
  }
};

// 加载基础费用
const loadBaseFees = async () => {
  try {
    const response = await getBaseFees(productId);
    if (response.data && response.data.length > 0) {
      baseFees.value = response.data;
      usesMockData.value = false;
    } else {
      // 使用模拟数据
      baseFees.value = generateMockBaseFees();
      usesMockData.value = true;
    }
  } catch (error) {
    console.error('加载基础费用失败', error);
    // 使用模拟数据
    baseFees.value = generateMockBaseFees();
    usesMockData.value = true;
  }
};

// 加载附加费
const loadSurcharges = async () => {
  try {
    const response = await getSurcharges(productId);
    if (response && Array.isArray(response) && response.length > 0) {
      surcharges.value = response;
    } else {
      // 使用模拟数据
      surcharges.value = generateMockSurcharges();
      usesMockData.value = true;
    }
  } catch (error) {
    console.error('加载附加费失败', error);
    // 使用模拟数据
    surcharges.value = generateMockSurcharges();
    usesMockData.value = true;
  }
};

// 加载季节性费用
const loadSeasonalFees = async () => {
  try {
    const response = await getSeasonalFees(productId);
    if (response && Array.isArray(response) && response.length > 0) {
      seasonalFees.value = response;
    } else {
      // 使用模拟数据
      seasonalFees.value = generateMockSeasonalFees();
      usesMockData.value = true;
    }
  } catch (error) {
    console.error('加载季节性费用失败', error);
    // 使用模拟数据
    seasonalFees.value = generateMockSeasonalFees();
    usesMockData.value = true;
  }
};

// 保存产品基本信息
const saveProductBasicInfo = async (productData: any) => {
  try {
    saving.value = true;
    await updateProduct(productId, productData);
    ElMessage.success('保存成功');
    saving.value = false;
  } catch (error) {
    console.error('保存产品基本信息失败', error);
    ElMessage.error('保存产品基本信息失败');
    saving.value = false;
  }
};

// 保存基础费用
const saveBaseFees = async (baseFeesData: any[]) => {
  try {
    saving.value = true;
    await saveBaseFeeData(productId, baseFeesData);
    ElMessage.success('保存基础费用成功');
    saving.value = false;
  } catch (error) {
    console.error('保存基础费用失败', error);
    ElMessage.error('保存基础费用失败');
    saving.value = false;
  }
};

// 保存附加费
const saveSurcharges = async (surchargesData: any[]) => {
  try {
    saving.value = true;
    await saveSurchargeData(productId, surchargesData);
    ElMessage.success('保存附加费成功');
    saving.value = false;
  } catch (error) {
    console.error('保存附加费失败', error);
    ElMessage.error('保存附加费失败');
    saving.value = false;
  }
};

// 保存季节性费用
const saveSeasonalFees = async (seasonalFeesData: any[]) => {
  try {
    saving.value = true;
    await saveSeasonalFeeData(productId, seasonalFeesData);
    ElMessage.success('保存季节性费用成功');
    saving.value = false;
  } catch (error) {
    console.error('保存季节性费用失败', error);
    ElMessage.error('保存季节性费用失败');
    saving.value = false;
  }
};

// API调用函数
const saveBaseFeeData = (productId: string, data: any[]) => {
  return axiosInstance({
    url: `/api/v1/products/base-fees/batch_save/`,
    method: 'post',
    data: {
      product_id: productId,
      base_fees: data
    }
  });
};

const saveSurchargeData = (productId: string, data: any[]) => {
  return axiosInstance({
    url: `/api/v1/products/surcharges/batch_save/`,
    method: 'post',
    data: {
      product_id: productId,
      surcharges: data
    }
  });
};

const saveSeasonalFeeData = (productId: string, data: any[]) => {
  return axiosInstance({
    url: `/api/v1/products/seasonal-fees/batch_save/`,
    method: 'post',
    data: {
      product_id: productId,
      seasonal_fees: data
    }
  });
};

// 基础费用相关方法
const addBaseFee = () => {
  const newBaseFee = {
    weight: 1,
    weight_unit: 'kg',
    fee_type: 'STEP',
    zone1_price: 10,
    zone1_unit_price: 2,
    zone2_price: 12,
    zone2_unit_price: 2.5,
    zone3_price: 15,
    zone3_unit_price: 3,
    zone4_price: 18,
    zone4_unit_price: 3.5,
    zone5_price: 20,
    zone5_unit_price: 4
  };
  baseFees.value.push(newBaseFee);
};

const removeBaseFee = (index: number) => {
  baseFees.value.splice(index, 1);
};

const updateBaseFee = (item: any, index: number) => {
  // 基础费用更新逻辑
  baseFees.value[index] = { ...item };
};

const checkBaseFeeData = () => {
  // 检查是否有空值或者无效值
  const hasInvalidData = baseFees.value.some(item => {
    return !item.weight || item.weight <= 0;
  });
  
  if (hasInvalidData) {
    ElMessage.warning('基础费用中存在无效数据，请检查');
  } else {
    ElMessage.success('基础费用数据检查通过');
  }
};

const reloadBaseFeeData = async () => {
  await loadBaseFees();
  ElMessage.success('基础费用数据已刷新');
};

// 附加费相关方法
const handleSurchargeChange = (newSurcharges: any[]) => {
  surcharges.value = newSurcharges;
};

const checkSurchargeData = () => {
  // 检查是否有空值或者无效值
  const hasInvalidData = surcharges.value.some(item => {
    return !item.name || !item.type || !item.calculation_method || !item.applicable_zones || item.applicable_zones.length === 0;
  });
  
  if (hasInvalidData) {
    ElMessage.warning('附加费中存在无效数据，请检查');
  } else {
    ElMessage.success('附加费数据检查通过');
  }
};

const reloadSurchargeData = async () => {
  await loadSurcharges();
  ElMessage.success('附加费数据已刷新');
};

// 季节性费用相关方法
const handleSeasonalFeeChange = (newSeasonalFees: any[]) => {
  seasonalFees.value = newSeasonalFees;
};

const checkSeasonalFeeData = () => {
  // 检查是否有空值或者无效值
  const hasInvalidData = seasonalFees.value.some(item => {
    return !item.name || !item.type || !item.start_date || !item.end_date || 
      !item.calculation_method || !item.applicable_zones || item.applicable_zones.length === 0;
  });
  
  if (hasInvalidData) {
    ElMessage.warning('季节性费用中存在无效数据，请检查');
  } else {
    ElMessage.success('季节性费用数据检查通过');
  }
};

const reloadSeasonalFeeData = async () => {
  await loadSeasonalFees();
  ElMessage.success('季节性费用数据已刷新');
};

// 生成模拟数据
const generateMockBaseFees = () => {
  return [
    {
      weight: 0.5,
      weight_unit: 'kg',
      fee_type: 'STEP',
      zone1_price: 10,
      zone1_unit_price: 2,
      zone2_price: 12,
      zone2_unit_price: 2.5,
      zone3_price: 15,
      zone3_unit_price: 3,
      zone4_price: 18,
      zone4_unit_price: 3.5,
      zone5_price: 20,
      zone5_unit_price: 4
    },
    {
      weight: 1,
      weight_unit: 'kg',
      fee_type: 'STEP',
      zone1_price: 12,
      zone1_unit_price: 2.2,
      zone2_price: 14,
      zone2_unit_price: 2.7,
      zone3_price: 17,
      zone3_unit_price: 3.2,
      zone4_price: 20,
      zone4_unit_price: 3.7,
      zone5_price: 22,
      zone5_unit_price: 4.2
    },
    {
      weight: 5,
      weight_unit: 'kg',
      fee_type: 'STEP',
      zone1_price: 20,
      zone1_unit_price: 3,
      zone2_price: 25,
      zone2_unit_price: 3.5,
      zone3_price: 30,
      zone3_unit_price: 4,
      zone4_price: 35,
      zone4_unit_price: 4.5,
      zone5_price: 40,
      zone5_unit_price: 5
    },
    {
      weight: 10,
      weight_unit: 'kg',
      fee_type: 'STEP',
      zone1_price: 30,
      zone1_unit_price: 3.5,
      zone2_price: 35,
      zone2_unit_price: 4,
      zone3_price: 40,
      zone3_unit_price: 4.5,
      zone4_price: 45,
      zone4_unit_price: 5,
      zone5_price: 50,
      zone5_unit_price: 5.5
    },
    {
      weight: 20,
      weight_unit: 'kg',
      fee_type: 'LINEAR',
      zone1_price: 50,
      zone1_unit_price: 4,
      zone2_price: 60,
      zone2_unit_price: 4.5,
      zone3_price: 70,
      zone3_unit_price: 5,
      zone4_price: 80,
      zone4_unit_price: 5.5,
      zone5_price: 90,
      zone5_unit_price: 6
    }
  ];
};

const generateMockSurcharges = () => {
  return [
    {
      name: '燃油附加费',
      type: 'FUEL',
      calculation_method: 'PERCENTAGE',
      applicable_zones: ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'],
      value: 10,
      min_charge: 5,
      max_charge: 100,
      is_active: true
    },
    {
      name: '安全费',
      type: 'SECURITY',
      calculation_method: 'FIXED',
      applicable_zones: ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'],
      value: 5,
      min_charge: 5,
      max_charge: 5,
      is_active: true
    },
    {
      name: '偏远地区费',
      type: 'REMOTE_AREA',
      calculation_method: 'FIXED',
      applicable_zones: ['Zone3', 'Zone4', 'Zone5'],
      value: 15,
      min_charge: 15,
      max_charge: 15,
      is_active: true
    }
  ];
};

const generateMockSeasonalFees = () => {
  const today = new Date();
  
  // 圣诞节期间
  const xmasStart = new Date(today.getFullYear(), 11, 15); // 12月15日
  const xmasEnd = new Date(today.getFullYear(), 11, 31); // 12月31日
  
  // 新年期间
  const newYearStart = new Date(today.getFullYear(), 0, 1); // 1月1日
  const newYearEnd = new Date(today.getFullYear(), 0, 15); // 1月15日
  
  // 夏季旺季
  const summerStart = new Date(today.getFullYear(), 5, 1); // 6月1日
  const summerEnd = new Date(today.getFullYear(), 7, 31); // 8月31日
  
  return [
    {
      name: '圣诞节附加费',
      type: 'HOLIDAY',
      start_date: xmasStart.toISOString().split('T')[0],
      end_date: xmasEnd.toISOString().split('T')[0],
      calculation_method: 'PERCENTAGE',
      applicable_zones: ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'],
      value: 15,
      min_charge: 10,
      max_charge: 200,
      is_active: true
    },
    {
      name: '新年附加费',
      type: 'HOLIDAY',
      start_date: newYearStart.toISOString().split('T')[0],
      end_date: newYearEnd.toISOString().split('T')[0],
      calculation_method: 'PERCENTAGE',
      applicable_zones: ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'],
      value: 12,
      min_charge: 8,
      max_charge: 150,
      is_active: true
    },
    {
      name: '夏季旺季附加费',
      type: 'PEAK_SEASON',
      start_date: summerStart.toISOString().split('T')[0],
      end_date: summerEnd.toISOString().split('T')[0],
      calculation_method: 'PERCENTAGE',
      applicable_zones: ['Zone3', 'Zone4', 'Zone5'],
      value: 8,
      min_charge: 5,
      max_charge: 100,
      is_active: false
    }
  ];
};

// 页面初始化
onMounted(() => {
  loadProductData();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.form-container {
  margin-bottom: 30px;
}

.loading-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}
</style> 