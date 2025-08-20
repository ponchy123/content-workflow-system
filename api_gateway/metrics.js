const client = require('prom-client');
const collectDefaultMetrics = client.collectDefaultMetrics;

// 收集默认的Node.js指标
collectDefaultMetrics();

// 自定义指标
const apiRequestCounter = new client.Counter({
  name: 'api_requests_total',
  help: 'Total number of API requests',
  labelNames: ['method', 'route', 'status_code']
});

const apiRequestDurationHistogram = new client.Histogram({
  name: 'api_request_duration_seconds',
  help: 'API request duration in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5]
});

const activeUsersGauge = new client.Gauge({
  name: 'active_users',
  help: 'Number of active users'
});

const taskCounter = new client.Counter({
  name: 'tasks_total',
  help: 'Total number of tasks processed',
  labelNames: ['type', 'status']
});

const taskDurationHistogram = new client.Histogram({
  name: 'task_duration_seconds',
  help: 'Task processing duration in seconds',
  labelNames: ['type', 'status'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30]
});

// 业务指标
const businessMetrics = {
  totalUsers: new client.Gauge({
    name: 'total_users',
    help: 'Total number of registered users'
  }),
  totalTasks: new client.Gauge({
    name: 'total_tasks',
    help: 'Total number of tasks created'
  }),
  avgTaskProcessingTime: new client.Gauge({
    name: 'avg_task_processing_time_seconds',
    help: 'Average task processing time in seconds'
  })
};

// 导出指标和工具函数
module.exports = {
  // 指标
  apiRequestCounter,
  apiRequestDurationHistogram,
  activeUsersGauge,
  taskCounter,
  taskDurationHistogram,
  businessMetrics,

  // 中间件 - 记录API请求指标
  requestMetricsMiddleware: (req, res, next) => {
    const start = Date.now();

    // 在响应结束时记录指标
    res.on('finish', () => {
      const duration = (Date.now() - start) / 1000;
      const route = req.route ? req.route.path : req.path;

      apiRequestCounter.inc({
        method: req.method,
        route,
        status_code: res.statusCode
      });

      apiRequestDurationHistogram.observe({
        method: req.method,
        route,
        status_code: res.statusCode
      }, duration);
    });

    next();
  },

  // 获取所有指标的JSON格式
  getMetrics: async () => {
    return client.register.metrics();
  }
};