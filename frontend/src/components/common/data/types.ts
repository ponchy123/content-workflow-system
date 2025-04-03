export interface FilterField {
  prop: string;
  label: string;
  type?: 'input' | 'select' | 'date' | 'daterange' | string;
  placeholder?: string;
  startPlaceholder?: string;
  endPlaceholder?: string;
  options?: { label: string; value: any; disabled?: boolean }[];
  component?: string;
  props?: Record<string, any>;
  rules?: Record<string, any>[];
  span?: number;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
} 