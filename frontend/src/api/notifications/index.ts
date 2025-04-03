export * from './notifications';

export interface NotificationListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  module?: string;
  type?: string;
  read?: boolean;
  startDate?: string;
  endDate?: string;
}

export interface NotificationListResponse {
  results: Notification[];
  total: number;
  page: number;
  pageSize: number;
}
