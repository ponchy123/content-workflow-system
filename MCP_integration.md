# 内容创作工作流中的MCP（工具与平台集成）

本文档详细列出了内容创作工作流中涉及的主要工具、平台和服务（MCP）及其集成方式。

## 核心集成工具

### 1. n8n
- **类型**：工作流自动化平台
- **作用**：整个工作流的核心引擎，用于连接各种工具和服务。自1.90.2版本起支持MCP（可扩展计算协议）服务，既可以作为MCP客户端调用其他MCP服务，也可以作为MCP服务端提供服务。
- **集成方式**：通过Docker部署，使用其节点式可视化界面构建工作流。支持双向MCP和本地（stdio）MCP。
- **配置文件**：<mcfile name="docker-compose.yml" path="d:\lifespace\lifebook\LB6\docker-compose.yml"></mcfile>

#### n8n MCP服务配置步骤
1. **添加MCP Server Trigger节点**：打开n8n节点面板，找到"MCP Server Trigger"节点并添加，这是服务入口点。添加后会生成一个预生成的SSE访问地址，此URL是外部系统调用服务的通道。若为演示可暂时禁用身份验证，但生产环境中务必启用安全措施。
2. **构建服务能力矩阵**：可在"MCP Server Trigger"后连接任意数量的工具节点来扩展MCP服务能力。有两种扩展方式，一是通过"Call n8n Workflow Tool"节点引入已验证的自动化流程；二是将单个功能节点（如Gmail、Slack等）直接连接到MCP服务器。
3. **设置子工作流**：若复用现有工作流，被调用的子工作流必须以"Execute Sub-workflow"触发器开始。在"MCP Server Trigger"的"Tools"里添加"Call n8n Workflow Tool"节点，选择要调用的目标工作流，并设置参数映射，确保MCP请求能正确传递给子工作流。
4. **发布与激活服务**：保存工作流后，点击"Active"按钮将其激活为绿色状态，此时服务端准备好接收外部请求。复制"MCP Server Trigger"节点的"Production URL"，这就是服务访问端点。
5. **配置客户端连接**：在n8n内部创建MCP客户端，如构建一个AI Agent，通过"MCP Client Tool"连接刚才创建的服务器。双击打开"MCP Client Tool"，将其中的"SSE Endpoint"配置为之前复制的"Production URL"。同时，需精心设计AI Agent的系统提示词，让它了解可用的工具能力和使用场景，并可设置"Max Iterations"参数为10，确保AI Agent有足够迭代次数完成复杂任务。

### 2. Feedly
- **类型**：RSS阅读器
- **作用**：收集行业资讯和内容灵感
- **集成方式**：通过Feedly API获取内容流
- **认证**：API密钥
- **在工作流中的使用**：每日自动获取指定类别的最新内容

### 3. Notion
- **类型**：笔记和知识库管理工具
- **作用**：存储灵感收集和选题评估结果
- **集成方式**：通过Notion API进行数据读写
- **认证**：API密钥
- **在工作流中的使用**：
  - 保存筛选后的灵感
  - 存储选题评估结果
  - 作为内容日历的后端存储

### 4. OpenAI
- **类型**：AI服务
- **作用**：提供AI辅助选题评估和内容创作
- **集成方式**：通过OpenAI API调用GPT模型
- **认证**：API密钥
- **在工作流中的使用**：
  - 评估选题的时效性、深度潜力和转化潜力
  - 生成内容初稿（可扩展）
  - 优化标题和摘要（可扩展）

### 5. Discord
- **类型**：通讯平台
- **作用**：通知选题评估结果和工作流状态
- **集成方式**：通过Discord Bot API发送消息
- **认证**：Bot令牌
- **在工作流中的使用**：每周发送选题评估结果通知

## 扩展集成工具（根据需求可添加）

### 6. 微信
- **类型**：社交媒体平台
- **作用**：私域流量运营和用户沟通
- **集成方式**：
  - 企业微信API
  - 第三方工具（如Server酱）
- **潜在使用场景**：
  - 推送内容更新通知
  - 收集用户反馈
  - 私域转化跟踪

### 7. 内容发布平台
- **知乎**：通过知乎API自动发布文章
- **B站**：通过B站API自动发布视频
- **小红书**：通过小红书API自动发布笔记
- **抖音**：通过抖音API自动发布短视频
- **微信公众号**：通过微信公众号API自动发布文章

### 8. 数据分析工具
- **新榜/灰豚数据**：获取内容表现数据
- **Google Analytics**：网站流量分析
- **Excel/Google Sheets**：数据汇总和报表生成

### 9. 存储服务
- **MySQL**：可选的数据库存储（在docker-compose.yml中已提供配置）
- **云存储**：如AWS S3、阿里云OSS等，用于存储媒体文件

## 集成配置指南

### 通用配置步骤
1. 在对应平台的开发者门户注册账号并创建应用
2. 获取API密钥或认证凭证
3. 在n8n中创建对应的凭证
4. 配置工作流节点参数
5. 测试连接和数据传输

### 具体平台配置链接
- Feedly Developer Portal: <mcurl name="Feedly开发者门户" url="https://developer.feedly.com/"></mcurl>
- Notion Developer Portal: <mcurl name="Notion开发者门户" url="https://developers.notion.com/"></mcurl>
- OpenAI API: <mcurl name="OpenAI API" url="https://platform.openai.com/"></mcurl>
- Discord Developer Portal: <mcurl name="Discord开发者门户" url="https://discord.com/developers/"></mcurl>
- 知乎API: <mcurl name="知乎API" url="https://open.zhihu.com/"></mcurl>
- B站API: <mcurl name="B站API" url="https://open.bilibili.com/"></mcurl>

## 工作流集成架构图
```mermaid
flowchart TD
    A[n8n工作流引擎
(MCP服务端/客户端)] --> B[Feedly]
    A --> C[Notion]
    A --> D[OpenAI]
    A --> E[Discord]
    A --> F[可选: 微信集成]
    A --> G[可选: 内容发布平台]
    A --> H[可选: 数据分析工具]
    A <--> I[其他MCP服务]
    B --> |内容获取| A
    C --> |数据存储| A
    D --> |AI辅助| A
    E --> |通知| A
    F --> |私域运营| A
    G --> |内容发布| A
    H --> |数据反馈| A
    I --> |双向MCP通信| A
```

通过n8n的MCP服务，工作流可以实现更灵活的集成：
1. **作为MCP服务端**：可以将内容创作工作流的能力封装为服务，供其他系统调用
2. **作为MCP客户端**：可以调用外部的MCP服务，扩展自身功能
3. **双向通信**：支持与其他MCP服务进行双向数据交换和功能调用

## 安全考虑
- 所有API密钥和凭证应存储在n8n的密钥管理系统中，避免硬编码
- 定期轮换API密钥以提高安全性
- 限制API访问权限，遵循最小权限原则
- 对敏感数据进行加密处理
- 设置适当的访问控制和身份验证机制
- 监控API调用和工作流执行日志，及时发现异常活动
- 确保所有集成服务的API版本保持最新，以获取安全更新

### MCP服务特别安全考虑
- **启用身份验证**：在生产环境中务必为MCP Server Trigger启用身份验证，避免未授权访问
- **限制IP访问**：配置防火墙规则，只允许可信IP地址访问MCP服务端点
- **设置请求速率限制**：防止恶意请求导致服务过载
- **验证输入数据**：对MCP请求中的输入数据进行严格验证，防止注入攻击
- **加密通信**：确保MCP服务通信使用HTTPS，保护数据传输安全
- **监控MCP连接**：密切关注MCP服务的连接状态和数据传输，及时发现异常活动

通过这些MCP的集成，您的内容创作工作流可以实现从灵感收集、选题评估到内容发布和数据复盘的全流程自动化，显著提高工作效率。