export interface Breadcrumb {
  title: string;
  path: string;
}

export interface AppTheme {
  colorMode: 'light' | 'dark' | 'auto';
  primaryColor: string;
  layoutMode: 'vertical' | 'horizontal';
  contentWidth: 'fixed' | 'fluid';
}

export interface AppLayout {
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  headerFixed: boolean;
  footerFixed: boolean;
}

export interface AppState {
  title: string;
  breadcrumbs: Breadcrumb[];
  theme: AppTheme;
  layout: AppLayout;
  isMobile: boolean;
  isLoading: boolean;
  globalError: string | null;
  lastNetworkActivity: number;
  initialized: boolean;
  reloadRequired: boolean;
  activeModals: string[];
}

export interface AppGetters {
  isDarkMode: boolean;
  currentBreadcrumbs: Breadcrumb[];
}

export interface AppActions {
  setTitle: (title: string) => void;
  setBreadcrumbs: (breadcrumbs: Breadcrumb[]) => void;
  updateTheme: (theme: Partial<AppTheme>) => void;
  updateLayout: (layout: Partial<AppLayout>) => void;
  toggleSidebar: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  initialize: () => Promise<void>;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
  checkAppUpdates: () => Promise<boolean>;
} 