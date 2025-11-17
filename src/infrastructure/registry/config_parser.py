"""配置解析器

集成各种验证器，提供统一的配置解析接口。
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml
import logging

from .config_validator import BaseConfigValidator, ValidationResult, ValidationSeverity
from .registry_validator import RegistryConfigValidator
from .workflow_validator import WorkflowConfigValidator

logger = logging.getLogger(__name__)


class ConfigParseError(Exception):
    """配置解析错误"""
    pass


class ConfigParser:
    """配置解析器
    
    集成各种验证器，提供统一的配置解析接口。
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """初始化配置解析器
        
        Args:
            base_path: 配置文件基础路径
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logger = logging.getLogger(f"{__name__}.ConfigParser")
        
        # 初始化验证器
        self._registry_validators = {
            "workflows": RegistryConfigValidator("workflows"),
            "tools": RegistryConfigValidator("tools"),
            "state_machine": RegistryConfigValidator("state_machine")
        }
        self._workflow_validator = WorkflowConfigValidator()
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._validation_cache: Dict[str, ValidationResult] = {}
    
    def parse_registry_config(self, registry_type: str, config_path: str) -> Dict[str, Any]:
        """解析注册表配置
        
        Args:
            registry_type: 注册表类型（workflows, tools, state_machine）
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 解析后的配置
            
        Raises:
            ConfigParseError: 配置解析失败
        """
        # 检查缓存
        cache_key = f"{registry_type}:{config_path}"
        if cache_key in self._config_cache:
            self.logger.debug(f"从缓存获取注册表配置: {cache_key}")
            return self._config_cache[cache_key]
        
        try:
            # 加载配置文件
            config = self._load_yaml_file(config_path)
            
            # 验证配置
            validator = self._registry_validators.get(registry_type)
            if not validator:
                raise ConfigParseError(f"不支持的注册表类型: {registry_type}")
            
            validation_result = validator.validate(config)
            
            # 检查验证结果
            if not validation_result.is_valid:
                error_msg = f"注册表配置验证失败: {config_path}"
                for error in validation_result.errors:
                    error_msg += f"\n  - {error}"
                raise ConfigParseError(error_msg)
            
            # 记录警告和信息
            for warning in validation_result.warnings:
                self.logger.warning(f"注册表配置警告: {warning}")
            
            for info in validation_result.info:
                self.logger.info(f"注册表配置信息: {info}")
            
            # 缓存结果
            self._config_cache[cache_key] = config
            self._validation_cache[cache_key] = validation_result
            
            self.logger.info(f"成功解析注册表配置: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"解析注册表配置失败: {config_path}, 错误: {e}")
            raise ConfigParseError(f"解析注册表配置失败: {e}")
    
    def parse_workflow_config(self, config_path: str) -> Dict[str, Any]:
        """解析工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 解析后的配置
            
        Raises:
            ConfigParseError: 配置解析失败
        """
        # 检查缓存
        cache_key = f"workflow:{config_path}"
        if cache_key in self._config_cache:
            self.logger.debug(f"从缓存获取工作流配置: {cache_key}")
            return self._config_cache[cache_key]
        
        try:
            # 加载配置文件
            config = self._load_yaml_file(config_path)
            
            # 处理继承关系
            config = self._process_inheritance(config, config_path)
            
            # 验证配置
            validation_result = self._workflow_validator.validate(config)
            
            # 检查验证结果
            if not validation_result.is_valid:
                error_msg = f"工作流配置验证失败: {config_path}"
                for error in validation_result.errors:
                    error_msg += f"\n  - {error}"
                raise ConfigParseError(error_msg)
            
            # 记录警告和信息
            for warning in validation_result.warnings:
                self.logger.warning(f"工作流配置警告: {warning}")
            
            for info in validation_result.info:
                self.logger.info(f"工作流配置信息: {info}")
            
            # 缓存结果
            self._config_cache[cache_key] = config
            self._validation_cache[cache_key] = validation_result
            
            self.logger.info(f"成功解析工作流配置: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"解析工作流配置失败: {config_path}, 错误: {e}")
            raise ConfigParseError(f"解析工作流配置失败: {e}")
    
    def parse_tool_config(self, config_path: str) -> Dict[str, Any]:
        """解析工具配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 解析后的配置
            
        Raises:
            ConfigParseError: 配置解析失败
        """
        # 检查缓存
        cache_key = f"tool:{config_path}"
        if cache_key in self._config_cache:
            self.logger.debug(f"从缓存获取工具配置: {cache_key}")
            return self._config_cache[cache_key]
        
        try:
            # 加载配置文件
            config = self._load_yaml_file(config_path)
            
            # 基础验证
            validation_result = self._validate_tool_config(config)
            
            # 检查验证结果
            if not validation_result.is_valid:
                error_msg = f"工具配置验证失败: {config_path}"
                for error in validation_result.errors:
                    error_msg += f"\n  - {error}"
                raise ConfigParseError(error_msg)
            
            # 记录警告和信息
            for warning in validation_result.warnings:
                self.logger.warning(f"工具配置警告: {warning}")
            
            for info in validation_result.info:
                self.logger.info(f"工具配置信息: {info}")
            
            # 缓存结果
            self._config_cache[cache_key] = config
            self._validation_cache[cache_key] = validation_result
            
            self.logger.info(f"成功解析工具配置: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"解析工具配置失败: {config_path}, 错误: {e}")
            raise ConfigParseError(f"解析工具配置失败: {e}")
    
    def parse_multiple_configs(self, config_paths: List[str], config_type: str = "workflow") -> List[Dict[str, Any]]:
        """解析多个配置文件
        
        Args:
            config_paths: 配置文件路径列表
            config_type: 配置类型（workflow, tool, registry）
            
        Returns:
            List[Dict[str, Any]]: 解析后的配置列表
            
        Raises:
            ConfigParseError: 配置解析失败
        """
        configs = []
        errors = []
        
        for config_path in config_paths:
            try:
                if config_type == "workflow":
                    config = self.parse_workflow_config(config_path)
                elif config_type == "tool":
                    config = self.parse_tool_config(config_path)
                elif config_type == "registry":
                    # 需要指定注册表类型
                    raise ConfigParseError("解析注册表配置需要指定注册表类型")
                else:
                    raise ConfigParseError(f"不支持的配置类型: {config_type}")
                
                configs.append(config)
                
            except Exception as e:
                errors.append(f"解析配置文件 {config_path} 失败: {e}")
        
        if errors:
            error_msg = "部分配置文件解析失败:"
            for error in errors:
                error_msg += f"\n  - {error}"
            raise ConfigParseError(error_msg)
        
        return configs
    
    def get_validation_result(self, config_type: str, config_path: str) -> Optional[ValidationResult]:
        """获取配置验证结果
        
        Args:
            config_type: 配置类型
            config_path: 配置文件路径
            
        Returns:
            Optional[ValidationResult]: 验证结果，如果不存在则返回None
        """
        cache_key = f"{config_type}:{config_path}"
        return self._validation_cache.get(cache_key)
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._config_cache.clear()
        self._validation_cache.clear()
        self.logger.info("已清除配置缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "config_cache_size": len(self._config_cache),
            "validation_cache_size": len(self._validation_cache),
            "cached_configs": list(self._config_cache.keys())
        }
    
    def _load_yaml_file(self, config_path: str) -> Dict[str, Any]:
        """加载YAML文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
            
        Raises:
            ConfigParseError: 文件加载失败
        """
        # 构建完整路径
        full_path = self.base_path / config_path
        
        # 检查文件是否存在
        if not full_path.exists():
            raise ConfigParseError(f"配置文件不存在: {full_path}")
        
        # 检查文件是否为文件
        if not full_path.is_file():
            raise ConfigParseError(f"配置路径不是文件: {full_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                config = {}
            
            return config
            
        except yaml.YAMLError as e:
            raise ConfigParseError(f"YAML解析错误: {e}")
        except Exception as e:
            raise ConfigParseError(f"读取文件失败: {e}")
    
    def _process_inheritance(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置继承关系
        
        Args:
            config: 配置字典
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 处理后的配置
        """
        if "inherits_from" not in config:
            return config
        
        parent_path = config["inherits_from"]
        
        # 构建父配置文件的完整路径
        config_dir = Path(config_path).parent
        parent_full_path = config_dir / parent_path
        
        try:
            # 加载父配置
            parent_config = self._load_yaml_file(str(parent_full_path))
            
            # 递归处理父配置的继承关系
            parent_config = self._process_inheritance(parent_config, str(parent_full_path))
            
            # 合并配置
            merged_config = self._merge_configs(parent_config, config)
            
            self.logger.debug(f"成功处理继承关系: {config_path} 继承自 {parent_path}")
            return merged_config
            
        except Exception as e:
            self.logger.warning(f"处理继承关系失败: {config_path} 继承自 {parent_path}, 错误: {e}")
            # 继承失败时返回原配置
            return config
    
    def _merge_configs(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            parent: 父配置
            child: 子配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged = parent.copy()
        
        for key, value in child.items():
            if key == "inherits_from":
                # 跳过继承字段
                continue
            
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 递归合并字典
                merged[key] = self._merge_configs(merged[key], value)
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                # 合并列表（子配置覆盖父配置）
                merged[key] = value
            else:
                # 直接覆盖
                merged[key] = value
        
        return merged
    
    def _validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置
        
        Args:
            config: 工具配置
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 基础验证
        self._validate_basic_structure(config, result)
        
        if not result.is_valid:
            return result
        
        # 验证必需字段
        required_fields = ["name", "tool_type", "description"]
        self._validate_required_fields(config, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "name": str,
            "tool_type": str,
            "description": str,
            "enabled": bool,
            "timeout": int,
            "function_path": str
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证工具类型
        if "tool_type" in config:
            valid_types = ["rest", "rest", "mcp"]
            if config["tool_type"] not in valid_types:
                result.add_warning(f"未知的工具类型: {config['tool_type']}")
        
        # 验证类路径
        if "function_path" in config:
            self._validate_class_path(config["function_path"], result)
        
        return result
    
    def _validate_basic_structure(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证配置的基础结构
        
        Args:
            config: 配置字典
            result: 验证结果对象
        """
        if not isinstance(config, dict):
            result.add_error("配置必须是字典类型")
    
    def _validate_required_fields(self, config: Dict[str, Any], required_fields: List[str], result: ValidationResult) -> None:
        """验证必需字段
        
        Args:
            config: 配置字典
            required_fields: 必需字段列表
            result: 验证结果对象
        """
        for field in required_fields:
            if field not in config:
                result.add_error(f"缺少必需字段: {field}")
    
    def _validate_field_types(self, config: Dict[str, Any], type_rules: Dict[str, Any], result: ValidationResult) -> None:
        """验证字段类型
        
        Args:
            config: 配置字典
            type_rules: 字段类型规则字典
            result: 验证结果对象
        """
        for field, expected_type in type_rules.items():
            if field in config:
                if not isinstance(config[field], expected_type):
                    result.add_error(f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，得到 {type(config[field]).__name__}")
    
    def _validate_class_path(self, class_path: str, result: ValidationResult) -> None:
        """验证类路径
        
        Args:
            class_path: 类路径字符串（格式：module.ClassName 或 module.submodule.ClassName）
            result: 验证结果对象
        """
        if not isinstance(class_path, str):
            result.add_error(f"类路径必须是字符串，得到 {type(class_path).__name__}")
            return
        
        if "." not in class_path:
            result.add_error(f"类路径格式错误: {class_path}，应该包含模块和类名")
            return
        
        parts = class_path.rsplit(".", 1)
        if len(parts) != 2:
            result.add_error(f"类路径格式错误: {class_path}")
        else:
            module_path, class_name = parts
            if not module_path or not class_name:
                result.add_error(f"类路径格式错误: {class_path}，模块和类名不能为空")