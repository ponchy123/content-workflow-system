export interface DashboardState {
  // 运营仪表盘
  summary: {
    pendingOrders: number;      // 待处理订单
    todayOrders: number;        // 今日运单量
    monthlyRevenue: number;     // 本月运费
    abnormalOrders: number;     // 异常订单
    
    // 增长率
    pendingOrdersGrowth: number;
    todayOrdersGrowth: number;
    monthlyRevenueGrowth: number;
    abnormalOrdersGrowth: number;
  };

  // 运单趋势
  orderTrends: {
    hourly: Array<{
      hour: string;           // 小时 (如 "08:00")
      orderCount: number;     // 运单数量
      completionRate: number; // 完成率
    }>;
  };

  // 运费分布
  freightDistribution: {
    standard: number;    // 标准快递
    economic: number;    // 经济快递
    sameCity: number;    // 同城快递
    international: number; // 国际快递
  };

  // 异常订单监控
  abnormalOrders: Array<{
    type: string;        // 异常类型
    count: number;       // 数量
  }>;

  // 最新订单动态
  recentOrders: Array<{
    orderNumber: string;   // 运单号
    status: string;       // 状态
    route: string;        // 路线
    weight: number;       // 重量
    timestamp: string;    // 时间戳
  }>;
} 