# API网关服务

API网关是A2A+MCP多智能体系统的入口点，负责处理客户端请求、身份验证、授权和请求转发。

## 优化特性

### 1. 用户认证与授权
- 基于JWT的身份验证
- 支持令牌刷新机制
- 基于角色的访问控制(RBAC)
- 预定义角色: admin、user、guest

### 2. 错误处理与日志管理
- 结构化错误响应
- 详细的错误类型分类
- 集成ELK(Elasticsearch, Logstash, Kibana)堆栈支持
- 生产环境和开发环境日志配置分离

### 3. 数据持久化
- 完善的数据库模型
- 支持任务优先级和结果存储
- 数据备份和恢复功能
- 定时备份机制(可配置)

## API文档

### 认证接口
- `POST /auth/register`: 用户注册
- `POST /auth/login`: 用户登录
- `POST /auth/refresh-token`: 刷新令牌

### 用户接口
- `GET /tasks`: 获取当前用户的任务列表
- `POST /requests`: 提交新任务请求

### 管理员接口
- `GET /admin/dashboard`: 获取系统统计信息
- `POST /admin/backup`: 备份数据库
- `POST /admin/restore`: 恢复数据库
- `GET /tools/*`: 管理MCP工具(所有工具路由)

## 环境变量配置

```
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=a2a_mcp

# JWT配置
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=24h

# RabbitMQ配置
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# MCP注册中心配置
MCP_REGISTRY_URL=http://mcp_registry:8000

# 日志配置
LOG_LEVEL=info

# Elasticsearch配置(生产环境)
ELASTICSEARCH_URL=http://elasticsearch:9200
```

## 启动服务

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 启动生产服务器
npm start
```

## 数据备份与恢复

1. 备份数据库:
```bash
curl -X POST http://localhost:8001/admin/backup -H 'Authorization: Bearer <admin-token>'
```

2. 恢复数据库:
```bash
curl -X POST http://localhost:8001/admin/restore -H 'Authorization: Bearer <admin-token>' -H 'Content-Type: application/json' -d '{"backupPath": "/path/to/backup.sql"}'
```

## 安全特性

### API速率限制
- 对所有请求应用默认速率限制（15分钟内最多100个请求）
- 对敏感操作（注册、登录、刷新令牌）应用严格速率限制（15分钟内最多20个请求）

### 输入验证
- 使用express-validator对所有用户输入进行验证
- 验证规则包括字段长度、格式、内容要求等
- 提供详细的验证错误信息

### CSRF保护
- 实现跨站请求伪造保护
- 使用cookie存储CSRF令牌
- 提供`/csrf-token`端点获取CSRF令牌

### 安全最佳实践

1. 生产环境中使用HTTPS
2. 定期轮换JWT_SECRET
3. 定期备份数据库
4. 为不同用户分配适当的角色权限
5. 定期更新依赖包
6. 使用环境变量存储敏感信息
7. 实施适当的CORS策略

## 测试

### 单元测试
- 使用Jest框架实现
- 测试覆盖认证功能、速率限制、输入验证和CSRF保护
- 运行单个测试文件：`npm test -- tests/auth.test.js`
- 运行所有测试：`npm test`

### 测试覆盖率
- 配置了覆盖率收集，默认阈值为50%
- 查看覆盖率报告：`open coverage/lcov-report/index.html`

## CI/CD流水线
- 使用GitHub Actions实现
- 自动化测试：在推送到main和develop分支或创建拉取请求时运行
- 自动构建：测试通过后构建Docker镜像并推送到DockerHub
- 自动部署：推送到main分支时自动部署到生产环境
- 配置文件位置：`.github/workflows/ci-cd.yml`