<template>
  <div class="product-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>产品管理</h2>
          <el-button type="primary" @click="handleAdd">
            <el-icon><plus /></el-icon>
            新增产品
          </el-button>
          <el-upload
            class="ml-4"
            action="/api/v1/products/import"
            accept=".xlsx,.xls"
            :show-file-list="false"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
            :before-upload="beforeImportUpload"
          >
            <el-button type="primary">
              <el-icon><upload-filled /></el-icon>
              批量导入
            </el-button>
          </el-upload>
          <el-button type="primary" class="ml-4" @click="handleDownloadTemplate">
            <el-icon><download /></el-icon>
            下载模板
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="产品编号">
            <el-input v-model="searchForm.productId" placeholder="请输入产品编号" />
          </el-form-item>
          <el-form-item label="产品名称">
            <el-input v-model="searchForm.productName" placeholder="请输入产品名称" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择状态">
              <el-option label="全部" value="" />
              <el-option label="启用" value="1" />
              <el-option label="禁用" value="0" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 产品列表 -->
      <el-table :data="productList" border style="width: 100%" v-loading="loading">
        <el-table-column prop="productId" label="产品编号" width="150" />
        <el-table-column prop="productName" label="产品名称" width="200" />
        <el-table-column prop="dimFactor" label="体积重系数" width="120" />
        <el-table-column prop="effectiveDate" label="生效日期" width="120" />
        <el-table-column prop="expirationDate" label="失效日期" width="120" />
        <el-table-column prop="currencyCode" label="货币代码" width="100" />
        <el-table-column prop="weightUnit" label="重量单位" width="100" />
        <el-table-column prop="dimUnit" label="尺寸单位" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button type="primary" link @click="handleConfig(row)">配置</el-button>
              <el-button
                type="primary"
                link
                @click="handleToggleStatus(row)"
                :class="{ 'text-red-500': row.status === 1 }"
              >
                {{ row.status === 1 ? '禁用' : '启用' }}
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 产品表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增产品' : '编辑产品'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="产品编号" prop="productId">
          <el-input v-model="form.productId" placeholder="请输入产品编号" />
        </el-form-item>
        <el-form-item label="服务商" prop="providerId">
          <el-select v-model="form.providerId" placeholder="请选择服务商">
            <el-option
              v-for="provider in providers"
              :key="provider.id"
              :label="provider.name"
              :value="provider.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号" prop="version">
          <el-input-number v-model="form.version" :min="1" :step="1" />
        </el-form-item>
        <el-form-item label="产品名称" prop="productName">
          <el-input v-model="form.productName" placeholder="请输入产品名称" />
        </el-form-item>
        <el-form-item label="体积重系数" prop="dimFactor">
          <el-input-number v-model="form.dimFactor" :min="1" :precision="2" />
        </el-form-item>
        <el-form-item label="生效日期" prop="effectiveDate">
          <el-date-picker v-model="form.effectiveDate" type="date" placeholder="选择生效日期" />
        </el-form-item>
        <el-form-item label="失效日期" prop="expirationDate">
          <el-date-picker v-model="form.expirationDate" type="date" placeholder="选择失效日期" />
        </el-form-item>
        <el-form-item label="货币代码" prop="currencyCode">
          <el-select v-model="form.currencyCode" placeholder="请选择货币代码">
            <el-option label="USD" value="USD" />
            <el-option label="CNY" value="CNY" />
          </el-select>
        </el-form-item>
        <el-form-item label="重量单位" prop="weightUnit">
          <el-select v-model="form.weightUnit" placeholder="请选择重量单位">
            <el-option label="KG" value="KG" />
            <el-option label="LB" value="LB" />
          </el-select>
        </el-form-item>
        <el-form-item label="尺寸单位" prop="dimUnit">
          <el-select v-model="form.dimUnit" placeholder="请选择尺寸单位">
            <el-option label="CM" value="CM" />
            <el-option label="IN" value="IN" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 配置对话框 -->
    <ConfigDialog
      v-model:visible="configDialogVisible"
      :product-id="selectedProductId"
    />
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue';
  import { ElMessage, ElMessageBox } from 'element-plus';
  import { Plus, UploadFilled, Download } from '@element-plus/icons-vue';
  import type { FormInstance, FormRules } from 'element-plus';
  import ConfigDialog from '@/components/product/ConfigDialog.vue';

  // 搜索表单
  const searchForm = reactive({
    productId: '',
    productName: '',
    status: '',
  });

  // 表格数据
  const loading = ref(false);
  const productList = ref([]);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  // 对话框控制
  const dialogVisible = ref(false);
  const dialogType = ref<'add' | 'edit'>('add');
  const formRef = ref<FormInstance>();

  // 表单数据
  const form = reactive({
    productId: '',
    providerId: '',
    version: 1,
    productName: '',
    dimFactor: 139.0,
    effectiveDate: '',
    expirationDate: '',
    currencyCode: 'USD',
    weightUnit: 'LB',
    dimUnit: 'IN',
    status: 1,
  });

  // 服务商列表
  const providers = ref([
    { id: 1, name: 'UPS' },
    { id: 2, name: 'FedEx' },
    { id: 3, name: 'DHL' },
  ]);

  // 表单验证规则
  const rules: FormRules = {
    productId: [
      { required: true, message: '请输入产品编号', trigger: 'blur' },
      { pattern: /^[A-Z]{3}-[A-Z]{3}-\d{4}$/, message: '产品编号格式不正确', trigger: 'blur' },
    ],
    providerId: [{ required: true, message: '请选择服务商', trigger: 'change' }],
    version: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
    productName: [
      { required: true, message: '请输入产品名称', trigger: 'blur' },
      { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' },
    ],
    dimFactor: [{ required: true, message: '请输入体积重系数', trigger: 'blur' }],
    effectiveDate: [{ required: true, message: '请选择生效日期', trigger: 'change' }],
    expirationDate: [{ required: true, message: '请选择失效日期', trigger: 'change' }],
  };

  // 搜索方法
  const handleSearch = () => {
    // TODO: 实现搜索逻辑
  };

  // 重置搜索
  const resetSearch = () => {
    searchForm.productId = '';
    searchForm.productName = '';
    searchForm.status = '';
    handleSearch();
  };

  // 新增产品
  const handleAdd = () => {
    dialogType.value = 'add';
    dialogVisible.value = true;
    // 重置表单
    if (formRef.value) {
      formRef.value.resetFields();
    }
  };

  // 编辑产品
  const handleEdit = (row: any) => {
    dialogType.value = 'edit';
    dialogVisible.value = true;
    // 填充表单数据
    Object.assign(form, row);
  };

  // 添加配置对话框控制变量
  const configDialogVisible = ref(false);
  const selectedProductId = ref('');

  // 更新配置处理函数
  const handleConfig = (row: any) => {
    selectedProductId.value = row.id;
    configDialogVisible.value = true;
  };

  // 切换状态
  const handleToggleStatus = async (row: any) => {
    try {
      await ElMessageBox.confirm(`确认要${row.status === 1 ? '禁用' : '启用'}该产品吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      });
      // TODO: 实现状态切换逻辑
      ElMessage.success(`${row.status === 1 ? '禁用' : '启用'}成功`);
    } catch {
      // 用户取消操作
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    if (!formRef.value) return;

    await formRef.value.validate((valid, fields) => {
      if (valid) {
        // TODO: 实现表单提交逻辑
        dialogVisible.value = false;
        ElMessage.success(`${dialogType.value === 'add' ? '新增' : '编辑'}成功`);
      }
    });
  };

  // 分页方法
  const handleSizeChange = (val: number) => {
    pageSize.value = val;
    handleSearch();
  };

  const handleCurrentChange = (val: number) => {
    currentPage.value = val;
    handleSearch();
  };

  // 批量导入相关方法
  const handleImportSuccess = (response: any) => {
    ElMessage.success('导入成功');
    handleSearch(); // 刷新列表
  };

  const handleImportError = (error: any) => {
    ElMessage.error('导入失败：' + error.message);
  };

  const beforeImportUpload = (file: File) => {
    const isExcel =
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel';
    const isLt2M = file.size / 1024 / 1024 < 2;

    if (!isExcel) {
      ElMessage.error('只能上传Excel文件！');
      return false;
    }
    if (!isLt2M) {
      ElMessage.error('文件大小不能超过2MB！');
      return false;
    }
    return true;
  };

  const handleDownloadTemplate = () => {
    window.location.href = '/api/v1/products/template';
  };
</script>

<style scoped>
  .product-management {
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

  .config-dialog {
    width: 80% !important;
    max-width: 1200px;
  }

  .product-view {
    .page-header {
      margin-bottom: var(--spacing-large);

      .page-title {
        font-size: var(--font-size-extra-large);
        font-weight: var(--font-weight-bold);
        color: var(--text-color-primary);
        margin-bottom: var(--spacing-base);
      }

      .page-actions {
        display: flex;
        gap: var(--spacing-base);
      }
    }

    .product-container {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: var(--spacing-large);

      .product-card {
        background-color: var(--bg-color);
        border-radius: var(--border-radius-base);
        box-shadow: var(--box-shadow-light);
        transition: all var(--transition-duration) var(--transition-function);

        &:hover {
          transform: translateY(-2px);
          box-shadow: var(--box-shadow);
        }

        .card-header {
          padding: var(--spacing-base);
          border-bottom: 1px solid var(--border-color);

          .product-name {
            font-size: var(--font-size-large);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
            margin-bottom: var(--spacing-mini);
          }

          .product-code {
            font-size: var(--font-size-small);
            color: var(--text-color-secondary);
          }
        }

        .card-body {
          padding: var(--spacing-base);

          .info-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--spacing-base);

            .info-item {
              .item-label {
                font-size: var(--font-size-small);
                color: var(--text-color-secondary);
                margin-bottom: var(--spacing-mini);
              }

              .item-value {
                font-size: var(--font-size-base);
                color: var(--text-color-primary);
                font-weight: var(--font-weight-medium);
              }
            }
          }
        }

        .card-footer {
          padding: var(--spacing-base);
          border-top: 1px solid var(--border-color);
          background-color: var(--bg-color-light);
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-base);
        }
      }
    }

    .filter-section {
      margin-bottom: var(--spacing-large);
      padding: var(--spacing-base);
      background-color: var(--bg-color);
      border-radius: var(--border-radius-base);
      box-shadow: var(--box-shadow-light);

      .filter-form {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--spacing-base);

        :deep(.el-form-item) {
          margin-bottom: 0;
        }
      }
    }
  }
</style>
