<template>
  <div class="notification-stats">
    <div class="stat-item">
      <div class="stat-title">未读通知</div>
      <div class="stat-value">{{ stats.unread }}</div>
    </div>
    <el-divider />
    <div class="stat-item">
      <div class="stat-title">今日新增</div>
      <div class="stat-value">{{ stats.today }}</div>
    </div>
    <el-divider />
    <div class="stat-item">
      <div class="stat-title">本周通知</div>
      <div class="stat-value">{{ stats.thisWeek }}</div>
    </div>
    <el-divider />
    <div class="stat-breakdown">
      <h4>通知类型分布</h4>
      <div class="type-item" v-for="(count, type) in stats.typeBreakdown" :key="type">
        <span class="type-label">{{ getTypeLabel(type) }}</span>
        <el-progress
          :percentage="getTypePercentage(count)"
          :color="getTypeColor(type)"
          :show-text="false"
        />
        <span class="type-count">{{ count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { useNotificationStore } from '@/stores/notification/notification';

  const notificationStore = useNotificationStore();

  const stats = ref({
    unread: 0,
    today: 0,
    thisWeek: 0,
    typeBreakdown: {
      system: 0,
      business: 0,
      warning: 0,
      error: 0,
    },
  });

  const typeLabels = {
    system: '系统通知',
    business: '业务通知',
    warning: '警告通知',
    error: '错误通知',
  };

  const typeColors = {
    system: '#409EFF',
    business: '#67C23A',
    warning: '#E6A23C',
    error: '#F56C6C',
  };

  const getTypeLabel = (type: string) => {
    return typeLabels[type as keyof typeof typeLabels] || type;
  };

  const getTypeColor = (type: string) => {
    return typeColors[type as keyof typeof typeColors] || '#909399';
  };

  const getTypePercentage = (count: number) => {
    const total = Object.values(stats.value.typeBreakdown).reduce((sum, curr) => sum + curr, 0);
    return total === 0 ? 0 : Math.round((count / total) * 100);
  };

  const fetchStats = async () => {
    try {
      // 这里应该调用通知store中的方法获取统计数据
      // 暂时使用模拟数据
      stats.value = {
        unread: 5,
        today: 8,
        thisWeek: 23,
        typeBreakdown: {
          system: 10,
          business: 15,
          warning: 5,
          error: 2,
        },
      };
    } catch (error) {
      console.error('Failed to fetch notification stats:', error);
    }
  };

  onMounted(() => {
    fetchStats();
  });
</script>

<style scoped>
  .notification-stats {
    padding: 16px;
  }

  .stat-item {
    text-align: center;
    padding: 8px 0;
  }

  .stat-title {
    color: #909399;
    font-size: 14px;
    margin-bottom: 8px;
  }

  .stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
  }

  .stat-breakdown {
    margin-top: 16px;
  }

  .stat-breakdown h4 {
    margin: 0 0 16px 0;
    color: #303133;
  }

  .type-item {
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .type-label {
    width: 70px;
    font-size: 13px;
    color: #606266;
  }

  .type-count {
    width: 40px;
    text-align: right;
    font-size: 13px;
    color: #606266;
  }

  :deep(.el-progress) {
    flex: 1;
    margin: 0;
  }
</style>
