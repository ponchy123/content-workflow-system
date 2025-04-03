<template>
  <!-- 列表模式 - 表格视图 -->
  <div v-if="props.mode === 'list'" class="list-mode">
    <div class="table-actions">
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon>添加旺季附加费
      </el-button>
      <el-button @click="importFromExcel">
        <el-icon><Upload /></el-icon>从Excel导入
      </el-button>
    </div>

    <el-table :data="tableData" border stripe style="width: 100%" v-loading="loading">
      <el-table-column label="附加费类型" prop="surcharge_type" width="280px">
        <template #default="scope">
          <div>
            <el-input
              v-model="scope.row.name"
              size="small"
              placeholder="输入附加费名称"
              style="width: 120px; margin-right: 5px;"
              @change="() => handleDataChange(scope.row)"
            />
            <el-input
              v-model="scope.row.surcharge_type"
              size="small"
              placeholder="输入类型代码"
              style="width: 140px;"
              @change="() => handleDataChange(scope.row)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="开始日期" prop="start_date" width="120px">
        <template #default="scope">
          <el-date-picker
            v-model="scope.row.start_date"
            type="date"
            size="small"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 120px"
            @change="() => handleDataChange(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="结束日期" prop="end_date" width="120px">
        <template #default="scope">
          <el-date-picker
            v-model="scope.row.end_date"
            type="date"
            size="small"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 120px"
            @change="() => handleDataChange(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="费用金额" prop="fee_amount" width="120px">
        <template #default="scope">
          <div class="fee-input">
            <span class="currency-symbol">$</span>
            <el-input-number 
              v-model="scope.row.fee_amount" 
              size="small" 
              :precision="2" 
              :step="0.01" 
              :min="0"
              :controls="false"
              style="width: 90px"
              @change="() => handleDataChange(scope.row)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120px">
        <template #default="scope">
          <el-button size="small" type="danger" @click="deleteRow(scope.row)" plain>
            <el-icon><Delete /></el-icon>删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="matrix-note-container">
      <p class="matrix-note">旺季附加费在指定的日期范围内生效,适用于所有的分区。此类附加费一般在高峰期启用,以应对运输量增加带来的额外成本。</p>
    </div>
  </div>

  <!-- 表单模式 -->
  <el-form v-else ref="formRef" :model="form" :rules="rules" label-width="120px">
    <el-form-item label="名称" prop="name">
      <el-input v-model="form.name" placeholder="请输入旺季费用名称" />
    </el-form-item>
    <el-form-item label="开始日期" prop="start_date">
      <el-date-picker
        v-model="form.start_date"
        type="date"
        placeholder="选择开始日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
    </el-form-item>
    <el-form-item label="结束日期" prop="end_date">
      <el-date-picker
        v-model="form.end_date"
        type="date"
        placeholder="选择结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
      />
    </el-form-item>
    <el-form-item label="费用金额" prop="fee_amount">
      <el-input-number v-model="form.fee_amount" :precision="2" :step="0.01" :min="0" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="submitForm">确定</el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
  </el-form>

  <!-- 添加/编辑对话框 -->
  <el-dialog
    :title="dialogMode === 'add' ? '添加旺季附加费' : '编辑旺季附加费'"
    v-model="dialogVisible"
    width="500px"
  >
    <el-form ref="dialogFormRef" :model="dialogForm" :rules="rules" label-width="120px">
      <el-form-item label="附加费类型" prop="surcharge_type">
        <div style="display: flex; gap: 10px; align-items: center;">
          <el-input 
            v-model="dialogForm.name" 
            placeholder="输入附加费名称" 
            style="width: 170px;"
          />
          <el-input 
            v-model="dialogForm.surcharge_type" 
            placeholder="输入类型代码" 
            style="width: 170px;"
          />
        </div>
        <div class="form-item-tip">请分别输入附加费名称和类型代码</div>
      </el-form-item>
      <el-form-item label="开始日期" prop="start_date">
        <el-date-picker
          v-model="dialogForm.start_date"
          type="date"
          placeholder="选择开始日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      <el-form-item label="结束日期" prop="end_date">
        <el-date-picker
          v-model="dialogForm.end_date"
          type="date"
          placeholder="选择结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      <el-form-item label="费用金额" prop="fee_amount">
        <el-input-number v-model="dialogForm.fee_amount" :precision="2" :step="0.01" :min="0" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitDialogForm" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Plus, Upload, Edit, Delete } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import { createSeasonalFee, updateSeasonalFee, deleteSeasonalFee, getSeasonalFees, updateProductPeakSeasonSurcharges } from '@/api/products';
import type { PeakSeasonSurcharge } from '@/types/product';
import axios from 'axios';

interface SeasonalFeeForm {
  id?: string;
  name: string;
  surcharge_type: string;
  start_date: string;
  end_date: string;
  fee_amount: number;
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
    type: Object as () => SeasonalFeeForm | SeasonalFeeForm[],
    default: () => ({
      name: '',
      surcharge_type: '',
      start_date: '',
      end_date: '',
      fee_amount: 0
    })
  }
});

const emit = defineEmits(['success', 'cancel', 'save']);

const formRef = ref<FormInstance>();
const dialogFormRef = ref<FormInstance>();
const form = ref<SeasonalFeeForm>({
  name: '',
  surcharge_type: '',
  start_date: '',
  end_date: '',
  fee_amount: 0
});

// 对话框相关
const dialogVisible = ref(false);
const dialogMode = ref<'add' | 'edit'>('add');
const dialogForm = ref<SeasonalFeeForm>({
  name: '',
  surcharge_type: '',
  start_date: '',
  end_date: '',
  fee_amount: 0
});

// 表格数据
const tableData = ref<SeasonalFeeForm[]>([]);
const loading = ref(false);
const submitting = ref(false);
const currentEditId = ref<string | number | undefined>(undefined);

// 添加类型映射表
const TYPE_MAP: Record<string, string> = {
  'ADDITIONAL_HANDLING': 'OVERWEIGHT',
  'OVERSIZE_COMMERCIAL': 'OVERSIZE',
  'OVERSIZE_RESIDENTIAL': 'RESIDENTIAL',
  'OVERWEIGHT': 'OVERWEIGHT',
  'OVERSIZE': 'OVERSIZE',
  'RESIDENTIAL': 'RESIDENTIAL'
};

// 类型显示名称
const TYPE_DISPLAY: Record<string, string> = {
  'ADDITIONAL_HANDLING': '附加处理费',
  'OVERSIZE_COMMERCIAL': '超大尺寸商业件',
  'OVERSIZE_RESIDENTIAL': '超大尺寸住宅件',
  'OVERWEIGHT': '附加处理费',
  'OVERSIZE': '超大尺寸商业件',
  'RESIDENTIAL': '超大尺寸住宅件'
};

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  surcharge_type: [{ required: true, message: '请选择附加费类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [
    { required: true, message: '请选择结束日期', trigger: 'change' },
    { 
      validator: (rule, value, callback) => {
        if (value && form.value.start_date && value < form.value.start_date) {
          callback(new Error('结束日期不能早于开始日期'));
        } else {
          callback();
        }
      }, 
      trigger: 'change' 
    }
  ],
  fee_amount: [{ required: true, message: '请输入费用金额', trigger: 'blur' }]
};

// 监听props.data的变化
watch(() => props.data, (newData) => {
  console.log('props.data发生变化:', newData);
  if (props.mode === 'list') {
    loadTableData();
  } else if (props.mode === 'edit' && newData) {
    console.log('编辑模式数据更新:', newData);
    form.value = { ...newData as SeasonalFeeForm };
  }
}, { deep: true });

// 添加自动重试加载数据的功能
const retryLoadData = () => {
  console.log('尝试重新加载数据');
  const maxRetries = 3;
  let retryCount = 0;
  
  const tryLoad = () => {
    if (tableData.value.length === 0 && retryCount < maxRetries) {
      console.log(`第${retryCount + 1}次重试加载数据`);
      loadTableData();
      retryCount++;
      setTimeout(tryLoad, 1000);
    }
  };
  
  tryLoad();
};

// 修改onMounted钩子
onMounted(() => {
  console.log('SeasonalFeeForm组件已挂载');
  console.log('当前模式:', props.mode);
  console.log('接收到的数据:', props.data);
  
  if (props.mode === 'list') {
    loadTableData();
    // 如果首次加载失败，启动重试机制
    if (tableData.value.length === 0) {
      retryLoadData();
    }
  } else if (props.mode === 'edit' && props.data) {
    console.log('编辑模式，设置表单数据:', props.data);
    form.value = { ...props.data as SeasonalFeeForm };
  }
});

// 加载表格数据
const loadTableData = async () => {
  loading.value = true;
  try {
    let data: SeasonalFeeForm[] = [];
    
    // 尝试从API获取数据
    if (props.productId) {
      console.log('【调试】尝试从API获取旺季附加费数据，产品ID:', props.productId);
      try {
        // 直接使用 axios 发起请求，获取更详细的错误信息
        const token = localStorage.getItem('access_token');
        const apiUrl = `/api/v1/products/peak-season-surcharges/by_product/?product_id=${encodeURIComponent(props.productId)}&_t=${Date.now()}`;
        console.log('【调试】旺季附加费请求URL:', apiUrl);
        
        const apiResponse = await axios({
          url: apiUrl,
          method: 'get',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        
        console.log('【调试】旺季附加费API响应状态:', apiResponse.status);
        console.log('【调试】旺季附加费API响应数据:', apiResponse.data);
        
        if (apiResponse.data && Array.isArray(apiResponse.data) && apiResponse.data.length > 0) {
          console.log('成功从API获取旺季附加费数据:', apiResponse.data.length, '条记录');
          
          // 转换数据格式为表格所需的格式，确保fee_amount是数字类型
          const processedData = apiResponse.data.map((item: any) => {
            // 处理fee_amount，确保是数字
            let feeAmount: number = 5.00; // 默认值
            if (item.fee_amount !== undefined && item.fee_amount !== null) {
              if (typeof item.fee_amount === 'number') {
                feeAmount = item.fee_amount;
              } else if (typeof item.fee_amount === 'string') {
                feeAmount = parseFloat(item.fee_amount);
                if (isNaN(feeAmount)) feeAmount = 5.00;
              }
            }
            
            console.log(`处理数据项 ${item.id} 的fee_amount: ${feeAmount} (${typeof feeAmount})`);
            
            return {
              id: item.id || `temp-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
              name: item.name || '旺季附加费',
              surcharge_type: item.surcharge_type || 'PEAK_SEASON',
              start_date: item.start_date || '',
              end_date: item.end_date || '',
              fee_amount: feeAmount // 使用处理后的数值
            };
          });
          
          tableData.value = processedData;
          console.log('【调试】转换后的表格数据:', tableData.value);
        } else {
          console.warn('【警告】API返回的旺季附加费数据为空或格式不正确，使用模拟数据');
          
          // 使用模拟数据
          data = [
            {
              id: 'mock-1',
              name: '旺季附加费',
              surcharge_type: 'PEAK_SEASON',
              start_date: '2023-11-01',
              end_date: '2024-01-15',
              fee_amount: 3.75
            },
            {
              id: 'mock-2',
              name: '假日附加费',
              surcharge_type: 'HOLIDAY_SURCHARGE',
              start_date: '2023-12-15',
              end_date: '2023-12-31',
              fee_amount: 5.95
            }
          ];
          
          // 转换数据格式为表格所需的格式
          tableData.value = data;
          
          // 显示提示
          ElMessage.warning('API未返回数据，已加载模拟数据');
        }
      } catch (apiError: any) {
        console.error('【错误】从API获取旺季附加费数据失败:', apiError);
        console.error('错误详情:', apiError.response ? `状态码 ${apiError.response.status}` : '无响应');
        console.error('错误消息:', apiError.message);
        
        // 使用模拟数据
        data = [
          {
            id: 'mock-error-1',
            name: '旺季附加费(模拟)',
            surcharge_type: 'PEAK_SEASON',
            start_date: '2023-11-01',
            end_date: '2024-01-15',
            fee_amount: 3.75
          },
          {
            id: 'mock-error-2',
            name: '假日附加费(模拟)',
            surcharge_type: 'HOLIDAY_SURCHARGE',
            start_date: '2023-12-15',
            end_date: '2023-12-31',
            fee_amount: 5.95
          }
        ];
        
        // 转换数据格式为表格所需的格式
        tableData.value = data;
        
        // 显示错误提示
        ElMessage.error(`获取旺季附加费数据失败: ${apiError.message}`);
      }
      
      // 打印数据验证
      if (tableData.value.length > 0) {
        console.log('【数据检查】表格数据第一条:', tableData.value[0]);
        console.log('fee_amount类型:', typeof tableData.value[0].fee_amount);
      }
      
      loading.value = false;
      
      // 强制刷新视图
      tableData.value = [...tableData.value];
      
      return;
    }
    
    // 从props中获取数据
    if (Array.isArray(props.data) && props.data.length > 0) {
      console.log('接收到数组数据:', props.data);
      data = props.data;
    } else if (props.data && typeof props.data === 'object' && Object.keys(props.data).length > 0) {
      console.log('接收到单个对象数据:', props.data);
      data = [props.data as SeasonalFeeForm];
    } else {
      console.log('没有接收到有效数据，使用模拟数据');
      // 模拟数据
      data = [
        {
          id: '1',
          name: '旺季附加费',
          surcharge_type: 'PEAK_SEASON',
          start_date: '2023-11-01',
          end_date: '2024-01-15',
          fee_amount: 3.75
        },
        {
          id: '2',
          name: '假日附加费',
          surcharge_type: 'HOLIDAY_SURCHARGE',
          start_date: '2023-12-15',
          end_date: '2023-12-31',
          fee_amount: 5.95
        },
        {
          id: '3',
          name: '春节附加费',
          surcharge_type: 'CHINESE_NEW_YEAR',
          start_date: '2024-02-10',
          end_date: '2024-02-24',
          fee_amount: 4.50
        }
      ];
    }
    
    // 转换数据格式为表格所需的格式
    tableData.value = data.map(item => ({
      id: item.id,
      name: item.name || '旺季附加费',
      surcharge_type: item.surcharge_type || 'PEAK_SEASON',
      start_date: item.start_date || '',
      end_date: item.end_date || '',
      fee_amount: typeof item.fee_amount === 'number' ? item.fee_amount : parseFloat(item.fee_amount) || 0
    }));
    console.log('【调试】设置旺季附加费表格数据:', tableData.value);
  } catch (error) {
    console.error('加载旺季附加费数据失败:', error);
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 打开添加对话框
const openAddDialog = () => {
  dialogMode.value = 'add';
  dialogForm.value = {
    name: '旺季附加费',
    surcharge_type: 'PEAK_SEASON',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(new Date().setMonth(new Date().getMonth() + 2)).toISOString().split('T')[0],
    fee_amount: 5.00
  };
  dialogVisible.value = true;
};

// 编辑行
const editRow = (row: SeasonalFeeForm) => {
  // 标准化类型代码
  const standardType = TYPE_MAP[row.surcharge_type] || row.surcharge_type;
  
  dialogMode.value = 'edit';
  dialogForm.value = { 
    ...row,
    surcharge_type: standardType // 使用标准化的类型
  };
  currentEditId.value = row.id?.toString() || '';
  dialogVisible.value = true;
};

// 删除行
const deleteRow = (row: SeasonalFeeForm) => {
  ElMessageBox.confirm(
    `确定要删除旺季附加费 "${row.name}" 吗?`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      if (row.id) {
        await deleteSeasonalFee(row.id);
        ElMessage.success('删除成功');
        loadTableData();
      }
    } catch (error) {
      console.error('删除失败:', error);
      ElMessage.error('删除失败');
    }
  }).catch(() => {
    // 取消删除
  });
};

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const { id, ...restForm } = form.value;
        const submitData: Partial<PeakSeasonSurcharge> = {
          ...restForm,
          product_id: props.productId,
          status: true
        };
        
        if (props.mode === 'add') {
          await createSeasonalFee(submitData);
          ElMessage.success('添加成功');
        } else if (props.mode === 'edit' && !Array.isArray(props.data) && props.data?.id) {
          await updateSeasonalFee(props.data.id, submitData);
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
        console.log('提交表单数据:', dialogForm.value);
        
        // 确保fee_amount是数字类型
        const fee_amount = typeof dialogForm.value.fee_amount === 'number' 
          ? dialogForm.value.fee_amount 
          : parseFloat(dialogForm.value.fee_amount) || 5.00;
        
        const { id, ...restForm } = dialogForm.value;
        const submitData: Partial<PeakSeasonSurcharge> = {
          ...restForm,
          fee_amount, // 确保使用处理后的数字类型
          product_id: props.productId,
          status: true
        };
        
        console.log('处理后的提交数据:', submitData);
        console.log('fee_amount类型:', typeof submitData.fee_amount);
        
        if (dialogMode.value === 'add') {
          await createSeasonalFee(submitData);
          ElMessage.success('添加成功');
        } else if (currentEditId.value) {
          await updateSeasonalFee(currentEditId.value, submitData);
          ElMessage.success('更新成功');
        } else {
          throw new Error('编辑时缺少ID');
        }
        
        dialogVisible.value = false;
        loadTableData();
        emit('save');
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

// 处理数据变化
const handleDataChange = async (row: SeasonalFeeForm) => {
  console.log('数据变化:', row);
  try {
    // 确保fee_amount是数字类型
    const fee_amount = typeof row.fee_amount === 'number' 
      ? row.fee_amount 
      : parseFloat(row.fee_amount) || 5.00;
      
    // 如果是已有数据（有ID），则自动保存
    if (row.id) {
      // 确保所有必填字段存在
      if (!row.surcharge_type || !row.start_date || !row.end_date) {
        console.error('缺少必填字段，无法保存');
        ElMessage.error('保存失败：缺少必填字段(附加费类型、开始日期或结束日期)');
        // 重新加载数据以还原用户的更改
        loadTableData();
        return;
      }

      const { id, ...restRow } = row;
      const submitData: Partial<PeakSeasonSurcharge> = {
        ...restRow,
        fee_amount, // 使用处理后的数字类型
        product_id: props.productId,
        status: true
      };
      
      console.log('自动保存数据:', submitData);
      console.log('fee_amount类型:', typeof submitData.fee_amount);
      
      // 显示一个处理中的消息
      const loadingMessage = ElMessage({
        message: '保存中...',
        type: 'info',
        duration: 0
      });
      
      // 使用updateProductPeakSeasonSurcharges代替updateSeasonalFee
      // 因为后端API使用批量更新方式，需要保留其他记录
      try {
        // 先获取所有现有记录
        const existingData = await getSeasonalFees(props.productId);
        let allRecords = Array.isArray(existingData) ? [...existingData] : [];
        
        // 找到并替换当前编辑的记录
        const indexToUpdate = allRecords.findIndex(item => item.id === id || item.pss_id === id);
        if (indexToUpdate >= 0) {
          allRecords[indexToUpdate] = {...allRecords[indexToUpdate], ...submitData};
        } else {
          // 如果找不到现有记录，添加为新记录
          allRecords.push(submitData as PeakSeasonSurcharge);
        }
        
        // 发送完整数据集进行批量更新
        await updateProductPeakSeasonSurcharges(props.productId, allRecords);
      } catch (innerError) {
        console.error('批量更新失败，尝试单条更新:', innerError);
        await updateSeasonalFee(id, submitData);
      }
      
      // 关闭处理中的消息
      loadingMessage.close();
      ElMessage.success('保存成功');
      
      // 刷新数据
      loadTableData();
      
      // 通知父组件数据已保存
      emit('save');
    }
  } catch (error) {
    console.error('自动保存失败:', error);
    ElMessage.error('保存失败，请稍后重试');
    // 重新加载数据以还原用户的更改
    loadTableData();
  }
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
}

.el-date-picker {
  width: 100%;
}

.code-text {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.surcharge-type-code {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.fee-input {
  display: flex;
  align-items: center;
}

.currency-symbol {
  margin-right: 5px;
  color: #67c23a;
}

:deep(.el-input-number .el-input__inner) {
  color: #67c23a;
  font-weight: bold;
}
</style> 