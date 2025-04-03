<template>
  <TableForm 
    title="基础费用" 
    description="管理不同分区和重量段的基础费用"
    :uses-mock-data="usesMockData"
    :saving="saving"
    @save="handleBaseFeesSave"
  >
    <div class="basefee-table-wrapper">
      <div class="mock-basefee-table">
        <h3>基础费用列表</h3>
        <div class="table-header-actions">
          <div class="left-actions">
            <el-button type="primary" class="mb-3" @click="addBaseFee">
              <el-icon><Plus /></el-icon>添加基础费用
            </el-button>
            <el-button type="info" class="mb-3" @click="checkBaseFeeData">
              <el-icon><View /></el-icon>检查基础费用数据
            </el-button>
            <el-button type="success" class="mb-3" @click="reloadBaseFeeData">
              <el-icon><RefreshRight /></el-icon>刷新基础费用数据
            </el-button>
          </div>
          <div class="scroll-hint">
            <el-icon><Connection /></el-icon>
            <span>表格可横向滚动查看全部内容</span>
          </div>
        </div>
        
        <div class="example-table-wrapper">
          <div class="example-table-container">
            <table class="example-table" style="min-width: 800px;">
              <thead>
                <tr>
                  <th>重量</th>
                  <th>单位</th>
                  <th>计价类型</th>
                  <!-- 基础价格列 - 完全动态生成所有Zone列，不硬编码数字范围 -->
                  <template v-for="zone in availableZones" :key="`base-price-header-${zone}`">
                    <th>{{ formatZoneDisplayName(zone) }}基础价格</th>
                  </template>
                  <!-- 单位价格列 - 完全动态生成所有Zone单价列，不硬编码数字范围 -->
                  <template v-for="zone in availableZones" :key="`unit-price-header-${zone}`">
                    <th>{{ formatZoneDisplayName(zone) }}单位重量价格</th>
                  </template>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in baseFeeList" :key="`mock-basefee-${index}`">
                  <td>{{ item.weight }}</td>
                  <td>{{ item.weight_unit }}</td>
                  <td>{{ formatFeeType(item.fee_type) }}</td>
                  
                  <!-- 基础价格列 - 动态渲染 -->
                  <template v-for="zone in availableZones" :key="`base-price-${index}-${zone}`">
                    <td>
                      <el-input-number 
                        v-model="item[`zone${zone}_price`]" 
                        :precision="2" 
                        :step="0.5"
                        :min="0"
                        size="small"
                        controls-position="right"
                        @change="() => handleBaseFeeChanged(index, item)"
                      />
                    </td>
                  </template>
                  
                  <!-- 单位价格列 - 动态渲染 -->
                  <template v-for="zone in availableZones" :key="`unit-price-${index}-${zone}`">
                    <td>
                      <el-input-number 
                        v-model="item[`zone${zone}_unit_price`]" 
                        :precision="2" 
                        :step="0.1"
                        :min="0"
                        size="small"
                        controls-position="right"
                        @change="() => handleBaseFeeChanged(index, item)"
                      />
                    </td>
                  </template>
                  
                  <td>
                    <el-button 
                      type="danger" 
                      size="small" 
                      @click="handleRemoveBaseFee(index)"
                      icon="Delete"
                    >
                      删除
                    </el-button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- 批量操作工具栏 -->
        <div class="batch-actions">
          <h4>批量编辑工具</h4>
          <div class="batch-form">
            <div class="batch-row">
              <span class="batch-label">选择区间:</span>
              <el-select v-model="batchEditZone" placeholder="选择区间" style="width: 120px;">
                <el-option
                  v-for="zone in availableZones"
                  :key="zone"
                  :label="formatZoneDisplayName(zone)"
                  :value="zone"
                />
              </el-select>
            </div>
            
            <div class="batch-row">
              <span class="batch-label">操作类型:</span>
              <el-radio-group v-model="batchEditType">
                <el-radio label="add">增加</el-radio>
                <el-radio label="subtract">减少</el-radio>
                <el-radio label="multiply">乘以</el-radio>
                <el-radio label="set">设为</el-radio>
              </el-radio-group>
            </div>
            
            <div class="batch-row">
              <span class="batch-label">数值:</span>
              <el-input-number 
                v-model="batchEditValue" 
                :precision="2" 
                :step="batchEditType === 'multiply' ? 0.01 : 0.5"
                :min="batchEditType === 'multiply' ? 0 : undefined"
                size="small"
                controls-position="right"
              />
            </div>
            
            <div class="batch-row">
              <span class="batch-label">应用于:</span>
              <el-radio-group v-model="batchEditTarget">
                <el-radio label="base">基础价格</el-radio>
                <el-radio label="unit">单位重量价格</el-radio>
                <el-radio label="both">两者都是</el-radio>
              </el-radio-group>
            </div>
            
            <div class="batch-row">
              <el-button type="primary" @click="applyBatchEdit">
                应用批量编辑
              </el-button>
              <el-button type="warning" @click="resetBatchForm">
                重置
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </TableForm>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Check, Plus, View, RefreshRight, Connection, Delete, InfoFilled } from '@element-plus/icons-vue';
import TableForm from './TableForm.vue';

const props = defineProps<{
  baseFeeList: any[];
  availableZones: any[];
  usesMockData: boolean;
  saving: boolean;
  productId: string;
}>();

const emit = defineEmits<{
  (e: 'save', baseFeeList: any[]): void;
  (e: 'add'): void;
  (e: 'check'): void;
  (e: 'reload'): void;
  (e: 'remove', index: number): void;
  (e: 'update', item: any, index: number): void;
}>();

// 批量编辑状态
const batchEditZone = ref('');
const batchEditType = ref('add');
const batchEditValue = ref(0);
const batchEditTarget = ref('base');

// 格式化区间名称
const formatZoneDisplayName = (zone: string | number) => {
  return `区间${zone}`;
};

// 格式化费用类型
const formatFeeType = (feeType: string) => {
  const typeMap: Record<string, string> = {
    'STEP': '阶梯式',
    'LINEAR': '线性'
  };
  return typeMap[feeType] || feeType;
};

// 处理费用变更
const handleBaseFeeChanged = (index: number, item: any) => {
  emit('update', item, index);
};

// 处理移除费用
const handleRemoveBaseFee = (index: number) => {
  ElMessageBox.confirm(
    '确定要删除这条基础费用记录吗？',
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    emit('remove', index);
    ElMessage.success('删除成功');
  }).catch(() => {
    // 用户取消删除，不做任何操作
  });
};

// 添加基础费用
const addBaseFee = () => {
  emit('add');
};

// 检查基础费用数据
const checkBaseFeeData = () => {
  emit('check');
};

// 重新加载基础费用数据
const reloadBaseFeeData = () => {
  emit('reload');
};

// 保存基础费用
const handleBaseFeesSave = () => {
  emit('save', props.baseFeeList);
};

// 应用批量编辑
const applyBatchEdit = () => {
  if (!batchEditZone.value) {
    ElMessage.warning('请选择要编辑的区间');
    return;
  }

  const updatedList = props.baseFeeList.map(item => {
    const newItem = { ...item };
    
    // 决定要编辑的字段
    const baseField = `zone${batchEditZone.value}_price`;
    const unitField = `zone${batchEditZone.value}_unit_price`;
    
    // 根据编辑目标应用操作
    if (batchEditTarget.value === 'base' || batchEditTarget.value === 'both') {
      if (batchEditType.value === 'add') {
        newItem[baseField] = Number(newItem[baseField] || 0) + Number(batchEditValue.value);
      } else if (batchEditType.value === 'subtract') {
        newItem[baseField] = Math.max(0, Number(newItem[baseField] || 0) - Number(batchEditValue.value));
      } else if (batchEditType.value === 'multiply') {
        newItem[baseField] = Number(newItem[baseField] || 0) * Number(batchEditValue.value);
      } else if (batchEditType.value === 'set') {
        newItem[baseField] = Number(batchEditValue.value);
      }
    }
    
    if (batchEditTarget.value === 'unit' || batchEditTarget.value === 'both') {
      if (batchEditType.value === 'add') {
        newItem[unitField] = Number(newItem[unitField] || 0) + Number(batchEditValue.value);
      } else if (batchEditType.value === 'subtract') {
        newItem[unitField] = Math.max(0, Number(newItem[unitField] || 0) - Number(batchEditValue.value));
      } else if (batchEditType.value === 'multiply') {
        newItem[unitField] = Number(newItem[unitField] || 0) * Number(batchEditValue.value);
      } else if (batchEditType.value === 'set') {
        newItem[unitField] = Number(batchEditValue.value);
      }
    }
    
    return newItem;
  });
  
  // 发出更新事件，更新每个项目
  updatedList.forEach((item, index) => {
    emit('update', item, index);
  });
  
  ElMessage.success(`已对区间${batchEditZone.value}进行批量编辑`);
  resetBatchForm();
};

// 重置批量编辑表单
const resetBatchForm = () => {
  batchEditZone.value = '';
  batchEditType.value = 'add';
  batchEditValue.value = 0;
  batchEditTarget.value = 'base';
};
</script>

<style scoped>
.form-section {
  margin-bottom: 24px;
  padding: 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.section-header-with-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
}

.section-description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 0;
}

.table-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.mb-3 {
  margin-bottom: 12px;
  margin-right: 8px;
}

.scroll-hint {
  display: flex;
  align-items: center;
  color: #909399;
  font-size: 12px;
}

.scroll-hint svg {
  margin-right: 4px;
}

.example-table-wrapper {
  overflow: hidden;
  border-radius: 4px;
  border: 1px solid #EBEEF5;
  margin-bottom: 20px;
}

.example-table-container {
  overflow-x: auto;
  max-width: 100%;
}

.example-table {
  width: 100%;
  border-collapse: collapse;
}

.example-table th,
.example-table td {
  padding: 12px 8px;
  text-align: center;
  border-bottom: 1px solid #EBEEF5;
}

.example-table th {
  background-color: #F5F7FA;
  color: #606266;
  font-weight: 600;
  white-space: nowrap;
}

.example-table tbody tr:hover {
  background-color: #F5F7FA;
}

.batch-actions {
  margin-top: 24px;
  padding: 16px;
  background-color: #F5F7FA;
  border-radius: 4px;
}

.batch-actions h4 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.batch-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.batch-label {
  min-width: 80px;
  font-weight: 500;
}
</style> 