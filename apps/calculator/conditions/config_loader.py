import os
import json
import sys
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ConditionConfigLoader:
    """条件规则配置加载器"""
    
    @staticmethod
    def load_config():
        """加载条件规则配置"""
        try:
            # 尝试从配置文件加载
            config_path = os.path.join(settings.BASE_DIR, 'config', 'condition_rules.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"已加载条件规则配置: {config_path}", file=sys.stdout)
                    return config
            else:
                # 如果配置文件不存在，使用默认配置
                default_config = ConditionConfigLoader._get_default_config()
                
                # 创建配置目录和文件
                try:
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, ensure_ascii=False, indent=4)
                    print(f"已创建默认条件规则配置文件: {config_path}", file=sys.stdout)
                except Exception as write_error:
                    print(f"创建默认配置文件失败: {str(write_error)}", file=sys.stdout)
                
                return default_config
        except Exception as e:
            logger.error(f"加载条件配置失败: {str(e)}")
            # 使用空配置
            return {}
    
    @staticmethod
    def _get_default_config():
        """获取默认配置"""
        return {
            "unauthorized_package_conditions": [
                {
                    "type": "LENGTH_GIRTH",
                    "operator": ">",
                    "value": 165,
                    "description": "长+周长超过165英寸"
                },
                {
                    "type": "LENGTH",
                    "operator": ">",
                    "value": 108,
                    "description": "最长边超过108英寸"
                },
                {
                    "type": "WEIGHT",
                    "operator": ">",
                    "value": 150,
                    "description": "重量超过150磅"
                }
            ],
            "thresholds": {
                "length_girth": "165",
                "length": "108",
                "weight": "150"
            },
            # 按产品ID分类的特定条件
            "product_conditions": {
                # FEDEX GROUND的特定配置
                "FEDGND": [
                    {
                        "type": "LENGTH_GIRTH",
                        "operator": ">",
                        "value": 165,
                        "description": "FEDEX GROUND长+周长超过165英寸"
                    }
                ],
                # UPS GROUND的特定配置
                "UPSGND": [
                    {
                        "type": "LENGTH_GIRTH",
                        "operator": ">",
                        "value": 165,
                        "description": "UPS GROUND长+周长超过165英寸"
                    }
                ]
            }
        }
    
    @staticmethod
    def get_product_conditions(config, product_id):
        """获取指定产品的条件规则"""
        if not config or not product_id:
            return []
            
        # 尝试获取产品特定条件
        product_conditions = config.get('product_conditions', {}).get(str(product_id), [])
        return product_conditions
    
    @staticmethod
    def get_unauthorized_conditions(config):
        """获取不可发包裹条件"""
        if not config:
            return []
            
        return config.get('unauthorized_package_conditions', []) 