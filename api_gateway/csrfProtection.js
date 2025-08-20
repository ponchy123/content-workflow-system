const csrf = require('csurf');
const cookieParser = require('cookie-parser');

// 创建CSRF保护中间件
const csrfProtection = csrf({
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict'
  }
});

// 初始化CSRF保护
const initCsrfProtection = (app) => {
  // 首先使用cookie-parser中间件
  app.use(cookieParser());

  // 然后应用CSRF保护中间件
  app.use(csrfProtection);

  // 提供CSRF令牌的路由
  app.get('/csrf-token', (req, res) => {
    res.json({
      csrfToken: req.csrfToken()
    });
  });

  // 为WebSocket连接提供CSRF令牌
  app.get('/ws-csrf-token', (req, res) => {
    res.json({
      csrfToken: req.csrfToken()
    });
  });
};

module.exports = {
  initCsrfProtection
};