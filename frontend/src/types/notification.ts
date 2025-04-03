import type { PaginatedResponse } from '@/api/core';

export interface NotificationConfig {
  maxCount: number;
  expirationDays: number;
  soundEnabled: boolean;
  desktopNotification: boolean;
  groupByModule: boolean;
  autoCleanup: boolean;
}

export type NotificationType = 'system' | 'business' | 'warning' | 'error' | 'success' | 'info';

export interface NotificationFilter {
  search: string;
  module: string | null;
  type: NotificationType | null;
  read: boolean | null;
  startDate: Date | null;
  endDate: Date | null;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  module?: string;
  read: boolean;
  timestamp: string;
  data?: {
    url?: string;
    [key: string]: any;
  };
}

export interface NotificationListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  module?: string;
  type?: NotificationType;
  read?: boolean;
  startDate?: string;
  endDate?: string;
}

export interface NotificationListResponse extends PaginatedResponse<Notification> {}

export interface NotificationStats {
  total: number;
  unread: number;
  today: number;
  week: number;
  byType: Record<NotificationType, number>;
}

export interface NotificationResponse {
  items: Notification[];
  total: number;
  hasMore: boolean;
}

export interface NotificationSettings {
  maxCount: number;
  expirationDays: number;
  soundEnabled: boolean;
  desktopNotification: boolean;
  groupByModule: boolean;
  autoCleanup: boolean;
  notificationTypes?: NotificationType[];
  quietHoursStart?: string;
  quietHoursEnd?: string;
  frequency?: 'immediately' | 'daily' | 'weekly';
}

export interface NotificationSoundConfig {
  success: string;
  warning: string;
  error: string;
  info: string;
  system: string;
  business: string;
}
