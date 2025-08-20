const dotenv = require('dotenv');
const { pool } = require('../db');

// 加载环境变量
dotenv.config();

// 测试前设置
beforeAll(async () => {
  // 初始化测试数据库
  try {
    await pool.execute('CREATE TABLE IF NOT EXISTS test_users (
      id VARCHAR(36) PRIMARY KEY,
      username VARCHAR(50) NOT NULL,
      email VARCHAR(100) NOT NULL,
      password VARCHAR(100) NOT NULL,
      role VARCHAR(20) NOT NULL
    )');
    console.log('测试数据库表已创建');
  } catch (error) {
    console.error('创建测试数据库表失败:', error);
  }
});

// 测试后清理
afterAll(async () => {
  // 删除测试数据
  try {
    await pool.execute('DROP TABLE IF EXISTS test_users');
    console.log('测试数据库表已删除');
    await pool.end();
  } catch (error) {
    console.error('清理测试数据库失败:', error);
  }
});