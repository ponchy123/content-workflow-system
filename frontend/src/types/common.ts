/**
 * 通用类型定义
 */

// 通用响应类型
export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

// 分页请求参数
export interface PaginationQuery {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 分页响应数据
export interface PaginationResponse<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

// 基础实体类型
export interface BaseEntity {
  id: number | string;
  createdAt: string;
  updatedAt: string;
  createdBy?: number | string;
  updatedBy?: number | string;
}

// 通用状态类型
export type Status = 'active' | 'inactive' | 'pending' | 'archived';

// 通用选项类型
export interface Option {
  label: string;
  value: string | number;
  disabled?: boolean;
  children?: Option[];
}

// 通用树节点类型
export interface TreeNode {
  id: string | number;
  label: string;
  children?: TreeNode[];
  parentId?: string | number;
  [key: string]: any;
}

// 文件类型
export interface FileInfo {
  uid: string;
  name: string;
  size: number;
  type: string;
  url?: string;
  status: 'uploading' | 'done' | 'error';
  response?: any;
  error?: any;
}

// 用户信息类型
export interface UserInfo {
  id: number | string;
  username: string;
  nickname?: string;
  avatar?: string;
  email?: string;
  phone?: string;
  roles: string[];
  permissions: string[];
}
