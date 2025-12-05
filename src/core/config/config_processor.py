"""
配置处理器 - 统一处理配置继承、环境变量解析和验证
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .config_loader import ConfigLoader
from .processor.config_processor_chain import (
    ConfigProcessorChain,
    InheritanceProcessor,
    EnvironmentVariableProcessor,
    ReferenceProcessor
)
from .validation import BaseConfigValidator, ValidationResult, ValidationSeverity
from src.interfaces.configuration import (
    ConfigurationInheritanceError as ConfigInheritanceError,
    ConfigurationEnvironmentError as ConfigEnvironmentError,
    ConfigurationValidationError as ConfigValidationError
)


class ConfigProcessor:
    """统一配置处理器"""
    
    def __init__(self, loader: Optional[ConfigLoader] = None):
        """初始化处理器"""
        self.loader = loader or ConfigLoader()
        
        # 初始化处理器链
        self.processor_chain = ConfigProcessorChain()
        self.processor_chain.add_processor(InheritanceProcessor())
        self.processor_chain.add_processor(EnvironmentVariableProcessor())
        self.processor_chain.add_processor(ReferenceProcessor())
        
        self._validators = {}  # 存储特定类型的验证器
    
    def process(self, config: Dict[str, Any], config_path: Optional[str] = None) -> Dict[str, Any]:
        """处理配置（继承、环境变量、验证）"""
        # 使用处理器链处理配置
        processed_config = self.processor_chain.process(config, config_path or "")
        
        # 验证配置
        self._validate_config(processed_config, config_path)
        
        return processed_config
    
    def _validate_config(self, config: Dict[str, Any], config_path: Optional[str] = None) -> None:
        """验证配置"""
        # 基础验证
        if not isinstance(config, dict):
            raise ConfigValidationError("配置必须是字典类型")
        
        if not config:
            raise ConfigValidationError("配置不能为空")
        
        # 验证必需字段
        if "name" not in config:
            raise ConfigValidationError("配置必须包含 'name' 字段")
        
        # 类型特定验证
        config_type = config.get("type")
        if config_type:
            self._validate_config_by_type(config, config_type, config_path)
    
    def _validate_config_by_type(self, config: Dict[str, Any], config_type: str, config_path: Optional[str] = None) -> None:
        """按类型验证配置"""
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
        if "type" not in config:
            raise ConfigValidationError("工具配置必须包含 'type' 字段")
        
        tool_type = config.get("type")
        valid_types = ['rest', 'mcp', 'rest', 'external']
        if tool_type not in valid_types:
            raise ConfigValidationError(f"不支持的工具类型: {tool_type}")
    
    def _validate_tool_set_config(self, config: Dict[str, Any]) -> None:
        """验证工具集配置"""
        if "tools" not in config:
            raise ConfigValidationError("工具集配置必须包含 'tools' 字段")
        
        tools = config.get("tools")
        if not isinstance(tools, list):
            raise ConfigValidationError("工具集配置的 'tools' 字段必须是列表")
    
    def _validate_workflow_config(self, config: Dict[str, Any], config_path: Optional[str] = None) -> None:
        """验证工作流配置"""
        # 基础工作流配置验证
        if not isinstance(config, dict):
            raise ConfigValidationError("工作流配置必须是字典类型")
        
        # 验证必需字段
        if "name" not in config:
            raise ConfigValidationError("工作流配置必须包含 'name' 字段")
    
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
    
    def resolve_env_vars(self, obj: Any) -> Any:
        """解析对象中的环境变量
        
        Args:
            obj: 要处理的对象
            
        Returns:
            处理后的对象
        """
        processor = EnvironmentVariableProcessor()
        return processor._resolve_env_vars_recursive(obj)
    
    def clear_cache(self) -> None:
        """清除缓存"""
        # 处理器链中的缓存清理
        pass


# 工具函数
def process_config(config: Dict[str, Any], loader: Optional[ConfigLoader] = None) -> Dict[str, Any]:
    """处理单个配置"""
    processor = ConfigProcessor(loader)
    return processor.process(config)


def process_configs(configs: list[Dict[str, Any]], loader: Optional[ConfigLoader] = None) -> list[Dict[str, Any]]:
    """处理多个配置"""
    processor = ConfigProcessor(loader)
    return [processor.process(config) for config in configs]


# 环境变量解析工具函数
def resolve_env_vars(obj: Any) -> Any:
    """解析对象中的环境变量"""
    processor = EnvironmentVariableProcessor()
    return processor._resolve_env_vars_recursive(obj)


def resolve_env_string(text: str) -> str:
    """解析字符串中的环境变量"""
    processor = EnvironmentVariableProcessor()
    return processor._resolve_env_var_string(text)