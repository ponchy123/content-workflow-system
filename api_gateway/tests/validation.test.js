const request = require('supertest');
const express = require('express');
const { registerValidation, loginValidation, createTaskValidation, validate } = require('../validation');

// 创建测试用Express应用
const app = express();
app.use(express.json());

// 添加测试路由
app.post('/test-register-validation', registerValidation, validate, (req, res) => {
  res.status(200).json({ success: true });
});

app.post('/test-login-validation', loginValidation, validate, (req, res) => {
  res.status(200).json({ success: true });
});

app.post('/test-task-validation', createTaskValidation, validate, (req, res) => {
  res.status(200).json({ success: true });
});

// 测试输入验证功能
describe('Validation Middleware', () => {
  // 测试注册验证
  describe('Register Validation', () => {
    test('应该接受有效的注册数据', async () => {
      const response = await request(app)
        .post('/test-register-validation')
        .send({
          username: 'testuser',
          email: 'test@example.com',
          password: 'Test@1234'
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    test('应该拒绝无效的用户名', async () => {
      const response = await request(app)
        .post('/test-register-validation')
        .send({
          username: 't', // 太短
          email: 'test@example.com',
          password: 'Test@1234'
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'username')).toBe(true);
    });

    test('应该拒绝无效的邮箱', async () => {
      const response = await request(app)
        .post('/test-register-validation')
        .send({
          username: 'testuser',
          email: 'invalid-email',
          password: 'Test@1234'
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'email')).toBe(true);
    });

    test('应该拒绝无效的密码', async () => {
      const response = await request(app)
        .post('/test-register-validation')
        .send({
          username: 'testuser',
          email: 'test@example.com',
          password: 'password' // 不符合密码规则
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'password')).toBe(true);
    });
  });

  // 测试登录验证
  describe('Login Validation', () => {
    test('应该接受有效的登录数据', async () => {
      const response = await request(app)
        .post('/test-login-validation')
        .send({
          username: 'testuser',
          password: 'Test@1234'
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    test('应该拒绝缺少用户名的登录数据', async () => {
      const response = await request(app)
        .post('/test-login-validation')
        .send({
          password: 'Test@1234'
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'username')).toBe(true);
    });

    test('应该拒绝缺少密码的登录数据', async () => {
      const response = await request(app)
        .post('/test-login-validation')
        .send({
          username: 'testuser'
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'password')).toBe(true);
    });
  });

  // 测试创建任务验证
  describe('Create Task Validation', () => {
    test('应该接受有效的任务数据', async () => {
      const response = await request(app)
        .post('/test-task-validation')
        .send({
          title: 'Test Task',
          description: 'This is a test task',
          priority: 'medium',
          dueDate: '2024-12-31'
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    test('应该拒绝缺少标题的任务数据', async () => {
      const response = await request(app)
        .post('/test-task-validation')
        .send({
          description: 'This is a test task',
          priority: 'medium',
          dueDate: '2024-12-31'
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'title')).toBe(true);
    });

    test('应该拒绝无效的优先级', async () => {
      const response = await request(app)
        .post('/test-task-validation')
        .send({
          title: 'Test Task',
          description: 'This is a test task',
          priority: 'invalid',
          dueDate: '2024-12-31'
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'priority')).toBe(true);
    });

    test('应该拒绝无效的截止日期格式', async () => {
      const response = await request(app)
        .post('/test-task-validation')
        .send({
          title: 'Test Task',
          description: 'This is a test task',
          priority: 'medium',
          dueDate: '31-12-2024' // 无效格式
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toBeDefined();
      expect(response.body.errors.some(err => err.param === 'dueDate')).toBe(true);
    });
  });
});