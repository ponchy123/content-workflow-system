import type { RouteRecordRaw } from 'vue-router';
import Layout from '@/layouts/default.vue';

export const adminRoutes: RouteRecordRaw[] = [
  {
    path: '/admin',
    component: Layout,
    meta: {
      requiresAuth: true,
      roles: ['admin'],
    },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/dashboard.vue'),
        meta: { title: '管理仪表盘', icon: 'dashboard' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/admin/users.vue'),
        meta: { title: '用户管理', icon: 'user' },
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('@/views/admin/roles.vue'),
        meta: { title: '角色管理', icon: 'user-filled' },
      },
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('@/views/admin/permissions.vue'),
        meta: { title: '权限管理', icon: 'lock' },
      },
      {
        path: 'audit-logs',
        name: 'AuditLogs',
        component: () => import('@/views/admin/audit-logs.vue'),
        meta: { title: '审计日志', icon: 'document' },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/settings.vue'),
        meta: { title: '系统设置', icon: 'setting' },
      },
      {
        path: 'backup',
        name: 'AdminBackup',
        component: () => import('@/views/admin/backup.vue'),
        meta: { title: '数据备份', icon: 'download' },
      },
      {
        path: 'monitor',
        name: 'AdminMonitor',
        component: () => import('@/views/admin/monitor.vue'),
        meta: { title: '性能监控', icon: 'monitor' },
      },
    ],
  },
]; 