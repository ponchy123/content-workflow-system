const request = require('supertest');
const express = require('express');
const cookieParser = require('cookie-parser');
const { initCsrfProtection } = require('../csrfProtection');

// 创建测试用Express应用
const app = express();
app.use(cookieParser());
app.use(express.json());

// 初始化CSRF保护
initCsrfProtection(app);

// 添加测试路由
app.get('/test-csrf', (req, res) => {
  res.status(200).json({ message: 'CSRF test' });
});

app.post('/test-csrf', (req, res) => {
  res.status(200).json({ message: 'CSRF protected POST test' });
});

// 测试CSRF保护功能
describe('CSRF Protection Middleware', () => {
  test('应该为GET请求生成CSRF令牌', async () => {
    const response = await request(app).get('/csrf-token');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('csrfToken');
    expect(response.headers['set-cookie']).toBeDefined();
  });

  test('应该允许包含有效CSRF令牌的POST请求', async () => {
    // 先获取CSRF令牌
    const tokenResponse = await request(app).get('/csrf-token');
    const csrfToken = tokenResponse.body.csrfToken;
    const cookies = tokenResponse.headers['set-cookie'];

    // 使用CSRF令牌发送POST请求
    const response = await request(app)
      .post('/test-csrf')
      .set('Cookie', cookies)
      .set('X-CSRF-Token', csrfToken)
      .send({ data: 'test' });

    expect(response.status).toBe(200);
    expect(response.body.message).toBe('CSRF protected POST test');
  });

  test('应该拒绝不包含CSRF令牌的POST请求', async () => {
    // 先获取Cookie但不使用CSRF令牌
    const tokenResponse = await request(app).get('/csrf-token');
    const cookies = tokenResponse.headers['set-cookie'];

    // 不提供CSRF令牌发送POST请求
    const response = await request(app)
      .post('/test-csrf')
      .set('Cookie', cookies)
      .send({ data: 'test' });

    expect(response.status).toBe(403);
    expect(response.body.error).toBe('无效的CSRF令牌');
  });

  test('应该拒绝包含无效CSRF令牌的POST请求', async () => {
    // 先获取Cookie
    const tokenResponse = await request(app).get('/csrf-token');
    const cookies = tokenResponse.headers['set-cookie'];

    // 使用无效的CSRF令牌发送POST请求
    const response = await request(app)
      .post('/test-csrf')
      .set('Cookie', cookies)
      .set('X-CSRF-Token', 'invalid-token')
      .send({ data: 'test' });

    expect(response.status).toBe(403);
    expect(response.body.error).toBe('无效的CSRF令牌');
  });
});