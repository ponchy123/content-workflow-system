<template>
  <div class="cost-analysis">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>成本分析</h2>
          <div class="actions">
            <el-select v-model="periodType" placeholder="选择周期" style="width: 120px">
              <el-option label="每日" value="daily" />
              <el-option label="每周" value="weekly" />
              <el-option label="每月" value="monthly" />
              <el-option label="每季" value="quarterly" />
              <el-option label="每年" value="yearly" />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
            <el-button type="primary" @click="refreshData">
              查询
            </el-button>
          </div>
        </div>
      </template>

      <div class="cost-container">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card class="summary-card">
              <div class="summary-title">总计费费用</div>
              <div class="summary-value">¥ 128,564.85</div>
              <div class="summary-change positive">+12.8%</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="summary-card">
              <div class="summary-title">平均单次计费</div>
              <div class="summary-value">¥ 185.23</div>
              <div class="summary-change negative">-5.2%</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="summary-card">
              <div class="summary-title">计费订单总数</div>
              <div class="summary-value">6,942</div>
              <div class="summary-change positive">+18.9%</div>
            </el-card>
          </el-col>
        </el-row>

        <div class="chart-section">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="费用趋势" name="trend">
              <div class="chart-container">
                <div class="chart-placeholder">此处将展示费用趋势图表</div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="费用构成" name="composition">
              <div class="chart-container">
                <div class="chart-placeholder">此处将展示费用构成图表</div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="服务商分布" name="provider">
              <div class="chart-container">
                <div class="chart-placeholder">此处将展示服务商费用分布图表</div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <div class="table-section">
          <h3>费用明细</h3>
          <el-table :data="costDetails" border style="width: 100%">
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="provider" label="服务商" width="120" />
            <el-table-column prop="service" label="服务类型" width="150" />
            <el-table-column prop="orderCount" label="订单数" width="100" />
            <el-table-column prop="baseFee" label="基础费用" width="120" />
            <el-table-column prop="fuelSurcharge" label="燃油附加费" width="120" />
            <el-table-column prop="otherFees" label="其他费用" width="120" />
            <el-table-column prop="totalCost" label="总费用" width="120" />
          </el-table>
          <div class="pagination">
            <el-pagination
              layout="total, prev, pager, next"
              :total="100"
              :page-size="10"
            />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

// 查询条件
const periodType = ref('monthly');
const dateRange = ref('');

// 当前活动标签
const activeTab = ref('trend');

// 费用明细数据
const costDetails = ref([
  {
    date: '2024-01-01',
    provider: 'FedEx',
    service: 'Ground',
    orderCount: 245,
    baseFee: '¥ 15,680.50',
    fuelSurcharge: '¥ 1,568.05',
    otherFees: '¥ 780.20',
    totalCost: '¥ 18,028.75'
  },
  {
    date: '2024-01-01',
    provider: 'UPS',
    service: 'Ground',
    orderCount: 187,
    baseFee: '¥ 12,540.30',
    fuelSurcharge: '¥ 1,254.03',
    otherFees: '¥ 625.00',
    totalCost: '¥ 14,419.33'
  },
  {
    date: '2024-01-02',
    provider: 'FedEx',
    service: 'Express',
    orderCount: 132,
    baseFee: '¥ 18,975.60',
    fuelSurcharge: '¥ 1,897.56',
    otherFees: '¥ 945.00',
    totalCost: '¥ 21,818.16'
  },
  {
    date: '2024-01-02',
    provider: 'UPS',
    service: 'Express',
    orderCount: 98,
    baseFee: '¥ 15,680.50',
    fuelSurcharge: '¥ 1,568.05',
    otherFees: '¥ 780.20',
    totalCost: '¥ 18,028.75'
  },
  {
    date: '2024-01-03',
    provider: 'DHL',
    service: 'Global',
    orderCount: 76,
    baseFee: '¥ 22,450.75',
    fuelSurcharge: '¥ 2,245.08',
    otherFees: '¥ 1,120.00',
    totalCost: '¥ 25,815.83'
  }
]);

// 方法
const refreshData = () => {
  console.log('刷新数据', periodType.value, dateRange.value);
  // TODO: 根据查询条件获取数据
};

// 生命周期钩子
onMounted(() => {
  // 初始化
  console.log('成本分析页面已加载');
});
</script>

<style scoped>
.cost-analysis {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 10px;
}

.cost-container {
  margin-top: 20px;
}

.summary-card {
  text-align: center;
  padding: 20px;
  margin-bottom: 20px;
}

.summary-title {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  margin-bottom: 10px;
}

.summary-change {
  font-size: 14px;
}

.positive {
  color: var(--el-color-success);
}

.negative {
  color: var(--el-color-danger);
}

.chart-section {
  margin: 20px 0;
}

.chart-container {
  height: 400px;
  margin-top: 20px;
  border: 1px dashed var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  color: var(--el-text-color-secondary);
  font-size: 16px;
}

.table-section {
  margin-top: 30px;
}

.table-section h3 {
  margin-bottom: 15px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 