<template>
  <div class="fuel-rate-management">
    <!-- 全局错误提示 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>燃油费率管理</h2>
          <el-button type="primary" @click="handleCreate">
            <el-icon><plus /></el-icon>
            新增费率
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :inline="true" :model="queryParams">
          <el-form-item label="服务商">
            <el-select v-model="queryParams.provider_id" placeholder="选择服务商" clearable>
              <el-option
                v-for="item in providerOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="queryParams.status" placeholder="选择状态" clearable>
              <el-option label="启用" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 费率列表 -->
      <el-table :data="tableData" border style="width: 100%" v-loading="loading">
        <el-table-column prop="rate_id" label="费率ID" width="120" />
        <el-table-column prop="provider_name" label="服务商" width="120" />
        <el-table-column prop="rate_value" label="费率" width="120">
          <template #default="{ row }">
            {{ row.rate_value }}%
          </template>
        </el-table-column>
        <el-table-column prop="effective_date" label="生效日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.effective_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="expiration_date" label="失效日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.expiration_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button
                :type="row.status ? 'danger' : 'success'"
                link
                @click="handleToggleStatus(row)"
              >
                {{ row.status ? '禁用' : '启用' }}
              </el-button>
              <el-button
                type="danger"
                link
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @update:page-size="loadData"
          @update:current-page="loadData"
        />
      </div>
    </el-card>

    <!-- 费率表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '新增燃油费率' : '编辑燃油费率'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="服务商" prop="provider">
          <el-select
            v-model="form.provider"
            placeholder="选择服务商"
            style="width: 100%"
          >
            <el-option
              v-for="item in providerOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="费率值" prop="rate_value">
          <el-input-number
            v-model="form.rate_value"
            :min="0"
            :max="100"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="生效日期" prop="effective_date">
          <el-date-picker
            v-model="form.effective_date"
            type="date"
            placeholder="选择生效日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="失效日期" prop="expiration_date">
          <el-date-picker
            v-model="form.expiration_date"
            type="date"
            placeholder="选择失效日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="选填，请输入费率描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="form.status"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted, nextTick } from 'vue';
  import { ElMessage, ElMessageBox } from 'element-plus';
  import { Plus } from '@element-plus/icons-vue';
  import type { FormInstance, FormRules } from 'element-plus';
  import {
    getFuelRates,
    createFuelRate,
    updateFuelRate,
    deleteFuelRate,
    toggleFuelRateStatus,
  } from '@/api/fuel/fuelRates';
  import type {
    FuelRate,
    FuelRateCreateRequest,
    FuelRateUpdateRequest,
    ProviderType,
  } from '@/api/fuel/fuelRates';
  import type { PaginatedResponse } from '@/api/core';
  import dayjs from 'dayjs';
  // import { getServiceProviders } from '@/api/core/service-providers';
  
  // 手动模拟服务商数据
  const mockProviders: ProviderType[] = [
    { id: 1, name: '默认服务 商', code: 'DEFAULT', status: true },
    { id: 2, name: 'FedEx', code: 'FEDEX', status: true },
    { id: 3, name: 'UPS', code: 'UPS', status: true },
    { id: 4, name: 'DHL', code: 'DHL', status: true },
  ];

  // 表单数据接口
  interface FuelRateForm extends Omit<FuelRateCreateRequest, 'provider'> {
    rate_id?: string;
    provider: number;
    description?: string;
  }

  // 搜索表单
  const queryParams = reactive({
    provider_id: '',
    status: '',
    page: 1,
    page_size: 10,
    dateRange: [] as string[]
  });

  // 表格数据
  const loading = ref(false);
  const tableData = ref<FuelRate[]>([]);
  const total = ref(0);
  const page = ref(1);
  const pageSize = ref(10);
  const providerOptions = ref<ProviderType[]>([]);

  // 对话框控制
  const dialogVisible = ref(false);
  const dialogType = ref<'create' | 'edit'>('create');
  const formRef = ref<FormInstance>();

  // 表单数据
  const form = reactive<FuelRateForm>({
    provider: 0,
    rate_value: 0,
    effective_date: '',
    expiration_date: '',
    status: true,
    description: '',
  });

  // 表单验证规则
  const rules: FormRules = {
    provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
    rate_value: [{ required: true, message: '请输入费率值', trigger: 'blur' }, { type: 'number', min: 0, max: 100, message: '费率值必须在0到100之间', trigger: 'blur' }],
    effective_date: [{ required: true, message: '请选择生效日期', trigger: 'change' }],
    expiration_date: [{ required: true, message: '请选择失效日期', trigger: 'change' }],
    description: [
      { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' },
    ],
  };

  const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD');
  };

  const formatDateTime = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
  };

  // 加载数据
  const loadData = async () => {
    loading.value = true;
    try {
      const params: any = {
        page: page.value,
        page_size: pageSize.value,
        provider_id: queryParams.provider_id,
        status: queryParams.status === '' ? undefined : 
               queryParams.status === 'true' ? true :
               queryParams.status === 'false' ? false : undefined
      };

      // 如果有日期范围，添加日期过滤
      if (queryParams.dateRange?.length === 2) {
        params.effective_date_after = formatDate(queryParams.dateRange[0]);
        params.effective_date_before = formatDate(queryParams.dateRange[1]);
      } else {
        params.current_only = true;
      }

      console.log('请求参数:', params);
      const response = await getFuelRates(params);
      console.log('燃油费率数据:', response);
      
      // 直接使用响应数据，不再进行复杂的类型检查
      if (Array.isArray(response)) {
        // 如果响应是数组，直接使用
        tableData.value = response;
        total.value = response.length;
      } else {
        // 否则将表格清空
        console.error('API返回的数据格式不是数组:', response);
        tableData.value = [];
        total.value = 0;
        ElMessage.warning('返回数据格式异常');
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      tableData.value = [];
      total.value = 0;
      ElMessage.error('加载数据失败');
    } finally {
      loading.value = false;
    }
  };

  // 搜索方法
  const handleQuery = () => {
    page.value = 1;
    loadData();
  };

  // 重置搜索
  const resetQuery = () => {
    queryParams.provider_id = '';
    queryParams.status = '';
    queryParams.dateRange = [];
    page.value = 1;
    loadData();
  };

  // 新增费率
  const handleCreate = () => {
    dialogType.value = 'create';
    dialogVisible.value = true;
    if (formRef.value) {
      formRef.value.resetFields();
    }
  };

  // 编辑费率
  const handleEdit = (row: FuelRate) => {
    dialogType.value = 'edit';
    dialogVisible.value = true;
    
    // 清空表单
    if (formRef.value) {
      formRef.value.resetFields();
    }
    
    // 使用新的字段名称映射，并确保rate_value是数字类型
    Object.assign(form, {
      rate_id: row.rate_id,
      provider: Number(row.provider),
      rate_value: Number(row.rate_value), // 确保转换为数字
      effective_date: row.effective_date,
      expiration_date: row.expiration_date,
      status: row.status,
      description: row.description || ''
    });
  };

  // 删除费率
  const handleDelete = async (row: FuelRate) => {
    try {
      await ElMessageBox.confirm('确认要删除该费率吗？', '提示', {
        type: 'warning',
      });
      await deleteFuelRate(String(row.rate_id));
      ElMessage.success('删除成功');
      loadData();
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('删除失败');
      }
    }
  };

  // 切换状态
  const handleToggleStatus = async (row: FuelRate) => {
    try {
      const response = await toggleFuelRateStatus(String(row.rate_id));
      // 从response.data中获取状态
      row.status = response.data.status;
      ElMessage.success(`状态已切换为${row.status ? '启用' : '禁用'}`);
    } catch (error) {
      ElMessage.error('状态切换失败');
    }
  };

  // 提交表单
  const submitForm = async () => {
    if (!formRef.value) return;

    try {
      await formRef.value.validate();
      
      // 格式化日期为YYYY-MM-DD格式
      const formatISODate = (date: string | Date) => {
        return dayjs(date).format('YYYY-MM-DD');
      };
      
      const submitData: FuelRateCreateRequest = {
        provider: Number(form.provider),
        rate_value: form.rate_value,
        effective_date: formatISODate(form.effective_date),
        expiration_date: formatISODate(form.expiration_date),
        status: form.status
      };

      // 如果有描述信息，添加到提交数据中
      if (form.description) {
        submitData.description = form.description;
      }

      if (dialogType.value === 'create') {
        await createFuelRate(submitData);
        ElMessage.success('新增成功');
        // 新增成功后，回到第一页
        page.value = 1;
      } else if (form.rate_id) {
        await updateFuelRate(form.rate_id, submitData);
        ElMessage.success('编辑成功');
      }
      dialogVisible.value = false;
      // 确保在对话框关闭后再次刷新数据
      setTimeout(() => {
        loadData();
      }, 100);
    } catch (error: any) {
      console.error('提交失败:', error);
      // 提取更友好的错误信息
      let errorMessage = dialogType.value === 'create' ? '新增失败' : '编辑失败';
      
      // 处理特定的后端错误信息
      if (error?.response?.data?.message) {
        const serverError = error.response.data.message;
        
        // 针对特定错误提供更友好的提示
        if (serverError.includes("old_rate")) {
          errorMessage = '无法创建费率历史记录，后端数据处理错误，请联系管理员';
        } else {
          errorMessage = `${errorMessage}: ${serverError}`;
        }
      }
      
      ElMessage.error(errorMessage);
    }
  };

  // 加载服务商选项
  const loadProviderOptions = async () => {
    try {
      // 注意：服务商API未实现，使用模拟数据
      // const response = await getServiceProviders();
      // providerOptions.value = response.data.map((item: {id: number, name: string}) => ({
      //   id: item.id,
      //   name: item.name
      // }));
      
      // 使用模拟数据
      providerOptions.value = mockProviders;
    } catch (error) {
      console.error('获取服务商列表失败:', error);
      ElMessage.error('获取服务商列表失败，使用默认数据');
      // 发生错误时使用模拟数据
      providerOptions.value = mockProviders;
    }
  };

  onMounted(() => {
    loadProviderOptions();
    loadData();
  });
</script>

<style scoped>
  .fuel-rate-management {
    padding: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-bar {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    text-align: right;
  }

  .dialog-footer {
    text-align: right;
  }
</style>
