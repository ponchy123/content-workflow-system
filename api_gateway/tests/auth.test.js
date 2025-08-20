const request = require('supertest');
const express = require('express');
const cors = require('cors');
const { pool } = require('../db');
const authRouter = require('../auth');

// 创建测试用Express应用
const app = express();
app.use(cors());
app.use(express.json());

// 模拟auth.js的路由
app.post('/auth/register', authRouter.register);
app.post('/auth/login', authRouter.login);

// 测试数据
const testUser = {
  username: 'testuser',
  email: 'test@example.com',
  password: 'Test@1234'
};

// 测试注册功能
describe('Auth API - Register', () => {
  beforeEach(async () => {
    // 清理测试数据
    await pool.execute('DELETE FROM test_users');
  });

  test('应该成功注册新用户', async () => {
    const response = await request(app)
      .post('/auth/register')
      .send(testUser)
      .expect(201);

    expect(response.body.success).toBe(true);
    expect(response.body).toHaveProperty('token');
    expect(response.body.user.username).toBe(testUser.username);
    expect(response.body.user.email).toBe(testUser.email);
    expect(response.body.user.role).toBe('user');
  });

  test('应该拒绝注册已存在的用户名', async () => {
    // 先注册一个用户
    await request(app)
      .post('/auth/register')
      .send(testUser);

    // 尝试使用相同的用户名注册
    const response = await request(app)
      .post('/auth/register')
      .send({
        ...testUser,
        email: 'another@example.com'
      })
      .expect(400);

    expect(response.body.error).toBe('用户名或邮箱已存在');
  });

  test('应该拒绝注册无效的邮箱', async () => {
    const response = await request(app)
      .post('/auth/register')
      .send({
        ...testUser,
        email: 'invalid-email'
      })
      .expect(400);

    expect(response.body.error).not.toBeUndefined();
  });
});

// 测试登录功能
describe('Auth API - Login', () => {
  beforeEach(async () => {
    // 清理测试数据
    await pool.execute('DELETE FROM test_users');

    // 创建测试用户
    await request(app)
      .post('/auth/register')
      .send(testUser);
  });

  test('应该成功登录已注册用户', async () => {
    const response = await request(app)
      .post('/auth/login')
      .send({
        username: testUser.username,
        password: testUser.password
      })
      .expect(200);

    expect(response.body.success).toBe(true);
    expect(response.body).toHaveProperty('token');
    expect(response.body.user.username).toBe(testUser.username);
  });

  test('应该拒绝使用错误的密码登录', async () => {
    const response = await request(app)
      .post('/auth/login')
      .send({
        username: testUser.username,
        password: 'wrongpassword'
      })
      .expect(401);

    expect(response.body.error).toBe('用户名或密码错误');
  });

  test('应该拒绝登录不存在的用户', async () => {
    const response = await request(app)
      .post('/auth/login')
      .send({
        username: 'nonexistentuser',
        password: testUser.password
      })
      .expect(401);

    expect(response.body.error).toBe('用户名或密码错误');
  });
});