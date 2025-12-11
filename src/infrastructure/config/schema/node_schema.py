"""Node配置模式

定义Node模块的配置验证模式，与配置加载模块集成。
"""

from typing import Dict, Any, List, Optional
import logging

from .base_schema import BaseSchema
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class NodeSchema(BaseSchema):
    """Node配置模式
    
    定义Node模块的配置验证规则和模式，与配置加载模块集成。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化Node配置模式
        
        Args:
            config_loader: 配置加载器，用于动态加载配置模式
        """
        super().__init__()
        self.config_loader = config_loader
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("Node配置模式初始化完成")
    
    def get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        # 尝试从缓存获取
        if "node_config" in self._schema_cache:
            return self._schema_cache["node_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("node_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_node_config_schema()
        
        # 缓存模式
        self._schema_cache["node_config"] = schema
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
            schema_path = f"config/schema/node/{schema_name}"
            schema_config = self.config_loader.load(schema_path)
            
            if schema_config and "schema" in schema_config:
                logger.debug(f"从配置文件加载模式: {schema_name}")
                return schema_config["schema"]
            
        except Exception as e:
            logger.debug(f"无法从配置文件加载模式 {schema_name}: {e}")
        
        return None
    
    def _get_base_node_config_schema(self) -> Dict[str, Any]:
        """获取基础Node配置模式
        
        Returns:
            基础Node配置模式字典
        """
        return {
            "type": "object",
            "required": ["name", "function_name"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "节点名称"
                },
                "function_name": {
                    "type": "string",
                    "description": "函数名称"
                },
                "type": {
                    "type": "string",
                    "description": "节点类型"
                },
                "function_config": {
                    "type": "object",
                    "description": "函数配置"
                },
                "input_parameters": {
                    "type": "object",
                    "description": "输入参数"
                },
                "output_parameters": {
                    "type": "object",
                    "description": "输出参数"
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
        
        # Node特定验证
        errors.extend(self._validate_node_structure(config))
        errors.extend(self._validate_function_config(config))
        errors.extend(self._validate_parameters(config))
        
        # 生成警告
        warnings.extend(self._generate_warnings(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_node_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证节点结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证节点名称
        name = config.get("name")
        if not name:
            errors.append("节点名称不能为空")
        elif not isinstance(name, str):
            errors.append("节点名称必须是字符串")
        
        # 验证节点ID
        node_id = config.get("id")
        if node_id and not isinstance(node_id, str):
            errors.append("节点ID必须是字符串")
        
        # 验证函数名称
        function_name = config.get("function_name")
        if not function_name:
            errors.append("函数名称不能为空")
        elif not isinstance(function_name, str):
            errors.append("函数名称必须是字符串")
        
        # 验证节点类型
        node_type = config.get("type")
        if node_type:
            # 从模式定义获取有效类型
            schema = self.get_schema_definition()
            node_type_schema = schema.get("properties", {}).get("type", {})
            valid_types = node_type_schema.get("enum", [])
            
            if valid_types and node_type not in valid_types:
                errors.append(f"不支持的节点类型: {node_type}")
        
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
    
    def _validate_function_config(self, config: Dict[str, Any]) -> List[str]:
        """验证函数配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        node_type = config.get("type")
        function_config = config.get("function_config", {})
        
        if not isinstance(function_config, dict):
            errors.append("function_config必须是字典")
            return errors
        
        # 根据节点类型验证特定配置
        if node_type == "llm":
            if "model" not in function_config:
                errors.append("LLM节点必须指定模型")
            
            temperature = function_config.get("temperature")
            if temperature is not None:
                # 从模式定义获取温度范围
                schema = self.get_schema_definition()
                function_config_schema = schema.get("properties", {}).get("function_config", {})
                temperature_schema = function_config_schema.get("properties", {}).get("temperature", {})
                min_temp = temperature_schema.get("minimum", 0)
                max_temp = temperature_schema.get("maximum", 2)
                
                if not isinstance(temperature, (int, float)) or temperature < min_temp or temperature > max_temp:
                    errors.append(f"temperature必须在{min_temp}-{max_temp}之间")
            
            max_tokens = function_config.get("max_tokens")
            if max_tokens is not None:
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    errors.append("max_tokens必须是大于0的整数")
        
        elif node_type == "tool":
            if "tool_name" not in function_config and "timeout" not in function_config:
                errors.append("Tool节点必须指定tool_name或timeout")
            
            timeout = function_config.get("timeout")
            if timeout is not None:
                if not isinstance(timeout, int) or timeout <= 0:
                    errors.append("timeout必须是大于0的整数")
        
        elif node_type == "condition":
            error_handling = function_config.get("error_handling")
            if error_handling:
                # 从模式定义获取有效错误处理方式
                schema = self.get_schema_definition()
                function_config_schema = schema.get("properties", {}).get("function_config", {})
                error_handling_schema = function_config_schema.get("properties", {}).get("error_handling", {})
                valid_error_handling = error_handling_schema.get("enum", ["raise", "ignore", "log"])
                
                if error_handling not in valid_error_handling:
                    errors.append(f"error_handling必须是{', '.join(valid_error_handling)}之一")
        
        return errors
    
    def _validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证输入参数
        input_params = config.get("input_parameters", {})
        if not isinstance(input_params, dict):
            errors.append("input_parameters必须是字典")
        else:
            for param_name, param_config in input_params.items():
                if not isinstance(param_config, dict):
                    errors.append(f"输入参数 {param_name} 配置必须是字典")
                    continue
                
                if "type" not in param_config:
                    errors.append(f"输入参数 {param_name} 必须指定type")
        
        # 验证输出参数
        output_params = config.get("output_parameters", {})
        if not isinstance(output_params, dict):
            errors.append("output_parameters必须是字典")
        else:
            for param_name, param_config in output_params.items():
                if not isinstance(param_config, dict):
                    errors.append(f"输出参数 {param_name} 配置必须是字典")
                    continue
                
                if "type" not in param_config:
                    errors.append(f"输出参数 {param_name} 必须指定type")
        
        # 验证环境变量
        environment = config.get("environment", {})
        if not isinstance(environment, dict):
            errors.append("environment必须是字典")
        
        # 验证映射配置
        for mapping_name in ["input_mapping", "output_mapping", "state_updates"]:
            mapping = config.get(mapping_name, {})
            if not isinstance(mapping, dict):
                errors.append(f"{mapping_name}必须是字典")
        
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
            warnings.append("建议添加节点描述")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        # 检查超时配置
        timeout = config.get("timeout", 30)
        if timeout > 300:
            warnings.append("超时时间过长可能影响性能")
        
        # 检查日志配置
        if not config.get("log_inputs", True):
            warnings.append("禁用输入日志可能影响调试")
        
        if not config.get("log_outputs", True):
            warnings.append("禁用输出日志可能影响调试")
        
        # 检查参数数量
        input_params = config.get("input_parameters", {})
        output_params = config.get("output_parameters", {})
        
        if len(input_params) > 20:
            warnings.append("输入参数过多可能影响性能")
        
        if len(output_params) > 20:
            warnings.append("输出参数过多可能影响性能")
        
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
            function_config_schema = properties.get("function_config", {})
            function_properties = function_config_schema.get("properties", {})
            
            for field_name, field_schema in function_properties.items():
                if field_schema.get("type") in ["integer", "number"]:
                    min_val = field_schema.get("minimum")
                    max_val = field_schema.get("maximum")
                    if min_val is not None or max_val is not None:
                        ranges[f"function_config.{field_name}"] = (min_val, max_val)
            
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