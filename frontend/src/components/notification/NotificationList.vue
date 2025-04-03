<script setup lang="ts">
  import { ref, computed, onMounted, watch } from 'vue';
  import { storeToRefs } from 'pinia';
  import {
    ElPopover,
    ElBadge,
    ElButton,
    ElButtonGroup,
    ElForm,
    ElFormItem,
    ElInput,
    ElSelect,
    ElOption,
    ElDatePicker,
    ElInputNumber,
    ElSwitch,
    ElEmpty,
    ElDialog,
    ElDescriptions,
    ElDescriptionsItem,
    ElTag,
    ElTimeline,
    ElTimelineItem,
    ElCard,
    ElLink,
    ElIcon,
  } from 'element-plus';
  import { Bell, Filter, Setting, Delete, Check, ArrowRight } from '@element-plus/icons-vue';
  import { useNotificationStore } from '@/stores/notification/notification';
  import { useNotificationConfig } from '@/stores/notification/config';
  import { useNotificationFilter } from '@/stores/notification/filter';
  import NotificationItem from './NotificationItem.vue';
  import { useNotification } from '@/composables/useNotification';
  import { formatNotificationTime } from '@/utils/notification';
  import type { Notification, NotificationFilter } from '@/types/notification';

  const notificationStore = useNotificationStore();
  const configStore = useNotificationConfig();
  const filterStore = useNotificationFilter();

  const props = defineProps<{
    filter?: NotificationFilter;
    mode?: 'popover' | 'timeline';
  }>();

  const emit = defineEmits<{
    (e: 'update', total: number): void;
  }>();

  const {
    loading,
    hasMore,
    page,
    fetchNotifications,
    markAsRead,
    deleteNotification,
    markAllAsRead,
    clearNotifications,
  } = useNotification();

  const visible = ref(false);
  const showFilter = ref(false);
  const showConfig = ref(false);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  const { notifications, unreadCount, availableModules, availableTypes, groupedNotifications } =
    storeToRefs(notificationStore);
  const { config } = storeToRefs(configStore);
  const { filter } = storeToRefs(filterStore);

  const dateRange = computed({
    get: () =>
      filter.value.startDate && filter.value.endDate
        ? [filter.value.startDate, filter.value.endDate]
        : null,
    set: (value: [Date, Date] | null) => {
      filterStore.setFilter({
        startDate: value ? value[0] : null,
        endDate: value ? value[1] : null,
      });
    },
  });

  const handleDateRangeChange = (value: [Date, Date] | null) => {
    dateRange.value = value;
  };

  const showDetails = ref(false);
  const selectedNotification = ref<Notification | null>(null);

  const loadNotifications = async () => {
    const { notifications: data, total: dataTotal, hasMore: more } = await fetchNotifications(props.filter);
    if (page.value === 1) {
      notifications.value = data;
    } else {
      notifications.value.push(...data);
    }
    hasMore.value = more;
    total.value = dataTotal;
    emit('update', dataTotal);
  };

  const handleView = (notification: Notification) => {
    selectedNotification.value = notification;
    showDetails.value = true;
  };

  const handleDelete = async (id: string) => {
    if (await deleteNotification(id)) {
      notifications.value = notifications.value.filter(n => n.id !== id);
    }
  };

  const handleMarkAllAsRead = async () => {
    if (await markAllAsRead()) {
      notifications.value = notifications.value.map(n => ({ ...n, read: true }));
    }
  };

  const handleMarkAsRead = async (id: string) => {
    if (await markAsRead(id)) {
      notifications.value = notifications.value.map(n => 
        n.id === id ? { ...n, read: true } : n
      );
    }
  };

  const handleClear = async () => {
    if (await clearNotifications()) {
      notifications.value = [];
    }
  };

  const loadMore = () => {
    if (!loading.value && hasMore.value) {
      page.value++;
      loadNotifications();
    }
  };

  const handleSizeChange = (size: number) => {
    pageSize.value = size;
    loadNotifications();
  };

  const handleCurrentChange = (page: number) => {
    currentPage.value = page;
    loadNotifications();
  };

  watch(
    () => props.filter,
    () => {
      page.value = 1;
      loadNotifications();
    },
    { deep: true },
  );

  onMounted(() => {
    loadNotifications();
  });

  // 容器组件类型
  const containerComponent = computed(() => (props.mode === 'popover' ? ElPopover : 'div'));

  // 容器组件属性
  const containerProps = computed(() => {
    if (props.mode === 'popover') {
      return {
        width: 400,
        trigger: 'click',
        'v-model:visible': visible.value,
        'popper-class': 'notification-popover',
      };
    }
    return {};
  });

  // 时间线相关方法
  const getTimelineItemType = (type: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
    const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
      system: 'primary',
      business: 'success',
      warning: 'warning',
      error: 'danger',
      default: 'info'
    };
    return typeMap[type] || typeMap.default;
  };

  const getTimelineItemColor = (type: string) => {
    const colorConfig = {
      system: '#409EFF',
      business: '#67C23A',
      warning: '#E6A23C',
      error: '#F56C6C',
    };
    return colorConfig[type as keyof typeof colorConfig] || '#909399';
  };

  const formatTimestamp = (timestamp: string | number | Date) => {
    return formatNotificationTime(new Date(timestamp));
  };

  const formatDateTime = (timestamp?: string) => {
    if (!timestamp) return '';
    return formatTimestamp(timestamp);
  };

  const getNotificationTypeTag = (type?: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
    const typeMap: Record<string, 'success' | 'warning' | 'info' | 'primary' | 'danger'> = {
      system: 'info',
      business: 'success',
      warning: 'warning',
      error: 'danger'
    };
    return type ? typeMap[type] || 'info' : 'info';
  };

  const getNotificationTypeLabel = (type?: string): string => {
    const labelMap: Record<string, string> = {
      system: '系统通知',
      business: '业务通知',
      warning: '警告',
      error: '错误'
    };
    return type ? labelMap[type] || '其他' : '其他';
  };
</script>

<template>
  <component :is="containerComponent" v-bind="containerProps">
    <template #reference v-if="mode === 'popover'">
      <ElBadge :value="unreadCount" :hidden="unreadCount === 0">
        <ElButton :icon="Bell" circle />
      </ElBadge>
    </template>

    <div :class="['notification-container', mode]">
      <div class="notification-header" v-if="mode === 'popover'">
        <div class="notification-title">
          通知列表
          <el-badge :value="unreadCount" :hidden="!unreadCount" class="ml-base" />
        </div>
        <div class="notification-actions">
          <el-button type="primary" link @click="handleMarkAllAsRead" v-if="unreadCount">
            <el-icon><Check /></el-icon>全部已读
          </el-button>
          <el-button type="danger" link @click="handleClear" v-if="notifications.length">
            <el-icon><Delete /></el-icon>清空全部
          </el-button>
        </div>
      </div>

      <div class="notification-content">
        <el-empty v-if="!notifications.length" description="暂无通知" />
        <template v-else>
          <!-- 列表模式 -->
          <template v-if="mode === 'popover'">
            <template v-if="config.groupByModule">
              <div v-for="(group, module) in groupedNotifications" :key="module">
                <div class="module-title">{{ module }}</div>
                <NotificationItem
                  v-for="notification in group"
                  :key="notification.id"
                  :notification="notification"
                  @read="handleView"
                  @remove="handleDelete"
                />
              </div>
            </template>
            <template v-else>
              <NotificationItem
                v-for="notification in notifications"
                :key="notification.id"
                :notification="notification"
                @read="handleView"
                @remove="handleDelete"
              />
            </template>
          </template>

          <!-- 时间线模式 -->
          <template v-else>
            <el-timeline>
              <el-timeline-item
                v-for="notification in notifications"
                :key="notification.id"
                :type="getTimelineItemType(notification.type)"
                :color="getTimelineItemColor(notification.type)"
                :timestamp="formatTimestamp(notification.timestamp)"
                :hollow="notification.read"
              >
                <el-card class="timeline-card" :class="{ 'is-unread': !notification.read }">
                  <template #header>
                    <div class="card-header">
                      <span class="notification-title">{{ notification.title }}</span>
                      <div class="notification-actions">
                        <el-button
                          v-if="!notification.read"
                          type="primary"
                          link
                          @click="handleMarkAsRead(notification.id)"
                        >
                          标记已读
                        </el-button>
                        <el-button type="danger" link @click="handleDelete(notification.id)">
                          删除
                        </el-button>
                      </div>
                    </div>
                  </template>
                  <div class="notification-content">
                    <p>{{ notification.message }}</p>
                    <div v-if="notification.data?.url" class="notification-link">
                      <el-link type="primary" :href="notification.data.url" target="_blank">
                        查看详情
                        <el-icon class="el-icon--right"><arrow-right /></el-icon>
                      </el-link>
                    </div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </template>
        </template>
      </div>

      <div class="notification-footer" v-if="notifications.length">
        <template v-if="mode === 'popover'">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </template>
        <template v-else>
          <div v-if="hasMore" class="load-more">
            <el-button :loading="loading" @click="loadMore">加载更多</el-button>
          </div>
        </template>
      </div>
    </div>

    <!-- 通知详情对话框 -->
    <el-dialog
      v-model="showDetails"
      :title="selectedNotification?.title"
      width="600px"
      destroy-on-close
    >
      <div class="notification-detail">
        <div class="notification-meta mb-base">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="通知类型">
              <el-tag :type="getNotificationTypeTag(selectedNotification?.type)">
                {{ getNotificationTypeLabel(selectedNotification?.type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="发送时间">
              {{ formatDateTime(selectedNotification?.timestamp) }}
            </el-descriptions-item>
            <el-descriptions-item label="所属模块" v-if="selectedNotification?.module">
              {{ selectedNotification?.module }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="selectedNotification?.read ? 'info' : 'warning'">
                {{ selectedNotification?.read ? '已读' : '未读' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="notification-body result-content">
          {{ selectedNotification?.message }}
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetails = false">关闭</el-button>
          <el-button
            type="primary"
            @click="handleMarkAsRead(selectedNotification?.id)"
            v-if="selectedNotification && !selectedNotification.read"
          >
            标记已读
          </el-button>
        </div>
      </template>
    </el-dialog>
  </component>
</template>

<style scoped>
  .notification-container {
    max-height: 600px;
    overflow-y: auto;
  }

  .notification-container.timeline {
    padding: 16px;
  }

  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    border-bottom: 1px solid var(--el-border-color-light);
  }

  .notification-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-regular);
  }

  .notification-actions {
    display: flex;
    gap: 8px;
  }

  .notification-content {
    padding: 16px;
  }

  .notification-footer {
    padding: 16px;
    display: flex;
    justify-content: flex-end;
  }

  .notification-detail {
    .el-descriptions {
      margin-bottom: 0;
    }
  }

  .notification-body {
    white-space: pre-wrap;
    word-break: break-all;
  }

  .module-title {
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-regular);
    background-color: var(--el-fill-color-light);
  }

  :deep(.notification-popover) {
    padding: 0;
    max-width: 90vw;
  }

  .notification-list {
    background-color: var(--bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);

    .list-header {
      padding: var(--spacing-base);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;

      .title {
        font-size: var(--font-size-large);
        font-weight: var(--font-weight-medium);
        color: var(--text-color-primary);
      }

      .actions {
        display: flex;
        gap: var(--spacing-base);
      }
    }

    .list-body {
      .notification-item {
        padding: var(--spacing-base);
        border-bottom: 1px solid var(--border-color-light);
        transition: background-color var(--transition-duration) var(--transition-function);
        cursor: pointer;

        &:hover {
          background-color: var(--bg-color-light);
        }

        &:last-child {
          border-bottom: none;
        }

        &.unread {
          background-color: var(--color-primary-light-9);
        }

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--spacing-small);

          .title {
            font-size: var(--font-size-medium);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
          }

          .time {
            font-size: var(--font-size-small);
            color: var(--text-color-secondary);
          }
        }

        .item-content {
          color: var(--text-color-regular);
          margin-bottom: var(--spacing-small);
        }

        .item-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .tags {
            display: flex;
            gap: var(--spacing-small);
          }

          .actions {
            display: flex;
            gap: var(--spacing-small);
          }
        }
      }
    }

    .list-footer {
      padding: var(--spacing-base);
      border-top: 1px solid var(--border-color);
      background-color: var(--bg-color-light);
      display: flex;
      justify-content: center;

      .pagination {
        :deep(.el-pagination) {
          --el-pagination-button-bg-color: var(--bg-color);
          --el-pagination-hover-color: var(--color-primary);
        }
      }
    }

    .empty-state {
      padding: var(--spacing-extra-large);
      text-align: center;
      color: var(--text-color-secondary);

      .empty-icon {
        font-size: 48px;
        margin-bottom: var(--spacing-base);
      }

      .empty-text {
        font-size: var(--font-size-base);
      }
    }
  }

  .timeline-card {
    margin-bottom: 4px;
  }

  .timeline-card.is-unread {
    border-left: 2px solid var(--el-color-primary);
  }
</style>
