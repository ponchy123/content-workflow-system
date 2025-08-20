# A2A+MCP 交互界面

这个前端应用提供了与A2A+MCP多智能体系统交互的用户界面。

## 功能
- 发送数据分析请求
- 发送内容生成请求
- 查看任务进度和结果
- 管理已注册的工具

## 技术栈
- React
- Axios
- Socket.io (用于实时通信)
- Material-UI (UI组件库)

## 安装
1. 确保已安装Node.js和npm
2. 克隆仓库
3. 进入frontend目录
4. 运行 `npm install` 安装依赖
5. 运行 `npm start` 启动开发服务器

## 配置
在.env文件中设置以下环境变量:
- REACT_APP_API_URL: 后端API地址 (默认: http://localhost:8000)
- REACT_APP_WS_URL: WebSocket地址 (默认: ws://localhost:8001)