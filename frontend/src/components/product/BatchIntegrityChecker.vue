<template>
  <div class="batch-integrity-checker">
    <el-card :title="title" shadow="never" class="mb-4">
      <div class="desc-section mb-3">
        <el-alert 
          type="info"
          show-icon
          class="mb-3"
        >
          <span class="alert-title">
            批量数据完整性检查可以帮助您批量发现并修复多个产品的数据缺失或不完整问题。
          </span>
          <div class="alert-description">
            系统将检查所选产品的重量段、区域价格、附加费和特殊规则等数据项。
          </div>
        </el-alert>
      </div>

      <div class="batch-options mb-3">
        <el-form label-position="top">
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="选择产品">
                <el-select
                  v-model="selectedProductIds"
                  multiple
                  placeholder="选择要检查的产品"
                  :options="productOptions"
                  :loading="loadingProducts"
                  style="width: 100%"
                  collapse-tags
                  collapse-tags-tooltip
                  :max-collapse-tags="3"
                >
                  <el-option
                    v-for="option in productOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="处理模式">
                <div class="flex-row">
                  <el-switch 
                    v-model="dryRun" 
                    active-text="仅检查" 
                    inactive-text="检查并修复"
                  />
                  <span>{{ dryRun ? '仅检查数据完整性，不进行修复' : '检查并自动修复数据完整性问题' }}</span>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <div class="actions mb-3">
        <div class="flex-row">
          <el-button 
            type="primary" 
            :loading="loading"
            :disabled="selectedProductIds.length === 0"
            @click="startBatchCheck"
          >
            <el-icon><Check /></el-icon>
            开始批量检查
          </el-button>
          
          <el-button 
            @click="selectAll"
            :disabled="loadingProducts"
          >
            全选
          </el-button>
          
          <el-button 
            @click="clearSelection"
            :disabled="selectedProductIds.length === 0"
          >
            清空选择
          </el-button>
        </div>
      </div>

      <!-- 检查结果展示 -->
      <div v-if="result" class="results-section">
        <el-divider>检查结果</el-divider>
        
        <!-- 成功提示 -->
        <el-alert 
          type="success" 
          show-icon 
          :title="result.message"
          class="mb-3"
        />
        
        <el-descriptions title="汇总信息" :column="3" border>
          <el-descriptions-item label="检查产品数">{{ result.results?.total || 0 }}</el-descriptions-item>
          <el-descriptions-item label="完整产品数">{{ result.results?.complete || 0 }}</el-descriptions-item>
          <el-descriptions-item label="不完整产品数">{{ result.results?.incomplete || 0 }}</el-descriptions-item>
          
          <el-descriptions-item v-if="!dryRun" label="修复成功">{{ result.results?.fixed || 0 }}</el-descriptions-item>
          <el-descriptions-item v-if="!dryRun" label="修复失败">{{ result.results?.failed || 0 }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
    
    <!-- 详情弹窗 -->
    <el-dialog
      v-model:visible="detailsVisible"
      title="产品数据完整性详情"
      width="800px"
      @close="closeDetailsModal"
    >
      <div v-if="selectedProductDetails">
        <el-descriptions title="产品信息" :column="3" border>
          <el-descriptions-item label="产品ID">{{ selectedProductDetails.product_id }}</el-descriptions-item>
          <el-descriptions-item label="产品代码">{{ selectedProductDetails.product_code }}</el-descriptions-item>
          <el-descriptions-item label="产品名称">{{ selectedProductDetails.product_name }}</el-descriptions-item>
          <el-descriptions-item label="数据完整性">
            <el-tag :type="selectedProductDetails.is_complete ? 'success' : 'danger'">
              {{ selectedProductDetails.is_complete ? '完整' : '不完整' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedProductDetails.missing_data && !selectedProductDetails.is_complete" class="mb-3">
          <el-descriptions title="缺失数据项" :column="3" border>
            <el-descriptions-item label="重量段">
              <el-tag :type="selectedProductDetails.missing_data.weight_ranges ? 'danger' : 'success'">
                {{ selectedProductDetails.missing_data.weight_ranges ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
            
            <el-descriptions-item label="区域价格">
              <el-tag :type="selectedProductDetails.missing_data.zone_prices ? 'danger' : 'success'">
                {{ selectedProductDetails.missing_data.zone_prices ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
            
            <el-descriptions-item label="附加费">
              <el-tag :type="selectedProductDetails.missing_data.surcharges ? 'danger' : 'success'">
                {{ selectedProductDetails.missing_data.surcharges ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
            
            <el-descriptions-item label="旺季附加费">
              <el-tag :type="selectedProductDetails.missing_data.peak_season_surcharges ? 'danger' : 'success'">
                {{ selectedProductDetails.missing_data.peak_season_surcharges ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div v-if="selectedProductDetails.fix_result" class="mb-3">
          <el-collapse>
            <el-collapse-item title="修复详情">
              <el-descriptions title="修复结果" :column="3" border>
                <el-descriptions-item label="状态">
                  <el-tag :type="selectedProductDetails.fix_result.success ? 'success' : 'danger'">
                    {{ selectedProductDetails.fix_result.success ? '成功' : '失败' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="消息">{{ selectedProductDetails.fix_result.message }}</el-descriptions-item>
              </el-descriptions>
              
              <div v-if="selectedProductDetails.fix_result.repair_details">
                <el-divider>修复前</el-divider>
                <el-descriptions border>
                  <el-descriptions-item 
                    v-for="(value, key) in selectedProductDetails.fix_result.repair_details.before" 
                    :key="key"
                    :label="formatFieldName(key)"
                  >
                    <el-tag :type="value ? 'danger' : 'success'">
                      {{ value ? '缺失' : '完整' }}
                    </el-tag>
                  </el-descriptions-item>
                </el-descriptions>
                
                <el-divider>修复后</el-divider>
                <el-descriptions border>
                  <el-descriptions-item 
                    v-for="(value, key) in selectedProductDetails.fix_result.repair_details.after" 
                    :key="key"
                    :label="formatFieldName(key)"
                  >
                    <el-tag :type="value ? 'danger' : 'success'">
                      {{ value ? '缺失' : '完整' }}
                    </el-tag>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="closeDetailsModal">关闭</el-button>
        <el-button 
          v-if="selectedProductDetails && !selectedProductDetails.is_complete && dryRun"
          type="primary" 
          @click="fixFromModal"
        >
          修复此产品
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Check } from '@element-plus/icons-vue';
import { getProducts as getProductList } from '@/api/products';
import { batchCheckIntegrity, checkProductIntegrity } from '@/api/products';

const props = defineProps({
  title: {
    type: String,
    default: '批量数据完整性检查'
  },
  preselectedProductIds: {
    type: Array as () => (number | string)[],
    default: () => []
  }
});

const emit = defineEmits(['check-complete', 'data-changed']);

// 数据
const loading = ref(false);
const loadingProducts = ref(false);
const dryRun = ref(true);
const selectedProductIds = ref<string[]>([]);
const productOptions = ref<{ label: string; value: string }[]>([]);
const result = ref<any>(null);
const detailsVisible = ref(false);
const selectedProductDetails = ref<any>(null);

// 表格列定义
const resultColumns = [
  {
    title: '产品ID',
    dataIndex: 'product_id',
    key: 'product_id',
    width: '80px'
  },
  {
    title: '产品代码',
    dataIndex: 'product_code',
    key: 'product_code',
    width: '120px'
  },
  {
    title: '产品名称',
    dataIndex: 'product_name',
    key: 'product_name',
    width: '150px'
  },
  {
    title: '状态',
    key: 'status',
    width: '100px'
  },
  {
    title: '缺失数据项',
    key: 'missing',
    width: '200px'
  },
  {
    title: '修复状态',
    key: 'fixed',
    width: '100px'
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: '120px'
  }
];

// 格式化数据
const formatTableData = (details: any[]) => {
  return details.map((item, index) => ({
    ...item,
    key: item.product_id || index
  }));
};

// 格式化字段名称
const formatFieldName = (key: string | number) => {
  const fieldMap: Record<string, string> = {
    'weight_ranges': '重量段',
    'zone_prices': '区域价格',
    'surcharges': '附加费',
    'peak_season_surcharges': '旺季附加费'
  };
  
  return fieldMap[key.toString()] || String(key);
};

// 获取产品列表
const fetchProducts = async () => {
  loadingProducts.value = true;
  try {
    const res = await getProductList({});
    const productData = res as any; // 使用类型断言
    
    if (productData && productData.results) {
      productOptions.value = productData.results.map((product: any) => ({
        label: `${product.name || product.product_name} (${product.code || product.product_id})`,
        value: String(product.id || product.product_id)
      }));
    }
    
    // 如果有预选产品ID，则设置选中状态
    if (props.preselectedProductIds && props.preselectedProductIds.length > 0) {
      selectedProductIds.value = props.preselectedProductIds.map(id => String(id));
    }
  } catch (error) {
    ElMessage.error('获取产品列表失败');
    console.error('获取产品列表错误:', error);
  } finally {
    loadingProducts.value = false;
  }
};

// 全选产品
const selectAll = () => {
  selectedProductIds.value = productOptions.value.map(option => option.value);
};

// 清空选择
const clearSelection = () => {
  selectedProductIds.value = [];
};

// 开始批量检查
const startBatchCheck = async () => {
  if (selectedProductIds.value.length === 0) {
    ElMessage.warning('请选择至少一个产品进行检查');
    return;
  }
  
  loading.value = true;
  try {
    const data = {
      product_ids: selectedProductIds.value,
      dry_run: dryRun.value
    };
    
    const res = await batchCheckIntegrity(data);
    result.value = res;
    
    if (res.success) {
      ElMessage.success(res.message || '批量检查完成');
      
      // 如果不是干运行模式且成功执行了修复，则发送数据变更事件
      if (!dryRun.value && res.results?.fixed > 0) {
        emit('data-changed', res);
      }
    } else {
      ElMessage.error(res.message || '批量检查失败');
    }
  } catch (error) {
    ElMessage.error('执行批量检查时发生错误');
    console.error('批量检查错误:', error);
  } finally {
    loading.value = false;
  }
};

// 查看详情
const viewDetails = (record: any) => {
  selectedProductDetails.value = record;
  detailsVisible.value = true;
};

// 关闭详情弹窗
const closeDetailsModal = () => {
  detailsVisible.value = false;
  selectedProductDetails.value = null;
};

// 修复单个产品
const fixSingleProduct = async (productId: number | string) => {
  try {
    loading.value = true;
    const data = {
      product_id: productId,
      dry_run: false
    };
    
    const response = await checkProductIntegrity(data);
    
    // 更新结果中对应产品的状态
    if (result.value && result.value.results && result.value.results.details) {
      const productIndex = result.value.results.details.findIndex((item: any) => 
        item.product_id === productId);
      
      if (productIndex !== -1) {
        result.value.results.details[productIndex].fix_result = response;
        result.value.results.details[productIndex].is_complete = true;
        
        // 更新计数
        result.value.results.fixed += 1;
        result.value.results.incomplete -= 1;
      }
    }
    
    ElMessage.success(`产品 ${productId} 修复成功`);
    
    // 如果弹窗打开且是当前产品，更新弹窗中的详情
    if (detailsVisible.value && selectedProductDetails.value && 
        selectedProductDetails.value.product_id === productId) {
      selectedProductDetails.value.fix_result = response;
      selectedProductDetails.value.is_complete = true;
    }
    
    // 通知数据变更
    emit('data-changed', { productId, response });
    
  } catch (error: any) {
    ElMessage.error(`修复产品 ${productId} 失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

// 从弹窗中修复产品
const fixFromModal = async () => {
  if (!selectedProductDetails.value) return;
  
  await fixSingleProduct(selectedProductDetails.value.product_id);
};

// 生命周期钩子
onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
.batch-integrity-checker {
  width: 100%;
}

.mb-3 {
  margin-bottom: 15px;
}

.mb-4 {
  margin-bottom: 20px;
}

.flex-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-title {
  font-weight: bold;
}

.alert-description {
  margin-top: 8px;
  font-size: 13px;
}

.w-100 {
  width: 100%;
}

.justify-content-between {
  display: flex;
  justify-content: space-between;
}
</style> 