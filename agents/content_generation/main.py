import pika
import json
import os
import time
from dotenv import load_dotenv
import requests
import openai
from prometheus_client import start_http_server, Counter, Histogram, Gauge

# 加载环境变量
load_dotenv()

class ContentGenerationAgent:
    def __init__(self):
        # 初始化配置
        self.agent_id = 'content_gen_agent'
        self.rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.mcp_registry_url = os.environ.get('MCP_REGISTRY_URL', 'http://localhost:8000')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.metrics_port = int(os.environ.get('METRICS_PORT', '8003'))
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            print("警告: 未设置OPENAI_API_KEY环境变量")
            
        # 初始化指标
        self.initialize_metrics()
        # 启动指标服务器
        start_http_server(self.metrics_port)
        print(f"Prometheus指标服务器启动在端口 {self.metrics_port}")
        
        self.initialize_rabbitmq()
        self.initialize_mcp_tools()

    def initialize_metrics(self):
        # 定义指标
        self.request_counter = Counter('content_gen_requests_total', 'Total number of content generation requests', ['format_type'])
        self.request_latency = Histogram('content_gen_request_latency_seconds', 'Latency of content generation requests', ['format_type'])
        self.active_tasks = Gauge('content_gen_active_tasks', 'Number of active content generation tasks')
        self.rabbitmq_connections = Gauge('content_gen_rabbitmq_connections', 'Number of RabbitMQ connections')
        self.agent_count = Gauge('content_gen_agent_count', 'Number of running Content Generation Agents')
        self.openai_api_calls = Counter('content_gen_openai_api_calls_total', 'Total number of OpenAI API calls')
        self.api_error_counter = Counter('content_gen_api_errors_total', 'Total number of API errors', ['error_type'])
        
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

            if message['type'] == 'content_gen_request':
                # 增加活跃任务计数
                self.active_tasks.inc()
                try:
                    # 处理内容生成请求
                    self.handle_content_request(message)
                finally:
                    # 减少活跃任务计数
                    self.active_tasks.dec()
            else:
                print(f"未知消息类型: {message['type']}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"处理消息时出错: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def handle_content_request(self, message):
        """处理内容生成请求"""
        request_data = message['data']
        topic = request_data['topic']
        format_type = request_data['format']
        length = request_data.get('length', 'medium')
        requirements = request_data.get('requirements', {})

        # 增加请求计数
        self.request_counter.labels(format_type=format_type).inc()

        try:
            # 记录请求处理时间
            with self.request_latency.labels(format_type=format_type).time():
                # 根据格式类型选择不同的生成方法
                if format_type == 'article':
                    result = self.generate_article(topic, length, requirements)
                elif format_type == 'summary':
                    result = self.generate_summary(topic, requirements)
                elif format_type == 'social_media':
                    result = self.generate_social_media_post(topic, length, requirements)
                else:
                    # 如果没有匹配的格式类型，尝试通过MCP调用外部工具
                    result = self.call_external_tool('content_generator', {
                        'topic': topic,
                        'format': format_type,
                        'length': length,
                        'requirements': requirements
                    })

            # 将结果返回给请求方
            self.send_message(
                target_agent=message['source'],
                message_type='content_gen_result',
                data={
                    'request_id': request_data['request_id'],
                    'user_id': request_data['user_id'],
                    'content': result
                }
            )
        except Exception as e:
            # 记录错误
            error_type = type(e).__name__
            self.api_error_counter.labels(error_type=error_type).inc()
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

    def generate_article(self, topic, length, requirements):
        """生成文章"""
        if not self.openai_api_key:
            raise ValueError("未设置OPENAI_API_KEY环境变量")

        # 增加OpenAI API调用计数
        self.openai_api_calls.inc()

        # 根据长度设置大致字数
        word_count = {
            'short': '300-500',
            'medium': '800-1000',
            'long': '1500-2000'
        }.get(length, '800-1000')

        # 构建提示
        prompt = f"写一篇关于{topic}的文章，字数控制在{word_count}字。"
        if requirements:
            prompt += f"额外要求: {', '.join([f'{k}: {v}' for k, v in requirements.items()])}"

        # 调用OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一名专业的内容创作者，擅长撰写各种类型的文章。"},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()

    def generate_summary(self, topic, requirements):
        """生成摘要"""
        if not self.openai_api_key:
            raise ValueError("未设置OPENAI_API_KEY环境变量")

        # 增加OpenAI API调用计数
        self.openai_api_calls.inc()

        # 构建提示
        prompt = f"为{topic}生成一个简洁的摘要。"
        if requirements:
            prompt += f"额外要求: {', '.join([f'{k}: {v}' for k, v in requirements.items()])}"

        # 调用OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一名专业的内容编辑，擅长提炼核心观点。"},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()

    def generate_social_media_post(self, topic, length, requirements):
        """生成社交媒体帖子"""
        if not self.openai_api_key:
            raise ValueError("未设置OPENAI_API_KEY环境变量")

        # 增加OpenAI API调用计数
        self.openai_api_calls.inc()

        # 根据长度设置风格
        style = {
            'short': '简洁、吸引人',
            'medium': '详细、有深度',
            'long': '全面、富有洞察力'
        }.get(length, '详细、有深度')

        # 构建提示
        prompt = f"为社交媒体撰写一篇关于{topic}的帖子，风格要求{style}。"
        if requirements:
            prompt += f"额外要求: {', '.join([f'{k}: {v}' for k, v in requirements.items()])}"

        # 调用OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一名社交媒体营销专家，擅长撰写吸引人的社交媒体内容。"},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()

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
        print(f"内容生成Agent {self.agent_id} 已启动")
        self.channel.basic_consume(
            queue=self.agent_id,
            on_message_callback=self.handle_message
        )
        self.channel.start_consuming()

if __name__ == '__main__':
    agent = ContentGenerationAgent()
    agent.start()