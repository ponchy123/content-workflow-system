export interface ConfigItem {
  id: string;
  key: string;
  value: any;
  type: 'text' | 'number' | 'switch' | 'select' | 'date' | 'time' | 'json';
  description: string;
  status: boolean;
  createdAt?: string;
  updatedAt?: string;
  editing?: boolean;
  editValue?: any;
  editorProps?: Record<string, any>;
  displayProps?: Record<string, any>;
}

export interface ConfigTypeOption {
  label: string;
  value: ConfigItem['type'];
} 