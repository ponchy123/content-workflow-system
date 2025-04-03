<template>
  <div class="notification-icon">
    <el-popover
      v-model:visible="visible"
      :width="400"
      trigger="click"
      @show="handleVisibleChange(true)"
      @hide="handleVisibleChange(false)"
    >
      <template #reference>
        <el-badge :value="unreadCount" :hidden="!unreadCount">
          <el-button :icon="Bell" circle />
        </el-badge>
      </template>

      <div class="notification-popover">
        <div class="notification-header">
          <h3>通知中心</h3>
          <div class="header-actions">
            <el-button text @click="showFilter = true">
              <el-icon><Filter /></el-icon>
              筛选
            </el-button>
            <el-button text @click="showSettings = true">
              <el-icon><Setting /></el-icon>
              设置
            </el-button>
          </div>
        </div>

        <NotificationList :filter="filter" @update="handleTotalUpdate" />

        <div class="notification-footer">
          <el-button type="primary" link @click="$router.push('/notifications')">
            查看全部
            <el-icon class="el-icon--right"><arrow-right /></el-icon>
          </el-button>
        </div>
      </div>
    </el-popover>

    <!-- 筛选抽屉 -->
    <el-drawer v-model="showFilter" title="通知筛选" direction="rtl" size="300px">
      <NotificationFilter v-model="filter" @update:modelValue="handleFilterChange" />
    </el-drawer>

    <!-- 设置抽屉 -->
    <el-drawer v-model="showSettings" title="通知设置" direction="rtl" size="400px">
      <NotificationSettings v-model="settings" @save="handleSettingsChange" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import { Bell, Filter, Setting } from '@element-plus/icons-vue';
  import { useNotification } from '@/composables/useNotification';
  import NotificationList from './NotificationList.vue';
  import NotificationFilter from './NotificationFilter.vue';
  import NotificationSettings from './NotificationSettings.vue';
  import type { NotificationFilter as FilterType } from '@/types/notification';

  const visible = ref(false);
  const showFilter = ref(false);
  const showSettings = ref(false);
  const filter = ref<FilterType>({
    search: '',
    module: '',
    type: '',
    read: null,
    startDate: null,
    endDate: null
  });
  const settings = ref({
    maxCount: 50,
    expirationDays: 30,
    soundEnabled: true,
    desktopNotification: true,
    groupByModule: false,
    autoCleanup: true,
  });
  const total = ref(0);
  const unreadCount = computed(() => total.value);

  const handleVisibleChange = (value: boolean) => {
    visible.value = value;
  };

  const handleFilterChange = (newFilter: FilterType) => {
    filter.value = newFilter;
  };

  const handleSettingsChange = () => {
    showSettings.value = false;
  };

  const handleTotalUpdate = (newTotal: number) => {
    total.value = newTotal;
  };
</script>

<style scoped>
  .notification-icon {
    display: inline-block;
  }

  .notification-popover {
    max-height: 600px;
    display: flex;
    flex-direction: column;
  }

  .notification-header {
    padding: var(--el-spacing-base);
    border-bottom: 1px solid var(--el-border-color-light);
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: var(--el-font-size-large);
      font-weight: var(--el-font-weight-bold);
      color: var(--el-text-color-primary);
    }

    .header-actions {
      display: flex;
      gap: var(--el-spacing-small);
    }
  }

  .notification-footer {
    padding: var(--el-spacing-base);
    border-top: 1px solid var(--el-border-color-light);
    text-align: center;
  }

  :deep(.el-badge__content) {
    z-index: 1;
  }

  :deep(.el-drawer__body) {
    padding: 0;
  }
</style>
