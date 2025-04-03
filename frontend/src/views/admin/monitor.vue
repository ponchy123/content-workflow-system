<template>
  <div class="monitor-container">
    <el-row :gutter="20">
      <!-- 系统资源监控 -->
      <el-col :xs="24" :lg="12">
        <el-card class="mb-4">
          <template #header>
            <div class="card-header">
              <span>系统资源监控</span>
              <el-button-group>
                <el-button type="primary" size="small" @click="refreshSystemStatus">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
                <el-button type="success" size="small" @click="startAutoRefresh">
                  <el-icon><VideoPlay /></el-icon>
                  自动刷新
                </el-button>
              </el-button-group>
            </div>
          </template>
          
          <div class="resource-metrics">
            <div class="metric-item">
              <span class="metric-label">CPU使用率</span>
              <el-progress 
                :percentage="systemStatus.cpu" 
                :color="getDynamicColor(systemStatus.cpu)"
              />
            </div>
            <div class="metric-item">
              <span class="metric-label">内存使用率</span>
              <el-progress 
                :percentage="systemStatus.memory" 
                :color="getDynamicColor(systemStatus.memory)"
              />
            </div>
            <div class="metric-item">
              <span class="metric-label">磁盘使用率</span>
              <el-progress 
                :percentage="systemStatus.disk" 
                :color="getDynamicColor(systemStatus.disk)"
              />
            </div>
            <div class="metric-item">
              <span class="metric-label">网络带宽使用率</span>
              <el-progress 
                :percentage="systemStatus.network" 
                :color="getDynamicColor(systemStatus.network)"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 应用性能监控 -->
      <el-col :xs="24" :lg="12">
        <el-card class="mb-4">
          <template #header>
            <div class="card-header">
              <span>应用性能监控</span>
              <el-select v-model="timeRange" size="small">
                <el-option label="最近1小时" value="1h" />
                <el-option label="最近6小时" value="6h" />
                <el-option label="最近24小时" value="24h" />
              </el-select>
            </div>
          </template>
          <div ref="performanceChart" class="performance-chart"></div>
        </el-card>
      </el-col>

      <!-- 在线用户监控 -->
      <el-col :xs="24" :lg="12">
        <el-card class="mb-4">
          <template #header>
            <div class="card-header">
              <span>在线用户 ({{ onlineUsers.length }})</span>
              <el-button type="danger" size="small" @click="kickAllUsers">
                强制下线
              </el-button>
            </div>
          </template>
          <el-table :data="onlineUsers" style="width: 100%" height="350">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="ip" label="IP地址" />
            <el-table-column prop="loginTime" label="登录时间" />
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button 
                  type="danger" 
                  size="small"
                  @click="kickUser(scope.row)"
                >
                  下线
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 系统告警 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统告警</span>
              <el-button-group>
                <el-button type="primary" size="small" @click="acknowledgeAllAlerts">
                  全部确认
                </el-button>
                <el-button type="danger" size="small" @click="clearAllAlerts">
                  清空
                </el-button>
              </el-button-group>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="alert in alerts"
              :key="alert.id"
              :type="alert.type"
              :timestamp="alert.time"
              :color="getAlertColor(alert.level)"
            >
              {{ alert.message }}
              <template #dot>
                <el-icon :class="getAlertIcon(alert.level)">
                  <Warning v-if="alert.level === 'error'" />
                  <Bell v-else-if="alert.level === 'warning'" />
                  <InfoFilled v-else />
                </el-icon>
              </template>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, VideoPlay, Warning, Bell, InfoFilled } from '@element-plus/icons-vue';
import * as echarts from 'echarts';

interface Alert {
  id: number;
  type: 'success' | 'warning' | 'danger' | 'info' | 'primary';
  level: 'error' | 'warning' | 'info' | 'success';
  time: string;
  message: string;
}

// 系统状态
const systemStatus = ref({
  cpu: 45,
  memory: 68,
  disk: 72,
  network: 35
});

// 在线用户
const onlineUsers = ref([
  {
    id: 1,
    username: 'admin',
    ip: '192.168.1.100',
    loginTime: '2024-03-08 14:30:00'
  },
  {
    id: 2,
    username: 'user1',
    ip: '192.168.1.101',
    loginTime: '2024-03-08 15:00:00'
  }
]);

// 系统告警
const alerts = ref<Alert[]>([
  {
    id: 1,
    level: 'error',
    type: 'danger',
    time: '2024-03-08 15:30:00',
    message: 'CPU使用率超过90%'
  },
  {
    id: 2,
    level: 'warning',
    type: 'warning',
    time: '2024-03-08 15:25:00',
    message: '内存使用率超过80%'
  },
  {
    id: 3,
    level: 'info',
    type: 'info',
    time: '2024-03-08 15:20:00',
    message: '系统自动清理了过期日志'
  }
]);

// 性能图表
const timeRange = ref('1h');
const performanceChart = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

// 自动刷新
let refreshInterval: number | null = null;

// 获取动态颜色
const getDynamicColor = (value: number) => {
  if (value < 60) return '#67C23A';
  if (value < 80) return '#E6A23C';
  return '#F56C6C';
};

// 获取告警颜色
const getAlertColor = (level: string) => {
  switch (level) {
    case 'error':
      return '#F56C6C';
    case 'warning':
      return '#E6A23C';
    default:
      return '#909399';
  }
};

// 获取告警图标样式
const getAlertIcon = (level: string) => {
  return {
    'alert-icon': true,
    'is-error': level === 'error',
    'is-warning': level === 'warning',
    'is-info': level === 'info'
  };
};

// 刷新系统状态
const refreshSystemStatus = () => {
  // 模拟API调用
  systemStatus.value = {
    cpu: Math.floor(Math.random() * 100),
    memory: Math.floor(Math.random() * 100),
    disk: Math.floor(Math.random() * 100),
    network: Math.floor(Math.random() * 100)
  };
};

// 开启自动刷新
const startAutoRefresh = () => {
  if (refreshInterval) {
    window.clearInterval(refreshInterval);
    refreshInterval = null;
    ElMessage.info('已停止自动刷新');
  } else {
    refreshInterval = window.setInterval(refreshSystemStatus, 5000);
    ElMessage.success('已开启自动刷新（5秒）');
  }
};

// 踢出用户
const kickUser = (user: any) => {
  ElMessageBox.confirm(
    `确定要将用户 ${user.username} 强制下线吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    onlineUsers.value = onlineUsers.value.filter(u => u.id !== user.id);
    ElMessage.success(`已将用户 ${user.username} 强制下线`);
  });
};

// 踢出所有用户
const kickAllUsers = () => {
  ElMessageBox.confirm(
    '确定要将所有用户强制下线吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    onlineUsers.value = [];
    ElMessage.success('已将所有用户强制下线');
  });
};

// 确认所有告警
const acknowledgeAllAlerts = () => {
  ElMessage.success('已确认所有告警');
};

// 清空告警
const clearAllAlerts = () => {
  ElMessageBox.confirm(
    '确定要清空所有告警记录吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    alerts.value = [];
    ElMessage.success('已清空所有告警');
  });
};

// 初始化性能图表
const initPerformanceChart = () => {
  if (!performanceChart.value) return;

  chart = echarts.init(performanceChart.value);
  const option = {
    title: {
      text: '系统性能趋势'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['响应时间', 'QPS', '错误率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: Array.from({ length: 24 }, (_, i) => `${i}:00`)
    },
    yAxis: [
      {
        type: 'value',
        name: '响应时间(ms)'
      },
      {
        type: 'value',
        name: 'QPS/错误率',
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '响应时间',
        type: 'line',
        data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 500))
      },
      {
        name: 'QPS',
        type: 'line',
        yAxisIndex: 1,
        data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 1000))
      },
      {
        name: '错误率',
        type: 'line',
        yAxisIndex: 1,
        data: Array.from({ length: 24 }, () => (Math.random() * 2).toFixed(2))
      }
    ]
  };

  chart.setOption(option);
};

// 监听窗口大小变化
const handleResize = () => {
  chart?.resize();
};

onMounted(() => {
  refreshSystemStatus();
  initPerformanceChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (refreshInterval) {
    window.clearInterval(refreshInterval);
  }
  window.removeEventListener('resize', handleResize);
  chart?.dispose();
});
</script>

<style scoped>
.monitor-container {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-metrics {
  padding: 20px 0;
}

.metric-item {
  margin-bottom: 20px;
}

.metric-item:last-child {
  margin-bottom: 0;
}

.metric-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.performance-chart {
  height: 350px;
}

.alert-icon {
  font-size: 16px;
}

.is-error {
  color: #F56C6C;
}

.is-warning {
  color: #E6A23C;
}

.is-info {
  color: #909399;
}

:deep(.el-timeline-item__node) {
  background-color: transparent;
  border: none;
}

:deep(.el-timeline-item__dot) {
  left: -1px;
}
</style> 