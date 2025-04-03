import { createRouter, createWebHistory } from 'vue-router';
import { setupRouterGuard } from './guard';

// 导入各模块路由
import { rootRoutes } from './routes/root';
import { authRoutes } from './routes/auth';
import { dashboardRoutes } from './routes/dashboard';
import { calculatorRoutes } from './routes/calculator';
import { productRoutes } from './routes/product';
import { postalRoutes } from './routes/postal';
import { fuelRateRoutes } from './routes/fuel-rate';
import { reportRoutes } from './routes/report';
import { notificationRoutes } from './routes/notification';
import { systemRoutes } from './routes/system';
import { adminRoutes } from './routes/admin';

// 扩展 RouteMeta 接口以包含我们的自定义元数据
declare module 'vue-router' {
  interface RouteMeta {
    title?: string;
    icon?: string;
    public?: boolean;
    hidden?: boolean;
    roles?: string[];
    permissions?: string[];
    requiresAuth?: boolean;
  }
}

// 合并所有路由配置
const routes = [
  ...rootRoutes,
  ...authRoutes,
  ...dashboardRoutes,
  ...calculatorRoutes,
  ...productRoutes,
  ...postalRoutes,
  ...fuelRateRoutes,
  ...reportRoutes,
  ...notificationRoutes,
  ...systemRoutes,
  ...adminRoutes,
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 设置路由守卫
setupRouterGuard(router);

export default router;
