import { useUserStore } from '@/stores/user';

export function usePermission() {
  const userStore = useUserStore();

  const checkPermission = (permission?: string | string[]): boolean => {
    if (!permission) return true;
    if (Array.isArray(permission)) {
      return permission.some(p => userStore.permissions.includes(p));
    }
    return userStore.permissions.includes(permission);
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some(permission => checkPermission(permission));
  };

  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every(permission => checkPermission(permission));
  };

  return {
    checkPermission,
    hasAnyPermission,
    hasAllPermissions,
  };
} 