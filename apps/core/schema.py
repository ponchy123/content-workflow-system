from typing import Any, Dict, List, Optional, Tuple
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes

def preprocessing_filter_spec(endpoints: List[Tuple[str, str, str, Any]]) -> List[Tuple[str, str, str, Any]]:
    """
    预处理API端点，用于过滤和修改Swagger文档中的端点信息
    """
    filtered_endpoints = []
    for path, path_regex, method, callback in endpoints:
        # 跳过admin和debug相关的端点
        if path.startswith('/admin/') or path.startswith('/debug/'):
            continue
            
        # 添加版本信息
        if not path.startswith('/api/v'):
            path = f"/api/v1{path}"
            path_regex = f"/api/v1{path_regex}"
            
        filtered_endpoints.append((path, path_regex, method, callback))
        
    return filtered_endpoints

def postprocessing_filter_spec(result: Dict[str, Any], generator, request, public) -> Dict[str, Any]:
    """
    后处理API文档，用于修改生成的OpenAPI文档
    """
    # 添加全局响应格式
    if 'components' not in result:
        result['components'] = {}
    if 'schemas' not in result['components']:
        result['components']['schemas'] = {}

    # 添加通用响应格式
    result['components']['schemas']['APIResponse'] = {
        'type': 'object',
        'properties': {
            'status': build_basic_type(OpenApiTypes.STR),
            'code': build_basic_type(OpenApiTypes.STR),
            'message': build_basic_type(OpenApiTypes.STR),
            'data': {
                'type': 'object',
                'nullable': True,
            }
        },
        'required': ['status', 'code', 'message']
    }

    # 修改所有响应格式
    for path in result.get('paths', {}).values():
        for operation in path.values():
            if 'responses' in operation:
                for response in operation['responses'].values():
                    if 'content' in response and 'application/json' in response['content']:
                        response['content']['application/json']['schema'] = {
                            '$ref': '#/components/schemas/APIResponse'
                        }

    return result 