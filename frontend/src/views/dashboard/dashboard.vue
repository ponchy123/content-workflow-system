<template>
  <div class="dashboard-container">
    <h1>仪表盘</h1>
    <div class="header-section">
      <div>
        <el-button type="primary" size="small" @click="refreshCharts" icon="Refresh">
          刷新图表
        </el-button>
      </div>
      <el-switch
        v-model="advancedMode"
        active-text="高级模式"
        inactive-text="基础模式"
        class="mode-switch"
      />
    </div>
    
    <!-- 统计卡片区域，添加固定高度限制并减小更多 -->
    <el-row :gutter="10">
      <el-col :span="6">
        <el-card class="stat-card" style="max-height: 60px; height: 60px !important;">
          <div class="stat-value">{{ stats.totalOrders }}</div>
          <div class="stat-label">总订单数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" style="max-height: 60px; height: 60px !important;">
          <div class="stat-value">{{ stats.todayOrders }}</div>
          <div class="stat-label">今日订单</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" style="max-height: 60px; height: 60px !important;">
          <div class="stat-value">{{ stats.pendingOrders }}</div>
          <div class="stat-label">待处理</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" style="max-height: 60px; height: 60px !important;">
          <div class="stat-value">{{ stats.completedOrders }}</div>
          <div class="stat-label">已完成</div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 - 更直接的高度强制设置 -->
    <div style="margin-top: 5px; margin-bottom: 15px; height: 600px !important; min-height: 600px !important;">
      <div style="display: flex; justify-content: space-between; height: 100% !important; min-height: 580px !important;">
        <div style="width: 48%; height: 100% !important;">
          <el-card class="chart-card" style="height: 100% !important; min-height: 580px !important; overflow: visible !important;">
            <template #header>
              <div class="card-header">
                <span>订单统计</span>
                <el-select v-model="timeRange" placeholder="选择时间范围" size="small">
                  <el-option label="今日" value="today"></el-option>
                  <el-option label="本周" value="week"></el-option>
                  <el-option label="本月" value="month"></el-option>
                </el-select>
              </div>
            </template>
            <div ref="orderChartRef" style="height: 520px !important; width: 100%; position: relative;"></div>
          </el-card>
        </div>
        <div style="width: 48%; height: 100% !important;">
          <el-card class="chart-card" style="height: 100% !important; min-height: 580px !important; overflow: visible !important;">
            <template #header>
              <div class="card-header">
                <span>费率分布</span>
              </div>
            </template>
            <div ref="rateChartRef" style="height: 520px !important; width: 100%; position: relative;"></div>
          </el-card>
        </div>
      </div>
    </div>
    
    <!-- 高级模式内容和后续内容保持不变 -->
    <el-row :gutter="20" class="mb-4" v-if="advancedMode">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :component="icons.Document" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayOrders }}</div>
              <div class="stat-label">今日订单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon :component="icons.Timer" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pendingOrders }}</div>
              <div class="stat-label">待处理订单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon :component="icons.Money" />
            </div>
            <div class="stat-info">
              <div class="stat-value">${{ stats.totalAmount }}</div>
              <div class="stat-label">总计费用</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mb-4" v-if="advancedMode">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon :component="icons.TrendCharts" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completionRate }}%</div>
              <div class="stat-label">完成率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon :component="icons.User" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.activeUsers }}</div>
              <div class="stat-label">在线用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon danger">
              <el-icon :component="icons.Monitor" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.systemLoad }}%</div>
              <div class="stat-label">系统负载</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 高级模式系统状态 -->
    <el-row :gutter="20" class="mb-4" v-if="advancedMode">
      <el-col :span="24">
        <el-card class="mb-4">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">CPU使用率</div>
                <el-progress :percentage="32" :stroke-width="10" />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">内存使用率</div>
                <el-progress :percentage="45" :stroke-width="10" status="warning" />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">磁盘使用率</div>
                <el-progress :percentage="68" :stroke-width="10" status="success" />
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 高级模式运费计算趋势图表 -->
    <el-row :gutter="20" class="mb-4" v-if="advancedMode">
      <el-col :span="24">
        <el-card class="chart-card freight-chart-card">
          <template #header>
            <div class="card-header">
              <span>运费计算趋势</span>
              <div class="chart-controls">
                <el-radio-group v-model="freightTimeRange" size="small">
                  <el-radio-button value="week">周</el-radio-button>
                  <el-radio-button value="month">月</el-radio-button>
                  <el-radio-button value="quarter">季度</el-radio-button>
                  <el-radio-button value="year">年</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="chart-container" style="height: 450px !important; min-height: 450px !important;">
            <div ref="freightTrendChart" style="width: 100%; height: 450px !important; min-height: 450px !important;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 公告和欢迎卡片 - 高级模式 -->
    <el-row :gutter="20" class="mb-4" v-if="advancedMode">
      <el-col :span="12">
        <el-card class="announcement-card">
          <template #header>
            <div class="card-header">
              <span>系统公告</span>
              <el-button link>查看所有</el-button>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(announcement, index) in announcements"
              :key="index"
              :type="announcement.type"
              :timestamp="announcement.date"
            >
              {{ announcement.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <span>欢迎回来</span>
            </div>
          </template>
          <div class="welcome-content">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="用户名">
                <span class="username">{{ username || 'admin' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="上次登录时间">
                {{ lastLoginTime }}
              </el-descriptions-item>
              <el-descriptions-item label="登录位置">
                {{ lastLoginLocation }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近订单表格 -->
    <el-card class="recent-orders">
      <template #header>
        <div class="card-header">
          <span>最近订单</span>
          <el-button link>查看更多</el-button>
        </div>
      </template>
      <el-table :data="recentOrders" style="width: 100%">
        <el-table-column prop="order_id" label="订单编号" width="180"></el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
        <el-table-column prop="origin" label="发货地"></el-table-column>
        <el-table-column prop="destination" label="目的地"></el-table-column>
        <el-table-column prop="total_amount" label="总费用"></el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default>
            <el-button link size="small">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, watch, markRaw } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import * as echarts from 'echarts';
import {
  Document,
  Timer,
  Money,
  TrendCharts,
  User,
  Lock,
  Monitor,
  Download,
  Setting
} from '@element-plus/icons-vue';

// 模式切换
const advancedMode = ref(false);

// 标记图标组件为非响应式
const icons = {
  Document: markRaw(Document),
  Timer: markRaw(Timer),
  Money: markRaw(Money),
  TrendCharts: markRaw(TrendCharts),
  User: markRaw(User),
  Monitor: markRaw(Monitor),
  Lock: markRaw(Lock),
  Download: markRaw(Download),
  Setting: markRaw(Setting)
};

const router = useRouter();
const username = ref('');
const chartTimeRange = ref('week');
const timeRange = ref('week');

// 高级图表引用和实例
const freightTimeRange = ref('month');
const freightTrendChart = ref(null);
let freightChart: any = null;

// 基础图表引用
const orderChartRef = ref<HTMLElement | null>(null);
const rateChartRef = ref<HTMLElement | null>(null);
let orderChart: any = null;
let rateChart: any = null;

// 统计数据
const stats = reactive({
  totalOrders: '2,354',
  todayOrders: 42,
  pendingOrders: 8,
  completedOrders: '2,298',
  totalAmount: '12,580.00',
  completionRate: 94,
  activeUsers: 28,
  systemLoad: 32
});

// 系统公告
const announcements = ref([
  {
    date: '2024-03-07 10:00',
    content: '系统已更新至v2.0.1版本，新增多项功能优化',
    type: 'success' as const
  },
  {
    date: '2024-03-06 15:30',
    content: '燃油费率将于下周一进行调整，请注意查看通知',
    type: 'warning' as const
  },
  {
    date: '2024-03-05 09:15',
    content: '新增快递区域查询功能，欢迎试用',
    type: 'info' as const
  }
]);

const lastLoginTime = ref('2024-03-07 09:30:25');
const lastLoginLocation = ref('上海市');

// 近期订单数据
const recentOrders = ref([
  {
    order_id: 'ORD-2025-0001',
    created_at: '2025-03-09 12:34:56',
    origin: '上海',
    destination: '北京',
    total_amount: '¥128.50',
    status: '已完成'
  },
  {
    order_id: 'ORD-2025-0002',
    created_at: '2025-03-09 14:22:33',
    origin: '广州',
    destination: '深圳',
    total_amount: '¥56.80',
    status: '运输中'
  },
  {
    order_id: 'ORD-2025-0003',
    created_at: '2025-03-09 16:45:12',
    origin: '成都',
    destination: '重庆',
    total_amount: '¥95.20',
    status: '待处理'
  },
  {
    order_id: 'ORD-2025-0004',
    created_at: '2025-03-09 18:10:45',
    origin: '杭州',
    destination: '苏州',
    total_amount: '¥72.00',
    status: '已完成'
  },
  {
    order_id: 'ORD-2025-0005',
    created_at: '2025-03-09 19:30:22',
    origin: '天津',
    destination: '青岛',
    total_amount: '¥135.60',
    status: '已取消'
  }
]);

// 初始化订单统计图表
function initOrderChart() {
  if (!orderChartRef.value) return;
  
  // 清除旧图表实例
  if (orderChart) {
    orderChart.dispose();
  }
  
  orderChart = echarts.init(orderChartRef.value);
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['订单数量', '完成订单', '待处理订单'],
      bottom: '5%',
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      axisLabel: { fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      },
      axisLabel: { fontSize: 12 }
    },
    series: [
      {
        name: '订单数量',
        type: 'line',
        smooth: true,
        data: [120, 132, 101, 134, 90, 230, 210],
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '完成订单',
        type: 'bar',
        data: [80, 102, 91, 124, 70, 180, 170],
        itemStyle: {
          color: '#67C23A'
        }
      },
      {
        name: '待处理订单',
        type: 'bar',
        data: [40, 30, 10, 10, 20, 50, 40],
        itemStyle: {
          color: '#E6A23C'
        }
      }
    ]
  };
  
  orderChart.setOption(option);
  
  // 多次尝试调整大小，确保渲染完成
  [0, 200, 500, 1000].forEach(delay => {
    setTimeout(() => {
      orderChart?.resize();
    }, delay);
  });
}

// 初始化费率分布图表
function initRateChart() {
  if (!rateChartRef.value) return;
  
  // 清除旧图表实例
  if (rateChart) {
    rateChart.dispose();
  }
  
  rateChart = echarts.init(rateChartRef.value);
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: '10%',
      data: ['基础运费', '附加费', '燃油附加费', '其他费用'],
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { fontSize: 12 }
    },
    series: [
      {
        name: '费用分布',
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '40%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 1
        },
        label: {
          show: false,
          position: 'center',
          fontSize: 11
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 65, name: '基础运费', itemStyle: { color: '#409EFF' } },
          { value: 15, name: '附加费', itemStyle: { color: '#67C23A' } },
          { value: 12, name: '燃油附加费', itemStyle: { color: '#E6A23C' } },
          { value: 8, name: '其他费用', itemStyle: { color: '#F56C6C' } }
        ]
      }
    ]
  };
  
  rateChart.setOption(option);
  
  // 多次尝试调整大小，确保渲染完成
  [0, 200, 500, 1000].forEach(delay => {
    setTimeout(() => {
      rateChart?.resize();
    }, delay);
  });
}

// 初始化运费趋势图表
function initFreightTrendChart() {
  if (!freightTrendChart.value) return;
  
  // 清除旧图表实例
  if (freightChart) {
    freightChart.dispose();
  }
  
  freightChart = echarts.init(freightTrendChart.value);
  
  // 根据不同的时间范围设置不同的数据
  let xAxisData = [];
  let standardFreight = [];
  let expressFreight = [];
  let economyFreight = [];
  
  if (freightTimeRange.value === 'week') {
    xAxisData = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    standardFreight = [120, 132, 101, 134, 90, 230, 210];
    expressFreight = [150, 132, 121, 154, 130, 180, 160];
    economyFreight = [80, 92, 81, 114, 70, 130, 110];
  } else if (freightTimeRange.value === 'month') {
    xAxisData = Array.from({length: 30}, (_, i) => `${i+1}日`);
    standardFreight = Array.from({length: 30}, () => Math.floor(Math.random() * 100) + 100);
    expressFreight = Array.from({length: 30}, () => Math.floor(Math.random() * 150) + 120);
    economyFreight = Array.from({length: 30}, () => Math.floor(Math.random() * 80) + 70);
  } else if (freightTimeRange.value === 'quarter') {
    xAxisData = ['1月', '2月', '3月'];
    standardFreight = [320, 332, 301];
    expressFreight = [350, 332, 321];
    economyFreight = [280, 292, 281];
  } else { // year
    xAxisData = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    standardFreight = [120, 132, 101, 134, 90, 230, 210, 182, 191, 234, 290, 330];
    expressFreight = [220, 182, 191, 234, 290, 330, 310, 123, 442, 321, 90, 149];
    economyFreight = [150, 232, 201, 154, 190, 330, 410, 182, 191, 234, 290, 330];
  }
  
  const option = {
    title: {
      text: '运费走势分析',
      subtext: '按' + (freightTimeRange.value === 'week' ? '周' : 
                      freightTimeRange.value === 'month' ? '月' : 
                      freightTimeRange.value === 'quarter' ? '季度' : '年') + '统计',
      left: 'center',
      top: '0%',
      textStyle: {
        fontSize: 16
      },
      subtextStyle: {
        fontSize: 12
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['标准运费', '快递运费', '经济运费'],
      top: '10%',
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '25%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: {
        fontSize: 11,
        rotate: xAxisData.length > 12 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} 元',
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '标准运费',
        type: 'line',
        smooth: true,
        data: standardFreight,
        itemStyle: {
          color: '#409EFF'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 7
      },
      {
        name: '快递运费',
        type: 'line',
        smooth: true,
        data: expressFreight,
        itemStyle: {
          color: '#67C23A'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 7
      },
      {
        name: '经济运费',
        type: 'line',
        smooth: true,
        data: economyFreight,
        itemStyle: {
          color: '#E6A23C'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 7
      }
    ]
  };
  
  freightChart.setOption(option);
  
  // 确保图表适应容器
  [0, 100, 300, 500].forEach(delay => {
    setTimeout(() => {
      freightChart?.resize();
    }, delay);
  });
}

// 加载用户信息
function loadUserInfo() {
  try {
    const userInfoStr = localStorage.getItem('userInfo');
    if (!userInfoStr) return false;
    
    if (userInfoStr === '[object Object]') {
      username.value = 'admin';
      return true;
    }
    
    try {
      const userInfo = JSON.parse(userInfoStr);
      username.value = userInfo.username || '访客';
      return true;
    } catch (parseError) {
      username.value = 'admin';
      return true;
    }
  } catch (e) {
    username.value = '用户';
    return true;
  }
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    '已完成': 'success',
    '运输中': 'primary',
    '待处理': 'warning',
    '已取消': 'danger'
  };
  return statusMap[status] || 'info';
};

// 监听窗口大小变化，重绘图表
window.addEventListener('resize', () => {
  if (orderChart) orderChart.resize();
  if (rateChart) rateChart.resize();
  if (freightChart) freightChart.resize();
});

// 添加一个强制调整图表大小的函数
function forcedResizeCharts() {
  requestAnimationFrame(() => {
    if (orderChart) orderChart.resize({ animation: { duration: 0 }});
    if (rateChart) rateChart.resize({ animation: { duration: 0 }});
    
    // 在高级模式下也调整运费趋势图表大小
    if (advancedMode.value && freightChart) {
      freightChart.resize({ animation: { duration: 0 }});
    }
  });
}

// 修改刷新图表的方法，使其更加可靠
function refreshCharts() {
  console.log('手动刷新图表');
  
  // 确保容器高度
  if (orderChartRef.value) {
    orderChartRef.value.style.height = '520px';
    orderChartRef.value.style.minHeight = '520px';
  }
  
  if (rateChartRef.value) {
    rateChartRef.value.style.height = '520px';
    rateChartRef.value.style.minHeight = '520px';
  }
  
  // 先尝试重新初始化
  if (orderChartRef.value) {
    initOrderChart();
  }
  
  if (rateChartRef.value) {
    initRateChart();
  }
  
  // 强制调整图表大小
  forcedResizeCharts();
  
  // 然后多次尝试调整大小
  [100, 300, 600, 1000].forEach(delay => {
    setTimeout(() => {
      // 再次确保容器高度
      if (orderChartRef.value) {
        orderChartRef.value.style.height = '520px';
      }
      if (rateChartRef.value) {
        rateChartRef.value.style.height = '520px';  
      }
      forcedResizeCharts();
    }, delay);
  });
}

// 添加触发器监听DOM更新
onMounted(() => {
  // 立即初始化图表并多次尝试刷新以确保显示
  initOrderChart();
  initRateChart();
  
  // 如果默认就是高级模式，也初始化高级模式图表
  if (advancedMode.value) {
    initFreightTrendChart();
  }
  
  // 加载用户信息
  loadUserInfo();
  
  // 添加MutationObserver监听DOM变化并刷新图表
  const observer = new MutationObserver(() => {
    forcedResizeCharts();
  });
  
  // 监听整个容器
  if (orderChartRef.value && orderChartRef.value.parentElement) {
    observer.observe(orderChartRef.value.parentElement, { attributes: true, childList: true });
  }
  
  // 多次尝试重绘，确保图表正确渲染
  const resizeTimers = [100, 300, 500, 1000];
  resizeTimers.forEach(delay => {
    setTimeout(() => {
      forcedResizeCharts();
    }, delay);
  });
  
  console.log('仪表盘加载完成');
  
  return () => {
    observer.disconnect();
  };
});

// 监听高级模式变化，切换时初始化对应图表
watch(advancedMode, (newVal) => {
  if (newVal) {
    // 切换到高级模式时，初始化高级模式图表
    setTimeout(() => {
      initFreightTrendChart();
    }, 100);
  } else {
    // 切换回基础模式时，重新调整基础图表大小
    setTimeout(() => {
      if (orderChart) orderChart.resize();
      if (rateChart) rateChart.resize();
    }, 100);
  }
});

// 添加对freightTimeRange变化的监听，切换时刷新图表
watch(freightTimeRange, () => {
  if (advancedMode.value && freightTrendChart.value) {
    setTimeout(() => {
      initFreightTrendChart();
    }, 100);
  }
});

// 重新渲染
setTimeout(refreshCharts, 500);
setTimeout(refreshCharts, 1000);

onBeforeUnmount(() => {
  // 销毁图表实例
  if (orderChart) {
    orderChart.dispose();
    orderChart = null;
  }
  if (rateChart) {
    rateChart.dispose();
    rateChart = null;
  }
  if (freightChart) {
    freightChart.dispose();
    freightChart = null;
  }
  // 移除窗口大小变化监听
  window.removeEventListener('resize', () => {});
});
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

h1 {
  margin-bottom: 24px;
  font-size: 24px;
  color: var(--el-color-primary);
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.mode-switch {
  margin-right: 10px;
}

.mb-4 {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 0 !important;
  margin-bottom: 8px;
  box-shadow: var(--el-box-shadow-light);
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  min-height: unset !important; /* 移除最小高度限制 */
}

/* 更强的选择器权重，确保覆盖全局样式 */
.dashboard-container .el-row .el-col .stat-card :deep(.el-card__body) {
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: unset !important;
  max-height: 60px !important;
}

.stat-value {
  font-size: 18px; /* 进一步减小字体大小 */
  font-weight: bold;
  color: var(--el-color-primary);
  margin-bottom: 0px; /* 减少到零 */
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1;
  margin: 0;
  padding: 0;
}

/* 强制图表卡片高度 */
.chart-card {
  height: 600px !important;
  min-height: 580px !important;
  display: flex;
  flex-direction: column;
}

.chart-card :deep(.el-card__body) {
  flex: 1;
  padding: 5px !important;
  overflow: visible !important;
  height: auto !important;
  min-height: 520px !important;
}

.chart-card :deep(.el-card__header) {
  padding: 8px 10px !important;
  min-height: auto !important;
}

/* 图表区域强制高度 */
.dashboard-container :deep([ref="orderChartRef"]),
.dashboard-container :deep([ref="rateChartRef"]) {
  height: 520px !important;
  min-height: 520px !important;
  width: 100% !important;
  position: relative;
}

.chart-row {
  margin-bottom: 20px;
  height: 520px;
  min-height: 520px;
}

.chart-card {
  height: 480px;
}

.chart-container {
  height: 420px !important;
  min-height: 420px !important;
  width: 100%;
}

/* 图表卡片专用样式 */
.dashboard-container :deep(.el-card.chart-card) {
  height: 600px !important;
  min-height: 580px !important;
  overflow: visible !important;
}

.dashboard-container :deep(.el-card.chart-card .el-card__body) {
  height: calc(100% - 50px) !important;
  min-height: 520px !important;
  padding: 5px !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  min-height: 38px;
}

.el-card :deep(.el-card__header) {
  padding: 8px 10px;
}

.el-card :deep(.el-card__body) {
  padding: 10px;
}

.recent-orders {
  margin-bottom: 20px;
}

/* 高级模式样式 */
.stat-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 50px;
  height: 50px;
  border-radius: 8px;
  margin-right: 20px;
  color: #fff;
}

.stat-icon.warning {
  background-color: #e6a23c;
}

.stat-icon.success {
  background-color: #67c23a;
}

.stat-icon.info {
  background-color: #909399;
}

.stat-icon.primary {
  background-color: #409eff;
}

.stat-icon.danger {
  background-color: #f56c6c;
}

.stat-info {
  flex: 1;
}

.status-item {
  padding: 10px;
}

.status-label {
  margin-bottom: 8px;
  color: #606266;
}

.announcement-card, .welcome-card {
  height: 100%;
}

.announcement-card :deep(.el-timeline) {
  padding: 20px;
  height: 200px;
  overflow-y: auto;
}

.welcome-content {
  padding: 20px 0;
  height: 200px;
  display: flex;
  align-items: center;
}

.welcome-content :deep(.el-descriptions) {
  width: 100%;
}

.username {
  color: #409eff;
  font-weight: bold;
}

/* 确保图表完全显示 */
.el-card__body {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
}

/* 确保图表占满容器 */
.full-height {
  height: 100%;
  min-height: 400px;
}

/* 红框区域样式 */
.el-row .el-col .el-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 5px 15px;
  height: 100%;
}

/* 高级模式运费计算趋势图表 */
.freight-chart-card {
  height: 510px !important;
  min-height: 510px !important;
}

.freight-chart-card :deep(.el-card__body) {
  padding: 0 !important;
  height: calc(100% - 50px) !important;
  min-height: 460px !important;
}

.freight-chart-card .chart-container {
  height: 100% !important;
  width: 100%;
  padding: 0;
}

.freight-chart-card .el-radio-group {
  margin-left: 15px;
}

.chart-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
</style> 