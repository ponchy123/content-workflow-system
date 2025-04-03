<template>
  <div class="admin-dashboard-container">
    <h1>管理员仪表盘</h1>
    
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.totalUsers }}</div>
          <div class="stat-label">总用户数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.activeUsers }}</div>
          <div class="stat-label">活跃用户</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.totalOrders }}</div>
          <div class="stat-label">总订单数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.systemStatus }}</div>
          <div class="stat-label">系统状态</div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>系统资源监控</span>
              <el-radio-group v-model="monitorType" size="small">
                <el-radio-button value="cpu">CPU</el-radio-button>
                <el-radio-button value="memory">内存</el-radio-button>
                <el-radio-button value="disk">磁盘</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-placeholder">
            <el-empty description="系统资源图表加载中"></el-empty>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>用户活跃度</span>
              <el-select v-model="timeRange" placeholder="选择时间范围" size="small">
                <el-option label="今日" value="today"></el-option>
                <el-option label="本周" value="week"></el-option>
                <el-option label="本月" value="month"></el-option>
              </el-select>
            </div>
          </template>
          <div class="chart-placeholder">
            <el-empty description="用户活跃度图表加载中"></el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="log-table">
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div>
            <el-input placeholder="搜索日志" style="width: 200px; margin-right: 10px;" size="small" />
            <el-button type="primary" size="small">查询</el-button>
          </div>
        </div>
      </template>
      <el-table :data="systemLogs" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180"></el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="scope">
            <el-tag :type="getLogLevelType(scope.row.level)" size="small">{{ scope.row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="150"></el-table-column>
        <el-table-column prop="message" label="消息"></el-table-column>
        <el-table-column prop="user" label="用户" width="120"></el-table-column>
        <el-table-column label="操作" width="100">
          <template #default>
            <el-button link size="small">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-container">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="100"
          :page-size="10"
        />
      </div>
    </el-card>
  </div>
</template>

<script lang="ts">
import type { DirectiveBinding } from 'vue';

// 创建权限指令对象
const vPermission = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const permissionCode = binding.value;
    const userPermissions = localStorage.getItem('userPermissions')
      ? JSON.parse(localStorage.getItem('userPermissions') || '[]')
      : [];

    // 管理员角色直接通过权限检查
    const userRoles = localStorage.getItem('userRoles')
      ? JSON.parse(localStorage.getItem('userRoles') || '[]')
      : [];

    if (userRoles.includes('admin')) {
      return;
    }

    // 检查是否有权限
    if (!userPermissions.includes(permissionCode)) {
      el.parentNode?.removeChild(el);
    }
  },
};

export default {
  directives: {
    permission: vPermission,
  },
};
</script>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';

// 统计数据
const stats = reactive({
  totalUsers: '156',
  activeUsers: '48',
  totalOrders: '2,354',
  systemStatus: '正常'
});

// 监控类型
const monitorType = ref('cpu');

// 时间范围选择
const timeRange = ref('week');

// 系统日志数据
const systemLogs = ref([
  {
    timestamp: '2025-03-09 20:15:36',
    level: 'INFO',
    module: '用户认证',
    message: '用户登录成功',
    user: 'admin'
  },
  {
    timestamp: '2025-03-09 19:45:22',
    level: 'WARNING',
    module: '订单处理',
    message: '订单处理延迟超过预期阈值',
    user: 'system'
  },
  {
    timestamp: '2025-03-09 19:30:18',
    level: 'ERROR',
    module: '费率计算',
    message: '计算引擎出现异常，已自动恢复',
    user: 'system'
  },
  {
    timestamp: '2025-03-09 18:55:41',
    level: 'INFO',
    module: '系统监控',
    message: '系统资源使用率正常',
    user: 'system'
  },
  {
    timestamp: '2025-03-09 18:22:10',
    level: 'INFO',
    module: '用户管理',
    message: '新增用户账号',
    user: 'admin'
  }
]);

onMounted(() => {
  // 在实际应用中，这里会从API获取数据
  console.log('管理员仪表盘加载完成');
});

// 获取日志级别对应的标签类型
const getLogLevelType = (level: string) => {
  const levelMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'SUCCESS': 'success'
  };
  return levelMap[level] || 'info';
};
</script>

<style scoped>
.admin-dashboard-container {
  padding: 20px;
}

h1 {
  margin-bottom: 24px;
  font-size: 24px;
  color: var(--el-color-primary);
}

.stat-card {
  text-align: center;
  padding: 10px 0;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-color-primary);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.chart-row {
  margin-bottom: 15px;
}

.chart-card {
  height: 350px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-placeholder {
  height: 280px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.log-table {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
