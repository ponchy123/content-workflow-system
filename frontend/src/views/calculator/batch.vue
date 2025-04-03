<template>
  <div class="batch-calculator-view">
    <form-card title="批量运费计算">
      <!-- 操作按钮 -->
      <template #actions>
        <action-bar
          :primary-actions="[
            {
              key: 'history',
              label: '计算历史',
              type: 'info',
              icon: 'Clock',
              handler: showHistory,
            },
            {
              key: 'productQuery',
              label: '产品查询',
              type: 'warning',
              icon: 'Search',
              handler: showProductQuery,
            },
            {
              key: 'template',
              label: '模板预览',
              type: 'primary',
              icon: 'View',
              handler: showTemplatePreview,
            },
          ]"
        />
      </template>

      <!-- 上传区域 -->
      <el-upload
        class="upload-area"
        drag
        accept=".xlsx,.xls"
        :limit="1"
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
        :before-upload="handleBeforeUpload"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">只能上传 xlsx/xls 文件，且文件大小不超过 10MB</div>
        </template>
      </el-upload>

      <!-- 验证错误 -->
      <div v-if="validationResult?.errors" class="validation-errors">
        <el-alert
          v-for="(error, index) in validationResult.errors"
          :key="index"
          :title="error.message"
          :type="error.type || 'error'"
          show-icon
          :closable="false"
        />
      </div>
    </form-card>

    <!-- 模板预览对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      title="批量计算模板预览"
      width="80%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="template-preview-content">
        <p class="template-description">
          批量计算模板包含以下字段，请按照要求填写数据后上传：
        </p>
        <el-table :data="templateData" border style="width: 100%" :header-cell-style="{ background: '#f5f7fa' }">
          <el-table-column prop="field" label="字段名" width="150" />
          <el-table-column prop="name" label="中文名称" width="150" />
          <el-table-column prop="required" label="是否必填" width="100">
            <template #default="{ row }">
              <el-tag :type="row.required ? 'danger' : 'info'">
                {{ row.required ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" />
          <el-table-column prop="example" label="示例" width="150" />
        </el-table>

        <div class="template-example mt-4">
          <h4>填写实例：</h4>
          <el-table :data="templateExampleData" border style="width: 100%" :header-cell-style="{ background: '#f5f7fa' }">
            <el-table-column prop="fromAddress" label="发件地址" />
            <el-table-column prop="toAddress" label="收件地址" />
            <el-table-column prop="weight" label="重量(KG)" />
            <el-table-column prop="quantity" label="数量" />
            <el-table-column prop="productCode" label="产品代码" />
            <el-table-column prop="orderDate" label="订单时间" />
            <el-table-column prop="length" label="长(CM)" />
            <el-table-column prop="width" label="宽(CM)" />
            <el-table-column prop="height" label="高(CM)" />
          </el-table>
        </div>

        <div class="template-actions mt-4">
          <el-button type="primary" @click="exportTemplateExample">导出Excel模板</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 产品查询对话框 -->
    <el-dialog
      v-model="productQueryDialogVisible"
      title="产品代码查询"
      width="80%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="product-query-content">
        <div class="search-bar">
          <el-input
            v-model="productSearchKeyword"
            placeholder="输入产品名称或代码搜索"
            class="search-input"
            clearable
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
        </div>

        <el-table
          :data="filteredProducts"
          border
          stripe
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa' }"
          v-loading="productsLoading"
        >
          <el-table-column prop="code" label="产品代码" width="150" />
          <el-table-column prop="name" label="产品名称" width="200" />
          <el-table-column prop="provider" label="服务商" width="150" />
          <el-table-column prop="serviceType" label="服务类型" width="150" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="effectiveDate" label="生效日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.effectiveDate) }}
            </template>
          </el-table-column>
          <el-table-column prop="expirationDate" label="失效日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.expirationDate) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status ? 'success' : 'danger'">
                {{ row.status ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 数据预览 -->
    <form-card v-if="previewData.length" title="数据预览" class="preview-card">
      <template #actions>
        <action-bar
          :primary-actions="[
            {
              key: 'calculate',
              label: '开始计算',
              type: 'primary',
              loading: calculating,
              disabled: calculating || !validationResult?.isValid,
              handler: handleCalculate,
            },
          ]"
        />
      </template>

      <data-table :data="previewData" :columns="previewColumns" :loading="calculating">
        <template #column-status="{ value }">
          <status-tag :type="getStatusType(value)" :text="getStatusText(value)" />
        </template>
      </data-table>
    </form-card>

    <!-- 计算结果 -->
    <form-card v-if="currentTask" title="计算结果" class="result-card">
      <template #actions>
        <action-bar
          :primary-actions="[
            {
              key: 'export',
              label: '导出结果',
              type: 'primary',
              icon: 'Download',
              handler: handleExport,
            },
          ]"
        />
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务状态">
          <status-tag
            :type="getTaskStatusType(currentTask.status)"
            :text="getTaskStatusText(currentTask.status)"
          />
        </el-descriptions-item>
        <el-descriptions-item label="总记录数">
          {{ currentTask.total_records }}
        </el-descriptions-item>
        <el-descriptions-item label="成功记录">
          {{ currentTask.success_records }}
        </el-descriptions-item>
        <el-descriptions-item label="失败记录">
          {{ currentTask.failed_records }}
        </el-descriptions-item>
      </el-descriptions>

      <data-table :data="currentTask.calculation_results" :columns="resultColumns" :loading="exporting">
        <template #column-status="{ value }">
          <status-tag
            :type="getCalculationStatusType(value)"
            :text="getCalculationStatusText(value)"
          />
        </template>
        <template #column-total_charge="{ value }">
          {{ formatCurrency(value) }}
        </template>
      </data-table>
    </form-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import { ElMessage, ElUpload, ElDialog, ElTable, ElTableColumn, ElTag } from 'element-plus';
  import { useRouter } from 'vue-router';
  import { UploadFilled, View, Clock, Download, Search } from '@element-plus/icons-vue';
  import type { UploadFile, UploadFiles } from 'element-plus';
  import { FormCard, DataTable, ActionBar, StatusTag } from '@/components/common';
  import type { ValidationResult } from '@/types/calculator';
  import type { CalculationRequest } from '@/types/calculator';
  import { validateData, calculateBatch } from '@/api/calculator/index';
  import { formatCurrency } from '@/utils/format';
  import * as XLSX from 'xlsx';

  // 路由器
  const router = useRouter();

  // 跳转到计算历史
  const showHistory = () => {
    router.push('/calculator/history');
  };

  // 类型定义
  type Status = 'pending' | 'processing' | 'completed' | 'failed';
  type CalculationStatus = 'success' | 'failed' | 'invalid';
  type CommonTagType = 'success' | 'info' | 'warning' | 'danger';
  
  interface StatusInfo {
    type: CommonTagType;
    text: string;
  }

  interface ValidationError {
    row: number;
    field: string;
    message: string;
    type?: 'warning' | 'error';
  }

  interface FileValidationData {
    fromAddress: string;
    toAddress: string;
    weight: number;
    quantity: number;
    productCode: string;
    orderDate: string;
    dimensions?: {
      length: number;
      width: number;
      height: number;
    };
  }

  interface BatchCalculationTaskData {
    task_id: string;
    file_name: string;
    status: Status;
    total_records: number;
    processed_records: number;
    success_records: number;
    failed_records: number;
    calculation_results: Array<{
      status: CalculationStatus;
      total_charge: number;
      base_charge: number;
      fuel_surcharge: number;
    }>;
    created_at: string;
    updated_at: string;
  }

  interface BatchCalculationResponseData {
    taskId: string;
    filename: string;
    state: Status;
    total: number;
    processed: number;
    success: number;
    failed: number;
    items: Array<{
      status: CalculationStatus;
      totalCharge: number;
      baseCharge: number;
      fuelSurcharge: number;
    }>;
  }

  // 状态变量
  const validationResult = ref<ValidationResult | null>(null);
  const previewData = ref<CalculationRequest[]>([]);
  const previewColumns = ref([
    { prop: 'status', label: '状态' },
    { prop: 'fromAddress', label: '发件地址' },
    { prop: 'toAddress', label: '收件地址' },
    { prop: 'weight', label: '重量' },
    { prop: 'quantity', label: '数量' },
    { prop: 'productCode', label: '产品代码' },
    { prop: 'orderDate', label: '订单时间' },
    { prop: 'length', label: '长(CM)' },
    { prop: 'width', label: '宽(CM)' }, 
    { prop: 'height', label: '高(CM)' }
  ]);
  const currentTask = ref<BatchCalculationTaskData | null>(null);
  const resultColumns = ref([
    { prop: 'status', label: '状态' },
    { prop: 'total_charge', label: '总费用' },
    { prop: 'base_charge', label: '基础费用' },
    { prop: 'fuel_surcharge', label: '燃油附加费' }
  ]);
  const calculating = ref(false);
  const exporting = ref(false);
  const templateDialogVisible = ref(false);
  const productQueryDialogVisible = ref(false);
  const productSearchKeyword = ref('');
  const productsLoading = ref(false);

  // 模板相关类型定义
  interface TemplateField {
    field: string;
    name: string;
    required: boolean;
    description: string;
    example: string;
  }
  
  interface TemplateExample {
    fromAddress: string;
    toAddress: string;
    weight: number;
    quantity: number;
    productCode: string;
    orderDate: string;
    length: number;
    width: number;
    height: number;
  }

  // 产品相关类型定义
  interface Product {
    code: string;
    name: string;
    provider: string;
    serviceType: string;
    description: string;
    effectiveDate: string;
    expirationDate: string;
    status: boolean;
  }
  
  const templateData = ref<TemplateField[]>([]);
  const templateExampleData = ref<TemplateExample[]>([]);

  // 过滤后的产品列表
  const filteredProducts = computed(() => {
    if (!productSearchKeyword.value) {
      return allProducts.value;
    }
    
    const keyword = productSearchKeyword.value.toLowerCase();
    return allProducts.value.filter(product => 
      product.code.toLowerCase().includes(keyword) || 
      product.name.toLowerCase().includes(keyword) ||
      product.provider.toLowerCase().includes(keyword)
    );
  });

  // 状态映射
  const statusMap: Record<Status, StatusInfo> = {
    pending: { type: 'info', text: '待处理' },
    processing: { type: 'warning', text: '处理中' },
    completed: { type: 'success', text: '已完成' },
    failed: { type: 'danger', text: '失败' },
  };

  const taskStatusMap: Record<Status, StatusInfo> = {
    pending: { type: 'warning', text: '等待处理' },
    processing: { type: 'warning', text: '正在计算' },
    completed: { type: 'success', text: '计算完成' },
    failed: { type: 'danger', text: '计算失败' },
  };

  const calculationStatusMap: Record<CalculationStatus, StatusInfo> = {
    success: { type: 'success', text: '计算成功' },
    failed: { type: 'danger', text: '计算失败' },
    invalid: { type: 'warning', text: '数据无效' },
  };

  const getStatusType = (status: Status): CommonTagType => statusMap[status]?.type || 'info';
  const getStatusText = (status: Status): string => statusMap[status]?.text || status;

  const getTaskStatusType = (status: Status): CommonTagType => taskStatusMap[status]?.type || 'info';
  const getTaskStatusText = (status: Status): string => taskStatusMap[status]?.text || status;

  const getCalculationStatusType = (status: CalculationStatus): CommonTagType => calculationStatusMap[status]?.type || 'info';
  const getCalculationStatusText = (status: CalculationStatus): string => calculationStatusMap[status]?.text || status;

  // 文件处理函数
  const handleFileChange = async (uploadFile: UploadFile, uploadFiles: UploadFiles) => {
    try {
      const result = await validateData(uploadFile.raw as File);
      validationResult.value = result;
      if (result.isValid) {
        previewData.value = result.data.map((item: any) => ({
          fromAddress: item.fromAddress,
          toAddress: item.toAddress,
          weight: item.weight,
          quantity: item.quantity,
          productCode: item.productCode,
          orderDate: item.orderDate,
          productType: item.productCode || 'default',
          serviceLevel: 'standard',
          length: item.length || item.dimensions?.length || 0,
          width: item.width || item.dimensions?.width || 0,
          height: item.height || item.dimensions?.height || 0,
          volume: calculateVolume(
            item.length || item.dimensions?.length || 0, 
            item.width || item.dimensions?.width || 0, 
            item.height || item.dimensions?.height || 0
          )
        }));
      }
    } catch (error) {
      ElMessage.error('文件验证失败');
    }
  };

  // 计算体积辅助函数
  const calculateVolume = (length: number, width: number, height: number): number => {
    if (!length || !width || !height) return 0;
    return length * width * height / 1000000; // 转换为立方米
  };

  const handleBeforeUpload = (file: File) => {
    const isExcel = /\.(xlsx|xls)$/.test(file.name);
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isExcel) {
      ElMessage.error('只能上传 Excel 文件!');
      return false;
    }
    if (!isLt10M) {
      ElMessage.error('文件大小不能超过 10MB!');
      return false;
    }
    return true;
  };

  const handleCalculate = async () => {
    if (!validationResult.value?.isValid) return;
    calculating.value = true;
    try {
      const response = await calculateBatch({ items: previewData.value }) as unknown as BatchCalculationResponseData;
      const now = new Date().toISOString();
      
      // 将API响应数据转换为组件所需的格式
      currentTask.value = {
        task_id: response.taskId,
        file_name: response.filename || 'batch_calculation.xlsx',
        status: response.state,
        total_records: response.total || 0,
        processed_records: response.processed || 0,
        success_records: response.success || 0,
        failed_records: response.failed || 0,
        calculation_results: response.items?.map(item => ({
          status: item.status,
          total_charge: item.totalCharge || 0,
          base_charge: item.baseCharge || 0,
          fuel_surcharge: item.fuelSurcharge || 0
        })) || [],
        created_at: now,
        updated_at: now
      };
    } catch (error) {
      ElMessage.error('计算失败');
    } finally {
      calculating.value = false;
    }
  };

  const handleExport = () => {
    exporting.value = true;
    try {
      if (currentTask.value?.task_id) {
        // 实现导出逻辑
        console.log('导出任务:', currentTask.value.task_id);
      }
    } finally {
      exporting.value = false;
    }
  };

  const showTemplatePreview = () => {
    // 填充模板字段描述
    templateData.value = [
      { field: 'fromAddress', name: '发件地址', required: true, description: '发货地邮编，例如：100000', example: '100000' },
      { field: 'toAddress', name: '收件地址', required: true, description: '收货地邮编，例如：200000', example: '200000' },
      { field: 'weight', name: '重量', required: true, description: '货物重量，单位可为KG/LB/OZ', example: '10' },
      { field: 'quantity', name: '数量', required: true, description: '包裹数量', example: '1' },
      { field: 'productCode', name: '产品代码', required: true, description: '产品或报价单代码，用于确定计费标准', example: 'FDX-GRD' },
      { field: 'orderDate', name: '订单时间', required: true, description: '订单创建时间，用于判断旺季附加费，格式：YYYY/M/D', example: '2024/4/1' },
      { field: 'length', name: '长', required: true, description: '包裹长度，单位可为CM/IN', example: '30' },
      { field: 'width', name: '宽', required: true, description: '包裹宽度，单位可为CM/IN', example: '20' },
      { field: 'height', name: '高', required: true, description: '包裹高度，单位可为CM/IN', example: '10' }
    ];
    
    // 填充示例数据
    templateExampleData.value = [
      { fromAddress: '100000', toAddress: '200000', weight: 10, quantity: 1, productCode: 'FDX-GRD', orderDate: '2024/4/1', length: 30, width: 20, height: 10 },
      { fromAddress: '100000', toAddress: '300000', weight: 5, quantity: 2, productCode: 'UPS-STD', orderDate: '2024/4/2', length: 25, width: 15, height: 10 },
      { fromAddress: '200000', toAddress: '400000', weight: 15, quantity: 1, productCode: 'DHL-INT', orderDate: '2024/4/3', length: 40, width: 30, height: 20 }
    ];
    
    // 显示对话框
    templateDialogVisible.value = true;
  };

  const showProductQuery = () => {
    productQueryDialogVisible.value = true;
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
  };

  // 添加导出模板的方法
  const exportTemplateExample = () => {
    try {
      // 创建工作簿和工作表
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.json_to_sheet(templateExampleData.value);
      
      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, "模板示例");
      
      // 导出Excel文件
      XLSX.writeFile(wb, "批量计算模板.xlsx");
      
      ElMessage.success('模板导出成功');
    } catch (error) {
      console.error('导出模板失败:', error);
      ElMessage.error('导出模板失败');
    }
  };

  // 模拟产品数据
  const allProducts = ref<Product[]>([
    { 
      code: 'FDX-GRD', 
      name: 'FedEx 陆运', 
      provider: 'FedEx', 
      serviceType: '标准', 
      description: 'FedEx标准陆运服务', 
      effectiveDate: '2024-01-01', 
      expirationDate: '2024-12-31', 
      status: true 
    },
    { 
      code: 'UPS-STD', 
      name: 'UPS 标准', 
      provider: 'UPS', 
      serviceType: '标准', 
      description: 'UPS标准快递服务', 
      effectiveDate: '2024-01-01', 
      expirationDate: '2024-12-31', 
      status: true 
    },
    { 
      code: 'DHL-INT', 
      name: 'DHL 国际', 
      provider: 'DHL', 
      serviceType: '国际', 
      description: 'DHL国际快递服务', 
      effectiveDate: '2024-01-01', 
      expirationDate: '2024-12-31', 
      status: true 
    }
  ]);
</script>

<style>
  .batch-calculator-view {
    padding: var(--content-padding);
    max-width: var(--content-max-width);
    margin: 0 auto;
  }

  .upload-area {
    width: 100%;
    padding: 40px 0;
    border: 1px dashed var(--el-border-color);
    border-radius: 6px;
    background-color: var(--el-fill-color-light);
    text-align: center;
  }

  .el-icon--upload {
    font-size: 48px;
    color: var(--el-text-color-secondary);
    margin-bottom: 16px;
  }

  .el-upload__text {
    color: var(--el-text-color-regular);
    font-size: 16px;
    margin-bottom: 8px;
  }

  .el-upload__text em {
    color: var(--el-color-primary);
    font-style: normal;
  }

  .el-upload__tip {
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }

  .validation-errors {
    margin-top: 16px;
  }

  .validation-errors .el-alert {
    margin-bottom: 8px;
  }

  .preview-card,
  .result-card {
    margin-top: 24px;
  }

  /* 模板预览样式 */
  .template-preview-content {
    padding: 10px;
  }

  .template-description {
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin-bottom: 20px;
  }

  .template-example {
    margin-top: 30px;
  }

  .template-example h4 {
    margin-bottom: 15px;
    font-size: 16px;
    color: var(--el-text-color-primary);
  }

  .template-actions {
    margin-top: 30px;
    text-align: center;
  }

  .mt-4 {
    margin-top: 16px;
  }

  /* 产品查询对话框样式 */
  .product-query-content {
    padding: 10px;
  }

  .search-bar {
    margin-bottom: 16px;
  }

  .search-input {
    width: 100%;
  }
</style>
