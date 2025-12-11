"""Edge配置模式

定义Edge模块的配置验证模式，与配置加载模块集成。
"""

from typing import Dict, Any, List, Optional
import logging

from .base_schema import BaseSchema
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class EdgeSchema(BaseSchema):
    """Edge配置模式
    
    定义Edge模块的配置验证规则和模式，与配置加载模块集成。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化Edge配置模式
        
        Args:
            config_loader: 配置加载器，用于动态加载配置模式
        """
        super().__init__()
        self.config_loader = config_loader
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("Edge配置模式初始化完成")
    
    def get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        # 尝试从缓存获取
        if "edge_config" in self._schema_cache:
            return self._schema_cache["edge_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("edge_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_edge_config_schema()
        
        # 缓存模式
        self._schema_cache["edge_config"] = schema
        return schema
    
    def _load_schema_from_config(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """从配置文件加载模式
        
        Args:
            schema_name: 模式名称
            
        Returns:
            模式字典或None
        """
        if not self.config_loader:
            return None
        
        try:
            # 尝试加载模式配置文件
            schema_path = f"config/schema/edge/{schema_name}"
            schema_config = self.config_loader.load(schema_path)
            
            if schema_config and "schema" in schema_config:
                logger.debug(f"从配置文件加载模式: {schema_name}")
                return schema_config["schema"]
            
        except Exception as e:
            logger.debug(f"无法从配置文件加载模式 {schema_name}: {e}")
        
        return None
    
    def _get_base_edge_config_schema(self) -> Dict[str, Any]:
        """获取基础Edge配置模式
        
        Returns:
            基础Edge配置模式字典
        """
        return {
            "type": "object",
            "required": ["name", "from", "type"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "边名称"
                },
                "from": {
                    "type": "string",
                    "description": "起始节点"
                },
                "to": {
                    "type": "string",
                    "description": "目标节点"
                },
                "type": {
                    "type": "string",
                    "description": "边类型"
                },
                "condition": {
                    "type": "string",
                    "description": "条件表达式"
                },
                "path_map": {
                    "type": "object",
                    "description": "路径映射"
                },
                "data_transformation": {
                    "type": "object",
                    "description": "数据转换配置"
                },
                "filter": {
                    "type": "object",
                    "description": "过滤配置"
                }
            }
        }
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 基础验证
        base_result = super().validate(config)
        errors.extend(base_result.errors)
        warnings.extend(base_result.warnings)
        
        # Edge特定验证
        errors.extend(self._validate_edge_structure(config))
        errors.extend(self._validate_condition_config(config))
        errors.extend(self._validate_transformation_config(config))
        
        # 生成警告
        warnings.extend(self._generate_warnings(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_edge_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证边结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证边名称
        name = config.get("name")
        if not name:
            errors.append("边名称不能为空")
        elif not isinstance(name, str):
            errors.append("边名称必须是字符串")
        
        # 验证边ID
        edge_id = config.get("id")
        if edge_id and not isinstance(edge_id, str):
            errors.append("边ID必须是字符串")
        
        # 验证起始节点
        from_node = config.get("from")
        if not from_node:
            errors.append("起始节点不能为空")
        elif not isinstance(from_node, str):
            errors.append("起始节点必须是字符串")
        
        # 验证目标节点
        to_node = config.get("to")
        edge_type = config.get("type", "simple")
        if edge_type == "simple" and not to_node:
            errors.append("简单边必须指定目标节点")
        elif to_node and not isinstance(to_node, str):
            errors.append("目标节点必须是字符串")
        
        # 验证边类型
        # 从模式定义获取有效类型
        schema = self.get_schema_definition()
        edge_type_schema = schema.get("properties", {}).get("type", {})
        valid_types = edge_type_schema.get("enum", [])
        
        if valid_types and edge_type not in valid_types:
            errors.append(f"不支持的边类型: {edge_type}")
        
        # 验证数值字段
        numeric_fields = self._get_numeric_field_ranges()
        
        for field_name, (min_val, max_val) in numeric_fields.items():
            if field_name in config:
                value = config[field_name]
                if not isinstance(value, (int, float)):
                    errors.append(f"{field_name}必须是数字类型")
                elif min_val is not None and value < min_val:
                    errors.append(f"{field_name}必须大于等于{min_val}")
                elif max_val is not None and value > max_val:
                    errors.append(f"{field_name}必须小于等于{max_val}")
        
        return errors
    
    def _validate_condition_config(self, config: Dict[str, Any]) -> List[str]:
        """验证条件配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        edge_type = config.get("type")
        
        if edge_type == "conditional":
            # 验证条件配置
            condition = config.get("condition")
            condition_function = config.get("condition_function")
            path_map = config.get("path_map")
            
            if not condition and not condition_function and not path_map:
                errors.append("条件边必须指定condition、condition_function或path_map")
            
            # 验证条件函数参数
            condition_parameters = config.get("condition_parameters", {})
            if condition_parameters and not isinstance(condition_parameters, dict):
                errors.append("condition_parameters必须是字典")
            
            # 验证路径映射
            if path_map:
                if isinstance(path_map, dict):
                    if not path_map:
                        errors.append("路径映射不能为空")
                elif isinstance(path_map, list):
                    if not path_map:
                        errors.append("路径映射不能为空")
                else:
                    errors.append("路径映射必须是字典或数组")
        
        return errors
    
    def _validate_transformation_config(self, config: Dict[str, Any]) -> List[str]:
        """验证转换配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证数据转换配置
        data_transformation = config.get("data_transformation", {})
        if data_transformation and not isinstance(data_transformation, dict):
            errors.append("data_transformation必须是字典")
        else:
            if data_transformation:
                transform_function = data_transformation.get("transform_function")
                if data_transformation.get("enabled") and not transform_function:
                    errors.append("启用的数据转换必须指定transform_function")
                
                transform_parameters = data_transformation.get("transform_parameters", {})
                if transform_parameters and not isinstance(transform_parameters, dict):
                    errors.append("transform_parameters必须是字典")
        
        # 验证过滤配置
        filter_config = config.get("filter", {})
        if filter_config and not isinstance(filter_config, dict):
            errors.append("filter必须是字典")
        else:
            if filter_config:
                filter_function = filter_config.get("filter_function")
                if filter_config.get("enabled") and not filter_function:
                    errors.append("启用的过滤必须指定filter_function")
                
                filter_parameters = filter_config.get("filter_parameters", {})
                if filter_parameters and not isinstance(filter_parameters, dict):
                    errors.append("filter_parameters必须是字典")
        
        return errors
    
    def _generate_warnings(self, config: Dict[str, Any]) -> List[str]:
        """生成警告
        
        Args:
            config: 配置数据
            
        Returns:
            警告列表
        """
        warnings = []
        
        # 检查是否缺少描述
        if not config.get("description"):
            warnings.append("建议添加边描述")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        # 检查超时配置
        timeout = config.get("timeout", 30)
        if timeout > 300:
            warnings.append("超时时间过长可能影响性能")
        
        # 检查条件边配置
        edge_type = config.get("type")
        if edge_type == "conditional":
            condition = config.get("condition")
            path_map = config.get("path_map")
            
            if condition and path_map:
                warnings.append("同时指定condition和path_map可能导致混淆")
        
        # 检查转换配置
        data_transformation = config.get("data_transformation", {})
        if data_transformation.get("enabled"):
            warnings.append("数据转换可能影响性能")
        
        # 检查过滤配置
        filter_config = config.get("filter", {})
        if filter_config.get("enabled"):
            warnings.append("过滤可能影响性能")
        
        # 检查额外配置
        additional_config = config.get("additional_config", {})
        weight = additional_config.get("weight", 1.0)
        if weight > 10:
            warnings.append("权重过高可能影响性能")
        
        return warnings
    
    def _get_numeric_field_ranges(self) -> Dict[str, tuple]:
        """获取数值字段的范围
        
        Returns:
            字段名到范围元组的映射
        """
        # 默认范围
        default_ranges = {
            "timeout": (1, None),
            "retry_attempts": (0, None),
            "retry_delay": (0, None)
        }
        
        # 尝试从模式定义获取范围
        try:
            schema = self.get_schema_definition()
            ranges = {}
            
            properties = schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if field_schema.get("type") in ["integer", "number"]:
                    min_val = field_schema.get("minimum")
                    max_val = field_schema.get("maximum")
                    if min_val is not None or max_val is not None:
                        ranges[field_name] = (min_val, max_val)
            
            # 检查嵌套的数值字段
            data_transformation_schema = properties.get("data_transformation", {})
            transformation_properties = data_transformation_schema.get("properties", {})
            
            for field_name, field_schema in transformation_properties.items():
                if field_schema.get("type") in ["integer", "number"]:
                    min_val = field_schema.get("minimum")
                    max_val = field_schema.get("maximum")
                    if min_val is not None or max_val is not None:
                        ranges[f"data_transformation.{field_name}"] = (min_val, max_val)
            
            # 检查过滤配置中的数值字段
            filter_schema = properties.get("filter", {})
            filter_properties = filter_schema.get("properties", {})
            
            for field_name, field_schema in filter_properties.items():
                if field_schema.get("type") in ["integer", "number"]:
                    min_val = field_schema.get("minimum")
                    max_val = field_schema.get("maximum")
                    if min_val is not None or max_val is not None:
                        ranges[f"filter.{field_name}"] = (min_val, max_val)
            
            # 检查额外配置中的数值字段
            additional_config_schema = properties.get("additional_config", {})
            additional_properties = additional_config_schema.get("properties", {})
            
            for field_name, field_schema in additional_properties.items():
                if field_schema.get("type") in ["integer", "number"]:
                    min_val = field_schema.get("minimum")
                    max_val = field_schema.get("maximum")
                    if min_val is not None or max_val is not None:
                        ranges[f"additional_config.{field_name}"] = (min_val, max_val)
            
            # 如果从模式获取到了范围，使用它们；否则使用默认范围
            return ranges if ranges else default_ranges
            
        except Exception as e:
            logger.debug(f"获取数值字段范围失败: {e}")
            return default_ranges