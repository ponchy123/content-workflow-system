import { get, post, put, del } from '../core';
import type { PaginatedResponse } from '../core/types';
import type { Notification, NotificationSettings, NotificationType } from '@/types/notification';

// API 端点
const endpoints = {
  base: '/api/v1/notifications',
  detail: (id: string) => `/api/v1/notifications/${id}`,
  markAsRead: (id: string) => `/api/v1/notifications/${id}/read`,
  markAllAsRead: '/api/v1/notifications/mark-all-read',
  clearRead: '/api/v1/notifications/clear-read',
  unreadCount: '/api/v1/notifications/unread-count',
  settings: '/api/v1/notification-settings',
};

export interface NotificationListParams {
  page?: number;
  page_size?: number;
  type?: NotificationType;
  read?: boolean;
  start_date?: string;
  end_date?: string;
  sort_by?: 'timestamp' | 'type' | 'read';
  order?: 'asc' | 'desc';
}

export interface NotificationCreateParams {
  title: string;
  content: string;
  type: NotificationType;
  link?: string;
  metadata?: Record<string, any>;
  recipients?: string[];
}

export interface NotificationUpdateParams {
  title?: string;
  content?: string;
  type?: NotificationType;
  link?: string;
  metadata?: Record<string, any>;
  read?: boolean;
}

export type NotificationListResponse = PaginatedResponse<Notification>;

export interface NotificationSettingsUpdateParams {
  email_enabled?: boolean;
  push_enabled?: boolean;
  notification_types?: NotificationType[];
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  frequency?: 'immediately' | 'daily' | 'weekly';
}

/**
 * 获取通知列表
 * @param params 查询参数
 * @returns 通知列表和分页信息
 */
export const getNotificationList = async (params?: NotificationListParams): Promise<NotificationListResponse> => {
  const { data } = await get<NotificationListResponse>(endpoints.base, { params });
  return data;
};

/**
 * 获取通知详情
 * @param id 通知ID
 * @returns 通知详情
 */
export const getNotificationDetail = async (id: string): Promise<Notification> => {
  const { data } = await get<Notification>(endpoints.detail(id));
  return data;
};

/**
 * 创建通知
 * @param params 创建参数
 * @returns 创建的通知
 */
export const createNotification = async (params: NotificationCreateParams): Promise<Notification> => {
  const { data } = await post<Notification>(endpoints.base, params);
  return data;
};

/**
 * 更新通知
 * @param id 通知ID
 * @param params 更新参数
 * @returns 更新后的通知
 */
export const updateNotification = async (id: string, params: NotificationUpdateParams): Promise<Notification> => {
  const { data } = await put<Notification>(endpoints.detail(id), params);
  return data;
};

/**
 * 删除通知
 * @param id 通知ID
 */
export const deleteNotification = async (id: string): Promise<void> => {
  await del(endpoints.detail(id));
};

/**
 * 标记通知为已读
 * @param id 通知ID
 * @returns 更新后的通知
 */
export const markNotificationAsRead = async (id: string): Promise<Notification> => {
  const { data } = await post<Notification>(endpoints.markAsRead(id));
  return data;
};

/**
 * 标记所有通知为已读
 * @returns 操作结果
 */
export const markAllNotificationsAsRead = async (): Promise<{ success: boolean; count: number }> => {
  const { data } = await post<{ success: boolean; count: number }>(endpoints.markAllAsRead);
  return data;
};

/**
 * 清除已读通知
 * @returns 操作结果
 */
export const clearReadNotifications = async (): Promise<{ success: boolean; count: number }> => {
  const { data } = await post<{ success: boolean; count: number }>(endpoints.clearRead);
  return data;
};

/**
 * 获取未读通知数量
 * @returns 未读通知数量
 */
export const getUnreadCount = async (): Promise<number> => {
  const { data } = await get<{ count: number }>(endpoints.unreadCount);
  return data.count;
};

/**
 * 获取通知设置
 * @returns 通知设置
 */
export const getNotificationSettings = async (): Promise<NotificationSettings> => {
  const { data } = await get<NotificationSettings>(endpoints.settings);
  return data;
};

/**
 * 更新通知设置
 * @param params 更新参数
 * @returns 更新后的通知设置
 */
export const updateNotificationSettings = async (params: NotificationSettingsUpdateParams): Promise<NotificationSettings> => {
  const { data } = await put<NotificationSettings>(endpoints.settings, params);
  return data;
};
