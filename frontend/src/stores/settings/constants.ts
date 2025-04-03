// 本地化配置
export const LOCALE_CONFIG = {
  DATE_FORMATS: {
    short: {
      year: 'numeric' as const,
      month: '2-digit' as const,
      day: '2-digit' as const,
    },
    long: {
      year: 'numeric' as const,
      month: 'long' as const,
      day: 'numeric' as const,
      weekday: 'long' as const,
    },
    time: {
      hour: '2-digit' as const,
      minute: '2-digit' as const,
      second: '2-digit' as const,
    },
  },
  NUMBER_FORMATS: {
    currency: {
      style: 'currency' as const,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
    decimal: {
      style: 'decimal' as const,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    },
    percent: {
      style: 'percent' as const,
      minimumFractionDigits: 2,
    },
  },
};

// 主题配置
export const THEME_DEFAULTS = {
  light: {
    primaryColor: '#1890ff',
    fontFamily: 'Roboto, sans-serif',
    fontSize: 14,
  },
  dark: {
    primaryColor: '#1890ff',
    fontFamily: 'Roboto, sans-serif',
    fontSize: 14,
  },
};

// UI配置默认值
export const UI_DEFAULTS = {
  animationsEnabled: true,
  compactMode: false,
  showHelpIcons: true,
  sidebarCollapsed: false,
  tableRowsPerPage: 10,
  tableSize: 'default' as const
};

// 通知设置默认值
export const NOTIFICATION_DEFAULTS = {
  enabled: true,
  sound: true,
  desktop: true,
  enableEmailNotifications: false
}; 