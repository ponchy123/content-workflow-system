<template>
  <div class="report-view">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <span>数据统计报表</span>
          <el-button-group>
            <el-button type="primary" @click="refreshData"> 刷新数据 </el-button>
            <el-button @click="exportReport"> 导出报表 </el-button>
          </el-button-group>
        </div>
      </template>

      <div class="report-content">
        <statistics-chart :title="chartTitle" :data="chartData" :type="chartType" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import StatisticsChart from '@/components/report/StatisticsChart.vue';
  
  type ChartType = 'line' | 'bar' | 'pie' | 'stacked';
  
  const chartTitle = ref('运费统计分析');
  const chartType = ref<ChartType>('line');
  const chartData = ref([
    // 示例数据
    { date: '2024-01', value: 1200 },
    { date: '2024-02', value: 1400 },
    { date: '2024-03', value: 1100 },
  ]);

  const refreshData = async () => {
    // 实现数据刷新逻辑
  };

  const exportReport = () => {
    // 实现报表导出逻辑
  };
</script>

<style scoped>
  .report-view {
    padding: 20px;
  }

  .report-card {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .report-content {
    min-height: 500px;
  }
</style>
