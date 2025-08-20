import pika
import json
import os
import time
from dotenv import load_dotenv
import requests
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# 加载环境变量
load_dotenv()

class CoreSchedulerAgent:
    def __init__(self):
        # 初始化配置
        self.agent_id = 'core_scheduler'
        self.rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.mcp_registry_url = os.environ.get('MCP_REGISTRY_URL', 'http://localhost:8000')
        self.metrics_port = int(os.environ.get('METRICS_PORT', '8001'))
        self.agents = {
            'data_analysis': 'data_analysis_agent',
            'content_generation': 'content_gen_agent'
        }
        self.initialize_metrics()
        self.initialize_rabbitmq()

    def initialize_metrics(self):
        """初始化Prometheus指标"""
        # 启动指标暴露服务器
        start_http_server(self.metrics_port)
        
        # 定义指标
        self.request_counter = Counter('a2a_requests_total', 'Total number of requests processed', ['agent_id', 'request_type'])
        self.request_latency = Histogram('a2a_request_latency_seconds', 'Request processing latency', ['agent_id', 'request_type'])
        self.active_tasks = Gauge('a2a_active_tasks', 'Number of active tasks', ['agent_id'])
        self.rabbitmq_connection_status = Gauge('a2a_rabbitmq_connection_status', 'RabbitMQ connection status', ['agent_id'])
        self.agent_count = Gauge('a2a_agent_count', 'Number of available agents', ['agent_id'])
        
        # 设置可用Agent数量
        self.agent_count.labels(agent_id=self.agent_id).set(len(self.agents))
        
        print(f"Prometheus metrics server started on port {self.metrics_port}")

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
                self.rabbitmq_connection_status.labels(agent_id=self.agent_id).set(1)
                break
            except Exception as e:
                print(f"连接RabbitMQ失败: {e}")
                self.rabbitmq_connection_status.labels(agent_id=self.agent_id).set(0)
                print("5秒后重试...")
                time.sleep(5)

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
        start_time = time.time()
        try:
            message = json.loads(body)
            print(f"接收到来自 {message['source']} 的消息: {message['type']}")
            self.request_counter.labels(agent_id=self.agent_id, request_type=message['type']).inc()
            self.active_tasks.labels(agent_id=self.agent_id).inc()

            if message['type'] == 'user_request':
                # 处理用户请求
                self.handle_user_request(message)
            elif message['type'] == 'data_analysis_result':
                # 处理数据分析结果
                self.handle_data_analysis_result(message)
            elif message['type'] == 'content_gen_result':
                # 处理内容生成结果
                self.handle_content_gen_result(message)
            else:
                print(f"未知消息类型: {message['type']}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"处理消息时出错: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            self.active_tasks.labels(agent_id=self.agent_id).dec()
            self.request_latency.labels(agent_id=self.agent_id, request_type=message.get('type', 'unknown')).observe(time.time() - start_time)

    def handle_user_request(self, message):
        """处理用户请求"""
        request = message['data']
        request_id = request.get('id', str(time.time()))

        if request['type'] == 'analyze_data':
            # 转发给数据分析Agent
            self.send_message(
                target_agent=self.agents['data_analysis'],
                message_type='data_analysis_request',
                data={
                    'request_id': request_id,
                    'user_id': message['source'],
                    'dataset': request['dataset'],
                    'analysis_type': request['analysis_type'],
                    'parameters': request.get('parameters', {})
                }
            )
        elif request['type'] == 'generate_content':
            # 转发给内容生成Agent
            self.send_message(
                target_agent=self.agents['content_generation'],
                message_type='content_gen_request',
                data={
                    'request_id': request_id,
                    'user_id': message['source'],
                    'topic': request['topic'],
                    'format': request['format'],
                    'length': request.get('length', 'medium'),
                    'requirements': request.get('requirements', {})
                }
            )
        elif request['type'] == 'content_workflow':
            # 调用n8n工作流
            self.trigger_n8n_workflow(request, request_id, message['source'])
        else:
            # 未知请求类型
            self.send_message(
                target_agent=message['source'],
                message_type='error',
                data={
                    'request_id': request_id,
                    'error': f'未知的请求类型: {request["type"]}'
                }
            )

    def handle_data_analysis_result(self, message):
        """处理数据分析结果"""
        result = message['data']
        # 将结果返回给用户
        self.send_message(
            target_agent=result['user_id'],
            message_type='analysis_result',
            data={
                'request_id': result['request_id'],
                'analysis_result': result['result']
            }
        )

    def handle_content_gen_result(self, message):
        """处理内容生成结果"""
        result = message['data']
        # 将结果返回给用户
        self.send_message(
            target_agent=result['user_id'],
            message_type='content_result',
            data={
                'request_id': result['request_id'],
                'content': result['content']
            }
        )

    def trigger_n8n_workflow(self, request, request_id, user_id):
        """触发n8n工作流"""
        try:
            # 这里假设n8n的Webhook URL是http://n8n:5678/webhook/trigger
            n8n_url = 'http://n8n:5678/webhook/trigger'
            response = requests.post(
                n8n_url,
                json={
                    'workflow_id': request.get('workflow_id'),
                    'data': request.get('data', {})
                }
            )
            if response.status_code == 200:
                self.send_message(
                    target_agent=user_id,
                    message_type='workflow_triggered',
                    data={
                        'request_id': request_id,
                        'workflow_id': request.get('workflow_id'),
                        'status': 'success'
                    }
                )
            else:
                self.send_message(
                    target_agent=user_id,
                    message_type='error',
                    data={
                        'request_id': request_id,
                        'error': f'触发工作流失败: {response.text}'
                    }
                )
        except Exception as e:
            self.send_message(
                target_agent=user_id,
                message_type='error',
                data={
                    'request_id': request_id,
                    'error': f'触发工作流时出错: {str(e)}'
                }
            )

    def start(self):
        """启动Agent"""
        print(f"核心调度Agent {self.agent_id} 已启动")
        self.channel.basic_consume(
            queue=self.agent_id,
            on_message_callback=self.handle_message
        )
        self.channel.start_consuming()

if __name__ == '__main__':
    agent = CoreSchedulerAgent()
    agent.start()