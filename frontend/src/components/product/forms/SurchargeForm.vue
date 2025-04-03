<template>
  <!-- 列表模式 - 矩阵表格 -->
  <div v-if="props.mode === 'list'" class="list-mode">
    <div class="table-actions">
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon>添加附加费
      </el-button>
      <el-button @click="importFromExcel">
        <el-icon><Upload /></el-icon>从Excel导入
      </el-button>
      
      <!-- 分区管理按钮 -->
      <el-button type="success" @click="openZoneManagerDialog">
        <el-icon><Management /></el-icon>分区管理
      </el-button>
      
      <!-- 批量设置区域 -->
      <el-popover
        placement="bottom"
        :width="300"
        trigger="click"
      >
        <template #reference>
          <el-button>
            <el-icon><Setting /></el-icon>批量设置
          </el-button>
        </template>
        <div class="batch-settings">
          <h4>批量设置分区价格</h4>
          <el-form :model="batchSettings" label-width="100px" label-position="left">
            <el-form-item label="选择分区">
              <el-select v-model="batchSettings.zone" placeholder="请选择分区" style="width: 100%">
                <el-option v-for="zone in zones" :key="zone.id" :value="zone.id" :label="zone.name" />
                <el-option value="ALL" label="所有分区" />
              </el-select>
            </el-form-item>
            <el-form-item label="选择附加费">
              <el-select v-model="batchSettings.surchargeType" placeholder="请选择附加费类型" style="width: 100%">
                <el-option v-for="group in surchargeGroups" :key="group.id" :value="group.surcharge_type" :label="group.surcharge_type" />
                <el-option value="ALL" label="所有附加费" />
              </el-select>
            </el-form-item>
            <el-form-item label="设置价格">
              <el-input-number v-model="batchSettings.price" :precision="2" :step="0.5" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="applyBatchSettings">应用</el-button>
              <el-button @click="resetBatchSettings">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-popover>
    </div>

    <!-- 矩阵表格视图 -->
    <div class="matrix-table-container">
      <el-table :data="surchargeGroups" border stripe style="width: 100%" v-loading="loading">
        <el-table-column label="附加费类型" prop="name" width="200px">
          <template #default="scope">
            <div class="surcharge-cell">
              <el-input 
                v-model="scope.row.surcharge_type" 
                placeholder="请输入附加费类型" 
                size="small" 
                style="width: 100%;" 
                @change="() => updateSurchargeField(scope.row)"
              />
              <div class="action-buttons" v-if="scope.row.actions">
                <el-button type="danger" size="small" circle @click="deleteSurcharge(scope.row)" class="delete-btn always-visible">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="子类型" prop="subtype" width="180px">
          <template #default="scope">
            <el-input 
              v-model="scope.row.subtype" 
              placeholder="请输入子类型" 
              size="small" 
              style="width: 100%;" 
              @change="() => updateSurchargeField(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="条件描述" prop="condition_description" width="300px">
          <template #default="scope">
            <el-input 
              v-model="scope.row.condition_description" 
              placeholder="请输入条件描述" 
              size="small"
              @change="() => updateSurchargeField(scope.row)"
            />
          </template>
        </el-table-column>
        
        <!-- 动态生成各个分区的列 -->
        <el-table-column v-for="zone in zones" :key="zone.id" :label="zone.name" align="center">
          <template #header>
            <div class="zone-header">
              {{ zone.name }}
            </div>
          </template>
          <template #default="scope">
            <div class="zone-price-cell">
              <el-input-number 
                v-model="scope.row.zone_values[zone.id]" 
                controls-position="right"
                :min="0"
                :precision="2"
                :step="0.01"
                size="small"
                style="width: 100px;"
                @change="() => updateZonePriceDirectly(scope.row, zone.id, scope.row.zone_values[zone.id])"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="matrix-note-container">
      <p class="matrix-note">附加费规则表显示每个分区的附加费金额。注意: 附加费可以按照不同维度和条件进行设置,实际费用会根据每个包裹的具体特征计算。</p>
    </div>
  </div>

  <!-- 表单模式 -->
  <el-form v-else ref="formRef" :model="form" :rules="rules" label-width="120px">
    <el-form-item label="附加费名称" prop="name">
      <el-input v-model="form.name" placeholder="请输入附加费名称" />
    </el-form-item>
    <el-form-item label="费用类型" prop="type">
      <el-select v-model="form.type" placeholder="请选择费用类型">
        <el-option label="固定金额" value="fixed" />
        <el-option label="百分比" value="percentage" />
      </el-select>
    </el-form-item>
    <el-form-item :label="form.type === 'fixed' ? '金额' : '百分比'" prop="value">
      <el-input-number 
        v-model="form.value" 
        :precision="form.type === 'fixed' ? 2 : 1"
        :step="form.type === 'fixed' ? 1 : 0.1"
        :min="0"
      />
      <span v-if="form.type === 'percentage'">%</span>
    </el-form-item>
    <el-form-item label="状态" prop="is_active">
      <el-switch v-model="form.is_active" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="submitForm">确定</el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
  </el-form>

  <!-- 添加/编辑对话框 -->
  <el-dialog
    :title="dialogMode === 'add' ? '添加附加费' : '编辑附加费'"
    v-model="dialogVisible"
    width="500px"
  >
    <el-form ref="dialogFormRef" :model="dialogForm" :rules="rules" label-width="120px">
      <el-form-item label="附加费类型" prop="surcharge_type">
        <el-input v-model="dialogForm.surcharge_type" placeholder="请输入附加费类型" />
      </el-form-item>
      <el-form-item label="子类型" prop="subtype">
        <el-input v-model="dialogForm.subtype" placeholder="请输入子类型" />
      </el-form-item>
      <el-form-item label="条件描述" prop="condition_description">
        <el-input v-model="dialogForm.condition_description" type="textarea" :rows="3" placeholder="请输入条件描述" />
      </el-form-item>
      <el-form-item label="费用金额" prop="value">
        <el-input-number v-model="dialogForm.value" :precision="2" :step="0.01" :min="0" />
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="dialogForm.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitDialogForm" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>

  <!-- 编辑分区价格对话框 -->
  <el-dialog
    title="编辑分区价格"
    v-model="zonePriceDialogVisible"
    width="400px"
  >
    <el-form ref="zonePriceFormRef" :model="zonePriceForm" label-width="120px">
      <el-form-item label="附加费类型">
        <span>{{ zonePriceForm.surcharge_type }}</span>
      </el-form-item>
      <el-form-item label="分区">
        <span>{{ zonePriceForm.zone }}</span>
      </el-form-item>
      <el-form-item label="费用金额" prop="price">
        <el-input-number v-model="zonePriceForm.price" :precision="2" :step="0.01" :min="0" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="zonePriceDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="updateZonePrice" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>

  <!-- 分区管理对话框 -->
  <el-dialog
    title="分区管理"
    v-model="zoneManagerDialogVisible"
    width="600px"
  >
    <div class="zone-manager">
      <div class="zone-manager-header">
        <el-button type="primary" @click="addNewZone">
          <el-icon><Plus /></el-icon>添加分区
        </el-button>
      </div>
      <el-table :data="zonesForManager" border>
        <el-table-column label="分区名称" width="220">
          <template #default="scope">
            <el-input v-model="scope.row.name" placeholder="请输入分区名称" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <div class="zone-manager-actions">
              <el-button size="small" type="success" @click="saveZoneChanges(scope.row)">保存</el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteZone(scope.row)" 
                :disabled="zones.length <= 1"
              >删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <template #footer>
      <el-button @click="zoneManagerDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { Plus, Upload, Edit, Delete, Setting, Management } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import { createSurcharge, updateSurcharge, deleteSurcharge as apiDeleteSurcharge, getSurcharges } from '@/api/products';
import type { Surcharge as GlobalSurcharge } from '@/types/product';
import axios from 'axios';

// 组件内部使用的附加费接口
interface Surcharge {
  id?: string | number;
  name: string;
  type: 'fixed' | 'percentage';
  value: number;
  is_active: boolean;
  surcharge_type?: string;
  subtype?: string;
  condition_description?: string;
  product_id?: string;
  zone_values?: Record<string, number>;
  [key: string]: any;
  
  // 实现API所需的字段
  code?: string;
  amount?: number;
  effective_date?: string;
  expiration_date?: string;
  status?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface SurchargeGroup {
  id?: string | number;
  surcharge_type: string;
  subtype: string;
  condition_description: string;
  is_active: boolean;
  zone_values: Record<string, number>;
  actions?: boolean;
}

interface ZonePriceForm {
  id?: string | number;
  surcharge_type: string;
  zone: string;
  price: number;
}

interface Zone {
  id: string;
  name: string;
  isNew?: boolean;
}

const props = defineProps({
  productId: {
    type: String,
    required: true
  },
  mode: {
    type: String,
    required: true,
    validator: (value: string) => ['add', 'edit', 'list'].includes(value)
  },
  data: {
    type: Object as () => Surcharge | Surcharge[],
    default: () => ({
      name: '',
      type: 'fixed',
      value: 0,
      is_active: true
    })
  }
});

const emit = defineEmits(['success', 'cancel', 'save']);

const formRef = ref<FormInstance>();
const dialogFormRef = ref<FormInstance>();
const zonePriceFormRef = ref<FormInstance>();

// 表单数据
const form = ref<Surcharge>({
  name: '',
  type: 'fixed',
  value: 0,
  is_active: true
});

// 对话框数据
const dialogVisible = ref(false);
const dialogMode = ref<'add' | 'edit'>('add');
const dialogForm = ref<Surcharge & {surcharge_type?: string; subtype?: string; condition_description?: string}>({
  name: '',
  type: 'fixed',
  value: 0,
  is_active: true,
  surcharge_type: '',
  subtype: '',
  condition_description: ''
});

// 分区价格编辑对话框
const zonePriceDialogVisible = ref(false);
const zonePriceForm = ref<ZonePriceForm>({
  surcharge_type: '',
  zone: '',
  price: 0
});

// 表格数据
const surchargeGroups = ref<SurchargeGroup[]>([]);
const zones = ref<Zone[]>([
  { id: 'Zone2', name: 'Zone2' },
  { id: 'Zone3', name: 'Zone3' },
  { id: 'Zone4', name: 'Zone4' },
  { id: 'Zone5', name: 'Zone5' },
  { id: 'Zone6', name: 'Zone6' },
  { id: 'Zone7', name: 'Zone7' },
  { id: 'Zone8', name: 'Zone8' }
]);
const zonesForManager = computed(() => zones.value);
const loading = ref(false);
const submitting = ref(false);
const currentEditId = ref<string | number | undefined>(undefined);

// 批量设置
const batchSettings = ref({
  zone: 'ALL',
  surchargeType: 'ALL',
  price: 0
});

// 添加分区管理相关状态
const zoneManagerDialogVisible = ref(false);

// 验证规则
const rules: FormRules = {
  name: [{ required: true, message: '请输入附加费名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择费用类型', trigger: 'change' }],
  value: [{ required: true, message: '请输入费用值', trigger: 'blur' }],
  surcharge_type: [{ required: true, message: '请选择附加费类型', trigger: 'change' }],
  subtype: [{ required: true, message: '请选择子类型', trigger: 'change' }]
};

// 获取数据
onMounted(() => {
  console.log('SurchargeForm组件已挂载');
  console.log('当前模式:', props.mode);
  console.log('接收到的数据:', props.data);
  
  // 初始化分区数据
  initZones();
  
  if (props.mode === 'list') {
    loadSurchargeData();
  } else if (props.mode === 'edit' && props.data) {
    form.value = { ...props.data as any };
  }
});

// 从API或属性加载表格数据
const loadSurchargeData = async () => {
  loading.value = true;
  try {
    let surchargeData: any[] = [];
    
    // 首先尝试从props.data获取数据
    if (Array.isArray(props.data) && props.data.length > 0) {
      console.log('【调试】从props获取到附加费数据:', props.data.length, '条记录');
      surchargeData = props.data;
    } else if (props.productId) {
      // 如果props.data为空，尝试从API获取数据
      console.log('【调试】尝试从API获取附加费数据，产品ID:', props.productId);
      try {
        const token = localStorage.getItem('access_token');
        const apiUrl = `/api/v1/products/surcharges/by_product/?product_id=${encodeURIComponent(props.productId)}&_t=${Date.now()}`;
        console.log('【调试】附加费请求URL:', apiUrl);
        
        const apiResponse = await axios({
          url: apiUrl,
          method: 'get',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          },
          timeout: 10000
        });
        
        console.log('【调试】附加费API响应状态:', apiResponse.status);
        console.log('【调试】附加费API响应数据:', apiResponse.data);
        
        if (apiResponse.data && Array.isArray(apiResponse.data) && apiResponse.data.length > 0) {
          console.log('成功从API获取附加费数据:', apiResponse.data.length, '条记录');
          surchargeData = apiResponse.data;
        } else {
          console.warn('【警告】API返回的附加费数据为空或格式不正确，使用模拟数据');
          surchargeData = await generateMockSurcharges();
          ElMessage.warning('API未返回有效数据，已加载模拟数据');
        }
      } catch (apiError: any) {
        console.error('【错误】从API获取附加费数据失败:', apiError);
        console.error('错误详情:', apiError.response ? `状态码 ${apiError.response.status}` : '无响应');
        
        surchargeData = await generateMockSurcharges();
        ElMessage.error(`获取附加费数据失败: ${apiError.message}，已加载模拟数据`);
      }
    } else {
      // 如果没有productId，使用模拟数据
      console.log('【调试】未提供productId，使用模拟数据');
      surchargeData = await generateMockSurcharges();
    }
    
    // 处理获取到的数据
    if (surchargeData.length > 0) {
      console.log('附加费原始数据:', surchargeData);
      
      // 确保所有数据都有zone_fees字段，没有的初始化为空对象
      surchargeData.forEach(item => {
        item.zone_fees = item.zone_fees || {};
        
        // 为每个分区设置价格
        zones.value.forEach(zone => {
          const zoneKey = `zone${zone.id}`;
          
          // 检查价格是否存在，并确保是数字类型
          if (typeof item.zone_fees[zoneKey] === 'undefined') {
            item.zone_fees[zoneKey] = 0;
          } else if (typeof item.zone_fees[zoneKey] === 'string') {
            item.zone_fees[zoneKey] = parseFloat(item.zone_fees[zoneKey]) || 0;
          }
        });
      });
      
      // 按附加费类型分组
      const groupedData = groupSurchargesByType(surchargeData);
      surchargeGroups.value = groupedData;
      
      console.log('分组后的附加费数据:', surchargeGroups.value);
    } else {
      console.warn('没有获取到附加费数据，将使用空数组');
      surchargeGroups.value = [];
    }
    
    // 强制刷新视图
    surchargeGroups.value = [...surchargeGroups.value];
  } catch (error) {
    console.error('加载附加费数据失败:', error);
    ElMessage.error('加载数据失败，将使用空数据');
    surchargeGroups.value = [];
  } finally {
    loading.value = false;
  }
};

// 生成模拟附加费数据
const generateMockSurcharges = async () => {
  console.log('尝试从API获取附加费类型');
  try {
    // 尝试从API获取附加费类型列表
    const response = await fetch('/api/v1/products/surcharge-types/');
    if (response.ok) {
      const data = await response.json();
      let surchargeTypes = [];
      
      if (Array.isArray(data)) {
        surchargeTypes = data;
      } else if (data && data.results && Array.isArray(data.results)) {
        surchargeTypes = data.results;
      } else {
        console.warn('API返回的附加费类型格式不正确，将使用空数据');
        return [];
      }
      
      console.log('从API获取的附加费类型:', surchargeTypes);
      
      if (surchargeTypes.length === 0) {
        console.warn('API返回的附加费类型为空');
        return [];
      }
      
      const mockData = [];
      
      // 使用获取到的附加费类型生成模拟数据
      for (let i = 0; i < Math.min(6, surchargeTypes.length); i++) {
        const surcharge = surchargeTypes[i];
        const mockSurcharge: any = {
          id: `mock-surcharge-${i}`,
          surcharge_id: 1000 + i,
          product: props.productId,
          product_id: props.productId,
          name: surcharge.name || surcharge.surcharge_type,
          surcharge_type: surcharge.surcharge_type,
          subtype: surcharge.sub_type || `${surcharge.surcharge_type}-${i+1}`,
          condition_description: surcharge.condition_desc || surcharge.description || '无描述',
          display_order: i + 1,
          zone_fees: {}
        };
        
        // 为每个区域设置费用
        for (let zone = 1; zone <= 5; zone++) {
          const zoneKey = `zone${zone}`;
          mockSurcharge.zone_fees[zoneKey] = parseFloat((5 + i * 2 + zone * 1.5).toFixed(2));
        }
        
        mockData.push(mockSurcharge);
      }
      
      console.log('生成的模拟附加费数据:', mockData);
      return mockData;
    } else {
      console.error('获取附加费类型失败，将使用空数据');
      return [];
    }
  } catch (error) {
    console.error('获取附加费类型出错:', error);
    return [];
  }
};

// 获取指定分区的价格
const getZonePrice = (row: SurchargeGroup, zone: string): string => {
  if (!row.zone_values || !row.zone_values[zone]) {
    return '-';
  }
  return `$${row.zone_values[zone].toFixed(2)}`;
};

// 打开添加对话框
const openAddDialog = () => {
  dialogMode.value = 'add';
  dialogForm.value = {
    name: '',
    type: 'fixed',
    value: 0,
    is_active: true,
    surcharge_type: '',
    subtype: '',
    condition_description: ''
  };
  dialogVisible.value = true;
};

// 编辑附加费
const editSurcharge = (row: SurchargeGroup) => {
  dialogMode.value = 'edit';
  currentEditId.value = row.id;
  dialogForm.value = {
    name: row.surcharge_type,
    type: 'fixed',
    value: 0,
    is_active: row.is_active,
    surcharge_type: row.surcharge_type,
    subtype: row.subtype,
    condition_description: row.condition_description
  };
  
  // 设置默认值
  const firstZone = Object.keys(row.zone_values)[0];
  if (firstZone) {
    dialogForm.value.value = row.zone_values[firstZone];
  }
  
  dialogVisible.value = true;
};

// 删除附加费
const deleteSurcharge = (row: SurchargeGroup) => {
  ElMessageBox.confirm(
    `确定要删除附加费 "${row.surcharge_type}" 吗?`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      if (row.id) {
        await apiDeleteSurcharge(row.id);
        ElMessage.success('删除成功');
        loadSurchargeData();
      }
    } catch (error) {
      console.error('删除失败:', error);
      ElMessage.error('删除失败');
    }
  }).catch(() => {
    // 取消删除
  });
};

// 编辑分区价格
const editZonePrice = (row: SurchargeGroup, zone: string) => {
  zonePriceForm.value = {
    id: row.id,
    surcharge_type: row.surcharge_type,
    zone: zone,
    price: row.zone_values && row.zone_values[zone] ? row.zone_values[zone] : 0
  };
  zonePriceDialogVisible.value = true;
};

// 更新分区价格
const updateZonePrice = async () => {
  submitting.value = true;
  try {
    // 在数据模型中更新价格
    const index = surchargeGroups.value.findIndex(item => item.id === zonePriceForm.value.id);
    if (index !== -1) {
      if (!surchargeGroups.value[index].zone_values) {
        surchargeGroups.value[index].zone_values = {};
      }
      surchargeGroups.value[index].zone_values[zonePriceForm.value.zone] = zonePriceForm.value.price;
      
      // 这里应该调用API更新数据
      // await updateSurcharge(zonePriceForm.value.id, {...});
      
      ElMessage.success('更新成功');
      zonePriceDialogVisible.value = false;
    }
  } catch (error) {
    console.error('更新失败:', error);
    ElMessage.error('更新失败');
  } finally {
    submitting.value = false;
  }
};

// 将表单数据转换为API需要的格式
const convertToApiFormat = (data: any): any => {
  // 将zone_values转换为zone_fees所需的格式
  const zone_fees: Record<string, number> = {};
  
  // 处理直接在对象上的Zone1, Zone2等属性
  for (const key in data) {
    if (key.match(/^Zone\d+$/)) {
      const zoneNumber = key.replace('Zone', '');
      zone_fees[`zone${zoneNumber}`] = data[key];
    }
  }
  
  // 处理zone_values对象中的Zone1, Zone2等属性
  if (data.zone_values) {
    for (const key in data.zone_values) {
      if (key.match(/^Zone\d+$/)) {
        const zoneNumber = key.replace('Zone', '');
        zone_fees[`zone${zoneNumber}`] = data.zone_values[key];
      }
    }
  }
  
  return {
    product: data.product_id,
    surcharge_type: data.surcharge_type || '',
    sub_type: data.subtype || '',
    condition_desc: data.condition_description || '',
    zone_fees: zone_fees,
    is_deleted: false
  };
};

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const submitData = {
          ...form.value,
          product_id: props.productId
        };
        
        const apiData = convertToApiFormat(submitData);
        
        if (props.mode === 'add') {
          await createSurcharge(apiData);
          ElMessage.success('添加成功');
        } else if (props.mode === 'edit' && !Array.isArray(props.data) && props.data?.id) {
          await updateSurcharge(props.data.id, apiData);
          ElMessage.success('更新成功');
        } else {
          throw new Error('编辑时缺少ID');
        }
        
        emit('success');
      } catch (error) {
        console.error('提交失败:', error);
        ElMessage.error('操作失败，请重试');
      }
    }
  });
};

// 提交对话框表单
const submitDialogForm = async () => {
  if (!dialogFormRef.value) return;
  
  await dialogFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        const submitData: {
          name: string;
          type: string;
          value: number;
          is_active: boolean;
          surcharge_type: string;
          subtype?: string;
          condition_description?: string;
          zone_values: Record<string, number>;
          product_id: string;
        } = {
          name: dialogForm.value.surcharge_type || '',
          type: 'fixed',
          value: dialogForm.value.value,
          is_active: dialogForm.value.is_active,
          surcharge_type: dialogForm.value.surcharge_type || '',
          subtype: dialogForm.value.subtype,
          condition_description: dialogForm.value.condition_description,
          zone_values: {},
          product_id: props.productId
        };
        
        // 为所有分区设置相同的价格
        zones.value.forEach(zone => {
          submitData.zone_values[zone.id] = dialogForm.value.value;
        });
        
        const apiData = convertToApiFormat(submitData);
        
        if (dialogMode.value === 'add') {
          await createSurcharge(apiData);
          ElMessage.success('添加成功');
        } else if (currentEditId.value) {
          await updateSurcharge(currentEditId.value, apiData);
          ElMessage.success('更新成功');
        } else {
          throw new Error('编辑时缺少ID');
        }
        
        dialogVisible.value = false;
        loadSurchargeData();
      } catch (error) {
        console.error('提交失败:', error);
        ElMessage.error('操作失败，请重试');
      } finally {
        submitting.value = false;
      }
    }
  });
};

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

// 从Excel导入
const importFromExcel = () => {
  ElMessage.info('Excel导入功能正在开发中');
};

// 更新分区价格直接
const updateZonePriceDirectly = async (row: SurchargeGroup, zone: string, price: number) => {
  try {
    // 确保zone_values存在
    if (!row.zone_values) {
      row.zone_values = {};
    }
    
    // 更新价格
    row.zone_values[zone] = price;
    
    // 如果有ID且不是模拟数据，则调用API更新
    if (row.id && !String(row.id).startsWith('mock')) {
      // 构建更新数据
      const updateData = {
        id: row.id,
        surcharge_type: row.surcharge_type,
        subtype: row.subtype,
        condition_description: row.condition_description,
        is_active: row.is_active,
        zone_values: row.zone_values,
        product_id: props.productId
      };
      
      // 调用API
      const apiData = convertToApiFormat(updateData);
      await updateSurcharge(String(row.id), apiData);
    }
    
    ElMessage.success('更新价格成功');
  } catch (error) {
    console.error('更新价格失败:', error);
    ElMessage.error('更新价格失败');
  }
};

// 更新附加费字段
const updateSurchargeField = async (row: SurchargeGroup) => {
  try {
    // 如果有ID且不是模拟数据，则调用API更新
    if (row.id && !String(row.id).startsWith('mock')) {
      // 构建更新数据
      const updateData = {
        id: row.id,
        surcharge_type: row.surcharge_type,
        subtype: row.subtype,
        condition_description: row.condition_description,
        is_active: row.is_active,
        zone_values: row.zone_values,
        product_id: props.productId
      };
      
      // 调用API
      const apiData = convertToApiFormat(updateData);
      await updateSurcharge(String(row.id), apiData);
    }
    
    ElMessage.success('更新成功');
  } catch (error) {
    console.error('更新失败:', error);
    ElMessage.error('更新失败');
  }
};

// 应用批量设置
const applyBatchSettings = () => {
  const { zone, surchargeType, price } = batchSettings.value;
  
  surchargeGroups.value.forEach(row => {
    // 如果选择了特定附加费类型且与当前行不匹配，则跳过
    if (surchargeType !== 'ALL' && row.surcharge_type !== surchargeType) {
      return;
    }
    
    // 确保 zone_values 存在
    if (!row.zone_values) {
      row.zone_values = {};
    }
    
    // 如果选择了所有分区，则设置所有分区价格
    if (zone === 'ALL') {
      zones.value.forEach(z => {
        row.zone_values[z.id] = price;
      });
    } else {
      // 设置特定分区价格
      row.zone_values[zone] = price;
    }
  });
  
  ElMessage.success('批量设置成功');
};

// 重置批量设置
const resetBatchSettings = () => {
  batchSettings.value = {
    zone: 'ALL',
    surchargeType: 'ALL',
    price: 0
  };
};

// 打开分区管理对话框
const openZoneManagerDialog = () => {
  zoneManagerDialogVisible.value = true;
};

// 保存分区修改
const saveZoneChanges = (zone: Zone) => {
  const index = zones.value.findIndex(z => z.id === zone.id);
  
  if (index !== -1) {
    zones.value[index].name = zone.name;
    ElMessage.success('分区保存成功');
  }
};

// 添加新分区
const addNewZone = () => {
  const newZoneId = `Zone${zones.value.length + 1}`;
  zones.value.push({ id: newZoneId, name: newZoneId, isNew: true });
  
  // 为所有附加费添加新分区的价格
  surchargeGroups.value.forEach(group => {
    if (!group.zone_values) {
      group.zone_values = {};
    }
    group.zone_values[newZoneId] = 0;
  });
  
  ElMessage.success('添加新分区成功');
};

// 删除分区
const deleteZone = (zone: Zone) => {
  if (zones.value.length <= 1) {
    ElMessage.warning('至少需要保留一个分区');
    return;
  }
  
  ElMessageBox.confirm(
    `确定要删除分区 "${zone.name}" 吗?`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    const index = zones.value.findIndex(z => z.id === zone.id);
    
    if (index !== -1) {
      zones.value.splice(index, 1);
      
      // 从所有附加费中移除该分区的价格
      surchargeGroups.value.forEach(group => {
        if (group.zone_values && group.zone_values[zone.id]) {
          delete group.zone_values[zone.id];
        }
      });
      
      ElMessage.success('分区删除成功');
    }
  }).catch(() => {
    // 取消删除
  });
};

// 初始化分区数据
const initZones = () => {
  // 设置默认分区
  zones.value = [
    { id: '1', name: 'Zone1' },
    { id: '2', name: 'Zone2' },
    { id: '3', name: 'Zone3' },
    { id: '4', name: 'Zone4' },
    { id: '5', name: 'Zone5' }
  ];
  console.log('初始化默认分区:', zones.value);
};

// 按附加费类型分组数据
const groupSurchargesByType = (data: any[]): SurchargeGroup[] => {
  if (!data || data.length === 0) {
    console.log('无数据用于分组');
    return [];
  }
  
  console.log('分组数据类型:', data.map(item => typeof item));
  
  return data.map(item => {
    // 创建zone_values对象，将zone_fees中的字段映射到zone_values中
    const zone_values: Record<string, number> = {};
    
    if (item.zone_fees) {
      Object.keys(item.zone_fees).forEach(key => {
        // 转换keyName: zone1 -> Zone1
        const zoneKey = 'Zone' + key.substring(4);
        zone_values[zoneKey] = parseFloat(item.zone_fees[key]) || 0;
      });
    }
    
    return {
      id: item.id || `temp-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      surcharge_type: item.surcharge_type || item.name || '',
      subtype: item.subtype || item.sub_type || '',
      condition_description: item.condition_description || item.condition_desc || '',
      is_active: item.is_active !== false,
      zone_values: zone_values,
      actions: true
    };
  });
};
</script>

<style scoped>
.list-mode {
  margin-bottom: 20px;
}

.table-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.matrix-table-container {
  margin-bottom: 20px;
}

.surcharge-cell {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.zone-price-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
}

.zone-price-cell .edit-btn {
  visibility: visible;
  margin-left: 5px;
}

.action-buttons {
  display: flex;
  gap: 5px;
}

.always-visible {
  visibility: visible !important;
}

.zone-header {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.zone-header-actions {
  position: absolute;
  right: 5px;
  display: flex;
}

.matrix-note-container {
  margin-top: 15px;
}

.matrix-note {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.el-form {
  max-width: 500px;
  margin: 0 auto;
}

.el-input-number {
  width: 180px;
  margin-right: 10px;
}

.edit-btn, .delete-btn {
  padding: 4px;
}

.batch-settings {
  padding: 10px;
}

.batch-settings h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #606266;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 8px;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f5f7fa;
}

:deep(.el-input-number.is-controls-right .el-input-number__decrease, 
       .el-input-number.is-controls-right .el-input-number__increase) {
  line-height: 15px;
}

:deep(.el-table th) {
  background-color: #f0f2f5;
  color: #606266;
  font-weight: bold;
}

:deep(.el-table--border th) {
  border-right: 1px solid #EBEEF5;
}

:deep(.el-table .cell) {
  padding-left: 8px;
  padding-right: 8px;
}

.zone-manager {
  padding: 20px;
}

.zone-manager-header {
  margin-bottom: 20px;
}

.zone-manager-actions {
  display: flex;
  gap: 10px;
}
</style> 