import type { Router, RouteLocationNormalized, RouteRecordRaw } from 'vue-router';
import { useUserStore } from '@/stores/user/index';
import { useAppStore } from '@/stores/app';
import { logger } from '@/utils/logger';
import { storage } from '@/utils/storage';
import { TOKEN_KEY, WHITE_LIST_PATHS, LOGIN_PATH } from '@/types/auth';

// 定义PermissionMeta接口
interface PermissionMeta {
  roles?: string[];
  permissions?: string[];
  requiresAuth?: boolean;
  public?: boolean;
  title?: string;
}

const whiteList = new Set(WHITE_LIST_PATHS);
const permissionCache = new Map<string, boolean>();

export function setupRouterGuard(router: Router) {
  router.beforeEach(async (to, from, next) => {
    const startTime = performance.now();
    const userStore = useUserStore();
    const appStore = useAppStore();
    
    console.log('路由守卫处理:', from.path, '->', to.path);
    
    // 开始加载
    appStore.setLoading(true);

    try {
      // 白名单路由或公开路由直接通过
      if (whiteList.has(to.path) || to.meta.public) {
        console.log('白名单或公开路由，直接通过:', to.path);
        next();
        return;
      }

      // 检查token
      const token = localStorage.getItem(TOKEN_KEY);
      console.log('路由守卫检查token:', token ? `有效(${token.substring(0, 10)}...)` : '未登录');

      // 优先检查localStorage，因为这是最新的状态
      if (!token) {
        console.log('未检测到token，重定向到登录页');
        // 保存当前路径以便登录后返回
        next({
          path: LOGIN_PATH,
          query: { redirect: to.fullPath },
          replace: true
        });
        return;
      }

      // 检查token是否有效（简单检查格式）
      if (token === 'null' || token === 'undefined' || token === 'mock-access-token-refreshed-1742444825377') {
        console.warn('检测到无效token格式，清除本地存储并重定向到登录页');
        // 清除存储的错误令牌
        localStorage.removeItem(TOKEN_KEY);
        
        // 立即重定向到登录页
        next({
          path: LOGIN_PATH,
          query: { error: '登录已过期，请重新登录', redirect: to.fullPath },
          replace: true
        });
        return;
      }

      // 已登录用户访问登录页，重定向到首页或原定目标
      if (to.path === LOGIN_PATH) {
        // 检查是否确实已登录
        if (token && token !== 'null' && token !== 'undefined') {
          console.log('已登录用户访问登录页，重定向到首页');
          // 如果from路径有效且不是登录页，则重定向回来源页面
          if (from.path && from.path !== LOGIN_PATH && from.path !== '/') {
            next(from.path);
          } else {
            // 否则重定向到默认首页
            next('/');
          }
          return;
        }
        // 未登录用户访问登录页，允许通过
        next();
        return;
      }

      // 已登录，允许访问
      next();
    } catch (error) {
      console.error('路由守卫出错:', error);
      next({ path: '/500' });
    } finally {
      const endTime = performance.now();
      console.log(`路由守卫执行完成，耗时: ${(endTime - startTime).toFixed(2)}ms`);
      appStore.setLoading(false);
    }
  });

  // 全局错误处理，拦截401错误
  window.addEventListener('unhandledrejection', function(event) {
    // 检查是否是401错误
    const error = event.reason;
    if (error && error.response && error.response.status === 401) {
      console.warn('捕获到未处理的401错误，重定向到登录页');
      // 清除令牌
      localStorage.removeItem(TOKEN_KEY);
      // 重定向到登录页
      window.location.replace(`${LOGIN_PATH}?error=登录已过期，请重新登录&t=${Date.now()}`);
      
      // 阻止错误继续冒泡
      event.preventDefault();
    }
  });

  router.afterEach(to => {
    const appStore = useAppStore();

    // 设置页面标题
    const title = to.meta.title;
    if (title) {
      document.title = `${title} - ${import.meta.env.VITE_APP_TITLE}`;
    }

    // 移动端下关闭侧边栏
    if (appStore.isMobile && !appStore.sidebar.collapsed) {
      appStore.toggleSidebar();
    }

    // 清理过期的权限缓存
    if (permissionCache.size > 100) {
      const now = Date.now();
      permissionCache.clear();
    }
  });

  router.onError(error => {
    logger.error('Route error', { error });
    const appStore = useAppStore();
    appStore.setError(error);
    appStore.setLoading(false);
  });
}

async function checkRoutePermission(to: RouteLocationNormalized, userStore: any): Promise<boolean> {
  try {
    // 检查路由是否需要认证
    if (to.meta.requiresAuth === false) {
      return true;
    }

    // 检查角色权限
    if (to.meta.roles && to.meta.roles.length > 0) {
      const hasRole = to.meta.roles.some(role => userStore.hasRole(role));
      if (!hasRole) {
        return false;
      }
    }

    // 检查具体权限
    if (to.meta.permissions && to.meta.permissions.length > 0) {
      const hasPermission = to.meta.permissions.some(permission => 
        userStore.hasPermission(permission)
      );
      if (!hasPermission) {
        return false;
      }
    }

    return true;
  } catch (error) {
    console.error('权限检查出错:', error);
    return false;
  }
}

// 重置路由
export function resetRouter(router: Router) {
  const routes = router.getRoutes();
  routes.forEach(route => {
    const { name } = route;
    if (name && !whiteList.has(route.path)) {
      router.removeRoute(name);
    }
  });
  permissionCache.clear();
}

// 添加路由
export function addRoutes(router: Router, routes: RouteRecordRaw[]) {
  routes.forEach(route => {
    if (!router.hasRoute(route.name as string)) {
      router.addRoute(route);
    }
  });
}

// 权限验证
export function hasRoutePermission(route: RouteRecordRaw): boolean {
  const userStore = useUserStore();
  const meta = route.meta as PermissionMeta;

  if (!meta) return true;
  if (meta.requiresAuth && !userStore.isLoggedIn) return false;

  // 无特殊角色要求，通过
  if (!meta.roles || meta.roles.length === 0) {
    return true;
  }
  
  // 如果用户是admin，直接允许
  if (userStore.userInfo?.roles?.includes('admin')) {
    return true;
  }

  // 检查角色
  if (meta.roles && meta.roles.length > 0) {
    return meta.roles.some(role => userStore.hasRole(role));
  }

  // 默认通过
  return true;
}
