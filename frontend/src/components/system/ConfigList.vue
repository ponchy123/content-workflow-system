<template>
  <div class="config-list">
    <!-- 搜索和过滤区域 -->
    <el-card class="filter-container">
      <el-form :inline="true" :model="queryParams" @submit.prevent="handleSearch">
        <el-form-item label="配置类型">
          <el-select v-model="queryParams.config_type" placeholder="请选择配置类型" clearable>
            <el-option
              v-for="(label, value) in configTypes"
              :key="value"
              :label="label"
              :value="value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.search"
            placeholder="搜索配置键或描述"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮区域 -->
    <div class="operation-container">
      <el-button type="primary" @click="handleAdd">新增配置</el-button>
      <el-button type="success" @click="handleImport">导入配置</el-button>
      <el-button type="warning" @click="handleExport">导出配置</el-button>
      <el-button type="danger" @click="handleResetDefaults">重置默认值</el-button>
      <el-button @click="handleClearCache">清除缓存</el-button>
    </div>

    <!-- 配置列表 -->
    <el-card>
      <el-table v-loading="loading" :data="configList" border style="width: 100%">
        <el-table-column prop="key" label="配置键" min-width="150" />
        <el-table-column prop="value" label="配置值" min-width="200">
          <template #default="{ row }">
            <config-value-display :value="row.value" :type="getValueType(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="config_type" label="类型" width="120">
          <template #default="{ row }">
            {{ configTypes[row.config_type] }}
          </template>
        </el-table-column>
        <el-table-column prop="is_public" label="是否公开" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'">
              {{ row.is_public ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 配置编辑对话框 -->
    <config-edit-dialog
      v-model="dialogVisible"
      :config-data="currentConfig || undefined"
      :config-types="configTypes"
      @success="handleEditSuccess"
    />

    <!-- 导入配置对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入配置" width="500px">
      <el-upload
        class="upload-container"
        action="/api/system-configs/import-configs/"
        :headers="uploadHeaders"
        :on-success="handleImportSuccess"
        :on-error="handleImportError"
        accept=".json"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">只能上传 JSON 文件</div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, reactive } from 'vue';
  import { ElMessage, ElMessageBox } from 'element-plus';
  import { UploadFilled } from '@element-plus/icons-vue';
  import ConfigEditDialog from './ConfigEditDialog.vue';
  import ConfigValueDisplay from './ConfigValueDisplay.vue';
  import { useUserStore } from '@/stores/user';

  interface ConfigItem {
    id: number;
    key: string;
    value: any;
    description: string;
    config_type: string;
    is_public: boolean;
    validation_rules?: {
      type?: string;
      [key: string]: any;
    };
  }

  interface QueryParams {
    page: number;
    page_size: number;
    config_type: string;
    search: string;
  }

  // 状态定义
  const loading = ref(false);
  const dialogVisible = ref(false);
  const importDialogVisible = ref(false);
  const currentConfig = ref<ConfigItem | null>(null);
  const configList = ref<ConfigItem[]>([]);
  const total = ref(0);
  const configTypes = ref<Record<string, string>>({});

  // 查询参数
  const queryParams = reactive<QueryParams>({
    page: 1,
    page_size: 10,
    config_type: '',
    search: '',
  });

  // 上传相关
  const userStore = useUserStore();
  const uploadHeaders = {
    Authorization: `Bearer ${userStore.token}`,
  };

  // 获取配置类型列表
  const fetchConfigTypes = async () => {
    try {
      const response = await fetch('/api/system-configs/types/');
      const data = await response.json();
      configTypes.value = data;
    } catch (error) {
      console.error('获取配置类型失败:', error);
      ElMessage.error('获取配置类型失败');
    }
  };

  // 获取配置列表
  const fetchConfigList = async () => {
    loading.value = true;
    try {
      const params = new URLSearchParams({
        page: queryParams.page.toString(),
        page_size: queryParams.page_size.toString(),
        config_type: queryParams.config_type,
        search: queryParams.search,
      });

      const response = await fetch(`/api/system-configs/?${params}`);
      const data = await response.json();

      configList.value = data.results;
      total.value = data.count;
    } catch (error) {
      console.error('获取配置列表失败:', error);
      ElMessage.error('获取配置列表失败');
    } finally {
      loading.value = false;
    }
  };

  // 判断值的类型
  const getValueType = (row: ConfigItem): string => {
    if (!row.validation_rules) return 'text';
    return row.validation_rules.type || 'text';
  };

  // 搜索处理
  const handleSearch = () => {
    queryParams.page = 1;
    fetchConfigList();
  };

  // 重置查询
  const resetQuery = () => {
    queryParams.config_type = '';
    queryParams.search = '';
    handleSearch();
  };

  // 分页处理
  const handleSizeChange = (val: number) => {
    queryParams.page_size = val;
    fetchConfigList();
  };

  const handleCurrentChange = (val: number) => {
    queryParams.page = val;
    fetchConfigList();
  };

  // 新增配置
  const handleAdd = () => {
    currentConfig.value = null;
    dialogVisible.value = true;
  };

  // 编辑配置
  const handleEdit = (row: ConfigItem) => {
    currentConfig.value = { ...row };
    dialogVisible.value = true;
  };

  // 删除配置
  const handleDelete = async (row: ConfigItem) => {
    try {
      await ElMessageBox.confirm(`确认删除配置"${row.key}"吗？`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      });

      const response = await fetch(`/api/system-configs/${row.id}/`, {
        method: 'DELETE',
      });

      if (response.ok) {
        ElMessage.success('删除成功');
        fetchConfigList();
      } else {
        throw new Error('删除失败');
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除配置失败:', error);
        ElMessage.error('删除配置失败');
      }
    }
  };

  // 编辑成功处理
  const handleEditSuccess = () => {
    dialogVisible.value = false;
    fetchConfigList();
  };

  // 导入配置
  const handleImport = () => {
    importDialogVisible.value = true;
  };

  // 导入成功处理
  const handleImportSuccess = (response: any) => {
    ElMessage.success('导入成功');
    importDialogVisible.value = false;
    fetchConfigList();
  };

  // 导入失败处理
  const handleImportError = (error: any) => {
    console.error('导入失败:', error);
    ElMessage.error('导入失败');
  };

  // 导出配置
  const handleExport = async () => {
    try {
      const response = await fetch('/api/system-configs/export-configs/');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'system_configs.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出失败:', error);
      ElMessage.error('导出失败');
    }
  };

  // 重置默认值
  const handleResetDefaults = async () => {
    try {
      await ElMessageBox.confirm('确认重置所有配置为默认值吗？此操作不可恢复！', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      });

      const response = await fetch('/api/system-configs/reset-defaults/', {
        method: 'POST',
      });

      if (response.ok) {
        ElMessage.success('重置成功');
        fetchConfigList();
      } else {
        throw new Error('重置失败');
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('重置默认值失败:', error);
        ElMessage.error('重置默认值失败');
      }
    }
  };

  // 清除缓存
  const handleClearCache = async () => {
    try {
      const response = await fetch('/api/system-configs/clear-cache/', {
        method: 'POST',
      });

      if (response.ok) {
        ElMessage.success('缓存清除成功');
      } else {
        throw new Error('缓存清除失败');
      }
    } catch (error) {
      console.error('清除缓存失败:', error);
      ElMessage.error('清除缓存失败');
    }
  };

  // 生命周期钩子
  onMounted(() => {
    fetchConfigTypes();
    fetchConfigList();
  });
</script>

<style scoped>
  .config-list {
    padding: 20px;
  }

  .filter-container {
    margin-bottom: 20px;
  }

  .operation-container {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .upload-container {
    text-align: center;
  }
</style>
