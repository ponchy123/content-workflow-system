# A2A+MCP多智能体系统实现方案

## 系统概述

本方案实现了一个不依赖n8n的A2A+MCP多智能体系统，通过自主设计的架构实现智能体间通信(A2A)和能力扩展(MCP)。系统由以下核心组件构成：

1. **核心调度Agent**：负责接收用户请求、分配任务给专业Agent并整合结果
2. **专业Agent群**：包括数据分析Agent和内容生成Agent，处理具体任务
3. **A2A通信总线**：基于RabbitMQ实现智能体间异步通信
4. **MCP能力扩展层**：注册和管理外部工具，提供能力共享机制
5. **MySQL数据库**：存储工具注册信息、任务记录和系统配置

## 技术栈

- **容器化**：Docker & Docker Compose
- **通信**：RabbitMQ
- **数据库**：MySQL
- **后端**：Python 3.9 (FastAPI, Pika)
- **API安全**：OAuth 2.1 / JWT

## 快速开始

### 前提条件

- 安装Docker和Docker Compose
- 获取OpenAI API密钥 (用于内容生成功能)

### 配置修改

1. 编辑`.env`文件，替换以下占位符：
   - `your_jwt_secret_key_here`: 为MCP注册中心设置一个安全的JWT密钥
   - `your_openai_api_key_here`: 填入你的OpenAI API密钥

### 启动系统

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 访问服务

- **n8n界面**: http://localhost:5678
- **MCP工具注册中心API**: http://localhost:8000/docs

### 停止系统

```bash
# 停止所有服务
docker-compose down

# 停止并删除所有数据卷
docker-compose down -v
```

## 系统组件详解

### 1. 核心调度Agent

- 负责接收和解析用户请求
- 根据任务类型分配给合适的专业Agent
- 整合和返回结果给用户
- 触发n8n工作流(如果需要)

### 2. 数据分析Agent

- 提供描述性统计分析
- 执行趋势分析和预测
- 进行相关性分析
- 支持调用外部分析工具

### 3. 内容生成Agent

- 生成文章、摘要和社交媒体内容
- 集成OpenAI API进行自然语言生成
- 支持多种格式和风格的内容创作

### 4. MCP工具注册中心

- 提供工具注册、查询、更新和删除API
- 实现工具访问控制和权限管理
- 存储工具元数据和调用信息

### 5. A2A通信总线

- 基于RabbitMQ实现发布/订阅模式
- 支持点对点和广播消息传递
- 确保消息可靠投递

## 安全措施

- 使用HTTPS加密通信(可选配置)
- 实现OAuth 2.1 / JWT认证机制
- 敏感信息存储在环境变量中
- 定期轮换API密钥和密码

## 扩展建议

1. **添加新Agent**：
   - 创建新的Agent目录和Dockerfile
   - 实现A2A通信接口
   - 在docker-compose.yml中添加服务定义

2. **集成新工具**：
   - 在MCP注册中心注册新工具
   - 实现工具调用适配器
   - 更新相关Agent以使用新工具

3. **性能优化**：
   - 为RabbitMQ添加集群配置
   - 优化数据库查询性能
   - 实现Agent自动扩缩容

## 故障排除

### 常见问题

1. **服务无法启动**：
   - 检查Docker和Docker Compose版本
   - 确认端口未被占用
   - 查看容器日志: `docker-compose logs <service_name>`

2. **API调用失败**：
   - 检查.env文件配置是否正确
   - 确认服务间网络连通性
   - 验证认证令牌是否有效

3. **内容生成失败**：
   - 检查OpenAI API密钥是否有效
   - 确认网络连接正常
   - 查看内容生成Agent日志

### 日志查看

```bash
# 查看核心调度Agent日志
docker-compose logs core_scheduler

# 查看数据分析Agent日志
docker-compose logs data_analysis

# 查看内容生成Agent日志
docker-compose logs content_generation

# 查看MCP注册中心日志
docker-compose logs mcp_registry

# 查看RabbitMQ日志
docker-compose logs rabbitmq

# 查看MySQL日志
docker-compose logs mysql
```