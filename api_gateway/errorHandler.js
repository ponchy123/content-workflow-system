const winston = require('winston');
const Elasticsearch = require('winston-elasticsearch');

// 定义错误类型
const ErrorTypes = {
  AUTHENTICATION: 'AUTHENTICATION_ERROR',
  AUTHORIZATION: 'AUTHORIZATION_ERROR',
  VALIDATION: 'VALIDATION_ERROR',
  DATABASE: 'DATABASE_ERROR',
  EXTERNAL_API: 'EXTERNAL_API_ERROR',
  SERVER: 'SERVER_ERROR',
  NOT_FOUND: 'NOT_FOUND_ERROR'
};

// 创建ES传输器
const esTransport = new Elasticsearch({
  level: 'info',
  clientOpts: {
    node: process.env.ELASTICSEARCH_URL || 'http://elasticsearch:9200'
  },
  indexPrefix: 'a2a-mcp-logs',
  transformer: (logData) => {
    return {
      '@timestamp': logData.timestamp,
      level: logData.level,
      message: logData.message,
      metadata: logData.metadata,
      service: 'api-gateway',
      environment: process.env.NODE_ENV || 'development'
    };
  }
});

// 创建日志记录器
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss.SSS'
    }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, metadata }) => {
          return `[${timestamp}] ${level.toUpperCase()}: ${message} ${metadata ? JSON.stringify(metadata) : ''}`;
        })
      )
    }),
    new winston.transports.File({
      filename: 'error.log',
      level: 'error'
    }),
    new winston.transports.File({
      filename: 'combined.log'
    }),
    // 只有在生产环境才启用ELK集成
    ...(process.env.NODE_ENV === 'production' ? [esTransport] : [])
  ]
});

// 错误处理中间件
const errorHandler = (err, req, res, next) => {
  // 提取错误信息
  let statusCode = err.statusCode || 500;
  let message = err.message || '服务器内部错误';
  let errorType = ErrorTypes.SERVER;

  // 确定错误类型
  if (statusCode === 401) {
    errorType = ErrorTypes.AUTHENTICATION;
  } else if (statusCode === 403) {
    errorType = ErrorTypes.AUTHORIZATION;
  } else if (statusCode === 400) {
    errorType = ErrorTypes.VALIDATION;
  } else if (statusCode === 404) {
    errorType = ErrorTypes.NOT_FOUND;
    message = message || '请求的资源不存在';
  } else if (err.name === 'SequelizeError' || err.name === 'DatabaseError') {
    errorType = ErrorTypes.DATABASE;
    statusCode = 500;
  } else if (err.code === 'ECONNREFUSED' || err.code === 'ETIMEDOUT') {
    errorType = ErrorTypes.EXTERNAL_API;
    statusCode = 503;
  }

  // 构建错误元数据
  const metadata = {
    path: req.path,
    method: req.method,
    headers: req.headers,
    body: req.body,
    params: req.params,
    query: req.query,
    stack: err.stack,
    error_type: errorType,
    error_code: err.code || null
  };

  // 记录错误日志
  if (statusCode >= 500) {
    logger.error(message, { metadata });
  } else if (statusCode >= 400) {
    logger.warn(message, { metadata });
  } else {
    logger.info(message, { metadata });
  }

  // 构建错误响应
  const errorResponse = {
    error: {
      type: errorType,
      message: message,
      code: err.code || null
    },
    request_id: req.requestId || 'unknown',
    timestamp: new Date().toISOString()
  };

  // 发送错误响应
  res.status(statusCode).json(errorResponse);
};

// 日志中间件
const loggingMiddleware = (req, res, next) => {
  // 生成请求ID
  req.requestId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

  // 记录请求信息
  const start = Date.now();
  logger.info(`${req.method} ${req.path}`, {
    metadata: {
      request_id: req.requestId,
      path: req.path,
      method: req.method,
      headers: req.headers,
      body: req.body,
      params: req.params,
      query: req.query
    }
  });

  // 监听响应完成
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info(`${req.method} ${req.path} ${res.statusCode} ${duration}ms`, {
      metadata: {
        request_id: req.requestId,
        status_code: res.statusCode,
        duration_ms: duration
      }
    });
  });

  next();
};

module.exports = {
  errorHandler,
  loggingMiddleware,
  logger
};