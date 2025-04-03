<template>
  <div class="calculator-container">
    <el-card class="calculator-card">
      <template #header>
        <div class="card-header">
          <h2>运费计算</h2>
          <div class="header-actions">
            <div v-if="lastUpdatedInfo" class="last-updated">上次更新: {{ lastUpdatedInfo }}</div>
            <el-button size="small" type="primary" @click="refreshCachedData" :loading="isRefreshing">
              <el-icon><Refresh /></el-icon> 刷新数据
            </el-button>
            <el-button type="info" @click="showHistory" icon="Clock">
              计算历史
            </el-button>
            <el-button type="warning" @click="showProductComparison" icon="Sort">
              产品比较
            </el-button>
            <el-button type="primary" @click="handleCalculate" :loading="loading">
              计算运费
            </el-button>
          </div>
        </div>
      </template>

      <!-- 错误提示 -->
      <div v-if="calculationError" class="error-container">
        <el-alert
          :title="calculationError"
          type="error"
          show-icon
          :closable="true"
          @close="calculationError = ''"
          style="margin-bottom: 16px; border-radius: 4px;"
        >
          <template v-if="calculationErrorDetails" #default>
            <div class="error-details">
              <el-button link size="small" @click="showErrorDetails = !showErrorDetails">
                {{ showErrorDetails ? '隐藏详情' : '查看详情' }}
              </el-button>
              <div v-if="showErrorDetails" class="error-details-content">
                <pre>{{ calculationErrorDetails }}</pre>
              </div>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 计算日期选择 -->
      <el-form :label-position="'right'" :label-width="'100px'" class="date-selection-form">
        <el-form-item label="计算日期">
          <el-date-picker
            v-model="calculationDate"
            type="date"
            placeholder="选择计算日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="true"
            :disabled="loading"
            @change="handleCalculationDateChange"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            默认使用当前日期
          </div>
        </el-form-item>
      </el-form>

      <calculator-form
        ref="calculatorFormRef"
        :label-position="'right'"
        :label-width="'100px'"
        :from-label="'起始地邮编'"
        :to-label="'目的地邮编'"
        :from-placeholder="'请输入起始地邮编'"
        :to-placeholder="'请输入目的地邮编'"
        :product-types="productTypesOptions"
        :show-insurance="false"
        :show-dimensions="true"
        :show-dangerous="false"
        :show-services="true"
        @from-address-change="handleOriginAddressChange"
        @to-address-change="handleDestinationAddressChange"
        @weight-change="handleWeightChange"
        @dimension-change="handleDimensionChange"
        @product-selection-mode-change="handleProductSelectionModeChange"
        @compare-products-change="handleCompareProductsChange"
      >
        <!-- 基本信息 -->
        <template #form-header>
          <h3 class="section-title">基本信息</h3>
        </template>

        <!-- 自定义发件地址选择 -->
        <template #from-address>
          <postal-code-input
            :model-value="calculatorFormRef?.form?.fromAddress || ''"
            @update:model-value="(value) => { if (calculatorFormRef?.form) calculatorFormRef.form.fromAddress = value }"
            placeholder="请输入起始地邮编"
            @search="(value) => handleOriginAddressChange(value)"
            @address-change="(result: PostalSearchResult | null) => originAddress = result"
            :required="true"
          />
        </template>

        <!-- 自定义收件地址选择 -->
        <template #to-address>
          <postal-code-input
            :model-value="calculatorFormRef?.form?.toAddress || ''"
            @update:model-value="(value) => { if (calculatorFormRef?.form) calculatorFormRef.form.toAddress = value }"
            placeholder="请输入目的地邮编"
            @search="(value) => handleDestinationAddressChange(value)"
            @address-change="(result: PostalSearchResult | null) => destinationAddress = result"
          />
        </template>

        <!-- 包裹信息 -->
        <template #package-header>
          <h3 class="section-title">包裹信息</h3>
        </template>

        <!-- 体积重量信息 -->
        <template #weight-info>
          <!-- 移除体积重量和计费重量显示 -->
        </template>
        
        <!-- 移除这个位置的计算日期选择 -->
        <template #after-form>
          <!-- 这里之前是日期选择器，现在移到了表单顶部 -->
        </template>
      </calculator-form>
    </el-card>

    <!-- 计算结果 -->
    <el-card v-if="calculatorStore.currentResult" class="result-card">
      <template #header>
        <div class="card-header">
          <h2>计算结果</h2>
          <div class="header-actions">
            <el-button type="primary" @click="createNewCalculation">新建计算</el-button>
            <el-button type="success" @click="handleSaveResult">保存结果</el-button>
          </div>
        </div>
      </template>
      
      <!-- 如果存在计算详情和顶层字段不一致的情况，显示提示 -->
      <div v-if="showResultFixedAlert" class="fixed-result-alert">
        <el-alert
          title="计算结果已自动修正"
          type="info"
          description="系统检测到API返回的基础运费和总费用数据有误，已根据计算详情自动修正显示值。"
          show-icon
          :closable="true"
          @close="showResultFixedAlert = false"
        />
      </div>
      
      <div v-if="showResult" class="result-content">
        <h2 class="result-title">计算结果</h2>
        
        <!-- 产品信息 -->
        <div class="result-section">
          <div class="result-item">
            <h3 class="result-label">产品类型</h3>
            <p class="result-value">{{ getSelectedProductName() || calculatorStore.currentResult?.product_code || '-' }}</p>
          </div>
          <div class="result-item">
            <h3 class="result-label">区域</h3>
            <p class="result-value">{{ calculatorStore.currentResult?.zone || '-' }}</p>
          </div>
        </div>

        <!-- 计算日期信息 -->
        <div class="result-section">
          <div class="result-item">
            <h3 class="result-label">计算日期</h3>
            <p class="result-value">{{ calculationDateDisplay }}</p>
          </div>
          <div class="result-item">
            <h3 class="result-label">计算时间</h3>
            <p class="result-value">{{ calculatorStore.currentResult?.calculationTime || '-' }}</p>
          </div>
        </div>

        <!-- 费用信息 -->
        <div class="result-section">
          <div class="result-item">
            <h3 class="result-label">基础运费</h3>
            <p class="result-value">{{ formatCurrency(getBaseCharge()) }}</p>
          </div>
          <div class="result-item">
            <h3 class="result-label">燃油附加费</h3>
            <p class="result-value">{{ formatCurrency(calculatorStore.currentResult?.fuelSurcharge || 0) }} <span class="rate-info" v-if="calculatorStore.currentResult?.fuelRate">比率: {{ calculatorStore.currentResult?.fuelRate }}%</span></p>
          </div>
        </div>

        <!-- 总运费显示区域 -->
        <div class="result-section total-section">
          <h3 class="result-label">总运费</h3>
          <p class="result-value total-value">{{ formatCurrency(getTotalCharge()) }}</p>
        </div>

        <!-- 调试信息 -->
        <div class="debug-section">
          <el-button type="info" size="small" @click="showRawApiResponse = true">显示原始API响应</el-button>
          <el-button type="primary" size="small" @click="showCalculationDetails = true">查看计算详情</el-button>
        </div>

        <!-- 原始API响应 -->
        <el-dialog
          v-model="showRawApiResponse"
          title="原始API响应"
          width="80%"
        >
          <div class="api-response-content">
            <pre>{{ JSON.stringify(calculatorStore.currentResult?.rawResponse || {}, null, 2) }}</pre>
          </div>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="showRawApiResponse = false">关闭</el-button>
              <el-button type="primary" @click="copyRawResponse">复制响应</el-button>
            </span>
          </template>
        </el-dialog>

        <!-- 计算详情 -->
        <el-dialog
          v-model="showCalculationDetails"
          title="计算详情"
          width="80%"
        >
          <div v-if="calculatorStore.currentResult?.calculationDetails?.length">
            <el-card v-for="(detail, index) in calculatorStore.currentResult.calculationDetails" :key="index" class="mb-10">
              <template #header>
                <div class="calculation-detail-header">
                  <span>{{ detail.fee_name || detail.name || '费用' }}</span>
                  <span class="amount">{{ formatCurrency(detail.amount || 0) }}</span>
                </div>
              </template>
              <div class="calculation-detail-body">
                <p><strong>类型:</strong> {{ detail.fee_type || detail.type || '-' }}</p>
                <p><strong>描述:</strong> {{ detail.description || '-' }}</p>
                <p><strong>条件:</strong> {{ detail.condition || '-' }}</p>
                <p v-if="detail.weight_used"><strong>使用:</strong> {{ detail.weight_used }} {{ detail.unit || 'KG' }}</p>
                <p v-if="detail.unit_price"><strong>单价:</strong> {{ detail.unit_price }}</p>
                <p v-if="detail.rate"><strong>比率:</strong> {{ detail.rate }}</p>
              </div>
            </el-card>
          </div>
          <div v-else class="empty-details">
            <el-empty description="没有计算详情"></el-empty>
          </div>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="showCalculationDetails = false">关闭</el-button>
            </span>
          </template>
        </el-dialog>

        <!-- 附加费用 -->
        <div class="surcharges-section">
          <h3 class="section-subtitle">附加费用</h3>
          <div class="table-container">
            <table class="surcharges-table">
              <thead>
                <tr>
                  <th>类型</th>
                  <th>名称</th>
                  <th>金额</th>
                  <th>条件</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(surcharge, index) in processedAdditionalCharges || []" :key="index" 
                    :class="Number((surcharge as any)?.amount || 0) > 0 ? 'active-surcharge' : 'inactive-surcharge'">
                  <td>{{ (surcharge as any)?.type }}</td>
                  <td>{{ (surcharge as any)?.name }}</td>
                  <td class="amount-cell">{{ formatCurrency(Number((surcharge as any)?.amount || 0)) }}</td>
                  <td class="condition-cell">{{ (surcharge as any)?.condition }}</td>
                  <td class="status-cell">
                    <span v-if="Number((surcharge as any)?.amount || 0) > 0" class="status-badge status-active">
                      已应用
                    </span>
                    <span v-else class="status-badge status-inactive">
                      未应用
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 单位转换信息 -->
        <div class="unit-conversion-info">
          <h3>单位转换</h3>
          <el-table :data="[unitConversionData]" border size="small">
            <el-table-column label="目标">
              <template #default>基本信息</template>
            </el-table-column>
            <el-table-column label="原始尺寸">
              <template #default="scope">
                {{ scope.row.originalDimension }}
              </template>
            </el-table-column>
            <el-table-column :label="`转换后${productUnitDisplay}`">
              <template #default="scope">
                {{ scope.row.convertedDimension }}
              </template>
            </el-table-column>
            <el-table-column label="长+周长">
              <template #default="scope">
                {{ scope.row.lengthGirth }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-table :data="[unitConversionData]" border size="small" class="mt-10">
            <el-table-column label="目标">
              <template #default>尺寸</template>
            </el-table-column>
            <el-table-column label="原始重量">
              <template #default="scope">
                {{ scope.row.originalWeight }}
              </template>
            </el-table-column>
            <el-table-column :label="`转换后${productWeightUnitDisplay}`">
              <template #default="scope">
                {{ scope.row.convertedWeight }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-table :data="[unitConversionData]" border size="small" class="mt-10">
            <el-table-column label="目标">
              <template #default>产品</template>
            </el-table-column>
            <el-table-column label="实际重量">
              <template #default="scope">
                {{ scope.row.convertedWeight }}
              </template>
            </el-table-column>
            <el-table-column label="体积重量">
              <template #default="scope">
                {{ scope.row.volumetricWeight }}
              </template>
            </el-table-column>
            <el-table-column label="产品重量(取值)">
              <template #default="scope">
                {{ scope.row.chargeableWeight }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- 产品比较 -->
    <el-card v-if="compareResult.length > 0" class="compare-result-card">
      <template #header>
        <div class="card-header">
          <h2>产品比较</h2>
          <div class="header-actions">
            <el-button type="primary" @click="handleSaveCompareResult">保存比较结果</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="compareResult" border stripe class="compare-table">
        <el-table-column prop="productType" label="产品类型" min-width="120"/>
        <el-table-column prop="baseCharge" label="基础运费" min-width="100">
          <template #default="scope">{{ formatCurrency(scope.row.baseCharge) }}</template>
        </el-table-column>
        <el-table-column prop="fuelSurcharge" label="燃油附加费" min-width="100">
          <template #default="scope">{{ formatCurrency(scope.row.fuelSurcharge) }}</template>
        </el-table-column>
        <el-table-column prop="totalCharge" label="总运费" min-width="100">
          <template #default="scope">{{ formatCurrency(scope.row.totalCharge) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button 
              type="primary" 
              link
              @click="() => {
                ElMessage.success(`选择产品: ${scope.row.productType}`);
              }"
            >
              <el-icon><Check /></el-icon> 选择产品
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 未授权警告 -->
    <div v-if="hasUnauthorizedConditionMet" class="unauthorized-warning">
      <el-alert
        title="警告：未授权包裹"
        type="error"
        description="未授权包裹尺寸超过了运输规定的范围，请检查。"
        show-icon
        :closable="false"
      />
    </div>
    
    <!-- 结果容器 -->
    <div v-if="calculatorStore.currentResult" class="result-container">
      <!-- ... existing code ... -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive, watch, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter, useRoute } from 'vue-router';
import { CalculatorForm } from '@/components/calculator';
import { useCalculatorStore } from '@/stores/calculator';
import type { PostalCode, PostalSearchResult } from '@/types/postal';
import type { CalculationRequest, CalculationResult, ComparisonResult, Currency } from '@/types/calculator';
import { getProductTypes, saveCalculationResult, compareProductsAsync, calculateFreight } from '@/api/calculator/index';
import { getProducts } from '@/api/products';
import { PostalCodeInput } from '@/components/postal';
import { getPostalCodes, getAddressByPostalCode } from '@/api/postal/postal';
import type { Ref } from 'vue';
import { Sort, Clock, Refresh, Check, Loading, InfoFilled } from '@element-plus/icons-vue';
import { formatDateTime, formatCurrency, DATE_FORMAT_CONSTANTS, VOLUMETRIC_CONSTANTS, DIMENSION_UNIT_DISPLAY, WEIGHT_UNIT_DISPLAY, DEFAULT_FUEL_RATE } from '@/utils/format';
import axios from 'axios';
import { TOKEN_KEY } from '@/types/auth';

const calculatorStore = useCalculatorStore();

// API常量
const API_CONSTANTS = {
  INCLUDE_ALL_SURCHARGES: true,
  RETURN_CALCULATION_DETAILS: true,
  VERBOSE_RESPONSE: true,
  DEFAULT_PRODUCT_CODE: '',
  DEFAULT_QUANTITY: 1
};

// 计算接口URL
const API_URL = reactive({
  GET_SURCHARGES: '/api/v1/products/surcharges/by_product/',  // 末尾斜杠
  GET_PEAK_SEASON_SURCHARGES: '/api/v1/products/peak-season-surcharges/by_product/'  // 末尾斜杠
});

// 缓存的附加费类型
const cachedSurchargeTypes = ref<any[]>([]);
// 缓存的峰值附加费类型
const cachedPeakSeasonTypes = ref<{ type: string; name: string; condition: string }[]>([]);

// 上次更新信息
const lastUpdatedInfo = ref<string>('未更新');

// 从API获取附加费类型列表
const fetchSurchargeTypes = async () => {
  try {
    // 如果已经缓存了数据，直接返回
    if (cachedSurchargeTypes.value && cachedSurchargeTypes.value.length > 0) {
      console.log('使用缓存的附加费类型');
      return cachedSurchargeTypes.value;
    }
    
    // 获取产品ID
    const productId = calculatorFormRef.value?.form?.productType || 
                     (productTypesOptions.value.length > 0 ? productTypesOptions.value[0].code : '');
    
    // 如果没有产品ID，使用模拟数据
    if (!productId) {
      console.log('无法获取产品ID，使用模拟附加费数据');
      cachedSurchargeTypes.value = getMockSurcharges();
      return cachedSurchargeTypes.value;
    }
    
    // 准备请求头
    const token = localStorage.getItem('token') || localStorage.getItem('access_token') || localStorage.getItem(TOKEN_KEY);
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    console.log('正在获取附加费数据，产品ID:', productId);
    
    // 发送请求获取附加费数据
    try {
      const response = await axios({
        method: 'get',
        url: `${API_URL.GET_SURCHARGES}?product_id=${productId}`,
        headers
      });
      
      // 处理响应数据
      let surchargesData: any[] = [];
      
      if (Array.isArray(response.data)) {
        surchargesData = response.data;
      } else if (response.data && response.data.surcharges && Array.isArray(response.data.surcharges)) {
        surchargesData = response.data.surcharges;
      } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
        surchargesData = response.data.results;
      }
      
      console.log('附加费数据条目数:', surchargesData.length);
      
      // 处理并缓存数据
      if (surchargesData && surchargesData.length > 0) {
        cachedSurchargeTypes.value = surchargesData.map(item => ({
          type: item.surcharge_type || item.type || '未知类型',
          name: item.surcharge_name || item.name || '未命名附加费',
          condition: item.condition_desc || item.condition || '无条件说明'
        }));
        
        // 更新缓存时间
        lastUpdatedInfo.value = new Date().toLocaleString();
      } else {
        console.log('API返回的附加费数据为空，使用模拟数据');
        cachedSurchargeTypes.value = getMockSurcharges();
      }
    } catch (apiError) {
      console.error('API请求失败:', apiError);
      cachedSurchargeTypes.value = getMockSurcharges();
    }
    
    return cachedSurchargeTypes.value;
  } catch (error) {
    console.error('获取附加费异常:', error);
    cachedSurchargeTypes.value = getMockSurcharges();
    return cachedSurchargeTypes.value;
  }
};

// 获取模拟附加费数据
const getMockSurcharges = () => {
  return [
    { type: '', name: '', condition: '' },
    { type: '', name: '', condition: '' },
    { type: '', name: '', condition: '' },
    { type: '', name: '', condition: '' }
  ];
};

// 附加费条目接口
interface SurchargeItem {
  surcharge_id?: number;
  product?: string;
  surcharge_type?: string;
  type?: string;
  sub_type?: string;
  name?: string;
  surcharge_name?: string;
  condition_desc?: string;
  condition_description?: string;
  condition?: string;
  display_order?: number;
  zone2?: number;
  zone3?: number;
  zone4?: number;
  zone5?: number;
  zone6?: number;
  zone7?: number;
  zone8?: number;
  [key: string]: any;
}

// 切换计算详情显示
const toggleCalculationDetails = () => {
  showCalculationDetails.value = !showCalculationDetails.value;
};

// 显示计算过程控制
const showCalculationProcess = ref<boolean>(false);

// 切换计算过程显示
const toggleCalculationProcess = () => {
  showCalculationProcess.value = !showCalculationProcess.value;
};

// 
const calculationProcessDetails = computed(() => {
  // 无计算结果时的默认显示
  if (!calculatorStore.currentResult) {
    return [{
      step: '没有计算',
      description: '未执行计算',
      details: '请先进行计算'
    }];
  }

  // 基本信息
  const basicInfo = {
    step: '基本信息',
    description: '计算的基本信息',
    details: `
    产品ID: ${calculatorStore.currentResult.product_code || 'N/A'}
    区域: ${calculatorStore.currentResult.zone || 'N/A'}
    时间: ${new Date().toLocaleString()}
    `
  };

  const feeCalculation = {
    step: '费用计算',
    description: '费用计算详情',
    details: `
    基础运费: ${calculatorStore.currentResult.baseCharge} ${calculatorStore.currentResult.currency || 'USD'}
    燃油附加费: ${calculatorStore.currentResult.fuelSurcharge} ${calculatorStore.currentResult.currency || 'USD'}
    其他附加费: 0 ${calculatorStore.currentResult.currency || 'USD'}
    总费用: ${calculatorStore.currentResult.totalCharge} ${calculatorStore.currentResult.currency || 'USD'}
    
    计算公式: 基础运费 ${calculatorStore.currentResult.baseCharge} +
           燃油附加费 ${calculatorStore.currentResult.fuelSurcharge} =
           总费用 ${calculatorStore.currentResult.totalCharge}
    `
  };

  // 检查是否有计算详情
  if (calculatorStore.currentResult.calculationDetails && 
      Array.isArray(calculatorStore.currentResult.calculationDetails) && 
      calculatorStore.currentResult.calculationDetails.length > 0) {
    // 有计算详情
    console.log('使用后端返回的计算详情');
    // 如果有计算详情数据，使用后端返回的数据
    console.log('使用后端返回的计算详情数据');
    return calculatorStore.currentResult.calculationDetails.map(item => {
      // 可能需要对数据进行直接修改原始数据
      const processedItem = { ...item };
      
      // 详情格式是否需要格式化
      if (processedItem.details && typeof processedItem.details === 'string') {
        // 移除每行开头的空格和多余换行
        processedItem.details = processedItem.details.replace(/^\s+/gm, '').replace(/\n{3,}/g, '\n\n');
      }
      return processedItem;
    });
  }

  // 如果没有后端返回的计算详情数据，使用前端构造的基础数据
  console.log('使用前端构造的计算详情');
  return [basicInfo, feeCalculation];
});

// ӷѵܺ
const getOtherSurchargesTotal = () => {
  if (!calculatorStore.currentResult) return 0;
  
  let total = 0;
  // additionalCharges㸽ӷܺ
  if (calculatorStore.currentResult.details?.additionalCharges) {
    total = calculatorStore.currentResult.details.additionalCharges.reduce(
      (sum, charge) => sum + Number(charge.amount || 0), 0
    );
  }
  
  // ܵԴ㸽ӷ
  const allSurcharges = calculatorStore.currentResult.allSurcharges || [];
  if (allSurcharges.length > 0) {
    // ųȼ͸ӷѣֻӷ
    const otherSurcharges = allSurcharges.filter((s: any) => {
      // ֶΣtypesurcharge_type
      const sType = (s.type || '').toLowerCase();
      const surchargeType = (s.surcharge_type || '').toLowerCase();
      
      // ųȼ͸ӷ
      return sType !== 'ȼ͸ӷ' && 
             sType !== 'fuel' && 
             surchargeType !== 'ȼ͸ӷ' && 
             surchargeType !== 'fuel';
    });
    
    // ܽѾЩӷѣظ
    if (otherSurcharges.length > 0 && total === 0) {
      total = otherSurcharges.reduce(
        (sum: number, charge: any) => sum + Number(charge.amount || 0), 0
      );
    }
  }
  
  return total;
};

// 获取基础运费（优先从计算详情中获取）
const getBaseCharge = () => {
  if (!calculatorStore.currentResult) return 0;
  
  // 如果baseCharge已经大于0，直接返回
  if (Number(calculatorStore.currentResult.baseCharge) > 0) {
    return Number(calculatorStore.currentResult.baseCharge);
  }
  
  // 尝试从计算详情中获取基础运费
  if (calculatorStore.currentResult.calculationDetails && 
      calculatorStore.currentResult.calculationDetails.length > 0) {
    // 查找基础运费相关的详情项
    const baseChargeFee = calculatorStore.currentResult.calculationDetails.find(
      detail => (detail.fee_type === 'BASE' || 
                detail.type === 'BASE' || 
                detail.step === '基础运费计算' ||
                detail.fee_name === '基础运费')
    );
    if (baseChargeFee && (baseChargeFee.amount || baseChargeFee.value)) {
      return Number(baseChargeFee.amount || baseChargeFee.value || 0);
    }
  }
  
  // 如果计算详情中没有找到，尝试从details中获取
  if (calculatorStore.currentResult.details && 
      calculatorStore.currentResult.details.weightCharge > 0) {
    return calculatorStore.currentResult.details.weightCharge;
  }
  
  // 最后返回原始值
  return Number(calculatorStore.currentResult.baseCharge || 0);
};

// 获取总费用（优先计算各项费用之和）
const getTotalCharge = () => {
  if (!calculatorStore.currentResult) return 0;
  
  // 如果totalCharge已经大于0，直接返回
  if (Number(calculatorStore.currentResult.totalCharge) > 0) {
    return Number(calculatorStore.currentResult.totalCharge);
  }
  
  // 如果totalCharge为0，手动计算各项费用之和
  const baseCharge = getBaseCharge();
  const fuelSurcharge = Number(calculatorStore.currentResult.fuelSurcharge || 0);
  const otherSurcharges = getOtherSurchargesTotal();
  
  const total = baseCharge + fuelSurcharge + otherSurcharges;
  return total > 0 ? total : Number(calculatorStore.currentResult.totalCharge || 0);
};

// scriptǩʼӽӿڶ
interface RawSurcharge {
  surcharge_id?: number;
  product?: string;
  surcharge_type?: string;
  type?: string;
  sub_type?: string;
  name?: string;
  surcharge_name?: string;
  condition_desc?: string;
  condition_description?: string;
  condition?: string;
  display_order?: number;
  zone2?: number;
  Zone2?: number;
  zone3?: number;
  Zone3?: number;
  zone4?: number;
  Zone4?: number;
  zone5?: number;
  Zone5?: number;
  zone6?: number;
  Zone6?: number;
  zone7?: number;
  Zone7?: number;
  zone8?: number;
  Zone8?: number;
  [key: string]: any;
}

// ޸fetchAllPossibleSurcharges
const fetchAllPossibleSurcharges = async (productId: string) => {
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token') || localStorage.getItem(TOKEN_KEY);
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // 获取所有可能的附加费
    const response = await axios({
      method: 'get',
      url: `${API_URL.GET_SURCHARGES}?product_id=${productId}&include_all=true`,
      headers: headers
    });

    console.log('获取潜在的附加费响应:', response.data);

    if (response.data) {
      let surcharges: RawSurcharge[] = [];
      if (Array.isArray(response.data)) {
        surcharges = response.data;
      } else if (response.data.results && Array.isArray(response.data.results)) {
        surcharges = response.data.results;
      } else if (response.data.surcharges && Array.isArray(response.data.surcharges)) {
        surcharges = response.data.surcharges;
      }

      // 处理每个附加费，确保包含所有必要的字段
      const processedSurcharges = surcharges.map((surcharge: RawSurcharge) => ({
        surcharge_id: surcharge.surcharge_id,
        product: surcharge.product,
        surcharge_type: surcharge.surcharge_type || surcharge.type,
        type: surcharge.type || surcharge.surcharge_type,
        sub_type: surcharge.sub_type,
        name: surcharge.name || surcharge.surcharge_name,
        surcharge_name: surcharge.surcharge_name || surcharge.name,
        condition_desc: surcharge.condition_desc || surcharge.condition,
        condition: surcharge.condition || surcharge.condition_desc,
        display_order: surcharge.display_order || 0,
        zone2: surcharge.zone2 || surcharge.Zone2 || 0,
        zone3: surcharge.zone3 || surcharge.Zone3 || 0,
        zone4: surcharge.zone4 || surcharge.Zone4 || 0,
        zone5: surcharge.zone5 || surcharge.Zone5 || 0,
        zone6: surcharge.zone6 || surcharge.Zone6 || 0,
        zone7: surcharge.zone7 || surcharge.Zone7 || 0,
        zone8: surcharge.zone8 || surcharge.Zone8 || 0
      }));

      console.log('处理后的附加费类型:', processedSurcharges.length);
      return processedSurcharges;
    }
    return [];
  } catch (error) {
    console.error('获取所有可能的附加费失败:', error);
    return [];
  }
};

// scriptǩʼӻ޸Ľӿڶ
interface ChargeItem {
  type: string;
  name: string;
  amount: number;
  condition: string;
  condition_met: boolean;
  reason: string;
}

interface PeakSeasonSurcharge {
  type?: string;
  surcharge_type?: string;
  name?: string;
  surcharge_name?: string;
  condition?: string;
  condition_description?: string;
  condition_desc?: string;
  start_date?: string;
  end_date?: string;
  amount?: number;
  fee_amount?: number;
}

// ޸Ļӽӿڶ
interface AppliedSurcharge {
  type: string;
  name: string;
  amount: number;
  surcharge_type?: string;
  condition?: string;
  condition_description?: string;
  condition_met?: boolean;
  reason?: string;
}

// ޸appliedSurcharges
const appliedSurcharges = (calculatorStore.currentResult?.allSurcharges || []) as AppliedSurcharge[];

// 产品比较结果
const compareResult = ref<ComparisonResult[]>([]);

// 未授权包裹标志
const hasUnauthorizedConditionMet = ref(false);

// 保存比较结果
const handleSaveCompareResult = () => {
  if (compareResult.value.length === 0) {
    ElMessage.warning('没有比较结果可保存');
    return;
  }
  
  // 这里可以添加保存比较结果的逻辑
  ElMessage.success('比较结果已保存');
};

// Թ
const showRawApiResponse = ref(false);
const showCalculationDetails = ref(false);

// ԭʼӦ
const copyRawResponse = () => {
  const responseText = JSON.stringify(calculatorStore.currentResult?.rawResponse || {}, null, 2);
  try {
    navigator.clipboard.writeText(responseText).then(() => {
      ElMessage.success('已复制到剪贴板');
    });
  } catch (error) {
    console.error('复制失败:', error);
    ElMessage.error('复制失败，请手动复制');
  }
};

// 显示修正提示
const showResultFixedAlert = ref(false);

// 显示计算结果
const showResult = ref(false);

// 计算日期显示
const calculationDate = ref<string>(new Date().toISOString().split('T')[0]);

// 计算日期显示格式化
const calculationDateDisplay = computed(() => {
  return calculationDate.value ? formatDateTime(calculationDate.value, DATE_FORMAT_CONSTANTS.DATE_ONLY) : '今天';
});

// 获取选中产品名称
const getSelectedProductName = () => {
  const selectedProductId = calculatorFormRef.value?.form?.productType || '';
  const selectedProduct = productTypesOptions.value.find(p => p.code === selectedProductId);
  return selectedProduct ? selectedProduct.name : '';
};

// 计算器表单引用
const calculatorFormRef = ref<InstanceType<typeof CalculatorForm> | null>(null);

// 产品类型选项
const productTypesOptions = ref<{ 
  code: string; 
  name: string; 
  description?: string;
  dim_unit?: string;
  weight_unit?: string;
  dim_factor?: string | number;
}[]>([]);

// 处理后的附加费
const processedAdditionalCharges = computed(() => {
  return calculatorStore.currentResult?.details?.additionalCharges || [];
});

// 单位转换数据
const unitConversionData = computed(() => {
  // 获取表单输入的尺寸和重量
  const length = calculatorFormRef.value?.form?.length || 0;
  const width = calculatorFormRef.value?.form?.width || 0;
  const height = calculatorFormRef.value?.form?.height || 0;
  const weight = calculatorFormRef.value?.form?.weight || 0;
  const dimensionUnit = calculatorFormRef.value?.form?.dimensionUnit || '';
  const weightUnit = calculatorFormRef.value?.form?.weightUnit || '';
  
  // 直接返回原始数据,不做任何转换
  return {
    originalDimension: `${length}x${width}x${height} ${dimensionUnit.toLowerCase()}`,
    convertedDimension: '-', // 由后端计算
    lengthGirth: '-', // 由后端计算
    originalWeight: `${weight} ${weightUnit.toLowerCase()}`,
    convertedWeight: '-', // 由后端计算
    volumetricWeight: '-', // 由后端计算
    chargeableWeight: '-' // 由后端计算
  };
});

// 产品单位显示
const productUnitDisplay = computed(() => {
  return DIMENSION_UNIT_DISPLAY.IN;
});

// 产品重量单位显示
const productWeightUnitDisplay = computed(() => {
  return WEIGHT_UNIT_DISPLAY.LB;
});

// 是否在刷新中
const isRefreshing = ref(false);

// 是否在加载中
const loading = ref(false);

// 刷新缓存数据
const refreshCachedData = async () => {
  isRefreshing.value = true;
  try {
    cachedSurchargeTypes.value = [];
    await fetchSurchargeTypes();
    ElMessage.success('数据已刷新');
  } catch (error) {
    ElMessage.error('刷新数据失败');
  } finally {
    isRefreshing.value = false;
  }
};

// 计算错误信息
const calculationError = ref('');
const calculationErrorDetails = ref('');
const showErrorDetails = ref(false);

// 创建新计算
const createNewCalculation = () => {
  calculatorStore.currentResult = null;
  showResult.value = false;
  calculationError.value = '';
  calculationErrorDetails.value = '';
  showErrorDetails.value = false;
};

// 显示历史记录
const showHistory = () => {
  ElMessage.info('历史记录功能待实现');
};

// 显示产品比较
const showProductComparison = () => {
  ElMessage.info('产品比较功能待实现');
};

// 处理计算
const handleCalculate = async () => {
  try {
    loading.value = true;
    calculationError.value = '';
    calculationErrorDetails.value = '';
    
    // 验证表单
    if (!calculatorFormRef.value) {
      ElMessage.error('表单组件未初始化');
      loading.value = false;
      return;
    }
    
    try {
      // 验证表单数据
      await calculatorFormRef.value.validate();
    } catch (validationError) {
      console.error('表单验证失败:', validationError);
      ElMessage.error('请检查表单数据是否正确填写');
      loading.value = false;
      return;
    }
    
    // 准备请求数据
    const requestData = {
      from_postal: calculatorFormRef.value.form.fromAddress,
      to_postal: calculatorFormRef.value.form.toAddress,
      weight: calculatorFormRef.value.form.weight,
      weightUnit: calculatorFormRef.value.form.weightUnit,
      length: calculatorFormRef.value.form.length,
      width: calculatorFormRef.value.form.width,
      height: calculatorFormRef.value.form.height,
      dimensionUnit: calculatorFormRef.value.form.dimensionUnit,
      productType: calculatorFormRef.value.form.productType,
      isResidential: calculatorFormRef.value.form.isResidential,
      calculationDate: calculationDate.value
    };
    
    console.log('计算请求数据:', requestData);
    
    // 调用后端API进行计算
    const result = await calculateFreight(requestData);
    console.log('计算结果:', result);
    
    // 存储计算结果
    calculatorStore.currentResult = result;
    showResult.value = true;
    
    // 检查是否需要显示计算过程
    if (result.calculationDetails && result.calculationDetails.length > 0) {
      showCalculationProcess.value = true;
    }
    
    // 计算完成
    loading.value = false;
    ElMessage.success('计算完成');
  } catch (error: any) {
    loading.value = false;
    console.error('计算出错:', error);
    
    // 处理错误信息
    if (error.response) {
      calculationError.value = `计算失败: 服务器返回错误 (${error.response.status})`;
      try {
        if (typeof error.response.data === 'object') {
          calculationErrorDetails.value = JSON.stringify(error.response.data, null, 2);
        } else {
          calculationErrorDetails.value = error.response.data;
        }
      } catch (e) {
        calculationErrorDetails.value = '无法解析错误详情';
      }
    } else if (error.message) {
      calculationError.value = `计算失败: ${error.message}`;
    } else {
      calculationError.value = '计算失败，请稍后重试';
    }
  }
};

// 保存结果
const handleSaveResult = () => {
  ElMessage.info('保存结果功能待实现');
};

// 处理计算日期变更
const handleCalculationDateChange = () => {
  console.log('计算日期变更为:', calculationDate.value);
};

// 地址信息
const originAddress = ref<PostalSearchResult | null>(null);
const destinationAddress = ref<PostalSearchResult | null>(null);

// 处理起始地址变更
const handleOriginAddressChange = (code: string) => {
  console.log('起始地址变更为:', code);
};

// 处理目的地址变更
const handleDestinationAddressChange = (code: string) => {
  console.log('目的地址变更为:', code);
};

// 处理重量变更
const handleWeightChange = (value: { weight: number; unit: string }) => {
  console.log('重量变更为:', value.weight, value.unit);
};

// 处理尺寸变更
const handleDimensionChange = (dimensions: {length: number; width: number; height: number}) => {
  console.log('尺寸变更为:', dimensions);
};

// 处理产品选择模式变更
const handleProductSelectionModeChange = (mode: string) => {
  console.log('产品选择模式变更为:', mode);
};

// 处理比较产品变更
const handleCompareProductsChange = (products: string[]) => {
  console.log('比较产品变更为:', products);
};

// 生命周期钩子
onMounted(async () => {
  try {
    // 加载产品类型
    console.log('开始获取产品类型...');
    const productsResponse = await getProductTypes();
    console.log('产品类型API响应:', productsResponse);
    
    // 检查API返回的数据格式并适当处理
    if (productsResponse && Array.isArray(productsResponse)) {
      productTypesOptions.value = productsResponse.map(p => {
        // 处理不同的数据格式
        return {
          code: p.product_id || p.id || p.code || '',
          name: p.product_name || p.name || '',
          description: p.description || p.provider_name || '',
          dim_unit: p.dim_unit || '',
          weight_unit: p.weight_unit || '',
          dim_factor: p.dim_factor || ''
        };
      });
      console.log('处理后的产品类型选项:', productTypesOptions.value);
    } else {
      // 手动添加一些测试数据，以便页面能正常显示
      console.log('API未返回有效的产品类型数据，使用测试数据');
      productTypesOptions.value = [
        { code: 'FEDEX_GROUND', name: 'FedEx 地面服务', description: '经济型地面配送服务', dim_unit: 'CM', weight_unit: 'KG', dim_factor: 1 },
        { code: 'FEDEX_EXPRESS', name: 'FedEx 快递', description: '快速空运服务', dim_unit: 'CM', weight_unit: 'KG', dim_factor: 1 },
        { code: 'UPS_GROUND', name: 'UPS 地面服务', description: '可靠的地面配送', dim_unit: 'CM', weight_unit: 'KG', dim_factor: 1 }
      ];
    }
    
    // 如果成功获取数据，设置默认产品类型
    if (productTypesOptions.value.length > 0 && calculatorFormRef.value) {
      const defaultProductCode = productTypesOptions.value[0].code;
      console.log('设置默认产品类型:', defaultProductCode);
      calculatorFormRef.value.form.productType = defaultProductCode;
    }
    
    // 加载附加费类型
    await fetchSurchargeTypes();
    
    console.log('组件已挂载，初始化完成');
  } catch (error) {
    console.error('初始化数据失败:', error);
    ElMessage.error('初始化数据失败，请刷新页面重试');
    
    // 出错时也添加一些测试数据
    productTypesOptions.value = [
      { code: 'FEDEX_GROUND', name: 'FedEx 地面服务', description: '经济型地面配送服务', dim_unit: 'CM', weight_unit: 'KG', dim_factor: 1 },
      { code: 'FEDEX_EXPRESS', name: 'FedEx 快递', description: '快速空运服务', dim_unit: 'CM', weight_unit: 'KG', dim_factor: 1 },
      { code: 'UPS_GROUND', name: 'UPS 地面服务', description: '可靠的地面配送', dim_unit: 'CM', weight_unit: 'KG', dim_factor: 1 }
    ];
    
    // 设置默认产品类型
    if (productTypesOptions.value.length > 0 && calculatorFormRef.value) {
      calculatorFormRef.value.form.productType = productTypesOptions.value[0].code;
    }
  }
});

</script>

<style>
  .calculator-container {
    width: 100%;
    margin: 0 auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  /* 计算结果样式 */
  .calculation-details-container {
    margin-top: 20px;
  }

  /* 计算详情结果水平布局 */
  .calculation-detail-steps {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  /* 确保每个计算步骤显示 */
  .calculation-step-card {
    flex: 1 1 300px;
    max-width: 100%;
    margin-bottom: 15px;
  }

  /* 为了保持计算结果宽度不会过宽难看 */
  .calculation-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  /* 计算结果标题样式设置 */
  .calculation-detail-header .amount {
    font-weight: bold;
    color: #409EFF;
  }

  /* 计算详情结果内容设计 */
  .calculation-detail-body {
    font-size: 14px;
    padding: 10px 0;
  }

  /* 计算详情内容附加样式 */
  .calculation-detail-body p {
    margin: 5px 0;
    line-height: 1.5;
  }

  /* 附件信息附加样式 */
  .empty-details {
    padding: 20px;
    text-align: center;
  }

  /* 单位转换信息表格附加样式 */
  .unit-conversion-info {
    margin-top: 15px;
  }

  /* 表格样式统一 */
  .mt-10 {
    margin-top: 10px;
  }

  /* 结果详情内容文本颜色 */
  .unit-conversion-info .el-table {
    font-size: 12px;
  }

  /* 单位显示字段样式 */
  .unit-suffix {
    color: #909399;
    font-size: 0.9em;
    margin-left: 3px;
  }

  /* 表格样式 */
  .surcharges-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
  }
  
  /* 调试区域样式 */
  .debug-section {
    margin-top: 10px;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
  
  .api-response-content {
    max-height: 60vh;
    overflow-y: auto;
    background-color: #f8f8f8;
    padding: 15px;
    border-radius: 4px;
    font-family: monospace;
  }
  
  .api-response-content pre {
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* 隐藏字段 */
  .calculator-container :deep([label="属性值"]),
  .calculator-container :deep([label="关税"]) {
    display: none !important;
  }

  /* 产品选择样式 */
  .product-option {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }

  .product-option-info {
    margin-left: 8px;
    flex-grow: 1;
  }

  .product-option-details {
    display: flex;
    flex-direction: column;
    font-size: 12px;
    color: #999;
  }

  .product-option-label {
    font-weight: bold;
  }

  .product-option-meta {
    display: flex;
    gap: 8px;
    margin-top: 4px;
  }

  .product-option-meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  /* 加载中显示样式 */
  .el-select-dropdown__loading {
    padding: 10px;
    text-align: center;
    color: #909399;
  }

  /* 卡片样式 */
  .result-card {
    background-color: #fff;
    border-radius: 6px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    margin-bottom: 0;
  }

  .result-card :deep(.el-card__body) {
    padding: 0 !important;
  }

  .result-card :deep(.el-card__header) {
    padding: 15px 20px;
    border-bottom: 1px solid #ebeef5;
    position: sticky;
    top: 0;
    background-color: white;
    z-index: 10;
  }

  .calculator-card,
  .compare-result-card {
    background-color: #fff;
    border-radius: 6px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    margin-bottom: 0;
  }

  .calculator-card :deep(.el-card__body) {
    padding: 20px;
  }

  .calculator-form :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .card-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }

  .section-title {
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    border-bottom: 1px solid #ebeef5;
  }

  .product-selection-container {
    background-color: #f8f9fa;
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 10px;
  }

  .selection-mode {
    margin-bottom: 16px !important;
  }

  .product-select {
    margin-bottom: 0 !important;
  }

  /* 计算结果样式 */
  .result-content {
    padding: 20px;
    width: 100%;
    box-sizing: border-box;
  }

  .result-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
    color: #303133;
  }

  .result-section {
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 20px;
    gap: 20px;
  }

  .result-item {
    flex: 1;
    min-width: 200px;
  }

  .result-label {
    font-size: 14px;
    font-weight: 500;
    color: #606266;
    margin-bottom: 5px;
  }

  .result-value {
    font-size: 16px;
    color: #303133;
  }

  .total-section {
    border-top: 1px solid #ebeef5;
    padding-top: 15px;
  }

  .total-section .result-label {
    font-size: 16px;
    color: #303133;
  }

  .total-value {
    font-size: 20px;
    font-weight: 600;
    color: #f56c6c;
  }

  .rate-info {
    font-size: 12px;
    color: #909399;
    margin-left: 8px;
  }

  .surcharges-section {
    margin: 25px 0;
  }

  .section-subtitle {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 15px;
    color: #303133;
  }

  /* 表格水平滚动 */
  .table-container {
    width: 100%;
    overflow-x: auto;
    margin-bottom: 20px;
  }

  /* 确保表格显示 */
  .surcharges-table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    border: 1px solid #ebeef5;
  }

  .surcharges-table th, 
  .surcharges-table td {
    padding: 12px 10px;
    text-align: left;
    border-bottom: 1px solid #ebeef5;
    white-space: normal;
    word-break: break-word;
    vertical-align: top;
  }

  .surcharges-table th:first-child,
  .surcharges-table td:first-child {
    width: 15%;
  }

  .surcharges-table th:nth-child(2),
  .surcharges-table td:nth-child(2) {
    width: 20%;
  }

  .surcharges-table th:nth-child(3),
  .surcharges-table td:nth-child(3) {
    width: 10%;
    text-align: right;
  }

  .surcharges-table th:nth-child(4),
  .surcharges-table td:nth-child(4) {
    width: 45%;
  }

  .surcharges-table th:nth-child(5),
  .surcharges-table td:nth-child(5) {
    width: 10%;
    text-align: center;
  }

  .active-surcharge {
    background-color: #fff;
  }

  .inactive-surcharge {
    background-color: #f5f7fa;
    color: #909399;
  }

  .amount-cell {
    text-align: right;
  }

  /* 为了显示长条件 */
  .condition-cell {
    max-width: 300px;
    font-size: 13px;
    color: #606266;
    white-space: normal;
    word-break: break-word;
  }

  .status-cell {
    text-align: center;
  }

  .status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
  }

  .status-active {
    background-color: #f0f9eb;
    color: #67c23a;
  }

  .status-inactive {
    background-color: #f4f4f5;
    color: #909399;
  }

  .calculation-details {
    margin-top: 25px;
  }

  .details-container {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    overflow: hidden;
  }

  .details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background-color: #f5f7fa;
    border-bottom: 1px solid #ebeef5;
  }

  .details-title {
    font-weight: 500;
  }

  .details-toggle {
    color: #409eff;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    font-size: 14px;
  }

  /* 代码显示 */
  .details-content {
    padding: 15px;
    background-color: #f5f7fa;
    font-size: 14px;
    font-family: monospace;
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
  }

  .details-section-title {
    font-size: 14px;
    font-weight: 500;
    margin: 10px 0;
  }

  .calculation-step {
    margin-bottom: 12px;
    padding: 10px;
    background-color: #fff;
    border-radius: 4px;
  }

  /* 信息代码显示 */
  .debug-info {
    padding: 10px;
    background-color: #fff;
    border-radius: 4px;
    overflow-x: auto;
    max-height: 300px;
    overflow-y: auto;
  }

  .no-details-info {
    font-style: italic;
    color: #909399;
  }

  /* 转换代码显示 */
  .unit-conversion-info {
    margin-top: 30px;
    overflow-x: auto;
    background-color: #fff;
    padding: 20px;
    border-radius: 4px;
  }

  .unit-conversion-info h3 {
    margin-bottom: 15px;
    font-size: 16px;
    color: #303133;
    font-weight: 600;
  }

  .mt-10 {
    margin-top: 15px;
  }
  
  /* 样式统一 */
  .surcharges-table,
  .unit-conversion-info :deep(.el-table) {
    width: 100%;
    background-color: #fff;
    border: 1px solid #ebeef5;
    border-radius: 4px;
  }
  
  .surcharges-table th,
  .unit-conversion-info :deep(.el-table th) {
    background-color: #f5f7fa;
    color: #606266;
    font-weight: 500;
    padding: 12px 10px;
  }
  
  .surcharges-table td,
  .unit-conversion-info :deep(.el-table td) {
    padding: 12px 10px;
  }
  
  /* 文本颜色 */
  .details-content {
    padding: 15px;
    background-color: #fff;
    font-size: 14px;
    font-family: monospace;
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #ebeef5;
    margin-top: 5px;
  }
  
  .details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background-color: #f5f7fa;
    border: 1px solid #ebeef5;
    border-radius: 4px 4px 0 0;
  }

  .result-descriptions :deep(.el-descriptions__body) {
    padding: 16px;
  }

  .total-charge {
    font-size: 16px;
    font-weight: 600;
    color: #f56c6c;
  }

  .compare-table {
    width: 100%;
    margin-top: 10px;
  }

  /* 响应式设计*/
  @media (max-width: 768px) {
    .calculator-container {
      padding: 10px;
    }
    
    .header-actions {
      flex-direction: column;
      gap: 8px;
    }
    
    .product-selection-container {
      padding: 12px;
    }

    .result-section {
      flex-direction: column;
    }

    .result-item {
      min-width: 100%;
    }
  }

  .date-selection-form {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #ebeef5;
  }

  .date-selection-form :deep(.el-form-item) {
    margin-bottom: 0;
  }

  .calculator-card :deep(.el-card__body) {
    padding: 20px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .cache-info {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .last-updated {
    font-size: 13px;
    color: #606266;
    margin-right: 10px;
  }

  /* 按钮样式 */
  .header-actions .el-button + .el-button {
    margin-left: 10px;
  }

  .error-container {
    margin-bottom: 20px;
  }

  .error-details {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .error-details-content {
    max-height: 200px;
    overflow: auto;
    background-color: #f5f7fa;
    border-radius: 4px;
    padding: 8px;
    margin-top: 8px;
    font-family: monospace;
    font-size: 12px;
    line-height: 1.5;
    border: 1px solid #e4e7ed;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* El-table样式 */
  .unit-conversion-info :deep(.el-table) {
    width: 100%;
    margin-bottom: 15px;
  }

  .unit-conversion-info :deep(.el-table__header-wrapper),
  .unit-conversion-info :deep(.el-table__body-wrapper) {
    overflow-x: visible;
  }

  .unit-conversion-info :deep(.el-table__inner-wrapper) {
    overflow: visible;
  }

  .surcharges-table th {
    background-color: #f5f7fa;
    font-weight: 500;
    color: #606266;
  }

  .surcharges-section {
    margin: 25px 0;
  }

  .section-subtitle {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 15px;
    color: #303133;
  }

  /* 计算详情显示计算按钮 */
  .calculation-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    margin-bottom: 10px;
    padding: 0 10px;
  }

  .calculation-process-section {
    margin-top: 15px;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 20px;
    background-color: #fff;
  }

  .no-process-details {
    text-align: center;
    padding: 20px;
  }

  .process-help-text {
    color: #909399;
    font-size: 14px;
    margin-top: 10px;
  }

  .process-details {
    max-height: 500px;
    overflow-y: auto;
  }

  .process-detail-item {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px dashed #e6e6e6;
  }

  .process-detail-item:last-child {
    border-bottom: none;
  }

  .process-code {
    background-color: #f5f7fa;
    padding: 10px;
    border-radius: 4px;
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 12px;
    overflow-x: auto;
  }

  .unauthorized-warning {
    margin: 15px 0;
  }

  .result-container {
    margin-top: 20px;
    padding: 20px;
    background-color: #fff;
    border-radius: 6px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }
  
  /* 边距样式 */
  .mb-10 {
    margin-bottom: 10px;
  }
  
  .calculation-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .calculation-detail-header .amount {
    font-weight: bold;
    color: #409EFF;
  }
  
  .calculation-detail-body {
    padding: 10px 0;
  }
  
  .calculation-detail-body p {
    margin: 5px 0;
  }
  
  .empty-details {
    padding: 30px 0;
    text-align: center;
  }
  
  /* 提示显示样式 */
  .fixed-result-alert {
    margin-bottom: 15px;
  }
  
  .header-actions {
    display: flex;
    gap: 10px;
  }

  /* 计算结果样式 */
  .calculation-details-container {
    margin-top: 20px;
  }

  /* 计算详情结果水平布局 */
  .calculation-detail-steps {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  /* 确保每个计算步骤显示 */
  .calculation-step-card {
    flex: 1 1 300px;
    max-width: 100%;
    margin-bottom: 15px;
  }
</style>

