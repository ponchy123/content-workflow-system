require('dotenv').config();
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const amqp = require('amqplib');
const { v4: uuidv4 } = require('uuid');
const { authenticateJWT, register, login, refreshToken, authorizeRoles, ROLES } = require('./auth');
const { errorHandler, loggingMiddleware, logger } = require('./errorHandler');
const { initDatabase, pool, backupDatabase, restoreDatabase } = require('./db');
const metrics = require('./metrics');
const { createRateLimiters } = require('./rateLimit');
const { validate, registerValidation, loginValidation, createTaskValidation } = require('./validation');
const { initCsrfProtection } = require('./csrfProtection');

// 初始化速率限制器
const rateLimiters = createRateLimiters();




// 创建Express应用
const app = express();// 应用中间件
app.use(cors());
app.use(express.json());
app.use(loggingMiddleware);
app.use(metrics.requestMetricsMiddleware);

// 应用默认速率限制到所有请求
app.use(rateLimiters.default);

// 初始化CSRF保护
initCsrfProtection(app); 创建HTTP服务器并附加Express应用
const server = http.createServer(app);

// 创建Socket.io服务器
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// RabbitMQ连接配置
let rabbitmqConnection = null;
let channel = null;
const EXCHANGE_NAME = 'a2a_bus';
const CORE_SCHEDULER_QUEUE = 'core_scheduler';

// 存储请求响应映射
const requestMap = new Map();
const { pool } = require('./db');


// 连接RabbitMQ
async function connectRabbitMQ() {
  try {
    rabbitmqConnection = await amqp.connect(process.env.RABBITMQ_URL);
    channel = await rabbitmqConnection.createChannel();

    // 声明交换机
    await channel.assertExchange(EXCHANGE_NAME, 'topic', { durable: true });

    // 声明响应队列
    const responseQueue = await channel.assertQueue('', { exclusive: true });

    // 监听响应队列
    channel.consume(responseQueue.queue, (msg) => {
      if (msg) {
        const content = JSON.parse(msg.content.toString());
        const requestId = content.request_id;

        // 更新任务状态到数据库
        try {
          const status = content.status || 'completed';
          pool.execute(
            'UPDATE tasks SET status = ?, data = ? WHERE id = ?',
            [status, JSON.stringify(content), requestId]
          );
          logger.info('任务状态已更新', { taskId: requestId, status });
        } catch (error) {
          logger.error('更新任务状态失败', { error, taskId: requestId });
        }

        if (requestMap.has(requestId)) {
          // 通过WebSocket发送响应
          const socketId = requestMap.get(requestId);
          io.to(socketId).emit('task_update', content);
          requestMap.delete(requestId);
        }

        channel.ack(msg);
      }
    });

    console.log('成功连接到RabbitMQ');
  } catch (error) {
    logger.error('连接RabbitMQ失败:', { error });
    // 5秒后重试
    setTimeout(connectRabbitMQ, 5000);
  }
}

// 初始化连接
connectRabbitMQ();

// API路由: 发送请求到核心调度器 (受保护，用户和管理员可访问)
app.post('/requests', authenticateJWT, authorizeRoles(ROLES.USER, ROLES.ADMIN), createTaskValidation, validate, async (req, res) => {
  try {
    if (!channel) {
      return res.status(503).json({
        error: 'RabbitMQ连接未建立，请稍后再试'
      });
    }

    const { type, data } = req.body;
    const requestId = uuidv4();
    const socketId = req.headers['socket-id'] || 'unknown';
    const userId = req.user.id;


    // 存储请求ID和Socket ID的映射
    requestMap.set(requestId, socketId);

    // 保存任务到数据库
    try {
      await pool.execute(
        'INSERT INTO tasks (id, user_id, type, status, data) VALUES (?, ?, ?, ?, ?)',
        [requestId, userId, type, 'pending', JSON.stringify(data)]
      );
      logger.info('任务已保存到数据库', { taskId: requestId });
    } catch (error) {
      logger.error('保存任务到数据库失败', { error, taskId: requestId });
    }


    // 构建消息
    const message = {
      source: 'api_gateway',
      target: CORE_SCHEDULER_QUEUE,
      type: 'user_request',
      data: {
        id: requestId,
        type,
        ...data
      },
      timestamp: Date.now()
    };

    // 发送消息到核心调度器
    channel.publish(
      EXCHANGE_NAME,
      `agent.${CORE_SCHEDULER_QUEUE}`,
      Buffer.from(JSON.stringify(message))
    );

    res.json({
      success: true,
      request_id: requestId,
      message: '请求已发送到调度器'
    });
  } catch (error) {
    logger.error('处理请求失败:', { error });
    res.status(500).json({
      error: '处理请求时发生错误'
    });
  }
});

// API路由: 转发到MCP注册中心 (受保护，仅管理员可访问)
app.use('/tools', authenticateJWT, authorizeRoles(ROLES.ADMIN), async (req, res) => {
  try {
    const url = `${process.env.MCP_REGISTRY_URL}/tools${req.path}`;
    const options = {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...req.headers
      },
      body: req.method !== 'GET' && req.method !== 'DELETE' ? JSON.stringify(req.body) : undefined
    };

    const response = await fetch(url, options);
    const data = await response.json();

    res.status(response.status).json(data);
  } catch (error) {
    logger.error('转发请求到MCP注册中心失败:', { error });
    res.status(500).json({
      error: '转发请求时发生错误'
    });
  }
});

// 处理Socket.io连接
io.on('connection', (socket) => {
  logger.info(`新的客户端连接: ${socket.id}`);

  // 客户端断开连接
  socket.on('disconnect', () => {
    logger.info(`客户端断开连接: ${socket.id}`);
    // 清理相关请求映射
    for (const [requestId, socketId] of requestMap.entries()) {
      if (socketId === socket.id) {
        requestMap.delete(requestId);
      }
    }
  });

  // 客户端注册请求ID
  socket.on('register_request', (requestId) => {
    requestMap.set(requestId, socket.id);
  });
});

// 认证路由 - 应用严格速率限制和输入验证
app.post('/auth/register', rateLimiters.strict, registerValidation, validate, register);
app.post('/auth/login', rateLimiters.strict, loginValidation, validate, login);

// API路由: 刷新令牌 - 应用严格速率限制
app.post('/auth/refresh-token', rateLimiters.strict, refreshToken);

// API路由: 管理员专用路由
app.get('/admin/dashboard', authenticateJWT, authorizeRoles(ROLES.ADMIN), async (req, res) => {
  try {
    // 获取系统统计信息
    const [tasksCount] = await pool.execute('SELECT COUNT(*) as count FROM tasks');
    const [usersCount] = await pool.execute('SELECT COUNT(*) as count FROM users');
    
    res.json({
      success: true,
      dashboard: {
        tasks: tasksCount[0].count,
        users: usersCount[0].count
      }
    });
  } catch (error) {
    logger.error('获取管理员仪表盘数据失败:', { error });
    res.status(500).json({
      error: '获取数据时发生错误'
    });
  }
});

// API路由: 备份数据库 (仅管理员可访问)
app.post('/admin/backup', authenticateJWT, authorizeRoles(ROLES.ADMIN), async (req, res) => {
  try {
    const backupPath = await backupDatabase();
    res.json({
      success: true,
      message: '数据库备份成功',
      backup_path: backupPath
    });
  } catch (error) {
    logger.error('数据库备份失败:', { error });
    res.status(500).json({
      error: '备份数据库时发生错误'
    });
  }
});

// API路由: 恢复数据库 (仅管理员可访问)
app.post('/admin/restore', authenticateJWT, authorizeRoles(ROLES.ADMIN), async (req, res) => {
  try {
    const { backupPath } = req.body;
    if (!backupPath) {
      return res.status(400).json({
        error: '未提供备份路径'
      });
    }
    
    await restoreDatabase(backupPath);
    res.json({
      success: true,
      message: '数据库恢复成功'
    });
  } catch (error) {
    logger.error('数据库恢复失败:', { error });
    res.status(500).json({
      error: '恢复数据库时发生错误'
    });
  }
});

// 获取用户任务路由 (受保护)
app.get('/tasks', authenticateJWT, async (req, res) => {
  try {
    const userId = req.user.id;
    const [tasks] = await pool.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC', [userId]);

    // 将data字段从JSON字符串转换为对象
    const formattedTasks = tasks.map(task => ({
      ...task,
      data: JSON.parse(task.data)
    }));

    res.json({
      success: true,
      tasks: formattedTasks
    });
  } catch (error) {
    logger.error('获取用户任务失败', { error, userId: req.user.id });
    res.status(500).json({
      error: '获取任务时发生错误'
    });
  }
});

// 健康检查路由
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: Date.now(),
    rabbitmq_connected: !!channel
  });
});

// 指标端点
app.get('/metrics', async (req, res) => {
  try {
    const metricsData = await metrics.getMetrics();
    res.set('Content-Type', 'text/plain');
    res.send(metricsData);
  } catch (error) {
    logger.error('获取指标失败:', { error });
    res.status(500).json({
      error: '获取指标时发生错误'
    });
  }
});

// 业务指标端点
app.get('/business-metrics', async (req, res) => {
  try {
    // 获取用户总数
    const [usersResult] = await pool.execute('SELECT COUNT(*) as count FROM users');
    metrics.businessMetrics.totalUsers.set(usersResult[0].count);

    // 获取任务总数
    const [tasksResult] = await pool.execute('SELECT COUNT(*) as count FROM tasks');
    metrics.businessMetrics.totalTasks.set(tasksResult[0].count);

    // 获取平均任务处理时间
    const [avgTimeResult] = await pool.execute(
      'SELECT AVG(TIMESTAMPDIFF(SECOND, created_at, completed_at)) as avg_time FROM tasks WHERE completed_at IS NOT NULL'
    );
    metrics.businessMetrics.avgTaskProcessingTime.set(avgTimeResult[0].avg_time || 0);

    const metricsData = await metrics.getMetrics();
    res.set('Content-Type', 'text/plain');
    res.send(metricsData);
  } catch (error) {
    logger.error('获取业务指标失败:', { error });
    res.status(500).json({
      error: '获取业务指标时发生错误'
    });
  }
});

// 错误处理中间件（应放在所有路由后面）
app.use(errorHandler);

// 初始化数据库并启动服务器
const PORT = process.env.PORT || 8000;

async function startServer() {
  try {
    // 初始化数据库
    await initDatabase();

    // 启动服务器
    server.listen(PORT, () => {
      logger.info(`API网关服务运行在端口 ${PORT}`);
    });
  } catch (error) {
    logger.error('服务器启动失败:', { error });
    process.exit(1);
  }
}

// 启动服务器
startServer();

// 优雅关闭
process.on('SIGINT', async () => {
  logger.info('正在关闭服务器...');
  if (rabbitmqConnection) {
    await rabbitmqConnection.close();
  }
  server.close(() => {
    logger.info('服务器已关闭');
    process.exit(0);
  });
});