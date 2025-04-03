export interface ThemeConfig {
  mode: 'light' | 'dark' | 'auto';
  primaryColor: string;
  primary_color: string;
  success_color: string;
  warning_color: string;
  danger_color: string;
  info_color: string;
  font_family: string;
  border_radius: string;
}

export interface LanguageConfig {
  code: string;
  name: string;
}

export interface SystemConfig {
  key: string;
  value: any;
  description: string;
  is_public: boolean;
  config_type: 'basic' | 'calculation' | 'notification' | 'api';
  validation_rules?: {
    type: string;
    [key: string]: any;
  };
  created_at?: string;
  updated_at?: string;
}

export interface LocaleConfig {
  dateFormat: Record<string, string>;
  numberFormat: Record<string, any>;
  timezone: string;
}
