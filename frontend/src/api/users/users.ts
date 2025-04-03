import { get, post, put, del } from '../core';
import type { PaginatedResponse } from '../core/types';
import type {
  User,
  UserCreateRequest,
  UserUpdateRequest,
  UserListResponse,
  Role,
  RoleCreateRequest,
  RoleUpdateRequest,
  RoleListResponse,
  Permission,
  PermissionListResponse,
} from '@/types/user';

export type {
  User,
  UserCreateRequest,
  UserUpdateRequest,
  UserListResponse,
  Role,
  RoleCreateRequest,
  RoleUpdateRequest,
  RoleListResponse,
  Permission,
  PermissionListResponse,
};

// 用户管理API
export const getUsers = async (params?: {
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<User>> => {
  const { data } = await get<PaginatedResponse<User>>('/api/v1/users/users/', { params });
  return data;
};

export const getUser = async (id: string): Promise<User> => {
  const { data } = await get<User>(`/api/v1/users/users/${id}/`);
  return data;
};

export const createUser = async (data: UserCreateRequest): Promise<User> => {
  const { data: response } = await post<User>('/api/v1/users/users/', data);
  return response;
};

export const updateUser = async (id: string, data: UserUpdateRequest): Promise<User> => {
  const { data: response } = await put<User>(`/api/v1/users/users/${id}/`, data);
  return response;
};

export const deleteUser = async (id: string): Promise<void> => {
  await del(`/api/v1/users/users/${id}/`);
};

// 角色管理API
export const getRoles = async (params?: {
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Role>> => {
  const { data } = await get<PaginatedResponse<Role>>('/api/v1/users/roles/', { params });
  return data;
};

export const getRole = async (id: string): Promise<Role> => {
  const { data } = await get<Role>(`/api/v1/users/roles/${id}/`);
  return data;
};

export const createRole = async (data: RoleCreateRequest): Promise<Role> => {
  const { data: response } = await post<Role>('/api/v1/users/roles/', data);
  return response;
};

export const updateRole = async (id: string, data: RoleUpdateRequest): Promise<Role> => {
  const { data: response } = await put<Role>(`/api/v1/users/roles/${id}/`, data);
  return response;
};

export const deleteRole = async (id: string): Promise<void> => {
  await del(`/api/v1/users/roles/${id}/`);
};

// 权限管理API
export const getPermissions = async (params?: {
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Permission>> => {
  const { data } = await get<PaginatedResponse<Permission>>('/api/v1/users/permissions/', { params });
  return data;
};

// 用户角色管理
export const assignRolesToUser = async (userId: string, roleIds: string[]): Promise<User> => {
  const { data } = await post<User>(`/api/users/users/${userId}/roles/`, {
    role_ids: roleIds,
  });
  return data;
};

export const removeRolesFromUser = async (userId: string, roleIds: string[]): Promise<User> => {
  const { data } = await post<User>(`/api/users/users/${userId}/remove-roles/`, {
    role_ids: roleIds,
  });
  return data;
};

// 角色权限管理
export const assignPermissionsToRole = async (
  roleId: string,
  permissionIds: string[],
): Promise<Role> => {
  const { data } = await post<Role>(`/api/users/roles/${roleId}/permissions/`, {
    permission_ids: permissionIds,
  });
  return data;
};

export const removePermissionsFromRole = async (
  roleId: string,
  permissionIds: string[],
): Promise<Role> => {
  const { data } = await post<Role>(`/api/users/roles/${roleId}/remove-permissions/`, {
    permission_ids: permissionIds,
  });
  return data;
};

// 登录日志
export const getLoginLogs = async (params?: {
  page?: number;
  page_size?: number;
  user_id?: string;
}): Promise<PaginatedResponse<any>> => {
  const { data } = await get<PaginatedResponse<any>>('/api/users/login_logs/', { params });
  return data;
};
