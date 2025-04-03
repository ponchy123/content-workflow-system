import { defineStore } from 'pinia';
import { storage } from '@/utils/storage';

interface AppState {
  theme: 'light' | 'dark';
  sidebar: {
    collapsed: boolean;
    width: number;
  };
  device: 'desktop' | 'tablet' | 'mobile';
  loading: boolean;
  error: Error | null;
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    theme: storage.get<'light' | 'dark'>('theme') ?? 'light',
    sidebar: {
      collapsed: storage.get<boolean>('sidebar_collapsed') ?? false,
      width: 240,
    },
    device: 'desktop',
    loading: false,
    error: null,
  }),

  getters: {
    isDarkTheme: state => state.theme === 'dark',
    isMobile: state => state.device === 'mobile',
    sidebarWidth: state => (state.sidebar.collapsed ? 64 : state.sidebar.width),
  },

  actions: {
    setTheme(theme: 'light' | 'dark') {
      this.theme = theme;
      storage.set('theme', theme);
      // 更新 HTML 的 class
      document.documentElement.classList.toggle('dark', theme === 'dark');
    },

    toggleTheme() {
      this.setTheme(this.theme === 'light' ? 'dark' : 'light');
    },

    toggleSidebar() {
      this.sidebar.collapsed = !this.sidebar.collapsed;
      storage.set('sidebar_collapsed', this.sidebar.collapsed);
    },

    setDevice(device: 'desktop' | 'tablet' | 'mobile') {
      this.device = device;
    },

    setLoading(loading: boolean) {
      this.loading = loading;
    },

    setError(error: Error | null) {
      this.error = error;
    },

    // 响应式布局处理
    handleResize() {
      const width = window.innerWidth;
      if (width < 768) {
        this.setDevice('mobile');
        this.sidebar.collapsed = true;
      } else if (width < 992) {
        this.setDevice('tablet');
        this.sidebar.collapsed = true;
      } else {
        this.setDevice('desktop');
        this.sidebar.collapsed = false;
      }
    },

    // 初始化应用状态
    init() {
      // 设置主题
      const theme = storage.get<'light' | 'dark'>('theme') ?? 'light';
      this.setTheme(theme);

      // 设置侧边栏状态
      const sidebarCollapsed = storage.get<boolean>('sidebar_collapsed') ?? false;
      this.sidebar.collapsed = sidebarCollapsed;

      // 初始化响应式布局
      this.handleResize();
      window.addEventListener('resize', this.handleResize);
    },

    // 清理
    cleanup() {
      window.removeEventListener('resize', this.handleResize);
    },
  },
});
