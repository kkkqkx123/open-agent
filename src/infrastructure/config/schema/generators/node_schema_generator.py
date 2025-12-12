"""节点Schema生成器

提供从节点配置生成JSON Schema的功能。
"""

from typing import Dict, Any, Optional
import logging

from ...impl.base_impl import BaseSchemaGenerator
from src.interfaces.config.impl import IConfigImpl

logger = logging.getLogger(__name__)


class NodeSchemaGenerator(BaseSchemaGenerator):
    """节点Schema生成器
    
    专门用于从节点配置数据生成JSON Schema。
    """
    
    def __init__(self, config_provider: Optional['IConfigImpl'] = None):
        """初始化节点Schema生成器
        
        Args:
            config_provider: 配置实现
        """
        super().__init__("node", config_provider)
        
        # 节点特定的字段定义
        self._node_fields = {
            "id": {"type": "string", "description": "节点ID"},
            "type": {"type": "string", "description": "节点类型"},
            "name": {"type": "string", "description": "节点名称"},
            "description": {"type": "string", "description": "节点描述"},
            "inputs": {"type": "array", "description": "输入定义"},
            "outputs": {"type": "array", "description": "输出定义"},
            "config": {"type": "object", "description": "节点配置"},
            "position": {"type": "object", "description": "节点位置"},
            "style": {"type": "object", "description": "节点样式"},
            "metadata": {"type": "object", "description": "元数据"}
        }
        
        # 必需字段
        self._required_fields = ["id", "type"]
        
        logger.debug("初始化节点Schema生成器")
    
    def generate_schema_from_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """从节点配置生成Schema
        
        Args:
            config_data: 节点配置数据
            
        Returns:
            Dict[str, Any]: JSON Schema
        """
        # 使用统一的缓存键生成
        from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator
        cache_key = f"schema:node:{DefaultCacheKeyGenerator.generate_params_key(config_data)}"
        
        # 检查缓存
        cached_schema = self.cache_manager.get(cache_key)
        if cached_schema:
            logger.debug(f"从缓存获取节点Schema: {cache_key}")
            return cached_schema
        
        logger.debug("开始生成节点Schema")
        
        # 生成Schema
        schema = self._generate_node_schema(config_data)
        
        # 缓存Schema
        self.cache_manager.set(cache_key, schema)
        
        logger.debug(f"节点Schema生成完成: {cache_key}")
        return schema
    
    def _generate_node_schema(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成节点Schema
        
        Args:
            config_data: 配置数据
            
        Returns:
            Dict[str, Any]: JSON Schema
        """
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
        
        # 处理每个配置项
        for key, value in config_data.items():
            if key == "description":  # 描述字段通常不需要在Schema中体现
                continue
            
            property_schema = self._infer_property_schema(key, value)
            schema["properties"][key] = property_schema
            
            # 判断字段是否必需
            if self._is_required_field(key, value):
                schema["required"].append(key)
        
        # 确保必需字段存在
        for required_field in self._required_fields:
            if required_field not in schema["required"]:
                schema["required"].append(required_field)
        
        # 添加节点特定的属性定义
        self._add_node_specific_properties(schema)
        
        return schema
    
    def _infer_property_schema(self, key: str, value: Any) -> Dict[str, Any]:
        """推断属性Schema
        
        Args:
            key: 属性名
            value: 属性值
            
        Returns:
            Dict[str, Any]: 属性Schema
        """
        # 如果有预定义的节点字段，使用预定义Schema
        if key in self._node_fields:
            return self._node_fields[key].copy()
        
        # 根据值类型推断
        return self._infer_type_from_value(value)
    
    def _infer_type_from_value(self, value: Any) -> Dict[str, Any]:
        """从值推断类型
        
        Args:
            value: 值
            
        Returns:
            Dict[str, Any]: 类型Schema
        """
        if isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, list):
            if value:  # 列表不为空，尝试推断元素类型
                item_schema = self._infer_type_from_value(value[0])
                return {"type": "array", "items": item_schema}
            else:  # 空列表
                return {"type": "array", "items": {"type": "string"}}
        elif isinstance(value, dict):
            return {"type": "object"}
        else:
            return {"type": "string"}  # 默认类型
    
    def _is_required_field(self, key: str, value: Any) -> bool:
        """判断字段是否必需
        
        Args:
            key: 字段名
            value: 字段值
            
        Returns:
            bool: 是否必需
        """
        # 检查是否在预定义的必需字段列表中
        if key in self._required_fields:
            return True
        
        # 根据字段名和值进行启发式判断
        required_keywords = ["id", "type", "name"]
        if any(keyword in key.lower() for keyword in required_keywords):
            return True
        
        # 如果值是None或空，通常不是必需的（除非明确指定）
        if value is None or value == "":
            return False
        
        return False
    
    def _add_node_specific_properties(self, schema: Dict[str, Any]) -> None:
        """添加节点特定的属性定义
        
        Args:
            schema: Schema对象
        """
        # 确保inputs属性有详细的定义
        if "inputs" in schema["properties"]:
            schema["properties"]["inputs"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "输入名称"},
                        "type": {"type": "string", "description": "输入类型"},
                        "description": {"type": "string", "description": "输入描述"},
                        "required": {"type": "boolean", "description": "是否必需"},
                        "default": {"description": "默认值"},
                        "validation": {"type": "object", "description": "验证规则"}
                    },
                    "required": ["name", "type"]
                },
                "description": "节点输入定义列表"
            }
        
        # 确保outputs属性有详细的定义
        if "outputs" in schema["properties"]:
            schema["properties"]["outputs"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "输出名称"},
                        "type": {"type": "string", "description": "输出类型"},
                        "description": {"type": "string", "description": "输出描述"}
                    },
                    "required": ["name", "type"]
                },
                "description": "节点输出定义列表"
            }
        
        # 确保position属性有详细的定义
        if "position" in schema["properties"]:
            schema["properties"]["position"] = {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X坐标"},
                    "y": {"type": "number", "description": "Y坐标"},
                    "z": {"type": "number", "description": "Z坐标（可选）"}
                },
                "required": ["x", "y"],
                "description": "节点位置坐标"
            }
        
        # 确保style属性有详细的定义
        if "style" in schema["properties"]:
            schema["properties"]["style"] = {
                "type": "object",
                "properties": {
                    "color": {"type": "string", "description": "颜色"},
                    "size": {"type": "string", "description": "大小"},
                    "shape": {"type": "string", "description": "形状"},
                    "icon": {"type": "string", "description": "图标"},
                    "label": {"type": "string", "description": "标签样式"}
                },
                "additionalProperties": True,
                "description": "节点样式定义"
            }
        
        # 添加metadata的详细定义
        if "metadata" in schema["properties"]:
            schema["properties"]["metadata"] = {
                "type": "object",
                "properties": {
                    "author": {"type": "string", "description": "作者"},
                    "created_at": {"type": "string", "description": "创建时间"},
                    "updated_at": {"type": "string", "description": "更新时间"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "标签"},
                    "version": {"type": "string", "description": "版本"},
                    "category": {"type": "string", "description": "分类"},
                    "complexity": {"type": "string", "description": "复杂度级别"}
                },
                "additionalProperties": True,
                "description": "节点元数据"
            }