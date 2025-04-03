<template>
  <div class="usage-statistics">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>使用统计</h2>
          <div class="actions">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              @change="handleDateChange"
            />
            <el-button type="primary" @click="refreshData">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="statistics-container">
        <el-row :gutter="20">
          <el-col :span="6" v-for="(item, index) in summaryData" :key="index">
            <el-card class="statistics-card" shadow="hover">
              <div class="statistics-value">{{ item.value }}</div>
              <div class="statistics-title">{{ item.title }}</div>
              <div class="statistics-change" :class="{ 'positive': item.change > 0, 'negative': item.change < 0 }">
                {{ item.change > 0 ? '+' : '' }}{{ item.change }}%
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-divider />

        <div class="chart-container">
          <StatisticsChart 
            title="每日计算次数统计"
            :data="chartData.datasets" 
            :type="'line'"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import StatisticsChart from '@/components/report/StatisticsChart.vue';
import type { DateModelType } from 'element-plus';

// 日期选择相关
const dateRange = ref<[DateModelType, DateModelType]>([
  new Date(new Date().setDate(new Date().getDate() - 30)),
  new Date()
]);

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

// 统计数据
const summaryData = ref([
  { title: '总计算次数', value: '1,286', change: 12.8 },
  { title: '单次计算', value: '865', change: 8.2 },
  { title: '批量计算', value: '421', change: 22.4 },
  { title: '平均计算时间', value: '235ms', change: -15.6 },
]);

// 图表数据
const chartData = ref({
  labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  datasets: [
    {
      label: '单次计算',
      data: [65, 59, 80, 81, 56, 55, 40],
      fill: false,
      borderColor: '#409EFF',
      tension: 0.4
    },
    {
      label: '批量计算',
      data: [28, 48, 40, 19, 86, 27, 90],
      fill: false,
      borderColor: '#67C23A',
      tension: 0.4
    }
  ]
});

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: '每日计算次数统计'
    }
  }
});

// 方法
const handleDateChange = (val: any) => {
  console.log('日期范围变更:', val);
  // TODO: 根据日期范围获取数据
};

const refreshData = () => {
  // TODO: 刷新统计数据
  console.log('刷新数据');
};

// 生命周期钩子
onMounted(() => {
  // 初始化加载数据
  console.log('组件挂载完成，开始加载数据');
});
</script>

<style scoped>
.usage-statistics {
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

.statistics-container {
  margin-top: 20px;
}

.statistics-card {
  text-align: center;
  padding: 20px;
  margin-bottom: 20px;
}

.statistics-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  margin-bottom: 10px;
}

.statistics-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 5px;
}

.statistics-change {
  font-size: 12px;
}

.positive {
  color: var(--el-color-success);
}

.negative {
  color: var(--el-color-danger);
}

.chart-container {
  height: 400px;
  margin-top: 20px;
}
</style> 