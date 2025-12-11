"""配置Schema生成器

从配置文件生成JSON Schema，用于验证节点配置。
"""

from typing import Dict, Any, List, Optional
from src.interfaces.dependency_injection import get_logger
from pathlib import Path

# TODO: 修复 node_config_loader 模块缺失问题
# from .node_config_loader import get_node_config_loader

logger = get_logger(__name__)


class SchemaGenerator:
    """配置Schema生成器"""
    
    def __init__(self):
        """初始化Schema生成器"""
        # TODO: 修复 node_config_loader 模块缺失问题
        # self._config_loader = get_node_config_loader()
        self._config_loader = None
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
    
    def generate_schema_from_config(self, node_type: str) -> Dict[str, Any]:
        """从配置文件生成Schema
        
        Args:
            node_type: 节点类型
            
        Returns:
            Dict[str, Any]: JSON Schema
        """
        # 检查缓存
        if node_type in self._schema_cache:
            return self._schema_cache[node_type]
        
        # 获取节点配置
        if self._config_loader is None:
            logger.warning(f"配置加载器不可用，使用默认Schema")
            return self._get_default_schema()
            
        config = self._config_loader.get_config(node_type)
        if not config:
            logger.warning(f"未找到节点 {node_type} 的配置，使用默认Schema")
            return self._get_default_schema()
        
        # 生成Schema
        schema = self._generate_schema_from_dict(config, node_type)
        
        # 缓存Schema
        self._schema_cache[node_type] = schema
        
        return schema
    
    def _generate_schema_from_dict(self, config: Dict[str, Any], node_type: str) -> Dict[str, Any]:
        """从字典生成Schema
        
        Args:
            config: 配置字典
            node_type: 节点类型
            
        Returns:
            Dict[str, Any]: JSON Schema
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # 添加描述
        schema["description"] = f"{node_type} 节点配置Schema"
        
        # 处理每个配置项
        for key, value in config.items():
            if key == "description":
                continue  # 跳过描述字段
            
            property_schema = self._infer_property_schema(key, value)
            schema["properties"][key] = property_schema
            
            # 判断是否为必需字段
            if self._is_required_field(key, value, node_type):
                schema["required"].append(key)
        
        return schema
    
    def _infer_property_schema(self, key: str, value: Any) -> Dict[str, Any]:
        """推断属性Schema
        
        Args:
            key: 属性键
            value: 属性值
            
        Returns:
            Dict[str, Any]: 属性Schema
        """
        if isinstance(value, bool):
            return {
                "type": "boolean",
                "description": f"{key} 配置项"
            }
        elif isinstance(value, int):
            return {
                "type": "integer",
                "description": f"{key} 配置项"
            }
        elif isinstance(value, float):
            return {
                "type": "number",
                "description": f"{key} 配置项"
            }
        elif isinstance(value, str):
            return {
                "type": "string",
                "description": f"{key} 配置项"
            }
        elif isinstance(value, list):
            if value:
                # 推断数组元素类型
                item_schema = self._infer_property_schema(f"{key}_item", value[0])
                return {
                    "type": "array",
                    "items": item_schema,
                    "description": f"{key} 配置项"
                }
            else:
                return {
                    "type": "array",
                    "description": f"{key} 配置项"
                }
        elif isinstance(value, dict):
            properties = {}
            for sub_key, sub_value in value.items():
                properties[sub_key] = self._infer_property_schema(sub_key, sub_value)
            
            return {
                "type": "object",
                "properties": properties,
                "description": f"{key} 配置项"
            }
        else:
            return {
                "type": "any",
                "description": f"{key} 配置项"
            }
    
    def _is_required_field(self, key: str, value: Any, node_type: str) -> bool:
        """判断字段是否为必需
        
        Args:
            key: 字段键
            value: 字段值
            node_type: 节点类型
            
        Returns:
            bool: 是否为必需字段
        """
        # 基于节点类型的特殊规则
        if node_type == "tool_node":
            return key == "tool_manager"
        elif node_type == "llm_node":
            # LLM节点没有必需字段，所有参数都有默认值
            return False
        elif node_type in ["start_node", "end_node"]:
            # START和END节点没有必需字段
            return False
        elif node_type == "condition_node":
            return key == "conditions"
        elif node_type == "wait_node":
            return False  # 等待节点所有参数都有默认值
        
        # 默认规则：如果值为None或空，则不是必需字段
        return value is not None and value != ""
    
    def _get_default_schema(self) -> Dict[str, Any]:
        """获取默认Schema
        
        Returns:
            Dict[str, Any]: 默认Schema
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
            "description": "默认节点配置Schema"
        }
    
    def clear_cache(self) -> None:
        """清除Schema缓存"""
        self._schema_cache.clear()
    
    def get_cached_schemas(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存的Schema
        
        Returns:
            Dict[str, Dict[str, Any]]: 缓存的Schema字典
        """
        return self._schema_cache.copy()


# 全局Schema生成器实例
_schema_generator: Optional[SchemaGenerator] = None


def get_schema_generator() -> SchemaGenerator:
    """获取全局Schema生成器实例
    
    Returns:
        SchemaGenerator: Schema生成器实例
    """
    global _schema_generator
    if _schema_generator is None:
        _schema_generator = SchemaGenerator()
    return _schema_generator


def generate_node_schema(node_type: str) -> Dict[str, Any]:
    """生成节点Schema
    
    Args:
        node_type: 节点类型
        
    Returns:
        Dict[str, Any]: 节点Schema
    """
    generator = get_schema_generator()
    return generator.generate_schema_from_config(node_type)