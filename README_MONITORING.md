# A2A+MCP多智能体系统监控指南

## 监控系统概述

本系统使用Prometheus和Grafana构建了完整的监控告警体系，用于监控A2A+MCP多智能体系统的各个组件性能和状态。

## 监控组件

1. **Prometheus**: 负责收集和存储各个组件的指标数据
2. **Grafana**: 负责可视化展示监控数据并设置告警规则

## 访问方式

### Prometheus

- 地址: http://localhost:9090
- 功能: 查看原始指标数据、执行PromQL查询

### Grafana

- 地址: http://localhost:3000
- 初始用户名: admin
- 初始密码: admin
- 功能: 查看仪表盘、配置告警规则

## 监控指标

### 核心调度Agent

- `core_scheduler_requests_total`: 处理的请求总数
- `core_scheduler_request_latency_seconds`: 请求处理延迟
- `core_scheduler_active_tasks`: 活跃任务数量
- `core_scheduler_rabbitmq_connections`: RabbitMQ连接数
- `core_scheduler_agent_count`: Agent实例数量

### 数据分析Agent

- `data_analysis_requests_total`: 数据分析请求总数
- `data_analysis_request_latency_seconds`: 数据分析请求延迟
- `data_analysis_active_tasks`: 活跃数据分析任务数量
- `data_analysis_rabbitmq_connections`: RabbitMQ连接数
- `data_analysis_agent_count`: Agent实例数量

### 内容生成Agent

- `content_gen_requests_total`: 内容生成请求总数
- `content_gen_request_latency_seconds`: 内容生成请求延迟
- `content_gen_active_tasks`: 活跃内容生成任务数量
- `content_gen_rabbitmq_connections`: RabbitMQ连接数
- `content_gen_agent_count`: Agent实例数量
- `content_gen_openai_api_calls_total`: OpenAI API调用总数
- `content_gen_api_errors_total`: API错误总数

### MCP注册中心

- `mcp_tool_count`: 注册的工具数量
- `mcp_requests_total`: 请求总数
- `mcp_request_latency_seconds`: 请求延迟

## 启动说明

1. 确保所有服务都已启动:
```bash
docker-compose up -d
```

2. 访问Prometheus确认指标是否正常采集: http://localhost:9090/targets

3. 访问Grafana并导入仪表盘:
   - 登录Grafana (admin/admin)
   - 导航到"Dashboards" > "Import"
   - 输入仪表盘ID或上传JSON文件

## 告警配置

1. 在Grafana中导航到"Alerting" > "Alert rules"
2. 点击"New alert rule"创建告警规则
3. 配置告警条件、通知渠道等

## 注意事项

1. 首次登录Grafana后请立即修改密码
2. 生产环境中建议为Prometheus和Grafana添加身份验证
3. 根据系统负载调整Prometheus的抓取间隔
4. 定期备份Grafana仪表盘配置