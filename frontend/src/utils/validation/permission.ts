import { useUserStore } from '@/stores/user';
import type { RouteRecordRaw } from 'vue-router';

export interface PermissionMeta {
  roles?: string[];
  permissions?: string[];
  requiresAuth?: boolean;
}

/**
 * 检查用户是否有权限访问路由
 */
export function hasRoutePermission(route: RouteRecordRaw): boolean {
  const userStore = useUserStore();
  const meta = route.meta as PermissionMeta;

  if (!meta) return true;
  if (meta.requiresAuth && !userStore.isLoggedIn) return false;

  if (meta.roles && meta.roles.length > 0) {
    return meta.roles.some(role => userStore.hasRole(role));
  }

  if (meta.permissions && meta.permissions.length > 0) {
    return meta.permissions.some(permission => userStore.hasPermission(permission));
  }

  return true;
}

/**
 * 过滤路由表，只保留有权限的路由
 */
export function filterAsyncRoutes(routes: RouteRecordRaw[]): RouteRecordRaw[] {
  const res: RouteRecordRaw[] = [];

  routes.forEach(route => {
    const tmp = { ...route };
    if (hasRoutePermission(tmp)) {
      if (tmp.children) {
        tmp.children = filterAsyncRoutes(tmp.children);
      }
      res.push(tmp);
    }
  });

  return res;
}

/**
 * 检查用户是否有权限执行操作
 */
export function checkPermission(permission: string | string[]): boolean {
  const userStore = useUserStore();
  const permissions = Array.isArray(permission) ? permission : [permission];

  return permissions.some(p => userStore.hasPermission(p));
}

/**
 * 检查用户是否有指定角色
 */
export function checkRole(role: string | string[]): boolean {
  const userStore = useUserStore();
  const roles = Array.isArray(role) ? role : [role];

  return roles.some(r => userStore.hasRole(r));
}

/**
 * 权限指令
 */
export const vPermission = {
  mounted(el: HTMLElement, binding: { value: string | string[] }) {
    const hasPermission = checkPermission(binding.value);
    if (!hasPermission) {
      el.parentNode?.removeChild(el);
    }
  },
};

/**
 * 角色指令
 */
export const vRole = {
  mounted(el: HTMLElement, binding: { value: string | string[] }) {
    const hasRole = checkRole(binding.value);
    if (!hasRole) {
      el.parentNode?.removeChild(el);
    }
  },
};
