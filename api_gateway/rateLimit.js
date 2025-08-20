const rateLimit = require('express-rate-limit');
const { logger } = require('./errorHandler');

// 自定义存储适配器 - 使用内存存储
class MemoryStore {}

// 速率限制配置
const rateLimitConfig = {
  // 默认配置
  default: {
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100, // 每个IP最多100个请求
    standardHeaders: true,
    legacyHeaders: false,
    message: {
      error: '请求过于频繁，请稍后再试',
      code: 'RATE_LIMIT_EXCEEDED',
      status: 429
    },
    handler: (req, res) => {
      logger.warn('速率限制触发:', { 
        ip: req.ip,
        path: req.path,
        method: req.method
      });
      res.status(429).json(rateLimitConfig.default.message);
    }
  },

  // 严格限制配置 - 用于敏感操作
  strict: {
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 20, // 每个IP最多20个请求
    standardHeaders: true,
    legacyHeaders: false,
    message: {
      error: '敏感操作请求过于频繁，请稍后再试',
      code: 'STRICT_RATE_LIMIT_EXCEEDED',
      status: 429
    },
    handler: (req, res) => {
      logger.warn('敏感操作速率限制触发:', { 
        ip: req.ip,
        path: req.path,
        method: req.method
      });
      res.status(429).json(rateLimitConfig.strict.message);
    }
  }
};

// 创建速率限制中间件
const createRateLimiters = () => {
  return {
    default: rateLimit(rateLimitConfig.default),
    strict: rateLimit(rateLimitConfig.strict)
  };
};

module.exports = {
  createRateLimiters
};