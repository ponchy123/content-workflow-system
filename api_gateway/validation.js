const { body, validationResult } = require('express-validator');

// 验证结果处理中间件
const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: '输入验证失败',
      details: errors.array().map(err => ({
        field: err.path,
        message: err.msg
      }))
    });
  }
  next();
};

// 注册用户验证规则
const registerValidation = [
  body('username')
    .notEmpty().withMessage('用户名不能为空')
    .isLength({ min: 3, max: 20 }).withMessage('用户名长度必须在3-20个字符之间')
    .matches(/^[a-zA-Z0-9_]+$/).withMessage('用户名只能包含字母、数字和下划线'),

  body('email')
    .notEmpty().withMessage('邮箱不能为空')
    .isEmail().withMessage('请提供有效的邮箱地址'),

  body('password')
    .notEmpty().withMessage('密码不能为空')
    .isLength({ min: 8 }).withMessage('密码长度至少为8个字符')
    .matches(/^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$/)
    .withMessage('密码必须包含至少一个字母、一个数字和一个特殊字符')
];

// 登录验证规则
const loginValidation = [
  body('username')
    .notEmpty().withMessage('用户名不能为空'),

  body('password')
    .notEmpty().withMessage('密码不能为空')
];

// 创建任务验证规则
const createTaskValidation = [
  body('type')
    .notEmpty().withMessage('任务类型不能为空')
    .isIn(['data_analysis', 'content_generation', 'other']).withMessage('无效的任务类型'),

  body('data')
    .notEmpty().withMessage('任务数据不能为空')
    .isObject().withMessage('任务数据必须是一个对象'),

  body('priority')
    .optional()
    .isIn(['low', 'medium', 'high']).withMessage('优先级必须是low、medium或high')
];

module.exports = {
  validate,
  registerValidation,
  loginValidation,
  createTaskValidation
};