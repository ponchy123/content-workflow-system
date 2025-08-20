const request = require('supertest');
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const { pool } = require('../db');
const { initCsrfProtection } = require('../csrfProtection');
const { createRateLimiters } = require('../rateLimit');
const { registerValidation, loginValidation, validate } = require('../validation');
const authRouter = require('../auth');

// 创建测试用Express应用
const app = express();
app.use(cors());
app.use(cookieParser());
app.use(express.json());

// 初始化安全组件
const rateLimiters = createRateLimiters();
initCsrfProtection(app);

// 应用中间件和路由
app.use(rateLimiters.default);
app.post('/auth/register', registerValidation, validate, authRouter.register);
app.post('/auth/login', loginValidation, validate, authRouter.login);

// 受CSRF保护的测试路由
app.post('/protected-resource', rateLimiters.strict, (req, res) => {
  res.status(200).json({ message: 'Access granted to protected resource' });
});

// 集成测试
describe('Integration Tests', () => {
  beforeEach(async () => {
    // 清理测试数据
    await pool.execute('DELETE FROM test_users');
  });

  test('应该能够注册用户、登录并访问受保护的资源', async () => {
    // 1. 注册新用户
    const registerResponse = await request(app)
      .post('/auth/register')
      .send({
        username: 'integrationtest',
        email: 'integration@example.com',
        password: 'Test@1234'
      })
      .expect(201);

    expect(registerResponse.body.success).toBe(true);
    expect(registerResponse.body).toHaveProperty('token');

    // 2. 登录用户
    const loginResponse = await request(app)
      .post('/auth/login')
      .send({
        username: 'integrationtest',
        password: 'Test@1234'
      })
      .expect(200);

    expect(loginResponse.body.success).toBe(true);
    expect(loginResponse.body).toHaveProperty('token');

    // 3. 获取CSRF令牌
    const csrfResponse = await request(app)
      .get('/csrf-token')
      .set('Cookie', loginResponse.headers['set-cookie'])
      .expect(200);

    const csrfToken = csrfResponse.body.csrfToken;
    const cookies = csrfResponse.headers['set-cookie'];

    // 4. 访问受保护的资源
    const protectedResponse = await request(app)
      .post('/protected-resource')
      .set('Cookie', cookies)
      .set('X-CSRF-Token', csrfToken)
      .set('Authorization', `Bearer ${loginResponse.body.token}`)
      .send({ data: 'test' })
      .expect(200);

    expect(protectedResponse.body.message).toBe('Access granted to protected resource');
  });

  test('应该拒绝未授权访问受保护的资源', async () => {
    // 尝试不登录访问受保护资源
    const response = await request(app)
      .post('/protected-resource')
      .send({ data: 'test' })
      .expect(401);

    expect(response.body.error).toBe('未授权访问');
  });

  test('应该在请求频率过高时拒绝访问', async () => {
    // 连续发送3个严格限制的请求
    for (let i = 0; i < 3; i++) {
      // 先获取CSRF令牌
      const csrfResponse = await request(app).get('/csrf-token');
      const csrfToken = csrfResponse.body.csrfToken;
      const cookies = csrfResponse.headers['set-cookie'];

      const response = await request(app)
        .post('/protected-resource')
        .set('Cookie', cookies)
        .set('X-CSRF-Token', csrfToken)
        .send({ data: 'test' });

      if (i < 2) {
        expect(response.status).toBe(401); // 未授权，但不是速率限制的问题
      } else {
        expect(response.status).toBe(429); // 速率限制
        expect(response.body.error).toBe('请求过于频繁，请稍后再试');
      }
    }
  });
});