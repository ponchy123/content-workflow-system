import type { LocaleType } from '@/i18n';
import type { ConfigItem } from '@/types/config';

export interface LocaleConfig {
  DATE_FORMATS: {
    short: Intl.DateTimeFormatOptions;
    long: Intl.DateTimeFormatOptions;
    time: Intl.DateTimeFormatOptions;
  };
  NUMBER_FORMATS: {
    currency: Intl.NumberFormatOptions;
    decimal: Intl.NumberFormatOptions;
    percent: Intl.NumberFormatOptions;
  };
}

export interface ThemeSettings {
  theme: 'light' | 'dark' | 'auto';
  primaryColor: string;
  fontFamily: string;
  fontSize: number;
}

export interface LanguageSettings {
  language: LocaleType;
  direction: 'ltr' | 'rtl';
  locale: LocaleConfig;
}

export interface UiSettings {
  animationsEnabled: boolean;
  compactMode: boolean;
  showHelpIcons: boolean;
  sidebarCollapsed: boolean;
  tableRowsPerPage: number;
  tableSize: 'small' | 'default' | 'large';
}

export interface NotificationSettings {
  enabled: boolean;
  sound: boolean;
  desktop: boolean;
  enableEmailNotifications: boolean;
}

export interface SettingsState {
  theme: ThemeSettings;
  language: LanguageSettings;
  ui: UiSettings;
  notifications: NotificationSettings;
  guidesCompleted: string[];
  loadingStates: Map<string, boolean>;
  isOnline: boolean;
  isReconnecting: boolean;
  reconnectAttempts: number;
}

export interface ConfigState {
  configs: ConfigItem[];
  loading: boolean;
} 