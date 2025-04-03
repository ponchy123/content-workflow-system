export type UserStatus = 'active' | 'inactive' | 'locked';

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  last_login?: string;
  date_joined: string;
  roles: string[];
  permissions: string[];
  nickname?: string;
  phone?: string;
  avatar?: string;
}

export interface UserFilter {
  username?: string;
  email?: string;
  roleId?: string;
  status?: UserStatus;
}

export interface UserState {
  userInfo: UserInfo | null;
  token: string | null;
  permissions: string[];
  roles: string[];
  loading: boolean;
}

export interface UserFormData {
  username: string;
  email: string;
  phone?: string;
  password?: string;
  confirmPassword?: string;
  status: UserStatus;
  roleIds: string[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  refresh: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface RegisterResponse {
  message: string;
  user: User;
}

export interface Permission {
  id: string;
  name: string;
  codename: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  is_active?: boolean;
  is_staff?: boolean;
  roles?: string[];
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  password?: string;
  is_active?: boolean;
  is_staff?: boolean;
  roles?: string[];
  nickname?: string;
  phone?: string;
}

export interface RoleCreateRequest {
  name: string;
  description: string;
  permissions: string[];
}

export interface RoleUpdateRequest {
  name?: string;
  description?: string;
  permissions?: string[];
}

export interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

export interface RoleListResponse {
  items: Role[];
  total: number;
  page: number;
  page_size: number;
}

export interface PermissionListResponse {
  items: Permission[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 用户信息
 */
export interface UserInfo {
  id: string | number;
  username: string;
  nickname?: string;
  avatar?: string;
  email?: string;
  phone?: string;
  roles: string[];
  permissions: string[];
}

/**
 * 用户个人信息更新
 */
export interface UserProfile {
  nickname: string;
  email: string;
  phone: string;
}

/**
 * 密码修改
 */
export interface PasswordChange {
  oldPassword: string;
  newPassword: string;
}
