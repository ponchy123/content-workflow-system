<template>
  <div class="data-integrity-checker">
    <el-card :title="title" shadow="never" class="mb-4">
      <div class="desc-section mb-3">
        <el-alert 
          type="info"
          show-icon
          class="mb-3"
        >
          <span class="alert-title">
            数据完整性检查可以帮助您发现并修复产品数据中的缺失或不完整问题。
          </span>
          <div class="alert-description">
            系统将检查以下数据项：重量段、区域价格、附加费和特殊规则。
          </div>
        </el-alert>
      </div>

      <div class="action-row mb-3">
        <div class="flex-between">
          <div class="flex-row">
            <el-switch 
              v-model="dryRun" 
              active-text="仅检查" 
              inactive-text="检查并修复"
            />
            <span>{{ dryRun ? '仅检查数据完整性，不进行修复' : '检查并自动修复数据完整性问题' }}</span>
          </div>
          
          <el-button 
            type="primary" 
            :loading="loading"
            @click="checkSingleProduct"
          >
            <el-icon><Check /></el-icon>
            检查当前产品
          </el-button>
        </div>
      </div>

      <!-- 检查结果展示 -->
      <div v-if="result">
        <el-divider>检查结果</el-divider>
        
        <!-- 成功提示 -->
        <el-alert 
          v-if="result.success" 
          type="success" 
          show-icon 
          :title="result.message"
          class="mb-3"
        />
        
        <!-- 失败提示 -->
        <el-alert 
          v-else 
          type="error" 
          show-icon 
          :title="result.message"
          class="mb-3"
        />
        
        <!-- 数据不完整时的详细信息 -->
        <div v-if="result.missing_data" class="mb-3">
          <el-descriptions title="数据完整性检查详情" :column="1" border>
            <el-descriptions-item label="重量段">
              <el-tag :type="result.missing_data.weight_ranges ? 'danger' : 'success'">
                {{ result.missing_data.weight_ranges ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
            
            <el-descriptions-item label="区域价格">
              <el-tag :type="result.missing_data.zone_prices ? 'danger' : 'success'">
                {{ result.missing_data.zone_prices ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
            
            <el-descriptions-item label="附加费">
              <el-tag :type="result.missing_data.surcharges ? 'danger' : 'success'">
                {{ result.missing_data.surcharges ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
            
            <el-descriptions-item label="旺季附加费">
              <el-tag :type="result.missing_data.peak_season_surcharges ? 'danger' : 'success'">
                {{ result.missing_data.peak_season_surcharges ? '缺失' : '完整' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- 修复细节 -->
        <div v-if="result.repair_details" class="mb-3">
          <el-collapse>
            <el-collapse-item title="修复详情" name="1">
              <el-descriptions title="修复前" :column="1" border>
                <el-descriptions-item label="重量段">
                  <el-tag :type="result.repair_details.before.weight_ranges ? 'danger' : 'success'">
                    {{ result.repair_details.before.weight_ranges ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="区域价格">
                  <el-tag :type="result.repair_details.before.zone_prices ? 'danger' : 'success'">
                    {{ result.repair_details.before.zone_prices ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="附加费">
                  <el-tag :type="result.repair_details.before.surcharges ? 'danger' : 'success'">
                    {{ result.repair_details.before.surcharges ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="旺季附加费">
                  <el-tag :type="result.repair_details.before.peak_season_surcharges ? 'danger' : 'success'">
                    {{ result.repair_details.before.peak_season_surcharges ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
              
              <el-descriptions title="修复后" :column="1" border class="mt-3">
                <el-descriptions-item label="重量段">
                  <el-tag :type="result.repair_details.after.weight_ranges ? 'danger' : 'success'">
                    {{ result.repair_details.after.weight_ranges ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="区域价格">
                  <el-tag :type="result.repair_details.after.zone_prices ? 'danger' : 'success'">
                    {{ result.repair_details.after.zone_prices ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="附加费">
                  <el-tag :type="result.repair_details.after.surcharges ? 'danger' : 'success'">
                    {{ result.repair_details.after.surcharges ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="旺季附加费">
                  <el-tag :type="result.repair_details.after.peak_season_surcharges ? 'danger' : 'success'">
                    {{ result.repair_details.after.peak_season_surcharges ? '缺失' : '完整' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Check } from '@element-plus/icons-vue';
import { checkProductIntegrity } from '@/api/products';

const props = defineProps({
  title: {
    type: String,
    default: '数据完整性检查'
  },
  productId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['check-complete', 'data-changed']);

// 状态
const loading = ref(false);
const dryRun = ref(true);
const result = ref<any>(null);

// 检查单个产品
const checkSingleProduct = async () => {
  if (!props.productId) {
    ElMessage.warning('缺少产品ID');
    return;
  }
  
  loading.value = true;
  try {
    const data = {
      product_id: props.productId,
      dry_run: dryRun.value
    };
    
    const res = await checkProductIntegrity(data);
    result.value = res;
    
    if (res.success) {
      ElMessage.success(res.message || '检查完成');
      
      // 通知父组件检查完成
      emit('check-complete', res);
      
      // 如果成功进行了修复，发送数据变更事件
      if (!dryRun.value && res.repair_details) {
        emit('data-changed', res);
      }
    } else {
      ElMessage.error(res.message || '检查失败');
    }
  } catch (error) {
    ElMessage.error('检查时发生错误');
    console.error('检查产品完整性错误:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.mb-3 {
  margin-bottom: 15px;
}

.mb-4 {
  margin-bottom: 20px;
}

.mt-3 {
  margin-top: 15px;
}

.flex-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-title {
  font-weight: bold;
}

.alert-description {
  margin-top: 8px;
  font-size: 13px;
}
</style> 