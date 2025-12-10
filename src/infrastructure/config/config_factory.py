"""配置工厂

提供配置系统各组件的创建和配置功能。
"""

from typing import Dict, Any, Optional, List, Type
from pathlib import Path
import logging

from .config_registry import ConfigRegistry
from .config_loader import ConfigLoader
from .impl.base_impl import BaseConfigImpl, ConfigProcessorChain, ConfigSchema
from src.interfaces.config.processor import IConfigProcessor
from .processor.validation_processor import ValidationProcessor, SchemaRegistry
from .processor.transformation_processor import TransformationProcessor, TypeConverter
from .processor.environment_processor import EnvironmentProcessor
from .processor.inheritance_processor import InheritanceProcessor
from .processor.reference_processor import ReferenceProcessor
from .provider.base_provider import BaseConfigProvider, IConfigProvider
from .provider.common_provider import CommonConfigProvider

logger = logging.getLogger(__name__)


class ConfigFactory:
    """配置工厂
    
    提供配置系统各组件的创建和配置功能。
    """
    
    def __init__(self, registry: Optional[ConfigRegistry] = None):
        """初始化配置工厂
        
        Args:
            registry: 配置注册表
        """
        self.registry = registry or ConfigRegistry()
        self._base_path = Path("configs")
        
        # 注册基础处理器
        self._register_base_processors()
        
        logger.debug("初始化配置工厂")
    
    def create_config_loader(self, base_path: Optional[Path] = None) -> ConfigLoader:
        """创建配置加载器
        
        Args:
            base_path: 基础路径
            
        Returns:
            配置加载器
        """
        loader = ConfigLoader(base_path or self._base_path)
        logger.debug("创建配置加载器")
        return loader
    
    def create_processor_chain(self, processor_names: List[str]) -> ConfigProcessorChain:
        """创建处理器链
        
        Args:
            processor_names: 处理器名称列表
            
        Returns:
            处理器链
        """
        chain = ConfigProcessorChain()
        
        for processor_name in processor_names:
            processor = self.registry.get_processor(processor_name)
            if processor:
                chain.add_processor(processor)
            else:
                logger.warning(f"未找到处理器: {processor_name}")
        
        logger.debug(f"创建处理器链: {processor_names}")
        return chain
    
    def create_default_processor_chain(self) -> ConfigProcessorChain:
        """创建默认处理器链
        
        Returns:
            默认处理器链
        """
        return self.create_processor_chain([
            "inheritance",
            "environment", 
            "reference",
            "transformation",
            "validation"
        ])
    
    def create_config_implementation(self, 
                                   module_type: str,
                                   config_loader: Optional[ConfigLoader] = None,
                                   processor_chain: Optional[ConfigProcessorChain] = None,
                                   schema: Optional[ConfigSchema] = None) -> BaseConfigImpl:
        """创建配置实现
        
        Args:
            module_type: 模块类型
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
            
        Returns:
            配置实现
        """
        loader = config_loader or self.create_config_loader()
        chain = processor_chain or self.create_default_processor_chain()
        
        # 如果没有schema，创建一个默认的空schema
        if schema is None:
            schema = ConfigSchema()
        
        impl = BaseConfigImpl(module_type, loader, chain, schema)
        
        # 注册到注册表
        self.registry.register_implementation(module_type, impl)
        
        logger.debug(f"创建{module_type}模块配置实现")
        return impl
    
    def create_config_provider(self,
                              module_type: str,
                              config_impl: Optional[BaseConfigImpl] = None,
                              provider_class: Optional[Type[BaseConfigProvider]] = None,
                              **kwargs) -> IConfigProvider:
        """创建配置提供者
        
        Args:
            module_type: 模块类型
            config_impl: 配置实现
            provider_class: 提供者类
            **kwargs: 其他参数
            
        Returns:
            配置提供者
        """
        impl = config_impl or self.registry.get_implementation(module_type)
        
        if not impl:
            # 如果没有实现，创建一个默认的
            impl = self.create_config_implementation(module_type)
        
        # 使用指定的提供者类或默认的通用提供者
        if provider_class:
            provider: IConfigProvider = provider_class(module_type, impl, **kwargs)
        else:
            provider = CommonConfigProvider(module_type, impl, **kwargs)
        
        # 注册到注册表
        self.registry.register_provider(module_type, provider)
        
        logger.debug(f"创建{module_type}模块配置提供者")
        return provider
    
    def register_module_config(self, 
                               module_type: str,
                               schema: Optional[ConfigSchema] = None,
                               processor_names: Optional[List[str]] = None,
                               provider_class: Optional[Type[BaseConfigProvider]] = None,
                               **kwargs) -> None:
        """注册模块配置
        
        Args:
            module_type: 模块类型
            schema: 配置模式
            processor_names: 处理器名称列表
            provider_class: 提供者类
            **kwargs: 其他参数
        """
        # 注册模式
        if schema:
            self.registry.register_schema(module_type, schema)
        
        # 创建处理器链
        chain = None
        if processor_names:
            chain = self.create_processor_chain(processor_names)
            self.registry._processor_chains[module_type] = chain
        
        # 创建配置实现
        impl = self.create_config_implementation(module_type, schema=schema, processor_chain=chain)
        
        # 创建配置提供者
        self.create_config_provider(module_type, impl, provider_class, **kwargs)
        
        logger.info(f"注册{module_type}模块配置")
    
    def setup_llm_config(self) -> IConfigProvider:
        """设置LLM配置
        
        Returns:
            LLM配置提供者
        """
        # 创建LLM特定的处理器链
        processor_names = ["inheritance", "environment", "transformation", "validation"]
        
        # 注册LLM配置
        self.register_module_config(
            "llm",
            processor_names=processor_names,
            cache_enabled=True,
            cache_ttl=300
        )
        
        provider = self.registry.get_provider("llm")
        if provider is None:
            raise RuntimeError("Failed to create LLM config provider")
        return provider
    
    def setup_workflow_config(self) -> IConfigProvider:
        """设置工作流配置
        
        Returns:
            工作流配置提供者
        """
        # 创建工作流特定的处理器链
        processor_names = ["inheritance", "reference", "transformation", "validation"]
        
        # 注册工作流配置
        self.register_module_config(
            "workflow",
            processor_names=processor_names,
            cache_enabled=True,
            cache_ttl=600
        )
        
        provider = self.registry.get_provider("workflow")
        if provider is None:
            raise RuntimeError("Failed to create workflow config provider")
        return provider
    
    def setup_tools_config(self) -> IConfigProvider:
        """设置工具配置
        
        Returns:
            工具配置提供者
        """
        # 创建工具特定的处理器链
        processor_names = ["inheritance", "environment", "transformation", "validation"]
        
        # 注册工具配置
        self.register_module_config(
            "tools",
            processor_names=processor_names,
            cache_enabled=True,
            cache_ttl=300
        )
        
        provider = self.registry.get_provider("tools")
        if provider is None:
            raise RuntimeError("Failed to create tools config provider")
        return provider
    
    def setup_state_config(self) -> IConfigProvider:
        """设置状态配置
        
        Returns:
            状态配置提供者
        """
        # 创建状态特定的处理器链
        processor_names = ["environment", "transformation", "validation"]
        
        # 注册状态配置
        self.register_module_config(
            "state",
            processor_names=processor_names,
            cache_enabled=True,
            cache_ttl=600
        )
        
        provider = self.registry.get_provider("state")
        if provider is None:
            raise RuntimeError("Failed to create state config provider")
        return provider
    
    def setup_all_configs(self) -> Dict[str, IConfigProvider]:
        """设置所有模块配置
        
        Returns:
            模块类型到提供者的映射
        """
        providers = {}
        
        # 设置各模块配置
        providers["llm"] = self.setup_llm_config()
        providers["workflow"] = self.setup_workflow_config()
        providers["tools"] = self.setup_tools_config()
        providers["state"] = self.setup_state_config()
        
        logger.info("设置所有模块配置完成")
        return providers
    
    def set_base_path(self, base_path: Path) -> None:
        """设置基础路径
        
        Args:
            base_path: 基础路径
        """
        self._base_path = base_path
        logger.debug(f"设置配置基础路径: {base_path}")
    
    def get_registry(self) -> ConfigRegistry:
        """获取配置注册表
        
        Returns:
            配置注册表
        """
        return self.registry
    
    def _register_base_processors(self) -> None:
        """注册基础处理器"""
        # 环境变量处理器
        env_processor = EnvironmentProcessor()
        self.registry.register_processor("environment", env_processor)
        
        # 继承处理器
        inheritance_processor = InheritanceProcessor()
        self.registry.register_processor("inheritance", inheritance_processor)
        
        # 引用处理器
        reference_processor = ReferenceProcessor()
        self.registry.register_processor("reference", reference_processor)
        
        # 转换处理器
        type_converter = TypeConverter()
        transformation_processor = TransformationProcessor(type_converter)
        self.registry.register_processor("transformation", transformation_processor)
        
        # 验证处理器
        validation_processor = ValidationProcessor(self.registry.schema_registry)
        self.registry.register_processor("validation", validation_processor)
        
        logger.debug("注册基础处理器完成")
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """获取工厂统计信息
        
        Returns:
            统计信息
        """
        return {
            "base_path": str(self._base_path),
            "registry_stats": self.registry.get_registry_stats(),
            "registry_validation": self.registry.validate_registry()
        }