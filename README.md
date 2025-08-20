# A2A+MCP多智能体系统用户交互界面

## 项目概述

本项目为A2A+MCP多智能体系统添加了用户交互界面，使用户能够方便地与系统进行交互，包括发送数据分析请求、内容生成请求、查看任务状态和管理工具。

## 项目结构

```
LB6/
├── agents/                  # 智能体相关代码
│   ├── core_scheduler/      # 核心调度器
│   ├── data_analysis/       # 数据分析智能体
│   └── content_generation/  # 内容生成智能体
├── api_gateway/             # API网关服务
│   ├── .env                 # 环境变量配置
│   ├── package.json         # 依赖配置
│   ├── README.md            # API网关说明
│   ├── server.js            # 主服务文件
│   └── Dockerfile           # Docker配置
├── frontend/                # 前端应用
│   ├── .env                 # 环境变量配置
│   ├── package.json         # 依赖配置
│   ├── README.md            # 前端说明
│   ├── public/              # 公共资源
│   ├── src/                 # 源代码
│   │   ├── index.js         # 入口文件
│   │   ├── App.js           # 主组件
│   │   ├── App.css          # 样式文件
│   │   ├── reportWebVitals.js # 性能监测
│   │   └── pages/           # 页面组件
│   └── Dockerfile           # Docker配置
├── mcp_registry/            # MCP注册中心
├── monitoring/              # 监控相关
├── docker-compose.yml       # Docker组合配置
├── start_frontend.bat       # 前端启动脚本
└── README.md                # 项目说明
```

## 技术栈

### 前端
- React
- Material-UI
- Axios
- Socket.io-client

### 后端
- Node.js
- Express
- Socket.io
- amqplib (RabbitMQ客户端)
- Docker

## 功能特点

1. **用户友好的界面**：提供直观的操作界面，支持数据分析、内容生成、任务状态查看和工具管理。
2. **实时通信**：使用Socket.io实现任务状态的实时更新。
3. **API网关**：作为前端和RabbitMQ之间的桥梁，处理请求转发和响应。
4. **Docker支持**：提供Docker配置，方便部署和启动。

## 启动指南

### 手动启动

1. **启动RabbitMQ**：
   ```
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management
   ```

2. **启动MCP注册中心**：
   ```
   cd mcp_registry
   python main.py
   ```

3. **启动核心调度器**：
   ```
   cd agents/core_scheduler
   python main.py
   ```

4. **启动前端应用和API网关**：
   双击运行 `start_frontend.bat` 脚本，或手动执行：
   ```
   # 启动前端
   cd frontend
   npm install
   npm start

   # 启动API网关
   cd ../api_gateway
   npm install
   npm start
   ```

5. **访问应用**：
   打开浏览器，访问 http://localhost:3000

### Docker启动 (可选)

如果您的网络环境允许连接Docker Hub，可以尝试使用Docker Compose启动整个系统：

```
# 使用国内镜像源
set DOCKER_CONFIG=.docker

docker-compose up --build -d
```

## 环境配置

### 前端环境变量 (.env)
- REACT_APP_API_URL: API网关地址 (默认: http://localhost:8001)
- REACT_APP_WS_URL: WebSocket地址 (默认: ws://localhost:8001)

### API网关环境变量 (.env)
- PORT: 服务器端口 (默认: 8000)
- RABBITMQ_URL: RabbitMQ连接地址 (默认: amqp://guest:guest@localhost:5672/)
- MCP_REGISTRY_URL: MCP注册中心地址 (默认: http://localhost:8000)

## 联系方式

如有问题或建议，请联系项目团队。

本项目提供了一个基于n8n的内容创作与分发工作流自动化方案，支持n8n双向MCP服务（自n8n 1.88.0版本起支持）。方案可以在Docker环境中运行，并通过API集成各种工具。

## 项目结构
```
├── docker-compose.yml       # Docker Compose配置文件
├── content_workflow_example.json  # n8n工作流示例
├── content_creation_workflow.md   # 工作流详细说明
├── content_calendar_template.csv  # 内容日历模板
└── README.md                # 部署和使用指南
```

## 环境要求
- Docker
- Docker Compose
- 互联网连接
- 各个集成工具的API密钥（如Feedly、Notion、OpenAI等）
- n8n 1.90.2或更高版本（如需使用MCP服务）

## 部署步骤

### 1. 克隆或下载项目
将本项目文件保存到本地目录 `d:\lifespace\lifebook\LB6`。

### 2. 配置环境变量
编辑 `docker-compose.yml` 文件，修改以下内容：
- `N8N_BASIC_AUTH_USER` 和 `N8N_BASIC_AUTH_PASSWORD`：设置n8n登录凭证
- 如需使用MySQL数据库，取消相关注释并设置数据库密码

### 3. 启动Docker容器
打开命令行，进入项目目录，运行以下命令：
```bash
cd d:\lifespace\lifebook\LB6
docker-compose up -d
```

### 4. 配置MCP服务（可选）
如需使用n8n双向MCP服务，请确保：
1. n8n版本为1.88.0或更高（docker-compose.yml中已配置最新版本）
2. 在n8n界面中添加MCP Server Trigger节点
3. 按照MCP_integration.md文档中的步骤配置MCP服务

> 注意：n8n MCP服务可以在Docker环境中运行，也可以通过其他方式部署（如直接安装、Kubernetes等）。Docker是推荐的部署方式，但不是唯一方式。

### 5. 访问n8n
在浏览器中访问 `http://localhost:5678`，使用你设置的用户名和密码登录。

## 6. 导入工作流
1. 登录n8n后，点击右上角的"Import Workflow"按钮
2. 选择 `content_workflow_example.json` 文件导入
3. 导入后，根据提示配置所需的凭证

## 工具集成指南

### 1. Feedly集成
- 访问 [Feedly Developer Portal](https://developer.feedly.com/) 获取API密钥
- 在n8n中创建Feedly凭证，填入API密钥
- 修改工作流中的Feedly节点，设置你的Feed ID

### 2. Notion集成
- 访问 [Notion Developer Portal](https://developers.notion.com/) 创建集成
- 获取Notion API密钥和数据库ID
- 在n8n中创建Notion凭证
- 确保你的Notion数据库有对应的字段（标题、摘要、来源链接、标签等）

### 3. OpenAI集成
- 访问 [OpenAI API](https://platform.openai.com/) 获取API密钥
- 在n8n中创建OpenAI凭证
- 根据需要调整AI提示和模型参数

### 4. 其他工具集成
- Discord：创建Discord机器人，获取令牌和频道ID
- 微信：可以通过企业微信API或第三方工具如Server酱集成
- 其他平台：参考对应平台的API文档进行集成

## 工作流说明
导入的工作流包含两个主要部分：
1. **每日灵感收集**：定期从Feedly获取内容，筛选后保存到Notion
2. **每周选题评估**：定期从Notion获取未评估的灵感，使用AI评估优先级并通知到Discord

你可以根据实际需求扩展工作流，添加更多节点如：
- 自动发布到知乎、B站等平台
- 数据统计和分析
- 私域转化跟踪

## 自定义开发
如需根据自身需求修改工作流：
1. 在n8n界面中编辑导入的工作流
2. 添加新节点或修改现有节点的参数
3. 连接节点形成完整的工作流逻辑
4. 测试并部署

## 常见问题

### 1. 如何更新n8n版本？
修改 `docker-compose.yml` 文件中的n8n镜像版本，然后运行：
```bash
docker-compose pull
docker-compose up -d
```

### 2. 工作流执行失败怎么办？
- 检查相关工具的API密钥是否有效
- 检查网络连接
- 查看n8n日志：`docker-compose logs -f n8n`

### 3. 如何备份工作流？
在n8n界面中导出工作流为JSON文件，保存到安全位置。

## 扩展建议
- 集成更多内容平台（如小红书、抖音API）
- 添加自动化的内容创作节点（如使用GPT生成初稿）
- 实现数据可视化报表生成
- 添加团队协作功能

希望这个解决方案能帮助你自动化内容创作工作流，提高效率！如有任何问题，请随时咨询。
