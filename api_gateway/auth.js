const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');
const { pool } = require('./db');
const { logger } = require('./errorHandler');

// JWT密钥
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRES_IN = '24h';
const REFRESH_TOKEN_EXPIRES_IN = '7d';

// 角色定义
const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest'
};

// 安装bcryptjs依赖
// npm install bcryptjs

// 哈希密码
const hashPassword = async (password) => {
  const salt = await bcrypt.genSalt(10);
  return bcrypt.hash(password, salt);
};

// 验证密码
const validatePassword = async (password, hashedPassword) => {
  return bcrypt.compare(password, hashedPassword);
};

// 生成访问令牌
const generateToken = (userId) => {
  return jwt.sign({ id: userId }, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
};

// 刷新令牌
const refreshToken = async (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken) {
    return res.status(400).json({ error: '未提供刷新令牌' });
  }

  try {
    const decoded = jwt.verify(refreshToken, JWT_SECRET);
    const userId = decoded.id;

    // 从数据库获取用户信息
    const [users] = await pool.execute('SELECT * FROM users WHERE id = ?', [userId]);

    if (users.length === 0) {
      return res.status(401).json({ error: '用户不存在' });
    }

    const user = users[0];
    const newToken = generateToken(userId);
    const newRefreshToken = generateRefreshToken(userId);

    // 更新数据库中的刷新令牌
    await pool.execute('UPDATE users SET refresh_token = ? WHERE id = ?', [newRefreshToken, userId]);

    res.json({
      success: true,
      token: newToken,
      refreshToken: newRefreshToken,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      }
    });
  } catch (error) {
    logger.error('刷新令牌失败:', { error });
    return res.status(403).json({ error: '无效的刷新令牌' });
  }
};

// 验证JWT令牌中间件
const authenticateJWT = async (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({ error: '未提供认证令牌' });
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const userId = decoded.id;

    // 从数据库获取用户信息
    const [users] = await pool.execute('SELECT * FROM users WHERE id = ?', [userId]);

    if (users.length === 0) {
      return res.status(401).json({ error: '用户不存在' });
    }

    const user = users[0];
    req.user = {
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role
    };

    next();
  } catch (error) {
    logger.error('JWT认证失败:', { error });
    return res.status(403).json({ error: '无效的认证令牌' });
  }
};

// 角色授权中间件
const authorizeRoles = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: '未认证' });
    }

    if (!roles.includes(req.user.role)) {
      logger.warn('权限不足', { userId: req.user.id, role: req.user.role, requiredRoles: roles });
      return res.status(403).json({ error: '权限不足' });
    }

    next();
  };
};

// 生成刷新令牌
const generateRefreshToken = (userId) => {
  return jwt.sign({ id: userId }, JWT_SECRET, { expiresIn: REFRESH_TOKEN_EXPIRES_IN });
};

// 注册用户
const register = async (req, res) => {
  try {
    const { username, password, email } = req.body;

    // 检查用户是否已存在
    const [existingUsers] = await pool.execute(
      'SELECT * FROM users WHERE username = ? OR email = ?',
      [username, email]
    );

    if (existingUsers.length > 0) {
      return res.status(400).json({ error: '用户名或邮箱已存在' });
    }

    // 创建新用户
    const userId = uuidv4();
    const hashedPassword = await hashPassword(password);

    await pool.execute(
      'INSERT INTO users (id, username, email, password, role) VALUES (?, ?, ?, ?, ?)',
      [userId, username, email, hashedPassword, 'user']
    );

    // 生成令牌
    const token = generateToken(userId);

    res.status(201).json({
      success: true,
      token,
      user: {
        id: userId,
        username,
        email,
        role: 'user'
      }
    });
  } catch (error) {
    console.error('注册用户失败:', error);
    res.status(500).json({ error: '注册用户时发生错误' });
  }
};

// 用户登录
const login = async (req, res) => {
  try {
    const { username, password } = req.body;

    // 查找用户
    const [users] = await pool.execute('SELECT * FROM users WHERE username = ?', [username]);

    if (users.length === 0) {
      return res.status(401).json({ error: '用户名或密码错误' });
    }

    const user = users[0];

    if (!(await validatePassword(password, user.password))) {
      return res.status(401).json({ error: '用户名或密码错误' });
    }

    // 生成令牌
    const token = generateToken(user.id);

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      }
    });
  } catch (error) {
    console.error('用户登录失败:', error);
    res.status(500).json({ error: '登录时发生错误' });
  }
};

module.exports = {
  authenticateJWT,
  authorizeRoles,
  register,
  login,
  refreshToken,
  ROLES
};