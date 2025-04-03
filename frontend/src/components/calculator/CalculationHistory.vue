<template>
  <div class="calculation-history">
    <div class="history-header">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :shortcuts="dateShortcuts"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </div>

    <data-table
      v-loading="loading"
      :data="historyList"
      :columns="columns"
      :pagination="true"
      :total="total"
      :page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      border
      stripe
      @update:pagination="handlePaginationChange"
    >
      <template #requestId="{ row }">
        {{ row.requestId }}
      </template>
      <template #fromAddress="{ row }">
        {{ row.request.fromAddress }}
      </template>
      <template #toAddress="{ row }">
        {{ row.request.toAddress }}
      </template>
      <template #weight="{ row }"> {{ row.request.weight }}kg </template>
      <template #productType="{ row }">
        {{ row.request.productType }}
      </template>
      <template #totalCharge="{ row }">
        <div class="total-charge">
          {{ formatCurrency(row.totalCharge) }}
        </div>
      </template>
      <template #timestamp="{ row }">
        {{ formatDateTime(row.timestamp) }}
      </template>
      <template #actions="{ row }">
        <el-button type="primary" link @click="handleViewDetail(row)"> 查看详情 </el-button>
      </template>
    </data-table>

    <el-dialog v-model="detailVisible" title="计算详情" width="60%" destroy-on-close>
      <el-descriptions title="请求信息" :column="2" border>
        <el-descriptions-item label="起始地">{{
          currentDetail?.request.fromAddress
        }}</el-descriptions-item>
        <el-descriptions-item label="目的地">{{
          currentDetail?.request.toAddress
        }}</el-descriptions-item>
        <el-descriptions-item label="重量"
          >{{ currentDetail?.request.weight }}kg</el-descriptions-item
        >
        <el-descriptions-item label="尺寸">
          {{ currentDetail?.request.volume ? `${currentDetail.request.volume}m³` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="产品类型">{{
          currentDetail?.request.productType
        }}</el-descriptions-item>
        <el-descriptions-item label="备注">
          {{ currentDetail?.request.note || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>费用明细</el-divider>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="基础运费">{{
          formatCurrency(currentDetail?.baseCharge || 0)
        }}</el-descriptions-item>
        <el-descriptions-item label="燃油附加费">{{
          formatCurrency(currentDetail?.fuelSurcharge || 0)
        }}</el-descriptions-item>
        <el-descriptions-item label="总费用">
          <span class="total-charge">{{
            formatCurrency(currentDetail?.totalCharge || 0)
          }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <template v-if="currentDetail?.details">
        <el-divider>计费明细</el-divider>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="重量费用">{{
            formatCurrency(currentDetail.details.weightCharge || 0)
          }}</el-descriptions-item>
          <el-descriptions-item label="距离费用">{{
            formatCurrency(currentDetail.details.distanceCharge || 0)
          }}</el-descriptions-item>
          <el-descriptions-item label="区域费用">{{
            formatCurrency(currentDetail.details.zoneCharge || 0)
          }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentDetail.details.additionalCharges.length">
          <el-divider>附加费用</el-divider>
          <el-table :data="currentDetail.details.additionalCharges" border>
            <el-table-column prop="name" label="费用名称" />
            <el-table-column prop="amount" label="金额">
              <template #default="{ row }">{{ formatCurrency(row.amount) }}</template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue';
  import { ElMessage } from 'element-plus';
  import { getHistory, getHistoryDetail, exportHistory } from '@/api/calculator/index';
  import { formatDateTime, formatCurrency } from '@/utils/format';
  import DataTable from '@/components/common/data/DataTable.vue';
  import type { CalculationHistory, HistoryDetail } from '@/types/calculator';

  interface PaginationChangeEvent {
    currentPage: number;
    pageSize: number;
  }

  interface TableColumn {
    prop: string;
    label: string;
    width?: number;
    fixed?: 'left' | 'right';
  }

  // 搜索表单
  const searchForm = reactive({
    dateRange: [] as string[],
  });

  // 日期快捷选项
  const dateShortcuts = [
    {
      text: '最近一周',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
        return [start, end];
      },
    },
    {
      text: '最近一个月',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
        return [start, end];
      },
    },
    {
      text: '最近三个月',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
        return [start, end];
      },
    },
  ];

  // 列表数据
  const loading = ref(false);
  const historyList = ref<CalculationHistory[]>([]);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  // 详情数据
  const detailVisible = ref(false);
  const currentDetail = ref<HistoryDetail | null>(null);

  // 表格列配置
  const columns: TableColumn[] = [
    { prop: 'requestId', label: '请求ID', width: 180 },
    { prop: 'request.fromAddress', label: '起始地', width: 200 },
    { prop: 'request.toAddress', label: '目的地', width: 200 },
    { prop: 'request.weight', label: '重量', width: 100 },
    { prop: 'request.productType', label: '产品类型', width: 120 },
    { prop: 'totalCharge', label: '总费用', width: 120 },
    { prop: 'timestamp', label: '计算时间', width: 180 },
    { prop: 'actions', label: '操作', width: 120, fixed: 'right' },
  ];

  // 加载历史记录
  const loadHistory = async () => {
    loading.value = true;
    try {
      const response = await getHistory({
        page: currentPage.value,
        pageSize: pageSize.value,
        startDate: searchForm.dateRange[0],
        endDate: searchForm.dateRange[1],
      });
      historyList.value = response.items;
      total.value = response.total;
    } catch (error) {
      console.error('加载历史记录失败:', error);
      ElMessage.error('加载历史记录失败');
    } finally {
      loading.value = false;
    }
  };

  // 处理搜索
  const handleSearch = () => {
    currentPage.value = 1;
    loadHistory();
  };

  // 处理导出
  const handleExport = async () => {
    try {
      const [startDate, endDate] = searchForm.dateRange;
      if (!startDate || !endDate) {
        ElMessage.warning('请选择导出时间范围');
        return;
      }
      const params = {
        startDate,
        endDate,
      };
      const blob = await exportHistory(params);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `运费计算历史记录_${startDate}_${endDate}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出历史记录失败:', error);
      ElMessage.error('导出历史记录失败');
    }
  };

  // 处理查看详情
  const handleViewDetail = async (row: CalculationHistory) => {
    try {
      currentDetail.value = await getHistoryDetail(row.id);
      detailVisible.value = true;
    } catch (error) {
      console.error('获取详情失败:', error);
      ElMessage.error('获取详情失败');
    }
  };

  // 处理分页变化
  const handlePaginationChange = (page: number, size: number) => {
    if (page !== currentPage.value) {
      currentPage.value = page;
    }
    if (size !== pageSize.value) {
      pageSize.value = size;
    }
    loadHistory();
  };

  // 初始化加载数据
  loadHistory();
</script>

<style scoped>
  .calculation-history {
    padding: 20px;
  }

  .history-header {
    margin-bottom: 20px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .total-charge {
    color: #409eff;
    font-weight: bold;
  }

  :deep(.el-descriptions) {
    margin-bottom: 20px;
  }

  :deep(.el-descriptions__title) {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 16px;
  }
</style>
