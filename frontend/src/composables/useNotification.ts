import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useNotificationStore } from '@/stores/notification/notification';
import type { Notification, NotificationFilter, NotificationListParams } from '@/types/notification';

export function useNotification() {
  const notificationStore = useNotificationStore();
  const loading = ref(false);
  const hasMore = ref(true);
  const page = ref(1);
  const pageSize = 10;

  const fetchNotifications = async (filter?: Partial<NotificationFilter>) => {
    try {
      loading.value = true;
      await notificationStore.fetchNotifications({
        page: page.value,
        pageSize,
        ...(filter || {}),
      } as NotificationListParams);

      return {
        notifications: notificationStore.notifications,
        total: notificationStore.total,
        hasMore: notificationStore.total > page.value * pageSize,
      };
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      ElMessage.error('获取通知列表失败');
      return {
        notifications: [],
        total: 0,
        hasMore: false,
      };
    } finally {
      loading.value = false;
    }
  };

  const markAsRead = async (id: string) => {
    try {
      await notificationStore.markAsRead(id);
      ElMessage.success('已标记为已读');
      return true;
    } catch (error) {
      ElMessage.error('操作失败，请重试');
      return false;
    }
  };

  const deleteNotification = async (id: string) => {
    try {
      await notificationStore.deleteNotification(id);
      ElMessage.success('删除成功');
      return true;
    } catch (error) {
      ElMessage.error('删除失败，请重试');
      return false;
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationStore.markAllAsRead();
      ElMessage.success('已全部标记为已读');
      return true;
    } catch (error) {
      ElMessage.error('操作失败，请重试');
      return false;
    }
  };

  const clearNotifications = async () => {
    try {
      await notificationStore.clearAllNotifications();
      ElMessage.success('已清空所有通知');
      return true;
    } catch (error) {
      ElMessage.error('操作失败，请重试');
      return false;
    }
  };

  return {
    loading,
    hasMore,
    page,
    pageSize,
    fetchNotifications,
    markAsRead,
    deleteNotification,
    markAllAsRead,
    clearNotifications,
  };
}
