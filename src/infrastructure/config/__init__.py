"""
基础设施层配置模块

提供配置加载、处理、验证和管理的完整基础设施实现。
采用impl+processor+provider架构模式。
"""

# 基础组件
from .loader import ConfigLoader
from .schema_loader import SchemaLoader
from .fixer import ConfigFixer
from .registry import ConfigRegistry, get_global_registry, set_global_registry
from .factory import ConfigFactory

# 配置实现层
from .impl import (
    BaseConfigImpl, IConfigProcessorChain,
    ConfigProcessorChain,
    LLMConfigImpl, WorkflowConfigImpl, GraphConfigImpl,
    NodeConfigImpl, EdgeConfigImpl, ToolsConfigImpl
)

# 配置处理器层
from .processor.base_processor import BaseConfigProcessor, IConfigProcessor
from .processor.validation_processor import ValidationProcessor, SchemaRegistry
from .processor.transformation_processor import TransformationProcessor, TypeConverter
from .processor import EnvironmentProcessor, InheritanceProcessor, ReferenceProcessor

# 配置模式层
from .schema import (
    LLMSchema, WorkflowSchema, GraphSchema, NodeSchema, EdgeSchema, ToolsSchema
)

# 配置模型层
from .models import (
    LLMClientConfig, OpenAIConfig, MockConfig, GeminiConfig,
    AnthropicConfig, HumanRelayConfig
)

__all__ = [
    # 基础组件
    "ConfigLoader",
    "SchemaLoader",
    "ConfigFixer",
    "ConfigRegistry",
    "get_global_registry",
    "set_global_registry",
    "ConfigFactory",
    
    # 配置实现层
    "BaseConfigImpl",
    "IConfigProcessorChain",
    "ConfigProcessorChain",
    "LLMConfigImpl",
    "WorkflowConfigImpl",
    "GraphConfigImpl",
    "NodeConfigImpl",
    "EdgeConfigImpl",
    "ToolsConfigImpl",
    
    # 配置处理器层
    "BaseConfigProcessor",
    "IConfigProcessor",
    "ValidationProcessor",
    "SchemaRegistry",
    "TransformationProcessor",
    "TypeConverter",
    "EnvironmentProcessor",
    "InheritanceProcessor",
    "ReferenceProcessor",
    
    # 配置模式层
    "LLMSchema",
    "WorkflowSchema",
    "GraphSchema",
    "NodeSchema",
    "EdgeSchema",
    "ToolsSchema",
    
    # 配置模型层
    "LLMClientConfig",
    "OpenAIConfig",
    "MockConfig",
    "GeminiConfig",
    "AnthropicConfig",
    "HumanRelayConfig",
]