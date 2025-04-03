// 用户Token相关常量
export const TOKEN_EXPIRE_TIME = 7200; // token有效期2小时
export const REFRESH_THRESHOLD = 300; // 剩余5分钟时刷新
export const REFRESH_CHECK_INTERVAL = 60 * 1000; // 每分钟检查一次

// 默认用户信息
export const DEFAULT_USER_INFO = {
  id: '',
  username: '',
  nickname: '',
  email: '',
  avatar: '',
  permissions: [],
  roles: [],
  lastLogin: '',
  status: 1,
}; 