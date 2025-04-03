"""
初始化系统配置命令
用于从外部配置文件或环境变量中加载配置
"""
import os
import sys
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models

class Command(BaseCommand):
    help = '从配置文件或环境变量初始化系统配置'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            type=str,
            help='配置文件路径',
        )
        parser.add_argument(
            '--show',
            action='store_true',
            help='显示当前配置',
        )

    def handle(self, *args, **options):
        if options['show']:
            self.show_config()
            return

        config_file = options['config_file']
        if config_file:
            self.load_from_file(config_file)
        else:
            self.load_from_env()

    def show_config(self):
        """显示当前配置"""
        self.stdout.write(self.style.SUCCESS('当前系统配置:'))
        
        # 获取配置项
        config_items = []
        for item in dir(settings):
            if (item.isupper() and not item.startswith('_') and 
                not callable(getattr(settings, item))):
                value = getattr(settings, item)
                
                # 处理特殊类型
                if isinstance(value, (dict, list, tuple)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                elif callable(value):
                    value = "<callable>"
                elif isinstance(value, models.Model):
                    value = f"<{value.__class__.__name__}>"
                
                config_items.append((item, value))
        
        # 按名称排序
        config_items.sort(key=lambda x: x[0])
        
        # 打印
        for name, value in config_items:
            self.stdout.write(f"  {name} = {value}")

    def load_from_file(self, config_file):
        """从文件加载配置"""
        if not os.path.exists(config_file):
            self.stdout.write(self.style.ERROR(f"配置文件不存在: {config_file}"))
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.stdout.write(self.style.SUCCESS(f"从配置文件加载配置: {config_file}"))
            
            # 设置配置
            for key, value in config.items():
                key = key.upper()  # 配置键名统一使用大写
                setattr(settings, key, value)
                self.stdout.write(f"  设置: {key} = {value}")
            
            self.stdout.write(self.style.SUCCESS("配置加载完成"))
            
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"配置文件格式错误: {config_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"加载配置失败: {str(e)}"))

    def load_from_env(self):
        """从环境变量加载配置"""
        # 查找以FREIGHT_开头的环境变量
        prefix = 'FREIGHT_'
        configs = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):]  # 去除前缀
                
                # 尝试解析JSON值
                try:
                    configs[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    # 非JSON，原样保存
                    configs[config_key] = value
        
        if not configs:
            self.stdout.write(self.style.WARNING(f"未找到以 {prefix} 开头的环境变量"))
            return
        
        self.stdout.write(self.style.SUCCESS("从环境变量加载配置:"))
        
        # 设置配置
        for key, value in configs.items():
            key = key.upper()  # 配置键名统一使用大写
            setattr(settings, key, value)
            self.stdout.write(f"  设置: {key} = {value}")
        
        self.stdout.write(self.style.SUCCESS("配置加载完成")) 