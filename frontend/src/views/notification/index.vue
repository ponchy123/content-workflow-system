<template>
  <div class="notification-center">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <el-card class="filter-card">
          <template #header>
            <div class="card-header">
              <span>通知筛选</span>
              <el-button-group>
                <el-button type="primary" @click="markAllAsRead">全部标记为已读</el-button>
                <el-button type="danger" @click="clearAll">清空通知</el-button>
              </el-button-group>
            </div>
          </template>
          <notification-filter @filter-change="handleFilterChange" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>通知统计</span>
            </div>
          </template>
          <notification-stats />
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span>通知列表</span>
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="list">列表视图</el-radio-button>
                <el-radio-button value="timeline">时间线</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div v-if="viewMode === 'list'">
            <notification-list :filter="currentFilter" />
          </div>
          <div v-else>
            <notification-timeline :filter="currentFilter" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import { ElMessage } from 'element-plus';
  import NotificationFilter from '@/components/notification/NotificationFilter.vue';
  import NotificationStats from '@/components/notification/NotificationStats.vue';
  import NotificationList from '@/components/notification/NotificationList.vue';
  import NotificationTimeline from '@/components/notification/NotificationTimeline.vue';
  import { useNotificationStore } from '@/stores/notification/notification';
  import type { NotificationType } from '@/types/notification';

  interface NotificationFilter {
    search: string;
    module: string;
    type: NotificationType | null;
    read: boolean;
    startDate: Date | null;
    endDate: Date | null;
  }

  const notificationStore = useNotificationStore();
  const viewMode = ref('list');
  const currentFilter = ref<NotificationFilter>({
    search: '',
    module: '',
    type: null,
    read: false,
    startDate: null,
    endDate: null
  });

  const handleFilterChange = (filter: NotificationFilter) => {
    currentFilter.value = filter;
  };

  const markAllAsRead = async () => {
    try {
      await notificationStore.markAllAsRead();
      ElMessage.success('已将所有通知标记为已读');
    } catch (error) {
      ElMessage.error('操作失败，请重试');
    }
  };

  const clearAll = async () => {
    try {
      await notificationStore.clearAllNotifications();
      ElMessage.success('已清空所有通知');
    } catch (error) {
      ElMessage.error('操作失败，请重试');
    }
  };
</script>

<style scoped>
  .notification-center {
    padding: 20px;
  }

  .mb-4 {
    margin-bottom: 16px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .filter-card,
  .stats-card,
  .list-card {
    width: 100%;
  }

  .list-card {
    min-height: 600px;
  }
</style>
