export type PermissionType = 'menu' | 'button' | 'api';

export interface Permission {
  id: string;
  name: string;
  code: string;
  type: PermissionType;
  parentId: string | null;
  description?: string;
  children?: Permission[];
  createdAt?: string;
  updatedAt?: string;
}

export interface PermissionGroup {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface PermissionTree extends Permission {
  children: PermissionTree[];
}

export interface PermissionFilter {
  name?: string;
  code?: string;
  type?: PermissionType;
  parentId?: string;
}

export interface PermissionState {
  permissions: Permission[];
  permissionGroups: PermissionGroup[];
  permissionTree: PermissionTree[];
  loading: boolean;
  error: Error | null;
}
