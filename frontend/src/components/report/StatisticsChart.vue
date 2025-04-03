<template>
  <div class="statistics-chart">
    <div class="chart-header">
      <div class="chart-title">{{ title }}</div>
      <div class="chart-controls">
        <el-select v-model="chartType" placeholder="图表类型">
          <el-option
            v-for="type in chartTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleDateChange"
        />
      </div>
    </div>

    <div class="chart-container" ref="chartRef">
      <div v-loading="loading" class="chart-content">
        <component
          :is="currentChartComponent"
          v-if="!loading"
          :data="chartData"
          :options="chartOptions"
          @chart-click="handleChartClick"
        />
      </div>
    </div>

    <div class="chart-footer">
      <div class="chart-summary">
        <div v-for="(stat, index) in statistics" :key="index" class="stat-item">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-trend" :class="stat.trend">
            {{ stat.percentage }}%
            <el-icon>
              <component :is="stat.trend === 'up' ? 'ArrowUp' : 'ArrowDown'" />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch, defineComponent } from 'vue';
  import { useElementSize } from '@vueuse/core';
  import { ArrowUp, ArrowDown } from '@element-plus/icons-vue';
  import { debounce } from 'lodash-es';
  import type { DateModelType } from 'element-plus';
  import * as echarts from 'echarts';

  // 临时导入图表组件，实际项目中需要创建这些组件
  const LineChart = defineComponent({ name: 'LineChart', render: () => null });
  const BarChart = defineComponent({ name: 'BarChart', render: () => null });
  const PieChart = defineComponent({ name: 'PieChart', render: () => null });
  const StackedBarChart = defineComponent({ name: 'StackedBarChart', render: () => null });

  type ChartType = 'line' | 'bar' | 'pie' | 'stacked';

  interface ChartTypeOption {
    label: string;
    value: ChartType;
  }

  interface StatItem {
    label: string;
    value: string;
    percentage: number;
    trend: 'up' | 'down';
  }

  interface ChartData {
    [key: string]: any;
  }

  interface ChartOptions {
    plugins?: {
      legend?: {
        position: string;
      };
      tooltip?: {
        enabled: boolean;
      };
    };
    scales?: {
      y?: {
        beginAtZero?: boolean;
        stacked?: boolean;
      };
      x?: {
        stacked?: boolean;
      };
    };
  }

  const props = defineProps<{
    title?: string;
    data: any[];
    type?: ChartType;
  }>();

  const chartRef = ref<HTMLElement | null>(null);
  const { width } = useElementSize(chartRef);
  const loading = ref(false);
  const chartType = ref<ChartType>(props.type || 'line');
  const dateRange = ref();

  const chartTypes: ChartTypeOption[] = [
    { label: '折线图', value: 'line' },
    { label: '柱状图', value: 'bar' },
    { label: '饼图', value: 'pie' },
    { label: '堆叠图', value: 'stacked' },
  ];

  const chartComponents = {
    line: LineChart,
    bar: BarChart,
    pie: PieChart,
    stacked: StackedBarChart,
  };

  const currentChartComponent = computed(() => chartComponents[chartType.value]);

  const statistics = ref<StatItem[]>([
    { label: '总计', value: '¥123,456', percentage: 12.5, trend: 'up' },
    { label: '平均值', value: '¥1,234', percentage: 5.2, trend: 'up' },
    { label: '环比', value: '98%', percentage: 2.1, trend: 'down' },
  ]);

  const chartOptions = computed<ChartOptions>(() => 
    getChartTypeSpecificOptions(chartType.value)
  );

  const chartData = computed(() => {
    return transformData(props.data, chartType.value);
  });

  // 处理图表点击事件
  const handleChartClick = (event: any) => {
    console.log('Chart clicked:', event);
  };

  // 处理日期范围变化
  const handleDateChange = debounce(async (dates: any) => {
    if (!dates?.[0] || !dates?.[1]) return;
    loading.value = true;
    try {
      await loadData(new Date(dates[0]), new Date(dates[1]));
    } finally {
      loading.value = false;
    }
  }, 300);

  // 图表自适应
  watch(width, () => {
    // 触发图表重绘
  });

  // 辅助函数
  function getChartTypeSpecificOptions(type: ChartType): ChartOptions {
    const baseOptions: ChartOptions = {
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          enabled: true,
        },
      },
    };

    const typeSpecificOptions: Record<ChartType, Partial<ChartOptions>> = {
      line: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
      bar: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
      pie: {},
      stacked: {
        scales: {
          y: {
            stacked: true,
          },
          x: {
            stacked: true,
          },
        },
      },
    };

    return { ...baseOptions, ...typeSpecificOptions[type] };
  }

  function transformData(data: any[], type: ChartType): ChartData {
    switch (type) {
      case 'pie':
        return transformToPieData(data);
      case 'stacked':
        return transformToStackedData(data);
      default:
        return data;
    }
  }

  function transformToPieData(data: any[]): ChartData {
    // 实现饼图数据转换逻辑
    return data;
  }

  function transformToStackedData(data: any[]): ChartData {
    // 实现堆叠图数据转换逻辑
    return data;
  }

  async function loadData(startDate: Date, endDate: Date): Promise<void> {
    // 实现数据加载逻辑
  }

  onMounted(() => {
    // 初始化逻辑
  });

  onUnmounted(() => {
    // 清理逻辑
  });
</script>

<style scoped>
  .statistics-chart {
    background: #fff;
    border-radius: 4px;
    padding: 20px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .chart-title {
    font-size: 16px;
    font-weight: bold;
  }

  .chart-controls {
    display: flex;
    gap: 12px;
  }

  .chart-container {
    position: relative;
    height: 400px;
  }

  .chart-content {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .chart-footer {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
  }

  .chart-summary {
    display: flex;
    justify-content: space-around;
  }

  .stat-item {
    text-align: center;
  }

  .stat-label {
    color: #909399;
    font-size: 14px;
  }

  .stat-value {
    font-size: 24px;
    font-weight: bold;
    margin: 8px 0;
  }

  .stat-trend {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
  }

  .stat-trend.up {
    color: #67c23a;
  }

  .stat-trend.down {
    color: #f56c6c;
  }
</style>
