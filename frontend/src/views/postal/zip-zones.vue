<!-- 邮编分区管理 -->
<template>
  <div class="zip-zones">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <h2 class="card-title">邮编分区管理</h2>
          <div class="header-buttons">
            <el-button type="info" @click="handlePreviewTemplate">模板预览</el-button>
            <el-button type="primary" @click="downloadTemplate">下载模板</el-button>
            <div class="file-upload-container">
              <input
                type="file"
                ref="fileInputRef"
                accept=".xlsx,.xls"
                style="display: none"
                @change="handleFileChange"
              />
              <el-button type="success" @click="triggerFileUpload">导入数据</el-button>
              <div class="el-upload__tip">仅支持xlsx、xls格式</div>
            </div>
            <el-button type="primary" @click="handleAdd">添加分区</el-button>
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
                <span class="query-title">快速查询分区</span>
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
              <el-form-item label="目的地邮编" required>
                <el-input v-model="queryForm.dest_zip" placeholder="请输入目的地邮编" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleQueryZone" :loading="queryLoading" icon="Search" class="query-button">查询分区</el-button>
              </el-form-item>
            </el-form>
            <div v-if="queryResult" class="query-result">
              <el-alert
                :title="`查询结果: ${queryResult.zone_number ? '分区 ' + queryResult.zone_number : '未找到匹配的分区'}`"
                :type="queryResult.zone_number ? 'success' : 'warning'"
                :description="queryResult.zone_number ? `目的地邮编范围: ${queryResult.dest_zip_start} - ${queryResult.dest_zip_end}` : '请检查输入的邮编是否正确'"
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
              <el-form-item label="分区号码">
                <el-input v-model="searchForm.zone_number" placeholder="请输入分区号码" clearable />
              </el-form-item>
              <el-form-item label="目的地邮编">
                <el-input v-model="searchForm.dest_zip" placeholder="请输入目的地邮编" clearable />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>

      <!-- 数据表格 -->
      <div class="table-container">
        <el-table 
          :data="zipZones" 
          border 
          stripe 
          v-loading="loading"
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa' }"
        >
          <el-table-column prop="id" label="ID" width="100" align="center" />
          <el-table-column prop="provider_id" label="服务商" width="120" align="center">
            <template #default="{ row }">
              {{ row.provider?.name || getProviderName(row.provider_id) }}
            </template>
          </el-table-column>
          <el-table-column prop="origin_zip" label="始发地邮编" width="150" align="center" />
          <el-table-column prop="dest_zip_start" label="目的地邮编起始" width="150" align="center" />
          <el-table-column prop="dest_zip_end" label="目的地邮编终止" width="150" align="center" />
          <el-table-column prop="zone_number" label="分区号码" width="100" align="center" />
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
      :title="dialogType === 'add' ? '添加邮编分区' : '编辑邮编分区'"
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
        <el-form-item label="目的地邮编起始" prop="dest_zip_start">
          <el-input v-model="form.dest_zip_start" />
        </el-form-item>
        <el-form-item label="目的地邮编终止" prop="dest_zip_end">
          <el-input v-model="form.dest_zip_end" />
        </el-form-item>
        <el-form-item label="分区号码" prop="zone_number">
          <el-input v-model.number="form.zone_number" />
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
import axios from 'axios';
import { getZipZones, getZipZone, createZipZone, updateZipZone, deleteZipZone, queryZoneByZip, checkZipZoneExists, importZipZones } from '@/api/postal/postal';
import type { ZipZone, ZipZoneCreateRequest, ZipZoneUpdateRequest, ZipZoneListParams } from '@/types/postal';
import { getServiceProviders } from '@/api/core/provider';
import type { ServiceProvider } from '@/types/core';
import * as XLSX from 'xlsx';
import { useUserStore } from '@/stores/user';

// 定义导入响应的接口
interface ImportResponse {
  data: {
    status?: string;
    message?: string;
    [key: string]: any;
  };
}

const zipZones = ref<ZipZone[]>([]);
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
const form = reactive<ZipZoneCreateRequest & Partial<ZipZone> & ZipZoneUpdateRequest>({
  id: 0,
  provider_id: 0,
  origin_zip: '',
  dest_zip_start: '',
  dest_zip_end: '',
  zone_number: 0
});

const rules = {
  provider_id: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  origin_zip: [{ required: true, message: '请输入始发地邮编', trigger: 'blur' }],
  dest_zip_start: [{ required: true, message: '请输入目的地邮编起始', trigger: 'blur' }],
  dest_zip_end: [{ required: true, message: '请输入目的地邮编终止', trigger: 'blur' }],
  zone_number: [{ required: true, message: '请输入分区号码', trigger: 'blur' }]
};

// 搜索表单
const searchForm = reactive<ZipZoneListParams>({
  page: 1,
  page_size: pageSize.value,
  provider_id: undefined,
  origin_zip: '',
  zone_number: undefined,
  dest_zip: ''
});

// 查询表单
const queryForm = reactive({
  provider_id: undefined as number | undefined,
  origin_zip: '',
  dest_zip: ''
});

// 查询结果
const queryResult = ref<ZipZone | null>(null);
const queryLoading = ref(false);

onMounted(() => {
  fetchZipZones();
  loadProviders();
});

const fetchZipZones = async () => {
  loading.value = true;
  try {
    console.log('正在获取邮编分区列表，参数:', {
      page: currentPage.value,
      page_size: pageSize.value,
      provider_id: searchForm.provider_id,
      origin_zip: searchForm.origin_zip || undefined,
      zone_number: searchForm.zone_number,
      dest_zip: searchForm.dest_zip || undefined
    });
    
    const response = await getZipZones({
      page: currentPage.value,
      page_size: pageSize.value,
      provider_id: searchForm.provider_id,
      origin_zip: searchForm.origin_zip || undefined,
      zone_number: searchForm.zone_number,
      dest_zip: searchForm.dest_zip || undefined
    });
    
    console.log('获取邮编分区列表响应:', response);
    
    // 处理DRF标准分页响应格式
    if (response) {
      if (Array.isArray(response.results)) {
        // DRF格式
        zipZones.value = response.results;
        total.value = response.count || 0;
      } else if (Array.isArray(response)) {
        // 直接返回数组的情况
        zipZones.value = response;
        total.value = response.length;
      } else {
        console.error('无法识别的API响应格式:', response);
        zipZones.value = [];
        total.value = 0;
      }
    } else {
      console.error('无效的API响应:', response);
      zipZones.value = [];
      total.value = 0;
    }
    
    console.log('处理后的邮编分区列表:', zipZones.value, '总数:', total.value);
  } catch (error) {
    console.error('获取邮编分区列表失败:', error);
    ElMessage.error('获取邮编分区列表失败');
    zipZones.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  searchForm.page_size = size;
  fetchZipZones();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  searchForm.page = page;
  fetchZipZones();
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  form.id = 0;
  form.provider_id = 0;
  form.origin_zip = '';
  form.dest_zip_start = '';
  form.dest_zip_end = '';
  form.zone_number = 0;
};

const handleAdd = () => {
  dialogType.value = 'add';
  resetForm();
  dialogVisible.value = true;
};

const handleEdit = async (row: ZipZone) => {
  dialogType.value = 'edit';
  resetForm();
  dialogVisible.value = true;
  
  try {
    console.log('开始获取邮编分区详情，ID:', row.id);
    const zipZone = await getZipZone(row.id);
    console.log('获取到的邮编分区详情:', zipZone);
    
    // 确保数据正确映射到表单
    form.id = zipZone.id;
    form.provider_id = zipZone.provider_id || (zipZone.provider?.id as number);
    form.origin_zip = zipZone.origin_zip;
    form.dest_zip_start = zipZone.dest_zip_start;
    form.dest_zip_end = zipZone.dest_zip_end;
    form.zone_number = zipZone.zone_number;
    
    console.log('表单数据已更新:', form);
  } catch (error) {
    console.error('获取邮编分区详情失败:', error);
    ElMessage.error('获取邮编分区详情失败');
  }
};

const handleDelete = (row: ZipZone) => {
  ElMessageBox.confirm('确定要删除该邮编分区吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteZipZone(row.id);
      ElMessage.success('删除成功');
      fetchZipZones();
    } catch (error) {
      ElMessage.error('删除失败');
    }
  }).catch(() => {});
};

const submitForm = async () => {
  if (!formRef.value) return;
  
  try {
    // 验证表单
    await formRef.value.validate();
    
    // 转换分区号码为数字
    if (typeof form.zone_number === 'string') {
      form.zone_number = parseInt(form.zone_number, 10);
    }
    
    // 如果是添加操作
    if (dialogType.value === 'add') {
      try {
        // 先检查是否存在
        const exists = await checkZipZoneExists(
          form.provider_id,
          form.origin_zip,
          form.dest_zip_start,
          form.dest_zip_end,
          form.zone_number
        );
        
        if (exists) {
          ElMessage.warning('该服务商的始发地邮编、目的地邮编范围和分区号码组合已存在');
          return;
        }
        
        await createZipZone({
          provider_id: form.provider_id,
          origin_zip: form.origin_zip,
          dest_zip_start: form.dest_zip_start,
          dest_zip_end: form.dest_zip_end,
          zone_number: form.zone_number
        });
        ElMessage.success('添加成功');
        dialogVisible.value = false;
        fetchZipZones();
      } catch (error: any) {
        console.error('添加失败:', error);
        
        // 尝试提取详细错误信息
        let errorMsg = '添加失败';
        if (error.response?.data) {
          const errorData = error.response.data;
          console.log('错误响应数据:', errorData);
          
          // 检查是否是唯一性错误
          if (typeof errorData.message === 'string' && 
              (errorData.message.includes('唯一集合') || 
               errorData.message.includes('unique') || 
               errorData.message.includes('已存在'))) {
            errorMsg = '该服务商的始发地邮编、目的地邮编范围和分区号码组合已存在';
          } else if (errorData.message) {
            // 尝试解析更详细的错误消息
            try {
              // 处理可能被转义的JSON字符串
              const messageStr = errorData.message.replace(/'/g, '"');
              const messageObj = JSON.parse(messageStr);
              
              if (messageObj.non_field_errors) {
                errorMsg = messageObj.non_field_errors[0];
              } else {
                // 遍历可能的字段错误
                for (const field in messageObj) {
                  if (Array.isArray(messageObj[field]) && messageObj[field].length > 0) {
                    errorMsg = `${field}: ${messageObj[field][0]}`;
                    break;
                  }
                }
              }
            } catch (e) {
              // 如果解析失败，直接使用原始消息
              errorMsg = errorData.message;
            }
          } else if (errorData.detail) {
            errorMsg = errorData.detail;
          }
        }
        
        ElMessage.error(errorMsg);
      }
    } else {
      // 编辑操作
      try {
        // 先检查是否存在重复（排除自身）
        const exists = await checkZipZoneExists(
          form.provider_id,
          form.origin_zip,
          form.dest_zip_start,
          form.dest_zip_end,
          form.zone_number,
          form.id
        );
        
        if (exists) {
          ElMessage.warning('该服务商的始发地邮编、目的地邮编范围和分区号码组合已存在');
          return;
        }
        
        await updateZipZone(form.id!, {
          provider_id: form.provider_id,
          origin_zip: form.origin_zip,
          dest_zip_start: form.dest_zip_start,
          dest_zip_end: form.dest_zip_end,
          zone_number: form.zone_number
        });
        ElMessage.success('更新成功');
        dialogVisible.value = false;
        fetchZipZones();
      } catch (error: any) {
        console.error('更新失败:', error);
        
        // 提取错误信息，与添加部分类似
        let errorMsg = '更新失败';
        if (error.response?.data) {
          const errorData = error.response.data;
          
          // 检查是否是唯一性错误
          if (typeof errorData.message === 'string' && 
              (errorData.message.includes('唯一集合') || 
               errorData.message.includes('unique') || 
               errorData.message.includes('已存在'))) {
            errorMsg = '该服务商的始发地邮编、目的地邮编范围和分区号码组合已存在';
          } else if (errorData.message) {
            // 尝试解析更详细的错误消息
            try {
              // 处理可能被转义的JSON字符串
              const messageStr = errorData.message.replace(/'/g, '"');
              const messageObj = JSON.parse(messageStr);
              
              if (messageObj.non_field_errors) {
                errorMsg = messageObj.non_field_errors[0];
              } else {
                // 遍历可能的字段错误
                for (const field in messageObj) {
                  if (Array.isArray(messageObj[field]) && messageObj[field].length > 0) {
                    errorMsg = `${field}: ${messageObj[field][0]}`;
                    break;
                  }
                }
              }
            } catch (e) {
              // 如果解析失败，直接使用原始消息
              errorMsg = errorData.message;
            }
          } else if (errorData.detail) {
            errorMsg = errorData.detail;
          }
        }
        
        ElMessage.error(errorMsg);
      }
    }
  } catch (formError) {
    console.error('表单验证失败:', formError);
    ElMessage.error('请正确填写所有必填项');
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
  fetchZipZones();
};

// 重置搜索条件
const resetSearch = () => {
  searchForm.provider_id = undefined;
  searchForm.origin_zip = '';
  searchForm.zone_number = undefined;
  searchForm.dest_zip = '';
  handleSearch();
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
        
        try {
          // 使用importZipZones函数上传文件
          const response = await importZipZones(file) as ImportResponse;
          
          // 处理响应
          loadingMessage.close();
          console.log('文件上传成功，响应:', response);
          
          if (response && response.data && 'status' in response.data) {
            if (response.data.status === 'success') {
              ElMessage.success(response.data.message || '导入成功');
            } else if (response.data.status === 'error') {
              ElMessage.error(response.data.message || '导入失败');
            } else {
              ElMessage.success('导入成功');
            }
          } else {
            ElMessage.success('导入成功');
          }
          
          // 刷新数据列表
          fetchZipZones();
        } catch (error: any) {
          loadingMessage.close();
          console.error('文件上传失败:', error);
          
          // 提取错误信息
          let errorMsg = '导入失败';
          if (error.response) {
            console.error('错误响应:', error.response);
            const data = error.response.data;
            
            if (data && typeof data === 'object') {
              if (data.message) {
                errorMsg = data.message;
              } else if (data.detail) {
                errorMsg = data.detail;
              } else if (typeof data === 'string') {
                errorMsg = data;
              }
            } else if (typeof data === 'string') {
              errorMsg = data;
            }
            
            // 处理特定错误码
            if (error.response.status === 405) {
              errorMsg = '不支持的请求方法，请联系管理员检查API配置';
            } else if (error.response.status === 401) {
              errorMsg = '登录已过期，请重新登录';
            } else if (error.response.status === 500) {
              errorMsg = '服务器内部错误，请联系管理员';
            }
          } else if (error.message) {
            errorMsg = error.message;
          }
          
          ElMessage.error(errorMsg);
        }
      } catch (error: any) {
        console.error('处理文件上传过程中出错:', error);
        ElMessage.error(error.message || '导入过程发生错误');
      } finally {
        // 重置文件输入框
        if (fileInputRef.value) {
          fileInputRef.value.value = '';
        }
      }
    }
  }
};

// 触发文件上传点击
const triggerFileUpload = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

// 处理查询分区
const handleQueryZone = async () => {
  // 表单验证
  if (!queryForm.provider_id) {
    ElMessage.warning('请选择服务商');
    return;
  }
  if (!queryForm.origin_zip) {
    ElMessage.warning('请输入始发地邮编');
    return;
  }
  if (!queryForm.dest_zip) {
    ElMessage.warning('请输入目的地邮编');
    return;
  }

  queryLoading.value = true;
  try {
    const result = await queryZoneByZip(queryForm.provider_id, queryForm.origin_zip, queryForm.dest_zip);
    queryResult.value = result;
    if (!result?.zone_number) {
      ElMessage.warning('未找到匹配的分区信息');
    }
  } catch (error) {
    console.error('查询分区失败:', error);
    ElMessage.error('查询分区失败');
    queryResult.value = null;
  } finally {
    queryLoading.value = false;
  }
};

// 处理模板预览
const handlePreviewTemplate = () => {
  // 打开模板预览对话框或下载模板
  ElMessageBox.alert(
    `<div class="template-preview">
      <h3 style="text-align: center; margin-bottom: 20px; color: #303133;">邮编分区导入模板格式</h3>
      <p style="margin-bottom: 15px; color: #606266;">请按照以下格式准备Excel文件:</p>
      <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        <thead>
          <tr style="background-color: #f5f7fa; height: 40px;">
            <th style="text-align: center; min-width: 100px;">服务商</th>
            <th style="text-align: center; min-width: 100px;">始发地邮编</th>
            <th style="text-align: center; min-width: 120px;">目的地邮编起始</th>
            <th style="text-align: center; min-width: 120px;">目的地邮编终止</th>
            <th style="text-align: center; min-width: 100px;">分区号码</th>
          </tr>
        </thead>
        <tbody>
          <tr style="height: 36px;">
            <td style="text-align: center;">FedEx</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">200000</td>
            <td style="text-align: center;">299999</td>
            <td style="text-align: center;">2</td>
          </tr>
          <tr style="height: 36px;">
            <td style="text-align: center;">FedEx</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">300000</td>
            <td style="text-align: center;">399999</td>
            <td style="text-align: center;">3</td>
          </tr>
          <tr style="height: 36px;">
            <td style="text-align: center;">UPS</td>
            <td style="text-align: center;">100000</td>
            <td style="text-align: center;">400000</td>
            <td style="text-align: center;">499999</td>
            <td style="text-align: center;">4</td>
          </tr>
        </tbody>
      </table>
      <p style="margin-top: 15px; margin-bottom: 10px; color: #606266; font-weight: bold;">字段说明:</p>
      <ul style="color: #606266; padding-left: 20px; line-height: 1.8;">
        <li><b>服务商</b>: 填写服务商名称，如FedEx、UPS等，必须是系统中已存在的服务商</li>
        <li><b>始发地邮编</b>: 始发地邮编</li>
        <li><b>目的地邮编起始</b>: 目的地邮编起始值</li>
        <li><b>目的地邮编终止</b>: 目的地邮编结束值</li>
        <li><b>分区号码</b>: 分区号码</li>
      </ul>
      <div style="margin-top: 20px; padding: 12px; background-color: #f0f9eb; border-radius: 4px; border-left: 4px solid #67c23a;">
        <p style="margin: 0; color: #67c23a; font-weight: bold;">提示</p>
        <p style="margin: 5px 0 0; color: #606266;">导入前请确保数据格式正确，且服务商名称在系统中存在</p>
      </div>
    </div>`,
    '邮编分区导入模板',
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
    ['服务商', '始发地邮编', '目的地邮编起始', '目的地邮编终止', '分区号码'],
    ['FedEx', '100000', '200000', '299999', '2'],
    ['FedEx', '100000', '300000', '399999', '3'],
    ['UPS', '100000', '400000', '499999', '4']
  ];

  // 创建工作簿
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(templateData);

  // 设置列宽
  const colWidth = [
    {wch: 15}, // 服务商列宽
    {wch: 15}, // 始发地邮编列宽
    {wch: 15}, // 目的地邮编起始列宽
    {wch: 15}, // 目的地邮编终止列宽
    {wch: 10}  // 分区号码列宽
  ];
  ws['!cols'] = colWidth;

  // 添加到工作簿
  XLSX.utils.book_append_sheet(wb, ws, '邮编分区模板');
  
  // 导出文件
  XLSX.writeFile(wb, '邮编分区导入模板.xlsx');
  
  ElMessage.success('模板已下载');
};
</script>

<style scoped>
.zip-zones {
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