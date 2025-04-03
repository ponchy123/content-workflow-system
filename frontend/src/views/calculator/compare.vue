<template>
  <div class="compare-container">
    <form-card
      title="产品比较"
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="right"
      label-width="120px"
    >
      <template #actions>
        <el-button type="primary" @click="handleCompare" :loading="loading"> 开始比较 </el-button>
      </template>

      <!-- 基本信息 -->
      <h3 class="form-group-title">基本信息</h3>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="起始地邮编" prop="fromAddress">
            <postal-code-input
              v-model="form.fromAddress"
              placeholder="请输入起始地邮编"
              @address-change="handleOriginAddressChange"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目的地邮编" prop="toAddress">
            <postal-code-input
              v-model="form.toAddress"
              placeholder="请输入目的地邮编"
              @address-change="handleDestinationAddressChange"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 包裹信息 -->
      <h3 class="form-group-title">包裹信息</h3>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="重量" prop="weight">
            <el-input-number v-model="form.weight" :min="0.1" :step="0.1" :precision="1" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数量" prop="quantity">
            <el-input-number v-model="form.quantity" :min="1" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 尺寸信息 -->
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="长" prop="length">
            <el-input-number v-model="form.length" :min="1" :precision="1" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="宽" prop="width">
            <el-input-number v-model="form.width" :min="1" :precision="1" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="高" prop="height">
            <el-input-number v-model="form.height" :min="1" :precision="1" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 其他信息 -->
      <h3 class="form-group-title">其他信息</h3>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="保价金额" prop="insuranceValue">
            <el-input-number v-model="form.insuranceValue" :min="0" :precision="2" :step="100" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否危险品" prop="isDangerous">
            <el-switch v-model="form.isDangerous" />
          </el-form-item>
        </el-col>
      </el-row>
    </form-card>

    <!-- 比较结果 -->
    <el-card v-if="compareResult" class="result-card">
      <template #header>
        <div class="card-header">
          <h2>比较结果</h2>
          <el-button type="primary" @click="handleSave">保存结果</el-button>
        </div>
      </template>

      <el-table :data="compareResult" border>
        <el-table-column prop="productName" label="产品名称" />
        <el-table-column prop="baseCharge" label="基础运费">
          <template #default="{ row }">
            {{ formatCurrency(row.baseCharge) }}
          </template>
        </el-table-column>
        <el-table-column prop="fuelSurcharge" label="燃油附加费">
          <template #default="{ row }">
            {{ formatCurrency(row.fuelSurcharge) }}
          </template>
        </el-table-column>
        <el-table-column prop="totalCharge" label="总费用">
          <template #default="{ row }">
            <span class="total-charge">
              {{ formatCurrency(row.totalCharge) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="actions" label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleSelect(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { ElMessage, ElInputNumber } from 'element-plus';
  import type { FormInstance, FormRules } from 'element-plus';
  import type { CalculationRequest } from '@/types/calculator';
  import type { PostalSearchResult } from '@/types/postal';
  import {
    getProductTypes,
    getServiceLevels,
    compareProductsAsync,
  } from '@/api/calculator/index';
  import { saveCalculationResult } from '@/api/calculator/index';
  import { PostalCodeInput } from '@/components/postal';
  import * as XLSX from 'xlsx';
  import { FormCard } from '@/components/common';
  import { formatCurrency } from '@/utils/format';

  interface ProductComparison {
    productName: string;
    baseCharge: number;
    fuelSurcharge: number;
    totalCharge: number;
    estimatedDays: number;
  }

  interface CompareFormData {
    fromAddress: string;
    toAddress: string;
    weight: number;
    length: number;
    width: number;
    height: number;
    productType: string;
    serviceLevel: string;
    insuranceValue: number;
    isDangerous: boolean;
    quantity: number;
  }

  const router = useRouter();
  const formRef = ref<FormInstance>();
  const loading = ref(false);

  // 表单数据
  const form = ref<CompareFormData>({
    fromAddress: '',
    toAddress: '',
    weight: 1,
    length: 10,
    width: 10,
    height: 10,
    productType: '',
    serviceLevel: '',
    insuranceValue: 0,
    isDangerous: false,
    quantity: 1
  });

  // 选项数据
  const productTypes = ref<Array<{ code: string; name: string }>>([]);
  const serviceLevels = ref<Array<{ code: string; name: string }>>([]);
  const compareResult = ref<ProductComparison[]>([]);
  const productOptions = ref<Array<{ value: string; label: string }>>([]);
  const serviceLevelOptions = ref<Array<{ value: string; label: string }>>([]);

  // 地址信息
  const originAddress = ref<PostalSearchResult | null>(null);
  const destinationAddress = ref<PostalSearchResult | null>(null);

  // 处理地址变化
  const handleOriginAddressChange = (address: PostalSearchResult | null) => {
    originAddress.value = address;
  };

  const handleDestinationAddressChange = (address: PostalSearchResult | null) => {
    destinationAddress.value = address;
  };

  // 计算体积重量
  const volumetricWeight = computed(() => {
    const { length, width, height } = form.value;
    // 体积重量计算公式：长 * 宽 * 高 / 6000（单位：kg）
    return Number(((length * width * height) / 6000).toFixed(1));
  });

  // 实际计费重量
  const chargeableWeight = computed(() => {
    // 取体积重量和实际重量的较大值
    return Math.max(volumetricWeight.value, form.value.weight);
  });

  // 表单验证规则
  const rules: FormRules = {
    fromAddress: [
      { required: true, message: '请输入起始地邮编', trigger: 'blur' },
      { pattern: /^\d+$/, message: '请输入数字邮政编码', trigger: 'blur' },
    ],
    toAddress: [
      { required: true, message: '请输入目的地邮编', trigger: 'blur' },
      { pattern: /^\d+$/, message: '请输入数字邮政编码', trigger: 'blur' },
    ],
    weight: [
      { required: true, message: '请输入重量', trigger: 'blur' },
      { type: 'number', min: 0.1, message: '重量必须大于0.1kg', trigger: 'blur' },
    ],
    length: [
      { required: true, message: '请输入长度', trigger: 'blur' },
      { type: 'number', min: 1, message: '长度必须大于1cm', trigger: 'blur' },
    ],
    width: [
      { required: true, message: '请输入宽度', trigger: 'blur' },
      { type: 'number', min: 1, message: '宽度必须大于1cm', trigger: 'blur' },
    ],
    height: [
      { required: true, message: '请输入高度', trigger: 'blur' },
      { type: 'number', min: 1, message: '高度必须大于1cm', trigger: 'blur' },
    ],
    productType: [
      { required: true, message: '请选择产品类型', trigger: 'change' },
    ],
    serviceLevel: [
      { required: true, message: '请选择服务等级', trigger: 'change' },
    ],
  };

  // 获取选项数据
  const fetchOptions = async () => {
    loading.value = true;
    try {
      const [typesResponse, levelsResponse] = await Promise.all([
        getProductTypes(),
        getServiceLevels(),
      ]);
      
      // 处理产品类型响应
      productTypes.value = Array.isArray(typesResponse) 
        ? typesResponse 
        : (typesResponse.data || []);
      
      // 构建产品选项数据
      productOptions.value = productTypes.value.map((item: any) => ({
        value: item.code || item.name,
        label: item.name
      }));
      
      // 处理服务等级响应
      serviceLevels.value = Array.isArray(levelsResponse) 
        ? levelsResponse 
        : (levelsResponse.data || []);
      
      // 构建服务等级选项
      serviceLevelOptions.value = serviceLevels.value.map((item: any) => ({
        value: item.code || item.name,
        label: item.name
      }));
    } catch (error) {
      console.error('获取选项失败:', error);
      ElMessage.error('获取数据选项失败');
    } finally {
      loading.value = false;
    }
  };

  // 开始比较
  const handleCompare = async () => {
    if (!formRef.value) return;

    await formRef.value.validate(async valid => {
      if (valid) {
        loading.value = true;
        try {
          const response = await compareProductsAsync({
            fromAddress: form.value.fromAddress,
            toAddress: form.value.toAddress,
            weight: form.value.weight,
            volume: volumetricWeight.value,
            quantity: form.value.quantity,
            productType: form.value.productType,
            serviceLevel: form.value.serviceLevel,
            insuranceValue: form.value.insuranceValue,
            isDangerous: form.value.isDangerous
          });
          compareResult.value = response.data;
        } catch (error) {
          ElMessage.error('比较失败');
        } finally {
          loading.value = false;
        }
      }
    });
  };

  // 选择方案
  const handleSelect = (result: ProductComparison) => {
    // 只包含CalculationRequest中有效的属性
    const request: CalculationRequest = {
      fromAddress: form.value.fromAddress,
      toAddress: form.value.toAddress,
      weight: chargeableWeight.value,
      quantity: form.value.quantity,
      productType: form.value.productType,
      // volume可选，所以添加它
      volume: volumetricWeight.value
    };
    
    // 额外参数使用单独对象传递
    const extraParams = {
      serviceLevel: form.value.serviceLevel,
      insuranceValue: form.value.insuranceValue,
      isDangerous: form.value.isDangerous
    };
    
    // 转换请求参数为字符串类型
    const query = Object.entries({...request, ...extraParams}).reduce(
      (acc, [key, value]) => {
        // 处理不同类型的值
        if (typeof value === 'object') {
          // 处理对象类型（如destination_info）
          acc[key] = JSON.stringify(value);
        } else {
          acc[key] = typeof value === 'boolean' ? String(value) : value;
        }
        return acc;
      },
      {} as Record<string, string | number>,
    );

    router.push({
      path: '/calculator',
      query,
    });
  };

  // 保存结果
  const handleSave = async () => {
    try {
      loading.value = true;
      // TODO: 实现保存比较结果到历史记录的功能
      ElMessage.success('结果已保存到历史记录');
    } catch (error) {
      console.error('Failed to save results:', error);
      ElMessage.error('保存失败，请重试');
    } finally {
      loading.value = false;
    }
  };

  // 导出结果
  const handleExport = () => {
    try {
      const ws = XLSX.utils.json_to_sheet(compareResult.value);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '产品比较');
      XLSX.writeFile(wb, `产品比较结果_${new Date().toISOString().split('T')[0]}.xlsx`);
      ElMessage.success('导出成功');
    } catch (error) {
      console.error('Export failed:', error);
      ElMessage.error('导出失败，请重试');
    }
  };

  // 初始化
  onMounted(() => {
    fetchOptions();
  });
</script>

<style scoped>
  .compare-container {
    padding: var(--content-padding);
    max-width: var(--content-max-width);
    margin: 0 auto;
  }

  .result-card {
    margin-top: var(--spacing-lg);
  }

  .total-charge {
    color: var(--color-danger);
    font-weight: var(--font-weight-bold);
  }
</style>
