export interface Notification {
  id: string;
  title: string;
  content: string;
  type: 'info' | 'warning' | 'error' | 'success';
  source: 'system' | 'user' | 'task';
  isRead: boolean;
  timestamp: number;
  link?: string;
  data?: Record<string, any>;
}

export interface NotificationFilter {
  type?: ('info' | 'warning' | 'error' | 'success')[];
  source?: ('system' | 'user' | 'task')[];
  isRead?: boolean;
  startTime?: number;
  endTime?: number;
  search?: string;
}

export interface NotificationConfig {
  enableDesktopNotifications: boolean;
  enableSoundEffects: boolean;
  showUnreadOnly: boolean;
  autoRemoveAfterDays: number;
  maxNotificationsToShow: number;
}

export interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  filter: NotificationFilter;
  config: NotificationConfig;
  loading: boolean;
  error: string | null;
}

export interface NotificationGetters {
  filteredNotifications: Notification[];
  latestNotifications: Notification[];
  hasUnread: boolean;
}

export interface NotificationActions {
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'isRead'>) => string;
  removeNotification: (id: string) => void;
  markAsRead: (id: string) => void;
  markAsUnread: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
  fetchNotifications: () => Promise<Notification[]>;
  updateFilter: (filter: Partial<NotificationFilter>) => void;
  updateConfig: (config: Partial<NotificationConfig>) => void;
} 