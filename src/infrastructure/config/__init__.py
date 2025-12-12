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
from .event_manager import ConfigEventManager, CallbackService, create_config_event_manager, create_callback_service

# 配置实现层
from .impl import (
    BaseConfigImpl,
    ConfigProcessorChain,
    LLMConfigImpl, WorkflowConfigImpl, GraphConfigImpl,
    NodeConfigImpl, EdgeConfigImpl, ToolsConfigImpl
)

# 配置处理器层
from .processor.base_processor import BaseConfigProcessor, IConfigProcessor
from .processor.validation_processor_wrapper import ValidationProcessorWrapper
from .processor.transformation_processor import TransformationProcessor, TypeConverter
from .processor import EnvironmentProcessor, InheritanceProcessor, ReferenceProcessor

# 配置模式层
from .schema import (
    LLMSchema, WorkflowSchema, GraphSchema, NodeSchema, EdgeSchema, ToolsSchema
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
    "ConfigEventManager",
    "CallbackService",
    "create_config_event_manager",
    "create_callback_service",
    
    # 配置实现层
    "BaseConfigImpl",

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
    "ValidationProcessorWrapper",
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
]