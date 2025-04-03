<!-- 偏远地区管理 -->
<template>
  <div class="remote-areas">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <h2 class="card-title">偏远地区管理</h2>
          <div class="header-buttons">
            <el-button type="info" @click="handlePreviewTemplate">模板预览</el-button>
            <el-button type="primary" @click="downloadTemplate">下载模板</el-button>
            <input
              type="file"
              ref="fileInputRef"
              accept=".xlsx,.xls"
              style="display: none"
              @change="handleFileChange"
            />
            <el-button type="success" @click="triggerFileUpload">导入数据</el-button>
            <div class="el-upload__tip">仅支持xlsx、xls格式</div>
            <el-button type="primary" @click="handleAdd">添加偏远地区</el-button>
          </div>
        </div>
      </template>

      <!-- 查询和搜索区域 -->
      <el-row :gutter="20">
        <!-- 快速查询模块 -->
        <el-col :span="12">
          <el-card class="query-card" shadow="hover">
            <template #header>
              <div class="query-header">
                <span class="query-title">快速查询偏远地区</span>
              </div>
            </template>
            <el-form :inline="false" :model="queryForm" class="query-form">
              <el-form-item label="服务商" required>
                <el-select v-model="queryForm.provider_id" placeholder="请选择服务商" style="width: 100%">
                  <el-option
                    v-for="item in providerOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="始发地邮编" required>
                <el-input v-model="queryForm.origin_zip" placeholder="请输入始发地邮编" />
              </el-form-item>
              <el-form-item label="邮编" required>
                <el-input v-model="queryForm.zip_code" placeholder="请输入偏远地区邮编" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleQueryRemoteArea" :loading="queryLoading" icon="Search" class="query-button">查询偏远地区</el-button>
              </el-form-item>
            </el-form>
            <div v-if="queryResult" class="query-result">
              <el-alert
                :title="`查询结果: ${queryResult.remote_level ? '偏远等级 ' + queryResult.remote_level : '未找到匹配的偏远地区'}`"
                :type="queryResult.remote_level ? 'success' : 'warning'"
                :description="queryResult.remote_level ? `始发地邮编: ${queryResult.origin_zip}, 偏远地区邮编: ${queryResult.zip_code}` : '请检查输入的邮编是否正确'"
                show-icon
                :closable="false"
              />
            </div>
          </el-card>
        </el-col>

        <!-- 搜索区域 -->
        <el-col :span="12">
          <el-card class="search-card" shadow="hover">
            <template #header>
              <div class="search-header">
                <span class="search-title">高级搜索</span>
                <div class="search-buttons">
                  <el-button type="primary" size="small" @click="handleSearch" icon="Search">搜索</el-button>
                  <el-button size="small" @click="resetSearch" icon="RefreshRight">重置</el-button>
                </div>
              </div>
            </template>
            <el-form :inline="false" :model="searchForm" class="search-form">
              <el-form-item label="服务商">
                <el-select v-model="searchForm.provider_id" placeholder="请选择服务商" clearable style="width: 100%">
                  <el-option
                    v-for="item in providerOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="始发地邮编">
                <el-input v-model="searchForm.origin_zip" placeholder="请输入始发地邮编" clearable />
              </el-form-item>
              <el-form-item label="偏远地区邮编">
                <el-input v-model="searchForm.zip_code" placeholder="请输入偏远地区邮编" clearable />
              </el-form-item>
              <el-form-item label="偏远等级">
                <el-input v-model="searchForm.remote_level" placeholder="请输入偏远等级" clearable />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>

      <!-- 数据表格 -->
      <div class="table-container">
        <el-table 
          :data="remoteAreas" 
          border 
          stripe 
          v-loading="loading"
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa' }"
        >
          <el-table-column prop="id" label="ID" width="100" align="center" />
          <el-table-column prop="provider_id" label="服务商" width="120" align="center">
            <template #default="{ row }">
              {{ getProviderDisplayName(row) }}
            </template>
          </el-table-column>
          <el-table-column prop="origin_zip" label="始发地邮编" width="150" align="center" />
          <el-table-column prop="zip_code" label="偏远地区邮编" width="150" align="center" />
          <el-table-column prop="remote_level" label="偏远等级" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getRemoteLevelType(row.remote_level)">
                {{ row.remote_level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="180" align="center">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right" align="center">
            <template #default="{ row }">
              <el-button-group>
                <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
                <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          background
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加偏远地区' : '编辑偏远地区'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item label="服务商" prop="provider_id">
          <el-select v-model="form.provider_id" placeholder="请选择服务商" style="width: 100%">
            <el-option
              v-for="item in providerOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="始发地邮编" prop="origin_zip">
          <el-input v-model="form.origin_zip" />
        </el-form-item>
        <el-form-item label="偏远地区邮编" prop="zip_code">
          <el-input v-model="form.zip_code" />
        </el-form-item>
        <el-form-item label="偏远等级" prop="remote_level">
          <el-input v-model="form.remote_level" placeholder="请输入偏远等级，与产品附加费条件描述保持一致" />
          <div class="form-tip" style="font-size: 12px; color: #909399; margin-top: 5px;">
            注意：偏远等级应与产品的"偏远地区附加费"条件描述一致，支持自定义文本以精确匹配产品附加费
          </div>
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
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance } from 'element-plus';
import { getRemoteAreas, getRemoteArea, createRemoteArea, updateRemoteArea, deleteRemoteArea, checkRemoteAreaExists } from '@/api/postal/postal';
import type { RemoteArea, RemoteAreaCreateRequest, RemoteAreaUpdateRequest } from '@/types/postal';
import { getServiceProviders } from '@/api/core/provider';
import type { ServiceProvider } from '@/types/core';
import * as XLSX from 'xlsx';
import { getRemoteLevelType } from '@/utils/postal';

const remoteAreas = ref<RemoteArea[]>([]);
const loading = ref(false);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const dialogVisible = ref(false);
const dialogType = ref<'add' | 'edit'>('add');
const formRef = ref<FormInstance>();
const providerOptions = ref<ServiceProvider[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);

// 构建符合类型的表单
const form = reactive<RemoteAreaCreateRequest & Partial<RemoteArea> & RemoteAreaUpdateRequest>({
  provider_id: 0,
  origin_zip: '',
  zip_code: '',
  remote_level: '一级偏远',
  id: 0
});

const rules = {
  provider_id: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  origin_zip: [{ required: true, message: '请输入始发地邮编', trigger: 'blur' }],
  zip_code: [{ required: true, message: '请输入偏远地区邮编', trigger: 'blur' }],
  remote_level: [{ required: true, message: '请输入偏远等级', trigger: 'blur' }]
};

// 搜索表单
const searchForm = reactive({
  page: 1,
  page_size: 10,
  provider_id: undefined as number | undefined,
  origin_zip: '',
  zip_code: '',
  remote_level: undefined as string | undefined
});

// 查询表单
const queryForm = reactive({
  provider_id: undefined as number | undefined,
  origin_zip: '',
  zip_code: ''
});

// 查询结果
const queryResult = ref<RemoteArea | null>(null);
const queryLoading = ref(false);

// 添加记录原始表单内容的变量
const originalForm = reactive({
  provider_id: 0,
  origin_zip: '',
  zip_code: '',
  remote_level: ''
});

onMounted(() => {
  console.log('偏远地区管理页面加载...');
  // 确保先加载服务商数据
  loadProviders().then(() => {
    console.log('服务商数据加载完成，服务商列表:', providerOptions.value);
    // 加载服务商后再加载偏远地区数据
    fetchRemoteAreas();
  }).catch(error => {
    console.error('加载服务商数据失败:', error);
    // 即使服务商加载失败，也尝试加载偏远地区数据
    fetchRemoteAreas();
  });
});

const fetchRemoteAreas = async () => {
  loading.value = true;
  try {
    console.log('开始获取偏远地区数据...');
    const response = await getRemoteAreas({
      page: currentPage.value,
      page_size: pageSize.value,
      provider_id: searchForm.provider_id,
      origin_zip: searchForm.origin_zip || undefined,
      zip_code: searchForm.zip_code || undefined,
      remote_level: searchForm.remote_level
    });
    
    console.log('API原始响应数据:', response);
    
    // 从response.data获取真正的API响应数据
    const apiData = response.data || response;
    console.log('处理后的API数据:', apiData);
    
    // 首先尝试直接访问results数组（Django REST框架常见格式）
    if (apiData.results && Array.isArray(apiData.results)) {
      console.log('使用results字段');
      remoteAreas.value = apiData.results;
      total.value = apiData.count || 0;
    } 
    // 然后尝试items字段（标准PaginatedResponse格式）
    else if (apiData.items && Array.isArray(apiData.items)) {
      console.log('使用items字段');
      remoteAreas.value = apiData.items;
      total.value = apiData.total || 0;
    } 
    // 检查是否为数组
    else if (Array.isArray(apiData)) {
      console.log('API返回数组格式数据');
      remoteAreas.value = apiData;
      total.value = apiData.length;
    }
    // 检查是否有data字段（某些API标准）
    else if (apiData.data && Array.isArray(apiData.data)) {
      console.log('使用data字段');
      remoteAreas.value = apiData.data;
      total.value = apiData.total || apiData.count || apiData.data.length || 0;
    }
    // 检查响应本身是否可能包含数组字段
    else if (apiData && typeof apiData === 'object' && Object.keys(apiData).length > 0) {
      console.log('尝试使用响应对象自身');
      // 查找可能的数组字段
      const possibleArrayField = Object.entries(apiData).find(
        ([_, value]) => Array.isArray(value) && value.length > 0
      );
      
      if (possibleArrayField) {
        console.log(`使用找到的数组字段: ${possibleArrayField[0]}`);
        remoteAreas.value = possibleArrayField[1] as RemoteArea[];
        total.value = remoteAreas.value.length;
      } else if (Object.keys(apiData).includes('id')) {
        // 如果响应是单个对象且没有明显的数组字段但有id
        console.log('响应似乎是单个记录，将作为单个项目处理');
        remoteAreas.value = [apiData as RemoteArea];
        total.value = 1;
      } else {
        console.error('无法在响应中找到有效数据数组:', apiData);
        remoteAreas.value = [];
        total.value = 0;
      }
    } else {
      console.error('API返回的数据格式不正确或为空:', apiData);
      remoteAreas.value = [];
      total.value = 0;
    }
    
    console.log('处理后的表格数据:', remoteAreas.value);
    console.log('总记录数:', total.value);
    
  } catch (error) {
    console.error('获取偏远地区列表失败:', error);
    ElMessage.error('获取偏远地区列表失败');
    remoteAreas.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
    // 增加数据检查和处理
    if (remoteAreas.value.length > 0) {
      console.log('检查第一行数据的provider_id和provider:', 
        remoteAreas.value[0].provider_id, 
        remoteAreas.value[0].provider);
        
      // 确保所有记录都有provider_id字段
      remoteAreas.value = remoteAreas.value.map(area => {
        if (!area.provider_id && area.provider && area.provider.id) {
          return {
            ...area,
            provider_id: Number(area.provider.id)
          };
        }
        return area;
      });
    }
    checkTableData();
  }
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  fetchRemoteAreas();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchRemoteAreas();
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  form.provider_id = 0;
  form.origin_zip = '';
  form.zip_code = '';
  form.remote_level = '一级偏远';
  form.id = 0;
};

const handleAdd = () => {
  dialogType.value = 'add';
  resetForm();
  dialogVisible.value = true;
};

const handleEdit = async (row: RemoteArea) => {
  dialogType.value = 'edit';
  resetForm();
  dialogVisible.value = true;
  
  console.log('开始编辑记录:', row);
  // 确保填入ID
  form.id = row.id;
  
  try {
    console.log('正在获取详细数据，ID:', row.id);
    const response = await getRemoteArea(row.id);
    console.log('获取到的详细数据:', response);
    
    if (!response) {
      throw new Error('获取的详细数据为空');
    }
    
    // 如果provider_id为空但provider对象存在
    if (!response.provider_id && response.provider && response.provider.id) {
      response.provider_id = Number(response.provider.id);
    }
    
    // 确保将provider_id转换为数字类型
    if (response.provider_id || response.provider_id === 0) {
      response.provider_id = Number(response.provider_id);
    } else {
      console.warn('警告: provider_id 在响应中不存在或为空，使用行数据中的provider_id');
      // 尝试从原始行数据中获取provider_id
      if (row.provider_id || row.provider_id === 0) {
        response.provider_id = Number(row.provider_id);
      } else if (row.provider && row.provider.id) {
        response.provider_id = Number(row.provider.id);
      } else {
        console.error('无法获取provider_id，设置为默认值0');
        response.provider_id = 0;
      }
    }
    
    // 复制数据到表单
    Object.assign(form, response);
    
    // 保存原始表单数据，用于比较
    originalForm.provider_id = form.provider_id;
    originalForm.origin_zip = form.origin_zip || '';
    originalForm.zip_code = form.zip_code || '';
    originalForm.remote_level = form.remote_level || '';
    
    console.log('成功加载编辑数据:', form);
    console.log('保存的原始数据:', originalForm);
  } catch (error) {
    console.error('获取偏远地区详情失败:', error);
    
    // 尝试使用行数据填充表单
    form.id = row.id;
    form.provider_id = row.provider_id || (row.provider?.id ? Number(row.provider.id) : 0);
    form.origin_zip = row.origin_zip || '';
    form.zip_code = row.zip_code || '';
    form.remote_level = row.remote_level || '';
    
    // 保存原始表单数据
    originalForm.provider_id = form.provider_id;
    originalForm.origin_zip = form.origin_zip;
    originalForm.zip_code = form.zip_code;
    originalForm.remote_level = form.remote_level;
    
    console.log('使用行数据填充表单:', form);
    ElMessage.error('获取偏远地区详情失败，使用表格数据进行编辑');
  }
};

const handleDelete = (row: RemoteArea) => {
  ElMessageBox.confirm('确定要删除该偏远地区吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      console.log('准备删除记录，ID:', row.id);
      await deleteRemoteArea(row.id);
      ElMessage.success('删除成功');
      fetchRemoteAreas();
    } catch (error: any) {
      console.error('删除偏远地区失败:', error);
      
      // 获取错误详情
      let errorMsg = '删除失败';
      if (error.response) {
        const status = error.response.status;
        if (status === 404) {
          errorMsg = '要删除的记录不存在，可能已被他人删除';
        } else if (status === 403) {
          errorMsg = '没有删除此记录的权限';
        } else if (status === 500) {
          errorMsg = '服务器错误，请联系管理员';
        } else if (error.response.data) {
          // 尝试从响应中获取详细错误信息
          const errorData = error.response.data;
          if (typeof errorData === 'string') {
            errorMsg = errorData;
          } else if (errorData.detail) {
            errorMsg = errorData.detail;
          } else if (errorData.message) {
            errorMsg = errorData.message;
          }
        }
      } else if (error.message && error.message.includes('Network Error')) {
        errorMsg = '网络错误，请检查网络连接';
      }
      
      ElMessage.error(errorMsg);
    }
  }).catch(() => {
    // 用户取消删除操作，不做处理
  });
};

const submitForm = async () => {
  if (!formRef.value) return;
  
  try {
    // 手动检查必填字段
    if (!form.provider_id) {
      ElMessage.warning('请选择服务商');
      return;
    }
    if (!form.origin_zip) {
      ElMessage.warning('请输入始发地邮编');
      return;
    }
    if (!form.zip_code) {
      ElMessage.warning('请输入偏远地区邮编');
      return;
    }
    if (!form.remote_level) {
      ElMessage.warning('请输入偏远等级');
      return;
    }
    
    // 在添加新记录前检查是否已存在
    if (dialogType.value === 'add') {
      const exists = await checkRemoteAreaExists(
        form.provider_id,
        form.origin_zip,
        form.zip_code
      );
      
      if (exists) {
        ElMessage.warning('此服务商、始发地邮编和偏远地区邮编的组合已存在');
        return;
      }
      
      await createRemoteArea({
        provider_id: form.provider_id,
        origin_zip: form.origin_zip,
        zip_code: form.zip_code,
        remote_level: form.remote_level
      });
      ElMessage.success('添加成功');
    } else {
      if (!form.id) {
        ElMessage.error('ID不能为空');
        return;
      }
      
      // 检查更新后的组合是否与其他记录冲突
      if (form.provider_id !== originalForm.provider_id || 
          form.origin_zip !== originalForm.origin_zip || 
          form.zip_code !== originalForm.zip_code) {
        const exists = await checkRemoteAreaExists(
          form.provider_id,
          form.origin_zip,
          form.zip_code,
          form.id  // 传入当前编辑记录的ID，以排除自身
        );
        
        if (exists) {
          ElMessage.warning('此服务商、始发地邮编和偏远地区邮编的组合已存在');
          return;
        }
      }
      
      await updateRemoteArea(form.id, {
        provider_id: form.provider_id,
        origin_zip: form.origin_zip,
        zip_code: form.zip_code,
        remote_level: form.remote_level
      });
      ElMessage.success('更新成功');
    }
    dialogVisible.value = false;
    fetchRemoteAreas();
  } catch (error: any) {
    console.error('操作失败:', error);
    
    // 处理后端返回的错误信息
    let errorMsg = dialogType.value === 'add' ? '添加失败' : '更新失败';
    
    // 提取API错误信息
    if (error?.response?.data) {
      const errorData = error.response.data;
      
      if (typeof errorData === 'string') {
        errorMsg = errorData;
      } else if (errorData.detail) {
        errorMsg = errorData.detail;
      } else if (errorData.message) {
        // 检查唯一性错误
        if (errorData.message.includes('唯一集合')) {
          errorMsg = '此服务商、始发地邮编和偏远地区邮编的组合已存在';
        } else {
          try {
            // 尝试解析JSON错误消息
            const messageObj = JSON.parse(errorData.message.replace(/'/g, '"'));
            if (messageObj.non_field_errors) {
              errorMsg = messageObj.non_field_errors[0];
            } else if (messageObj.zip_code) {
              errorMsg = `邮编错误: ${messageObj.zip_code[0]}`;
            } else if (messageObj.origin_zip) {
              errorMsg = `始发地邮编错误: ${messageObj.origin_zip[0]}`;
            }
          } catch (e) {
            // 直接使用错误消息
            errorMsg = errorData.message;
          }
        }
      } else if (errorData.zip_code) {
        errorMsg = `邮编错误: ${errorData.zip_code[0]}`;
      } else if (errorData.origin_zip) {
        errorMsg = `始发地邮编错误: ${errorData.origin_zip[0]}`;
      }
    }
    
    ElMessage.error(errorMsg);
  }
};

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '';
  const date = new Date(dateTime);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// 加载服务商数据
const loadProviders = async () => {
  try {
    const response = await getServiceProviders({});
    providerOptions.value = response.results;
  } catch (error) {
    console.error('获取服务商列表失败:', error);
    ElMessage.error('获取服务商列表失败');
  }
};

// 获取服务商名称
const getProviderName = (providerId: number) => {
  const provider = providerOptions.value.find(item => item.id === providerId);
  return provider ? provider.name : `${providerId}`;
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  fetchRemoteAreas();
};

// 重置搜索条件
const resetSearch = () => {
  searchForm.provider_id = undefined;
  searchForm.origin_zip = '';
  searchForm.zip_code = '';
  searchForm.remote_level = undefined;
  handleSearch();
};

// 查询偏远地区
const handleQueryRemoteArea = async () => {
  // 表单验证
  if (!queryForm.provider_id) {
    ElMessage.warning('请选择服务商');
    return;
  }
  if (!queryForm.origin_zip) {
    ElMessage.warning('请输入始发地邮编');
    return;
  }
  if (!queryForm.zip_code) {
    ElMessage.warning('请输入偏远地区邮编');
    return;
  }

  queryLoading.value = true;
  try {
    // 使用过滤条件查询
    const response = await getRemoteAreas({
      provider_id: queryForm.provider_id,
      origin_zip: queryForm.origin_zip,
      zip_code: queryForm.zip_code,
      page: 1,
      page_size: 1
    });
    
    console.log('查询偏远地区响应:', response);
    
    // 从response.data获取真正的API响应数据
    const apiData = response.data || response;
    console.log('处理后的查询数据:', apiData);
    
    let foundRecord: RemoteArea | null = null;
    
    if (apiData === null || apiData === undefined) {
      foundRecord = null;
    } else if (Array.isArray(apiData)) {
      foundRecord = apiData.length > 0 ? apiData[0] : null;
    } else if (typeof apiData === 'object') {
      if (apiData.results && Array.isArray(apiData.results)) {
        foundRecord = apiData.results.length > 0 ? apiData.results[0] : null;
      } else if (apiData.items && Array.isArray(apiData.items)) {
        foundRecord = apiData.items.length > 0 ? apiData.items[0] : null;
      } else if (apiData.data && Array.isArray(apiData.data)) {
        foundRecord = apiData.data.length > 0 ? apiData.data[0] : null;
      } else {
        // 查找可能的数组字段
        const possibleArrayField = Object.entries(apiData).find(
          ([_, value]) => Array.isArray(value) && value.length > 0
        );
        
        if (possibleArrayField) {
          const arrayValue = possibleArrayField[1] as Array<any>;
          foundRecord = arrayValue.length > 0 ? arrayValue[0] : null;
        } else if (Object.keys(apiData).includes('id')) {
          // 如果响应包含ID字段，可能是单个对象
          foundRecord = apiData as RemoteArea;
        } else {
          foundRecord = null;
        }
      }
    } else {
      foundRecord = null;
    }
    
    if (foundRecord) {
      queryResult.value = foundRecord;
      console.log('找到匹配记录:', queryResult.value);
    } else {
      queryResult.value = { remote_level: '' } as RemoteArea;
      ElMessage.warning('未找到匹配的偏远地区');
    }
  } catch (error) {
    console.error('查询偏远地区失败:', error);
    ElMessage.error('查询偏远地区失败');
    queryResult.value = null;
  } finally {
    queryLoading.value = false;
  }
};

// 处理文件上传
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target && target.files) {
    const file = target.files[0];
    if (file) {
      // 检查文件类型
      const allowedTypes = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ];
      const allowedExtensions = ['.xlsx', '.xls'];
      
      // 检查文件扩展名
      const fileName = file.name.toLowerCase();
      const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
      
      if (!allowedTypes.includes(file.type) && !hasValidExtension) {
        ElMessage.error('请上传Excel格式的文件(.xlsx或.xls)');
        if (fileInputRef.value) {
          fileInputRef.value.value = '';
        }
        return;
      }

      // 检查文件大小（限制为10MB）
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        ElMessage.error('文件大小不能超过10MB');
        if (fileInputRef.value) {
          fileInputRef.value.value = '';
        }
        return;
      }

      try {
        // 显示上传中状态
        const loadingMessage = ElMessage({
          message: '正在上传文件，请稍候...',
          type: 'info',
          duration: 0,
          showClose: true
        });
        
        console.log('开始上传文件:', file.name, '文件类型:', file.type, '文件大小:', file.size);
        
        // 使用XMLHttpRequest上传
        const formData = new FormData();
        formData.append('file', file);
        
        // 从localStorage获取token
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        
        if (!token) {
          loadingMessage.close();
          ElMessage.error('请先登录后再进行导入操作');
          return;
        }
        
        try {
          const xhr = new XMLHttpRequest();
          
          // 设置进度事件
          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              const percentComplete = Math.round((event.loaded / event.total) * 100);
              console.log(`上传进度: ${percentComplete}%`);
            }
          };
          
          // 使用Promise处理上传逻辑
          const uploadPromise = new Promise((resolve, reject) => {
            xhr.onload = function() {
              if (xhr.status >= 200 && xhr.status < 300) {
                let response;
                try {
                  response = JSON.parse(xhr.responseText);
                } catch (e) {
                  response = {
                    data: xhr.responseText,
                    status: 'success'
                  };
                }
                console.log('上传成功，响应:', response);
                resolve(response);
              } else {
                console.error('上传失败，状态码:', xhr.status);
                let errorMessage = '上传失败';
                try {
                  const errorResponse = JSON.parse(xhr.responseText);
                  errorMessage = errorResponse.message || errorResponse.detail || '上传失败';
                } catch (e) {
                  errorMessage = xhr.responseText || `上传失败，状态码：${xhr.status}`;
                }
                reject(new Error(errorMessage));
              }
            };
            
            xhr.onerror = function() {
              console.error('请求错误');
              reject(new Error('网络错误，请检查网络连接'));
            };
            
            // 使用PUT方法，不是POST
            xhr.open('POST', '/api/v1/postcodes/import-remote-areas/', true);
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.send(formData);
          });
          
          // 等待上传完成
          const response = await uploadPromise;
          
          // 处理成功响应
          loadingMessage.close();
          ElMessage.success('数据导入成功');
          
          // 重新加载列表
          fetchRemoteAreas();
        } catch (error: any) {
          loadingMessage.close();
          console.error('文件上传失败:', error);
          ElMessage.error(error.message || '文件上传失败');
        }
      } catch (error: any) {
        console.error('文件处理失败:', error);
        ElMessage.error(error.message || '文件处理失败');
      } finally {
        // 重置文件输入框
        if (fileInputRef.value) {
          fileInputRef.value.value = '';
        }
      }
    }
  }
};

const triggerFileUpload = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

// 获取服务商显示名称，处理不同的数据格式
const getProviderDisplayName = (row: any): string => {
  console.log('获取服务商显示名称，行数据:', row);
  
  // 检查provider对象
  if (row.provider && typeof row.provider === 'object') {
    if (row.provider.name) {
      return row.provider.name;
    } else if (row.provider.id || row.provider.id === 0) {
      // 通过ID查找服务商名称
      const provider = providerOptions.value.find(p => p.id === Number(row.provider.id));
      if (provider) {
        return provider.name;
      }
    }
  }
  
  // 检查provider_name字段
  if (row.provider_name) {
    return row.provider_name;
  }
  
  // 检查provider_id字段
  if (row.provider_id || row.provider_id === 0) {
    // 通过ID查找服务商名称
    const provider = providerOptions.value.find(p => p.id === Number(row.provider_id));
    if (provider) {
      return provider.name;
    }
    return `服务商 ${row.provider_id}`;
  }
  
  return '未知服务商';
};

// 添加调试函数以检查表格数据
const checkTableData = () => {
  if (remoteAreas.value.length > 0) {
    console.log('检查表格第一行数据:', remoteAreas.value[0]);
    console.log('服务商字段值:', getProviderDisplayName(remoteAreas.value[0]));
  } else {
    console.log('表格数据为空');
  }
};

// 处理模板预览
const handlePreviewTemplate = () => {
  ElMessageBox.alert(
    `<div class="template-preview">
      <h3 style="text-align: center; margin-bottom: 20px; color: #303133;">偏远地区导入模板格式</h3>
      <p style="margin-bottom: 15px; color: #606266;">请按照以下格式准备Excel文件:</p>
      <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        <thead>
          <tr style="background-color: #f5f7fa; height: 40px;">
            <th style="text-align: center; min-width: 100px;">服务商</th>
            <th style="text-align: center; min-width: 100px;">始发地邮编</th>
            <th style="text-align: center; min-width: 120px;">偏远地区邮编</th>
            <th style="text-align: center; min-width: 250px;">偏远等级</th>
          </tr>
        </thead>
        <tbody>
          <tr style="height: 36px;">
            <td style="text-align: center;">FedEx</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">200000</td>
            <td style="text-align: center;">Commercial(FedEx Ground)</td>
          </tr>
          <tr style="height: 36px;">
            <td style="text-align: center;">FedEx</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">300000</td>
            <td style="text-align: center;">Extended Commercial(FedEx Ground)</td>
          </tr>
          <tr style="height: 36px;">
            <td style="text-align: center;">FedEx</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">400000</td>
            <td style="text-align: center;">一级偏远</td>
          </tr>
          <tr style="height: 36px;">
            <td style="text-align: center;">FedEx</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">500000</td>
            <td style="text-align: center;">商业地址偏远地区配送</td>
          </tr>
        </tbody>
      </table>
      <p style="margin-top: 15px; margin-bottom: 10px; color: #606266; font-weight: bold;">字段说明:</p>
      <ul style="color: #606266; padding-left: 20px; line-height: 1.8;">
        <li><b>服务商</b>: 填写服务商名称，如FedEx、UPS等，必须是系统中已存在的服务商</li>
        <li><b>始发地邮编</b>: 始发地邮编</li>
        <li><b>偏远地区邮编</b>: 偏远地区邮编</li>
        <li><b>偏远等级</b>: 偏远等级，可以是任何文本描述，系统会智能匹配产品中的偏远地区附加费条件描述。示例值：
          <ul style="margin-top: 5px;">
            <li>英文描述：Commercial(FedEx Ground)、Extended Residential(FedEx Ground)</li>
            <li>中文描述：一级偏远、商业地址偏远地区配送、极偏远住宅地址</li>
            <li>自定义文本：只要与产品附加费中的条件描述含有相同关键词即可</li>
          </ul>
        </li>
      </ul>
      <div style="margin-top: 20px; padding: 12px; background-color: #f0f9eb; border-radius: 4px; border-left: 4px solid #67c23a;">
        <p style="margin: 0; color: #67c23a; font-weight: bold;">提示</p>
        <p style="margin: 5px 0 0; color: #606266;">导入前请确保数据格式正确，且服务商名称在系统中存在。偏远等级越接近产品中的"偏远地区附加费"条件描述，匹配越精确。系统使用智能匹配算法，即使文本不完全一致，也能根据关键词进行匹配。</p>
      </div>
    </div>`,
    '偏远地区导入模板',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭',
      customClass: 'template-preview-dialog',
      callback: (action: string) => {
        // 可以添加下载模板的逻辑
      }
    }
  );
};

// 下载模板
const downloadTemplate = () => {
  // 创建模板数据
  const templateData = [
    ['服务商', '始发地邮编', '偏远地区邮编', '偏远等级'],
    ['FedEx', '100000', '200000', 'Commercial(FedEx Ground)'],
    ['FedEx', '100000', '300000', 'Extended Commercial(FedEx Ground)'],
    ['UPS', '100000', '400000', '一级偏远'],
    ['DHL', '100000', '500000', '商业地址偏远地区配送'],
    ['FedEx', '100000', '600000', 'Residential(FedEx Ground)'],
    ['UPS', '100000', '700000', '极偏远 -DAS Remote Resi']
  ];

  // 创建工作簿
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(templateData);

  // 设置列宽
  const colWidth = [
    {wch: 15}, // 服务商列宽
    {wch: 15}, // 始发地邮编列宽
    {wch: 15}, // 偏远地区邮编列宽
    {wch: 25}  // 偏远等级列宽，增加宽度以适应更长的描述
  ];
  ws['!cols'] = colWidth;

  // 添加到工作簿
  XLSX.utils.book_append_sheet(wb, ws, '偏远地区模板');
  
  // 导出文件
  XLSX.writeFile(wb, '偏远地区导入模板.xlsx');
  
  ElMessage.success('模板已下载');
};
</script>

<style scoped>
.remote-areas {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 100px);
}

.main-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}

.card-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-buttons {
  display: flex;
  gap: 12px;
}

.query-card, .search-card {
  height: 100%;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.query-header {
  padding: 8px 0;
}

.query-title, .search-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.query-form, .search-form {
  width: 100%;
}

.query-button {
  width: 100%;
}

.query-result {
  margin-top: 16px;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-buttons {
  display: flex;
  gap: 8px;
}

.table-container {
  margin-top: 16px;
  margin-bottom: 20px;
  background-color: #fff;
  border-radius: 4px;
  padding: 1px; /* 避免边缘重叠 */
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  padding: 10px 0;
}

:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset;
}
</style>

<!-- 全局样式：必须放在非scoped的style中才能影响MessageBox组件 -->
<style>
/* 自定义模板预览对话框样式 */
.template-preview-dialog {
  width: 750px !important;
  max-width: 90% !important;
}

.template-preview-dialog .el-message-box__content {
  padding: 20px;
}

.template-preview-dialog .el-message-box__header {
  padding-top: 15px;
  padding-bottom: 15px;
  background-color: #f5f7fa;
}

.template-preview-dialog .el-message-box__title {
  font-size: 18px;
  font-weight: 600;
}

.template-preview-dialog .el-message-box__headerbtn {
  font-size: 20px;
}

.template-preview-dialog .el-button--primary {
  padding: 10px 20px;
}
</style> 