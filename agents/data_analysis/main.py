import pika
import json
import os
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import requests
from prometheus_client import start_http_server, Counter, Histogram, Gauge

# 加载环境变量
load_dotenv()

class DataAnalysisAgent:
    def __init__(self):
        # 初始化配置
        self.agent_id = 'data_analysis_agent'
        self.rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.mcp_registry_url = os.environ.get('MCP_REGISTRY_URL', 'http://localhost:8000')
        self.metrics_port = int(os.environ.get('METRICS_PORT', '8002'))
        
        # 初始化指标
        self.initialize_metrics()
        # 启动指标服务器
        start_http_server(self.metrics_port)
        print(f"Prometheus指标服务器启动在端口 {self.metrics_port}")
        
        self.initialize_rabbitmq()
        self.initialize_mcp_tools()

    def initialize_metrics(self):
        # 定义指标
        self.request_counter = Counter('data_analysis_requests_total', 'Total number of data analysis requests', ['analysis_type'])
        self.request_latency = Histogram('data_analysis_request_latency_seconds', 'Latency of data analysis requests', ['analysis_type'])
        self.active_tasks = Gauge('data_analysis_active_tasks', 'Number of active data analysis tasks')
        self.rabbitmq_connections = Gauge('data_analysis_rabbitmq_connections', 'Number of RabbitMQ connections')
        self.agent_count = Gauge('data_analysis_agent_count', 'Number of running Data Analysis Agents')
        
        # 设置Agent计数为1
        self.agent_count.set(1)
        # 初始化RabbitMQ连接计数为0
        self.rabbitmq_connections.set(0)

    def initialize_rabbitmq(self):
        """初始化RabbitMQ连接"""
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
                self.channel = self.connection.channel()
                # 声明专用队列
                self.channel.queue_declare(queue=self.agent_id)
                # 绑定到广播交换机
                self.channel.exchange_declare(exchange='a2a_bus', exchange_type='topic')
                self.channel.queue_bind(exchange='a2a_bus', queue=self.agent_id, routing_key=f'agent.{self.agent_id}')
                print(f"成功连接到RabbitMQ: {self.rabbitmq_url}")
                # 更新RabbitMQ连接计数
                self.rabbitmq_connections.set(1)
                break
            except Exception as e:
                print(f"连接RabbitMQ失败: {e}")
                print("5秒后重试...")
                time.sleep(5)

    def initialize_mcp_tools(self):
        """初始化MCP工具"""
        self.tools = {}
        try:
            # 从MCP工具注册中心获取可用工具
            response = requests.get(f'{self.mcp_registry_url}/tools')
            if response.status_code == 200:
                tools_data = response.json()
                for tool in tools_data:
                    self.tools[tool['name']] = tool
                print(f"成功加载 {len(self.tools)} 个MCP工具")
            else:
                print(f"获取MCP工具失败: {response.status_code}")
        except Exception as e:
            print(f"初始化MCP工具时出错: {e}")

    def send_message(self, target_agent, message_type, data):
        """发送消息到目标Agent"""
        message = {
            'source': self.agent_id,
            'target': target_agent,
            'type': message_type,
            'data': data,
            'timestamp': time.time()
        }
        self.channel.basic_publish(
            exchange='a2a_bus',
            routing_key=f'agent.{target_agent}',
            body=json.dumps(message)
        )
        print(f"发送消息到 {target_agent}: {message_type}")

    def handle_message(self, ch, method, properties, body):
        """处理接收到的消息"""
        try:
            message = json.loads(body)
            print(f"接收到来自 {message['source']} 的消息: {message['type']}")

            if message['type'] == 'data_analysis_request':
                # 增加活跃任务计数
                self.active_tasks.inc()
                try:
                    # 处理数据分析请求
                    self.handle_analysis_request(message)
                finally:
                    # 减少活跃任务计数
                    self.active_tasks.dec()
            else:
                print(f"未知消息类型: {message['type']}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"处理消息时出错: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def handle_analysis_request(self, message):
        """处理数据分析请求"""
        request_data = message['data']
        analysis_type = request_data['analysis_type']
        dataset = request_data['dataset']
        parameters = request_data.get('parameters', {})

        # 增加请求计数
        self.request_counter.labels(analysis_type=analysis_type).inc()

        try:
            # 记录请求处理时间
            with self.request_latency.labels(analysis_type=analysis_type).time():
                # 根据分析类型选择不同的分析方法
                if analysis_type == 'summary_statistics':
                    result = self.perform_summary_statistics(dataset)
                elif analysis_type == 'trend_analysis':
                    result = self.perform_trend_analysis(dataset, parameters)
                elif analysis_type == 'correlation':
                    result = self.perform_correlation_analysis(dataset, parameters)
                else:
                    # 如果没有匹配的分析类型，尝试通过MCP调用外部工具
                    result = self.call_external_tool(analysis_type, {'dataset': dataset, **parameters})

            # 将结果返回给请求方
            self.send_message(
                target_agent=message['source'],
                message_type='data_analysis_result',
                data={
                    'request_id': request_data['request_id'],
                    'user_id': request_data['user_id'],
                    'result': result
                }
            )
        except Exception as e:
            # 发送错误消息
            self.send_message(
                target_agent=message['source'],
                message_type='error',
                data={
                    'request_id': request_data['request_id'],
                    'user_id': request_data['user_id'],
                    'error': str(e)
                }
            )

    def perform_summary_statistics(self, dataset):
        """执行描述性统计分析"""
        df = pd.DataFrame(dataset)
        result = {
            'mean': df.mean().to_dict(),
            'median': df.median().to_dict(),
            'std': df.std().to_dict(),
            'min': df.min().to_dict(),
            'max': df.max().to_dict(),
            'count': df.count().to_dict()
        }
        return result

    def perform_trend_analysis(self, dataset, parameters):
        """执行趋势分析"""
        df = pd.DataFrame(dataset)
        date_column = parameters.get('date_column', 'date')
        value_column = parameters.get('value_column', 'value')

        if date_column not in df.columns or value_column not in df.columns:
            raise ValueError(f"缺少必要的列: {date_column} 或 {value_column}")

        # 确保日期列是datetime类型
        df[date_column] = pd.to_datetime(df[date_column])
        # 按日期排序
        df = df.sort_values(by=date_column)
        # 计算移动平均值
        window = parameters.get('window', 7)
        df['moving_average'] = df[value_column].rolling(window=window).mean()

        result = {
            'original_data': df[[date_column, value_column]].to_dict('records'),
            'moving_average': df[[date_column, 'moving_average']].dropna().to_dict('records'),
            'trend': 'up' if df[value_column].iloc[-1] > df[value_column].iloc[0] else 'down'
        }
        return result

    def perform_correlation_analysis(self, dataset, parameters):
        """执行相关性分析"""
        df = pd.DataFrame(dataset)
        columns = parameters.get('columns', df.columns.tolist())

        # 确保所有列都存在
        for col in columns:
            if col not in df.columns:
                raise ValueError(f"列 {col} 不存在于数据集中")

        # 计算相关性矩阵
        corr_matrix = df[columns].corr().to_dict()

        result = {
            'correlation_matrix': corr_matrix,
            'strongest_correlations': self.find_strongest_correlations(corr_matrix, parameters.get('threshold', 0.7))
        }
        return result

    def find_strongest_correlations(self, corr_matrix, threshold):
        """找出最强的相关性"""
        strongest = []
        for col1 in corr_matrix:
            for col2 in corr_matrix[col1]:
                if col1 < col2:  # 避免重复
                    corr = corr_matrix[col1][col2]
                    if abs(corr) >= threshold:
                        strongest.append({
                            'variables': [col1, col2],
                            'correlation': corr
                        })
        # 按相关性强度排序
        strongest.sort(key=lambda x: abs(x['correlation']), reverse=True)
        return strongest

    def call_external_tool(self, tool_name, params):
        """通过MCP调用外部工具"""
        if tool_name not in self.tools:
            # 尝试刷新工具列表
            self.initialize_mcp_tools()
            if tool_name not in self.tools:
                raise ValueError(f"工具 {tool_name} 不存在于MCP注册中心")

        tool = self.tools[tool_name]
        try:
            # 调用工具API
            response = requests.post(
                tool['endpoint'],
                json=params
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"调用工具 {tool_name} 失败: {response.text}")
        except Exception as e:
            raise ValueError(f"调用工具 {tool_name} 时出错: {str(e)}")

    def start(self):
        """启动Agent"""
        print(f"数据分析Agent {self.agent_id} 已启动")
        self.channel.basic_consume(
            queue=self.agent_id,
            on_message_callback=self.handle_message
        )
        self.channel.start_consuming()

if __name__ == '__main__':
    agent = DataAnalysisAgent()
    agent.start()