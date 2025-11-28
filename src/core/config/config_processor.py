"""
配置处理器 - 统一处理配置继承、环境变量解析和验证
"""

import os
import re
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ..common.cache import ConfigCache
from .config_loader import ConfigLoader
from ..common.exceptions.config import (
    ConfigInheritanceError,
    ConfigEnvironmentError,
    ConfigValidationError
)
from .validation import BaseConfigValidator, ValidationResult, ValidationSeverity


class ConfigProcessor:
    """统一配置处理器"""
    
    def __init__(self, loader: Optional[ConfigLoader] = None):
        """初始化处理器"""
        self.loader = loader or ConfigLoader()
        self._inheritance_cache = ConfigCache()  # 使用统一缓存系统
        self._env_var_pattern = re.compile(r'\$\{([^}]+)\}')
        self._validators = {}  # 存储特定类型的验证器
    
    def process(self, config: Dict[str, Any], config_path: Optional[str] = None) -> Dict[str, Any]:
        """处理配置（继承、环境变量、验证）"""
        # 1. 处理继承
        config = self._process_inheritance(config, config_path)
        
        # 2. 解析环境变量
        config = self._resolve_env_vars(config)
        
        # 3. 验证配置
        self._validate_config(config, config_path)
        
        return config
    
    def _process_inheritance(self, config: Dict[str, Any], config_path: Optional[str] = None) -> Dict[str, Any]:
        """处理继承关系"""
        from src.core.common.utils.inheritance_handler import ConfigInheritanceHandler
        handler = ConfigInheritanceHandler(self.loader)
        # 获取配置文件的目录路径
        base_path = Path(config_path).parent if config_path else None
        return handler.resolve_inheritance(config, base_path)
    
    def _load_parent_config(self, parent_path: str, current_path: Optional[str] = None) -> Dict[str, Any]:
        """加载父配置"""
        # 检查循环继承
        if current_path and parent_path == current_path:
            raise ConfigInheritanceError(
                f"检测到循环继承: {parent_path}",
                current_path,
                parent_path
            )
        
        # 检查缓存
        cache_key = f"{parent_path}:{current_path}"
        cached_config = self._inheritance_cache.get(cache_key)
        if cached_config is not None:
            return cached_config
        
        # 加载父配置
        parent_config = self.loader.load(parent_path)
        
        # 递归处理父配置的继承
        if "inherits_from" in parent_config:
            parent_config = self._process_inheritance(parent_config, parent_path)
        
        # 缓存结果
        self._inheritance_cache.put(cache_key, parent_config)
        
        return parent_config
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """解析环境变量"""
        from src.core.common.utils.env_resolver import EnvResolver
        resolver = EnvResolver()
        return resolver.resolve(obj)
    
    def _validate_config(self, config: Dict[str, Any], config_path: Optional[str] = None) -> None:
        """验证配置"""
        # 使用通用验证器进行基础验证
        from src.core.common.utils.validator import Validator
        validator = Validator()
        
        # 基础验证
        if not isinstance(config, dict):
            raise ConfigValidationError("配置必须是字典类型")
        
        if not config:
            raise ConfigValidationError("配置不能为空")
        
        # 验证必需字段
        if "name" not in config:
            raise ConfigValidationError("配置必须包含 'name' 字段")
        
        # 使用通用验证器验证结构
        validation_result = validator.validate_structure(config, [])
        if not validation_result.is_valid:
            for error in validation_result.errors:
                raise ConfigValidationError(f"配置结构验证失败: {error}")
        
        # 类型特定验证
        config_type = config.get("type")
        if config_type:
            self._validate_config_by_type(config, config_type, config_path)
    
    def _validate_config_by_type(self, config: Dict[str, Any], config_type: str, config_path: Optional[str] = None) -> None:
        """按类型验证配置"""
        # 这里可以添加更具体的类型验证逻辑
        if config_type == "llm":
            self._validate_llm_config(config)
        elif config_type == "tool":
            self._validate_tool_config(config)
        elif config_type == "tool_set":
            self._validate_tool_set_config(config)
        elif config_type == "workflow":
            self._validate_workflow_config(config, config_path)
        elif config_type == "registry":
            self._validate_registry_config(config, config_path)
        else:
            # 使用通用验证器
            self._validate_generic_config(config, config_type, config_path)
    
    def _validate_llm_config(self, config: Dict[str, Any]) -> None:
        """验证LLM配置"""
        required_fields = ["provider", "model"]
        for field in required_fields:
            if field not in config:
                raise ConfigValidationError(f"LLM配置必须包含 '{field}' 字段")
        
        # 验证提供商
        provider = config.get("provider")
        valid_providers = ['openai', 'anthropic', 'gemini', 'mock', 'human_relay']
        if provider not in valid_providers:
            raise ConfigValidationError(f"不支持的LLM提供商: {provider}")
    
    def _validate_tool_config(self, config: Dict[str, Any]) -> None:
        """验证工具配置"""
        # 工具配置的基础验证
        if "type" not in config:
            raise ConfigValidationError("工具配置必须包含 'type' 字段")
        
        tool_type = config.get("type")
        valid_types = ['rest', 'mcp', 'rest', 'external']
        if tool_type not in valid_types:
            raise ConfigValidationError(f"不支持的工具类型: {tool_type}")
    
    def _validate_tool_set_config(self, config: Dict[str, Any]) -> None:
        """验证工具集配置"""
        # 工具集配置的基础验证
        if "tools" not in config:
            raise ConfigValidationError("工具集配置必须包含 'tools' 字段")
        
        tools = config.get("tools")
        if not isinstance(tools, list):
            raise ConfigValidationError("工具集配置的 'tools' 字段必须是列表")
    
    def _validate_workflow_config(self, config: Dict[str, Any], config_path: Optional[str] = None) -> None:
        """验证工作流配置"""
        from ..workflow.validation import WorkflowConfigValidator
        validator = WorkflowConfigValidator()
        result = validator.validate(config)
        if not result.is_valid:
            error_msg = f"工作流配置验证失败: {config_path or 'unknown'}\n"
            for error in result.errors:
                error_msg += f"  - {error}\n"
            raise ConfigValidationError(error_msg)
    
    def _validate_registry_config(self, config: Dict[str, Any], config_path: Optional[str] = None) -> None:
        """验证注册表配置"""
        from ...services.config.registry_validator import RegistryConfigValidator
        registry_type = config.get("registry_type", "generic")
        validator = RegistryConfigValidator(registry_type)
        result = validator.validate(config)
        if not result.is_valid:
            error_msg = f"注册表配置验证失败: {config_path or 'unknown'}\n"
            for error in result.errors:
                error_msg += f" - {error}\n"
            raise ConfigValidationError(error_msg)
    
    def _validate_generic_config(self, config: Dict[str, Any], config_type: str, config_path: Optional[str] = None) -> None:
        """验证通用配置"""
        # 使用基础验证器
        validator = BaseConfigValidator(f"GenericConfigValidator_{config_type}")
        result = validator.validate(config)
        if not result.is_valid:
            error_msg = f"通用配置验证失败: {config_path or 'unknown'}\n"
            for error in result.errors:
                error_msg += f" - {error}\n"
            raise ConfigValidationError(error_msg)
    
    def _merge_configs(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置"""
        from src.core.common.utils.dict_merger import DictMerger
        merger = DictMerger()
        return merger.deep_merge(base, update)
    
    def clear_cache(self) -> None:
        """清除继承缓存"""
        self._inheritance_cache.clear()


# 工具函数
def process_config(config: Dict[str, Any], loader: Optional[ConfigLoader] = None) -> Dict[str, Any]:
    """处理单个配置"""
    processor = ConfigProcessor(loader)
    return processor.process(config)


def process_configs(configs: List[Dict[str, Any]], loader: Optional[ConfigLoader] = None) -> List[Dict[str, Any]]:
    """处理多个配置"""
    processor = ConfigProcessor(loader)
    return [processor.process(config) for config in configs]


# 环境变量解析工具函数
def resolve_env_vars(obj: Any) -> Any:
    """解析对象中的环境变量"""
    processor = ConfigProcessor()
    return processor._resolve_env_vars(obj)


def resolve_env_string(text: str) -> str:
    """解析字符串中的环境变量"""
    processor = ConfigProcessor()
    return processor._resolve_env_string(text)