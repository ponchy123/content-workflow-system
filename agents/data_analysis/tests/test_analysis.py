import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from main import DataAnalysisAgent
import json
import time

class TestDataAnalysisAgent(unittest.TestCase):
    def setUp(self):
        # 保存原始环境变量
        self.original_env = os.environ.copy()
        # 设置测试环境变量
        os.environ['RABBITMQ_URL'] = 'amqp://guest:guest@localhost:5672/'
        os.environ['MCP_REGISTRY_URL'] = 'http://localhost:8000'
        os.environ['METRICS_PORT'] = '8002'

    def tearDown(self):
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('main.pika.BlockingConnection')
    @patch('main.requests.get')
    @patch('main.start_http_server')
    def test_initialization(self, mock_start_http, mock_requests_get, mock_pika):
        # 模拟pika连接
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        # 模拟MCP工具注册响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'name': 'test_tool', 'endpoint': 'http://test.com'}]
        mock_requests_get.return_value = mock_response

        # 创建agent实例
        agent = DataAnalysisAgent()

        # 验证初始化
        self.assertEqual(agent.agent_id, 'data_analysis_agent')
        self.assertEqual(agent.rabbitmq_url, 'amqp://guest:guest@localhost:5672/')
        self.assertEqual(agent.mcp_registry_url, 'http://localhost:8000')
        self.assertEqual(agent.metrics_port, 8002)

        # 验证指标服务器启动
        mock_start_http.assert_called_once_with(8002)

        # 验证RabbitMQ连接
        mock_pika.assert_called_once()
        mock_channel.queue_declare.assert_called_once_with(queue='data_analysis_agent')
        mock_channel.exchange_declare.assert_called_once_with(exchange='a2a_bus', exchange_type='topic')
        mock_channel.queue_bind.assert_called_once_with(
            exchange='a2a_bus', queue='data_analysis_agent', routing_key='agent.data_analysis_agent'
        )

        # 验证MCP工具加载
        mock_requests_get.assert_called_once_with('http://localhost:8000/tools')
        self.assertEqual(agent.tools, {'test_tool': {'name': 'test_tool', 'endpoint': 'http://test.com'}})

    def test_perform_summary_statistics(self):
        # 创建测试数据
        dataset = [
            {'value1': 1, 'value2': 2}, 
            {'value1': 2, 'value2': 4}, 
            {'value1': 3, 'value2': 6}
        ]

        # 创建agent实例（使用mock避免初始化外部依赖）
        with patch('main.DataAnalysisAgent.initialize_rabbitmq'), \
             patch('main.DataAnalysisAgent.initialize_mcp_tools'), \
             patch('main.start_http_server'):
            agent = DataAnalysisAgent()

        # 执行测试
        result = agent.perform_summary_statistics(dataset)

        # 验证结果
        self.assertEqual(result['mean'], {'value1': 2.0, 'value2': 4.0})
        self.assertEqual(result['median'], {'value1': 2.0, 'value2': 4.0})
        self.assertEqual(result['std'], {'value1': 1.0, 'value2': 2.0})
        self.assertEqual(result['min'], {'value1': 1, 'value2': 2})
        self.assertEqual(result['max'], {'value1': 3, 'value2': 6})
        self.assertEqual(result['count'], {'value1': 3, 'value2': 3})

    def test_perform_trend_analysis(self):
        # 创建测试数据
        dataset = [
            {'date': '2023-01-01', 'value': 10}, 
            {'date': '2023-01-02', 'value': 20}, 
            {'date': '2023-01-03', 'value': 30}, 
            {'date': '2023-01-04', 'value': 25}, 
            {'date': '2023-01-05', 'value': 40}
        ]

        # 创建agent实例（使用mock避免初始化外部依赖）
        with patch('main.DataAnalysisAgent.initialize_rabbitmq'), \
             patch('main.DataAnalysisAgent.initialize_mcp_tools'), \
             patch('main.start_http_server'):
            agent = DataAnalysisAgent()

        # 执行测试
        result = agent.perform_trend_analysis(dataset, {'window': 2})

        # 验证结果
        self.assertEqual(len(result['original_data']), 5)
        self.assertEqual(len(result['moving_average']), 4)
        self.assertEqual(result['trend'], 'up')

        # 测试缺少必要列的情况
        with self.assertRaises(ValueError):
            agent.perform_trend_analysis(dataset, {'date_column': 'non_existent', 'value_column': 'value'})

    def test_perform_correlation_analysis(self):
        # 创建测试数据
        dataset = [
            {'x': 1, 'y': 2, 'z': 3}, 
            {'x': 2, 'y': 4, 'z': 6}, 
            {'x': 3, 'y': 6, 'z': 9}, 
            {'x': 4, 'y': 8, 'z': 12}
        ]

        # 创建agent实例（使用mock避免初始化外部依赖）
        with patch('main.DataAnalysisAgent.initialize_rabbitmq'), \
             patch('main.DataAnalysisAgent.initialize_mcp_tools'), \
             patch('main.start_http_server'):
            agent = DataAnalysisAgent()

        # 执行测试
        result = agent.perform_correlation_analysis(dataset, {'columns': ['x', 'y', 'z'], 'threshold': 0.9})

        # 验证结果
        self.assertEqual(result['correlation_matrix']['x']['y'], 1.0)
        self.assertEqual(result['correlation_matrix']['x']['z'], 1.0)
        self.assertEqual(result['correlation_matrix']['y']['z'], 1.0)
        self.assertEqual(len(result['strongest_correlations']), 3)

        # 测试不存在的列
        with self.assertRaises(ValueError):
            agent.perform_correlation_analysis(dataset, {'columns': ['non_existent']})

    @patch('main.requests.post')
    def test_call_external_tool(self, mock_requests_post):
        # 创建agent实例（使用mock避免初始化外部依赖）
        with patch('main.DataAnalysisAgent.initialize_rabbitmq'), \
             patch('main.DataAnalysisAgent.initialize_mcp_tools') as mock_initialize_tools, \
             patch('main.start_http_server'):
            agent = DataAnalysisAgent()
            # 手动设置工具
            agent.tools = {'test_tool': {'name': 'test_tool', 'endpoint': 'http://test.com'}}

        # 模拟工具响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'test_result'}
        mock_requests_post.return_value = mock_response

        # 执行测试
        result = agent.call_external_tool('test_tool', {'param': 'value'})

        # 验证结果
        self.assertEqual(result, {'result': 'test_result'})
        mock_requests_post.assert_called_once_with('http://test.com', json={'param': 'value'})

        # 测试工具不存在的情况
        with self.assertRaises(ValueError):
            agent.call_external_tool('non_existent_tool', {})

    @patch('main.DataAnalysisAgent.send_message')
    def test_handle_analysis_request(self, mock_send_message):
        # 创建测试数据
        message = {
            'source': 'test_source',
            'data': {
                'request_id': 'test_id',
                'user_id': 'test_user',
                'analysis_type': 'summary_statistics',
                'dataset': [{'value1': 1, 'value2': 2}]
            }
        }

        # 创建agent实例（使用mock避免初始化外部依赖）
        with patch('main.DataAnalysisAgent.initialize_rabbitmq'), \
             patch('main.DataAnalysisAgent.initialize_mcp_tools'), \
             patch('main.start_http_server'):
            agent = DataAnalysisAgent()

        # 执行测试
        agent.handle_analysis_request(message)

        # 验证结果
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args[1]
        self.assertEqual(call_args['target_agent'], 'test_source')
        self.assertEqual(call_args['message_type'], 'data_analysis_result')
        self.assertEqual(call_args['data']['request_id'], 'test_id')
        self.assertEqual(call_args['data']['user_id'], 'test_user')
        self.assertIn('result', call_args['data'])

if __name__ == '__main__':
    unittest.main()