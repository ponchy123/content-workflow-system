import { formatDate } from '@/utils/format/date';

export const NotificationTypeConfig = {
  system: {
    type: 'primary',
    color: '#409EFF',
    label: '系统通知',
  },
  business: {
    type: 'success',
    color: '#67C23A',
    label: '业务通知',
  },
  warning: {
    type: 'warning',
    color: '#E6A23C',
    label: '警告通知',
  },
  error: {
    type: 'danger',
    color: '#F56C6C',
    label: '错误通知',
  },
};

export const getNotificationTypeInfo = (type: string) => {
  return (
    NotificationTypeConfig[type as keyof typeof NotificationTypeConfig] || {
      type: 'info',
      color: '#909399',
      label: type,
    }
  );
};

export const formatNotificationTime = (timestamp: string | number | Date) => {
  return formatDate(new Date(timestamp), 'YYYY-MM-DD HH:mm:ss');
};

export const getNotificationTypeLabel = (type: string) => {
  return getNotificationTypeInfo(type).label;
};

export const getNotificationTypeColor = (type: string) => {
  return getNotificationTypeInfo(type).color;
};

export const getNotificationTypeType = (type: string) => {
  return getNotificationTypeInfo(type).type;
};
