export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    [key: string]: any;
  }[];
}

export interface StatCard {
  id: string;
  title: string;
  value: number | string;
  change?: number;
  previousValue?: number | string;
  period?: string;
  icon?: string;
  color?: string;
}

export interface TableRow {
  id: string;
  [key: string]: any;
}

export interface DashboardFilter {
  startDate: Date | string;
  endDate: Date | string;
  compareWithPrevious: boolean;
  groupBy: 'day' | 'week' | 'month';
}

export interface CalculationSummary {
  totalCalculations: number;
  successRate: number;
  averageCost: number;
  populatProducts: string[];
  recentCalculations: any[];
}

export interface DashboardState {
  calculationStats: ChartData;
  cardsData: StatCard[];
  calculationSummary: CalculationSummary;
  recentActivity: TableRow[];
  popularProducts: TableRow[];
  filter: DashboardFilter;
  loading: {
    stats: boolean;
    cards: boolean;
    summary: boolean;
    activity: boolean;
    products: boolean;
  };
  error: string | null;
}

export interface DashboardGetters {
  hasData: boolean;
  trendingProducts: string[];
  topDestinations: string[];
}

export interface DashboardActions {
  loadDashboard: () => Promise<void>;
  loadCalculationStats: (filter?: Partial<DashboardFilter>) => Promise<ChartData>;
  loadCardData: () => Promise<StatCard[]>;
  loadCalculationSummary: () => Promise<CalculationSummary>;
  loadRecentActivity: () => Promise<TableRow[]>;
  loadPopularProducts: () => Promise<TableRow[]>;
  updateFilter: (filter: Partial<DashboardFilter>) => void;
  refreshDashboard: () => Promise<void>;
} 