<template>
  <div class="notification-timeline">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>
    <div v-else-if="notifications.length === 0" class="empty-container">
      <el-empty description="暂无通知" />
    </div>
    <el-timeline v-else>
      <el-timeline-item
        v-for="notification in groupedNotifications"
        :key="notification.date"
        :timestamp="notification.date"
        placement="top"
        :type="getTimelineItemType(notification.items[0].type)"
      >
        <el-card>
          <div class="timeline-group-header">{{ notification.date }} ({{ notification.items.length }}条)</div>
          <div
            v-for="item in notification.items"
            :key="item.id"
            class="notification-item"
            :class="{ 'is-read': item.is_read }"
            @click="handleNotificationClick(item)"
          >
            <div class="notification-icon">
              <el-icon>
                <component :is="getIconByType(item.type)" />
              </el-icon>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ item.title }}</div>
              <div class="notification-message">{{ item.message }}</div>
              <div class="notification-meta">
                <span class="notification-time">{{ formatTime(item.created_at) }}</span>
                <span class="notification-module">{{ item.module }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Bell, Message, Warning, InfoFilled, 
  SuccessFilled, CircleCheckFilled
} from '@element-plus/icons-vue';
import { useNotificationStore } from '@/stores/notification/notification';
import { formatDateTime } from '@/utils/format';
import type { Notification, NotificationType } from '@/types/notification';

interface NotificationFilter {
  search: string;
  module: string;
  type: NotificationType | null;
  read: boolean;
  startDate: Date | null;
  endDate: Date | null;
}

interface GroupedNotification {
  date: string;
  items: Notification[];
}

const props = defineProps<{
  filter: NotificationFilter;
}>();

const notificationStore = useNotificationStore();
const notifications = ref<Notification[]>([]);
const loading = ref(true);

// 按日期分组通知
const groupedNotifications = computed(() => {
  const groups: Record<string, Notification[]> = {};
  
  notifications.value.forEach(notification => {
    const date = new Date(notification.created_at);
    const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    
    if (!groups[dateStr]) {
      groups[dateStr] = [];
    }
    
    groups[dateStr].push(notification);
  });
  
  // 转换为数组并按日期排序
  return Object.entries(groups)
    .map(([date, items]) => ({ date, items }))
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
});

// 根据通知类型获取图标
const getIconByType = (type: NotificationType) => {
  switch (type) {
    case 'info':
      return InfoFilled;
    case 'success':
      return SuccessFilled;
    case 'warning':
      return Warning;
    case 'error':
      return 'CircleCloseFilled';
    case 'system':
      return Bell;
    default:
      return Message;
  }
};

// 根据通知类型获取时间线项的类型
const getTimelineItemType = (type: NotificationType) => {
  switch (type) {
    case 'info':
      return 'info';
    case 'success':
      return 'success';
    case 'warning':
      return 'warning';
    case 'error':
      return 'danger';
    default:
      return 'primary';
  }
};

// 格式化时间
const formatTime = (timestamp: string) => {
  return formatDateTime(timestamp, 'HH:mm:ss');
};

// 处理点击通知
const handleNotificationClick = async (notification: Notification) => {
  if (!notification.is_read) {
    try {
      await notificationStore.markAsRead(notification.id);
      // 更新本地状态
      const index = notifications.value.findIndex(n => n.id === notification.id);
      if (index !== -1) {
        notifications.value[index].is_read = true;
      }
    } catch (error) {
      console.error('标记已读失败', error);
    }
  }
  
  // 如果有链接，跳转到相应页面
  if (notification.link) {
    window.open(notification.link, '_blank');
  }
};

// 加载通知数据
const loadNotifications = async () => {
  loading.value = true;
  try {
    // 从store加载通知，应用过滤条件
    let filteredNotifications = await notificationStore.getNotifications();
    
    // 应用过滤条件
    if (props.filter.search) {
      const searchLower = props.filter.search.toLowerCase();
      filteredNotifications = filteredNotifications.filter(
        n => n.title.toLowerCase().includes(searchLower) || 
             n.message.toLowerCase().includes(searchLower)
      );
    }
    
    if (props.filter.module) {
      filteredNotifications = filteredNotifications.filter(
        n => n.module === props.filter.module
      );
    }
    
    if (props.filter.type) {
      filteredNotifications = filteredNotifications.filter(
        n => n.type === props.filter.type
      );
    }
    
    if (props.filter.read !== undefined) {
      filteredNotifications = filteredNotifications.filter(
        n => n.is_read === props.filter.read
      );
    }
    
    if (props.filter.startDate) {
      const startTime = props.filter.startDate.getTime();
      filteredNotifications = filteredNotifications.filter(
        n => new Date(n.created_at).getTime() >= startTime
      );
    }
    
    if (props.filter.endDate) {
      const endTime = props.filter.endDate.getTime();
      filteredNotifications = filteredNotifications.filter(
        n => new Date(n.created_at).getTime() <= endTime
      );
    }
    
    notifications.value = filteredNotifications;
  } catch (error) {
    console.error('加载通知失败', error);
    ElMessage.error('加载通知失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 监听过滤条件变化
watch(() => props.filter, () => {
  loadNotifications();
}, { deep: true });

onMounted(() => {
  loadNotifications();
});
</script>

<style scoped>
.notification-timeline {
  padding: 16px;
}

.loading-container, 
.empty-container {
  padding: 40px 0;
  text-align: center;
}

.timeline-group-header {
  font-weight: bold;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.notification-item {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.3s ease;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background-color: var(--el-fill-color-light);
}

.notification-item.is-read {
  opacity: 0.7;
}

.notification-icon {
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: bold;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.notification-message {
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.notification-module {
  background-color: var(--el-fill-color);
  padding: 2px 8px;
  border-radius: 12px;
}
</style> 