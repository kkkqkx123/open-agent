"""LLM配置模式

定义LLM模块的配置验证模式和规则，与配置加载模块集成。
"""

from typing import Dict, Any, List, Optional
import logging

from .base_schema import BaseSchema
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class LLMSchema(BaseSchema):
    """LLM配置模式
    
    定义LLM模块配置的验证规则和模式，与配置加载模块集成。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化LLM配置模式
        
        Args:
            config_loader: 配置加载器，用于动态加载配置模式
        """
        super().__init__()
        self.config_loader = config_loader
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("LLM配置模式初始化完成")
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 1. 验证顶级结构
        structure_errors, structure_warnings = self._validate_structure(config)
        errors.extend(structure_errors)
        warnings.extend(structure_warnings)
        
        # 2. 验证客户端配置
        if "clients" in config:
            client_errors, client_warnings = self._validate_clients(config["clients"])
            errors.extend(client_errors)
            warnings.extend(client_warnings)
        
        # 3. 验证模块配置
        if "module" in config:
            module_errors, module_warnings = self._validate_module(config["module"])
            errors.extend(module_errors)
            warnings.extend(module_warnings)
        
        # 4. 验证全局配置
        global_errors, global_warnings = self._validate_global_config(config)
        errors.extend(global_errors)
        warnings.extend(global_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义
        """
        # 尝试从缓存获取
        if "llm_config" in self._schema_cache:
            return self._schema_cache["llm_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("llm_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_llm_config_schema()
        
        # 缓存模式
        self._schema_cache["llm_config"] = schema
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
            schema_path = f"config/schema/llm/{schema_name}"
            schema_config = self.config_loader.load(schema_path)
            
            if schema_config and "schema" in schema_config:
                logger.debug(f"从配置文件加载模式: {schema_name}")
                return schema_config["schema"]
            
        except Exception as e:
            logger.debug(f"无法从配置文件加载模式 {schema_name}: {e}")
        
        return None
    
    def _get_base_llm_config_schema(self) -> Dict[str, Any]:
        """获取基础LLM配置模式
        
        Returns:
            基础LLM配置模式字典
        """
        return {
            "type": "object",
            "required": ["clients"],
            "properties": {
                "version": {
                    "type": "string",
                    "description": "配置版本"
                },
                "description": {
                    "type": "string",
                    "description": "配置描述"
                },
                "clients": {
                    "type": "object",
                    "description": "客户端配置"
                },
                "module": {
                    "type": "object",
                    "description": "模块配置"
                }
            }
        }
    
    def _validate_structure(self, config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证配置结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 检查是否为字典
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return errors, warnings
        
        # 获取模式定义
        schema = self.get_schema_definition()
        required_fields = schema.get("required", [])
        
        # 检查必要字段
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必要的{field}字段")
        
        # 特殊验证clients字段
        if "clients" in config:
            if not isinstance(config["clients"], dict):
                errors.append("clients字段必须是字典类型")
            elif len(config["clients"]) == 0:
                errors.append("至少需要配置一个客户端")
        
        return errors, warnings
    
    def _validate_clients(self, clients: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证客户端配置
        
        Args:
            clients: 客户端配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        for client_name, client_config in clients.items():
            client_errors, client_warnings = self._validate_single_client(client_name, client_config)
            errors.extend(client_errors)
            warnings.extend(client_warnings)
        
        return errors, warnings
    
    def _validate_single_client(self, client_name: str, client_config: Any) -> tuple[List[str], List[str]]:
        """验证单个客户端配置
        
        Args:
            client_name: 客户端名称
            client_config: 客户端配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 检查配置类型
        if not isinstance(client_config, dict):
            errors.append(f"客户端 {client_name} 的配置必须是字典类型")
            return errors, warnings
        
        # 检查必要字段
        required_fields = ["model_type", "model_name"]
        for field in required_fields:
            if field not in client_config:
                errors.append(f"客户端 {client_name} 缺少必要字段: {field}")
            elif not client_config[field]:
                errors.append(f"客户端 {client_name} 的字段 {field} 不能为空")
        
        # 验证模型类型
        if "model_type" in client_config:
            model_type = client_config["model_type"]
            # 从模式定义获取有效类型
            schema = self.get_schema_definition()
            clients_schema = schema.get("properties", {}).get("clients", {})
            pattern_properties = clients_schema.get("patternProperties", {})
            
            # 获取第一个模式（所有客户端共享）
            valid_types = []
            if pattern_properties:
                for pattern_schema in pattern_properties.values():
                    model_type_schema = pattern_schema.get("properties", {}).get("model_type", {})
                    valid_types = model_type_schema.get("enum", [])
                    break
            
            if valid_types and model_type not in valid_types:
                errors.append(f"客户端 {client_name} 的模型类型无效: {model_type}")
        
        # 验证数值范围
        numeric_fields = self._get_numeric_field_ranges("client")
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in client_config:
                value = client_config[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"客户端 {client_name} 的字段 {field} 必须是数值类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"客户端 {client_name} 的字段 {field} 值超出范围: {value}")
        
        # 验证数组字段
        array_fields = ["fallback_models"]
        for field in array_fields:
            if field in client_config:
                value = client_config[field]
                if not isinstance(value, list):
                    errors.append(f"客户端 {client_name} 的字段 {field} 必须是数组类型")
                elif not all(isinstance(item, str) for item in value):
                    errors.append(f"客户端 {client_name} 的字段 {field} 的所有元素必须是字符串")
        
        # 验证连接池配置
        if "connection_pool_config" in client_config:
            pool_config = client_config["connection_pool_config"]
            if not isinstance(pool_config, dict):
                errors.append(f"客户端 {client_name} 的连接池配置必须是字典类型")
            else:
                pool_errors, pool_warnings = self._validate_connection_pool_config(client_name, pool_config)
                errors.extend(pool_errors)
                warnings.extend(pool_warnings)
        
        return errors, warnings
    
    def _validate_connection_pool_config(self, client_name: str, pool_config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证连接池配置
        
        Args:
            client_name: 客户端名称
            pool_config: 连接池配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        pool_fields = {
            "max_connections": (1, 100),
            "max_keepalive": (1, 100),
            "connection_timeout": (1.0, 300.0),
            "read_timeout": (1.0, 300.0),
            "write_timeout": (1.0, 300.0),
            "connect_retries": (1, 10),
            "pool_timeout": (1.0, 300.0)
        }
        
        for field, (min_val, max_val) in pool_fields.items():
            if field in pool_config:
                value = pool_config[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"客户端 {client_name} 的连接池字段 {field} 必须是数值类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"客户端 {client_name} 的连接池字段 {field} 值超出范围: {value}")
        
        return errors, warnings
    
    def _validate_module(self, module: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证模块配置
        
        Args:
            module: 模块配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 验证数值范围
        numeric_fields = self._get_numeric_field_ranges("module")
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in module:
                value = module[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"模块配置的字段 {field} 必须是数值类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"模块配置的字段 {field} 值超出范围: {value}")
        
        # 验证数组字段
        array_fields = ["global_fallback_models"]
        for field in array_fields:
            if field in module:
                value = module[field]
                if not isinstance(value, list):
                    errors.append(f"模块配置的字段 {field} 必须是数组类型")
                elif not all(isinstance(item, str) for item in value):
                    errors.append(f"模块配置的字段 {field} 的所有元素必须是字符串")
        
        return errors, warnings
    
    def _validate_global_config(self, config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证全局配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 检查版本格式
        if "version" in config:
            version = config["version"]
            if not isinstance(version, str):
                errors.append("版本号必须是字符串类型")
            elif not self._is_valid_version(version):
                warnings.append(f"版本号格式可能不标准: {version}")
        
        # 检查默认模型是否存在
        if "module" in config and "default_model" in config["module"]:
            default_model = config["module"]["default_model"]
            if "clients" in config:
                model_exists = False
                for client_config in config["clients"].values():
                    if client_config.get("model_name") == default_model:
                        model_exists = True
                        break
                
                if not model_exists:
                    warnings.append(f"默认模型 {default_model} 在客户端配置中不存在")
        
        return errors, warnings
    
    def _is_valid_version(self, version: str) -> bool:
        """检查版本号格式是否有效
        
        Args:
            version: 版本号
            
        Returns:
            是否有效
        """
        import re
        # 简单的版本号格式检查：x.y.z
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _get_numeric_field_ranges(self, config_type: str) -> Dict[str, tuple]:
        """获取数值字段的范围
        
        Args:
            config_type: 配置类型（client或module）
            
        Returns:
            字段名到范围元组的映射
        """
        # 默认范围
        default_ranges = {
            "client": {
                "timeout": (1, 300),
                "max_retries": (0, 10),
                "temperature": (0.0, 2.0),
                "top_p": (0.0, 1.0),
                "max_fallback_attempts": (1, 5)
            },
            "module": {
                "default_timeout": (1, 300),
                "default_max_retries": (0, 10),
                "cache_ttl": (60, 86400),
                "cache_max_size": (1, 10000),
                "max_concurrent_requests": (1, 1000),
                "request_queue_size": (1, 10000),
                "default_max_connections": (1, 100),
                "default_max_keepalive": (1, 100),
                "default_connection_timeout": (1.0, 300.0)
            }
        }
        
        # 尝试从模式定义获取范围
        try:
            schema = self.get_schema_definition()
            ranges = {}
            
            if config_type == "client":
                clients_schema = schema.get("properties", {}).get("clients", {})
                pattern_properties = clients_schema.get("patternProperties", {})
                
                if pattern_properties:
                    # 获取第一个模式（所有客户端共享）
                    for pattern_schema in pattern_properties.values():
                        properties = pattern_schema.get("properties", {})
                        for field_name, field_schema in properties.items():
                            if field_schema.get("type") in ["integer", "number"]:
                                min_val = field_schema.get("minimum")
                                max_val = field_schema.get("maximum")
                                if min_val is not None and max_val is not None:
                                    ranges[field_name] = (min_val, max_val)
                        break
            
            elif config_type == "module":
                module_schema = schema.get("properties", {}).get("module", {})
                properties = module_schema.get("properties", {})
                
                for field_name, field_schema in properties.items():
                    if field_schema.get("type") in ["integer", "number"]:
                        min_val = field_schema.get("minimum")
                        max_val = field_schema.get("maximum")
                        if min_val is not None and max_val is not None:
                            ranges[field_name] = (min_val, max_val)
            
            # 如果从模式获取到了范围，使用它们；否则使用默认范围
            return ranges if ranges else default_ranges.get(config_type, {})
            
        except Exception as e:
            logger.debug(f"获取数值字段范围失败: {e}")
            return default_ranges.get(config_type, {})