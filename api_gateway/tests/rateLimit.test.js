const request = require('supertest');
const express = require('express');
const { createRateLimiters } = require('../rateLimit');

// 创建测试用Express应用
const app = express();
app.use(express.json());

// 初始化速率限制器
const rateLimiters = createRateLimiters();

// 应用速率限制中间件
app.get('/test-default', rateLimiters.default, (req, res) => {
  res.status(200).json({ message: 'Default rate limit test' });
});

app.get('/test-strict', rateLimiters.strict, (req, res) => {
  res.status(200).json({ message: 'Strict rate limit test' });
});

// 测试速率限制功能
describe('Rate Limit Middleware', () => {
  // 测试默认速率限制
  describe('Default Rate Limit', () => {
    test('应该允许在限制范围内的请求', async () => {
      // 连续发送5个请求
      for (let i = 0; i < 5; i++) {
        const response = await request(app).get('/test-default');
        expect(response.status).toBe(200);
        expect(response.body.message).toBe('Default rate limit test');
      }
    });

    test('应该拒绝超出限制的请求', async () => {
      // 连续发送11个请求，超出默认限制（10个/15分钟）
      for (let i = 0; i < 11; i++) {
        const response = await request(app).get('/test-default');
        if (i < 10) {
          expect(response.status).toBe(200);
        } else {
          expect(response.status).toBe(429);
          expect(response.body.error).toBe('请求过于频繁，请稍后再试');
        }
      }
    });
  });

  // 测试严格速率限制
  describe('Strict Rate Limit', () => {
    test('应该允许在严格限制范围内的请求', async () => {
      // 连续发送2个请求
      for (let i = 0; i < 2; i++) {
        const response = await request(app).get('/test-strict');
        expect(response.status).toBe(200);
        expect(response.body.message).toBe('Strict rate limit test');
      }
    });

    test('应该拒绝超出严格限制的请求', async () => {
      // 连续发送3个请求，超出严格限制（2个/15分钟）
      for (let i = 0; i < 3; i++) {
        const response = await request(app).get('/test-strict');
        if (i < 2) {
          expect(response.status).toBe(200);
        } else {
          expect(response.status).toBe(429);
          expect(response.body.error).toBe('请求过于频繁，请稍后再试');
        }
      }
    });
  });
});