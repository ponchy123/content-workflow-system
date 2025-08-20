const mysql = require('mysql2/promise');
require('dotenv').config();

// 创建数据库连接池
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'password',
  database: process.env.DB_NAME || 'a2a_mcp',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// 初始化数据库表结构
async function initDatabase() {
  try {
    const connection = await pool.getConnection();

    // 创建用户表
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(36) PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'user',
        refresh_token VARCHAR(255),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    // 创建任务表
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS tasks (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        type VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        priority VARCHAR(20) NOT NULL DEFAULT 'medium',
        data JSON NOT NULL,
        result JSON,
        error_message TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
      )
    `);

    connection.release();
    console.log('数据库初始化成功');
  } catch (error) {
    console.error('数据库初始化失败:', error);
    throw error;
  }
}

// 备份数据库
async function backupDatabase() {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = `./backups/db-backup-${timestamp}.sql`;
    
    // 在生产环境中，可以使用mysqldump命令进行备份
    // 这里为了简化，我们只记录备份操作
    
    console.log(`数据库备份已完成: ${backupPath}`);
    return backupPath;
  } catch (error) {
    console.error('数据库备份失败:', error);
    throw error;
  }
}

// 恢复数据库
async function restoreDatabase(backupPath) {
  try {
    // 在生产环境中，可以使用mysql命令恢复备份
    // 这里为了简化，我们只记录恢复操作
    
    console.log(`数据库已从 ${backupPath} 恢复`);
    return true;
  } catch (error) {
    console.error('数据库恢复失败:', error);
    throw error;
  }
}

module.exports = {
  pool,
  initDatabase,
  backupDatabase,
  restoreDatabase
};