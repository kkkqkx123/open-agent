"""配置工厂

提供配置系统各组件的创建和配置功能。
"""

from typing import Dict, Any, Optional, List, Type
from pathlib import Path
import logging

from .registry import ConfigRegistry
from .loader import ConfigLoader
from .impl.base_impl import BaseConfigImpl, ConfigProcessorChain
from src.interfaces.config.schema import IConfigSchema
from src.interfaces.config.schema import ISchemaGenerator
from src.interfaces.config.impl import IConfigImpl
from .processor.validation_processor_wrapper import ValidationProcessorWrapper
from .processor.transformation_processor import TransformationProcessor, TypeConverter
from .processor.environment_processor import EnvironmentProcessor
from .processor.inheritance_processor import InheritanceProcessor
from .processor.reference_processor import ReferenceProcessor

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
    
    def create_module_specific_processor_chain(self, module_type: str) -> ConfigProcessorChain:
        """创建模块特定的处理器链
        
        Args:
            module_type: 模块类型
            
        Returns:
            模块特定的处理器链
        """
        # 根据模块类型配置特定的处理器链
        if module_type == "graph":
            processor_names = ["inheritance", "environment", "reference", "transformation", "validation"]
        elif module_type == "node":
            processor_names = ["inheritance", "environment", "reference", "transformation", "validation"]
        elif module_type == "edge":
            processor_names = ["inheritance", "environment", "reference", "transformation", "validation"]
        elif module_type == "llm":
            processor_names = ["inheritance", "environment", "transformation", "validation_llm"]
        elif module_type == "tools":
            processor_names = ["inheritance", "environment", "transformation", "validation_tool"]
        elif module_type == "workflow":
            processor_names = ["inheritance", "reference", "transformation", "validation_workflow"]
        elif module_type == "state":
            processor_names = ["environment", "transformation", "validation_state"]
        else:
            # 使用默认处理器链
            processor_names = ["inheritance", "environment", "reference", "transformation", "validation"]
        
        logger.debug(f"为{module_type}模块创建处理器链: {processor_names}")
        return self.create_processor_chain(processor_names)
    
    def create_config_implementation(self,
                                   module_type: str,
                                   config_loader: Optional[ConfigLoader] = None,
                                   processor_chain: Optional[ConfigProcessorChain] = None,
                                   schema: Optional[IConfigSchema] = None) -> IConfigImpl:
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
        
        # 如果没有提供处理器链，创建模块特定的处理器链
        if processor_chain is None:
            chain = self.create_module_specific_processor_chain(module_type)
        else:
            chain = processor_chain
        
        # 如果没有schema，创建一个默认的空schema
        if schema is None:
            from .schema.base_schema import BaseSchema
            schema = BaseSchema()
        
        # 根据模块类型创建特定的实现
        if module_type == "llm":
            from .impl.llm_config_impl import LLMConfigImpl
            impl = LLMConfigImpl(loader, chain, schema)
        elif module_type == "tools":
            from .impl.tools_config_impl import ToolsConfigImpl
            impl = ToolsConfigImpl(loader, chain, schema)
        elif module_type == "workflow":
            from .impl.workflow_config_impl import WorkflowConfigImpl
            impl = WorkflowConfigImpl(loader, chain, schema)
        elif module_type == "state":
            # 状态配置使用基础实现
            impl = BaseConfigImpl("state", loader, chain, schema)
        elif module_type == "node":
            from .impl.node_config_impl import NodeConfigImpl
            impl = NodeConfigImpl(loader, chain, schema)
        elif module_type == "edge":
            from .impl.edge_config_impl import EdgeConfigImpl
            impl = EdgeConfigImpl(loader, chain, schema)
        elif module_type == "graph":
            from .impl.graph_config_impl import GraphConfigImpl
            impl = GraphConfigImpl(loader, chain, schema)
        else:
            # 使用基础实现
            impl = BaseConfigImpl(module_type, loader, chain, schema)
        
        # 注册到注册表
        self.registry.register_implementation(module_type, impl)
        
        logger.debug(f"创建{module_type}模块配置实现")
        return impl
    
    def get_config_implementation(self, module_type: str) -> Optional[IConfigImpl]:
        """获取配置实现
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置实现，如果不存在则返回None
        """
        impl = self.registry.get_implementation(module_type)
        
        if not impl:
            # 如果没有实现，创建一个默认的
            impl = self.create_config_implementation(module_type)
        
        return impl
    
    def register_module_config(self,
                               module_type: str,
                               schema: Optional[IConfigSchema] = None,
                               processor_names: Optional[List[str]] = None,
                               **kwargs: Any) -> None:
        """注册模块配置
        
        Args:
            module_type: 模块类型
            schema: 配置模式
            processor_names: 处理器名称列表
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
        
        logger.info(f"注册{module_type}模块配置")
    
    def setup_llm_config(self) -> IConfigImpl:
        """设置LLM配置
        
        Returns:
            LLM配置实现
        """
        # 使用模块特定的处理器链
        impl = self.create_config_implementation("llm")
        
        logger.info("设置LLM配置完成")
        return impl
    
    def setup_workflow_config(self) -> IConfigImpl:
        """设置工作流配置
        
        Returns:
            工作流配置实现
        """
        # 使用模块特定的处理器链
        impl = self.create_config_implementation("workflow")
        
        logger.info("设置工作流配置完成")
        return impl
    
    def setup_tools_config(self) -> IConfigImpl:
        """设置工具配置
        
        Returns:
            工具配置实现
        """
        # 使用模块特定的处理器链
        impl = self.create_config_implementation("tools")
        
        logger.info("设置工具配置完成")
        return impl
    
    def setup_state_config(self) -> IConfigImpl:
        """设置状态配置
        
        Returns:
            状态配置实现
        """
        # 使用模块特定的处理器链
        impl = self.create_config_implementation("state")
        
        logger.info("设置状态配置完成")
        return impl
    
    def setup_all_configs(self) -> Dict[str, IConfigImpl]:
        """设置所有模块配置
        
        Returns:
            模块类型到实现的映射
        """
        implementations = {}
        
        # 设置各模块配置
        implementations["llm"] = self.setup_llm_config()
        implementations["workflow"] = self.setup_workflow_config()
        implementations["tools"] = self.setup_tools_config()
        implementations["state"] = self.setup_state_config()
        implementations["graph"] = self.create_config_implementation("graph")
        implementations["node"] = self.create_config_implementation("node")
        implementations["edge"] = self.create_config_implementation("edge")
        
        logger.info("设置所有模块配置完成")
        return implementations
    
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
        
        # 验证处理器 - 直接使用 ConfigValidator
        validation_processor = ValidationProcessorWrapper()
        self.registry.register_processor("validation", validation_processor)
        
        # 为不同模块类型注册特定的验证处理器
        self._register_module_specific_validators()
        
        logger.debug("注册基础处理器完成")
    
    def _register_module_specific_validators(self) -> None:
        """注册模块特定的验证处理器"""
        # 为不同模块类型注册特定的验证处理器
        module_types = ["llm", "tool", "workflow", "global", "state"]
        
        for module_type in module_types:
            validator = ValidationProcessorWrapper(config_type=module_type)
            self.registry.register_processor(f"validation_{module_type}", validator)
            logger.debug(f"注册{module_type}模块验证处理器")
    
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
    
    def create_schema_generator(self, generator_type: str, config_impl: Optional[BaseConfigImpl] = None) -> ISchemaGenerator:
        """创建Schema生成器
        
        Args:
            generator_type: 生成器类型 (workflow, graph, node)
            config_impl: 配置实现
            
        Returns:
            ISchemaGenerator: Schema生成器实例
            
        Raises:
            ValueError: 如果不支持的生成器类型
        """
        logger.debug(f"创建Schema生成器: {generator_type}")
        
        if generator_type == "workflow":
            from .schema.generators.workflow_schema_generator import WorkflowSchemaGenerator
            return WorkflowSchemaGenerator(config_impl)
        elif generator_type == "graph":
            from .schema.generators.graph_schema_generator import GraphSchemaGenerator
            return GraphSchemaGenerator(config_impl)
        elif generator_type == "node":
            from .schema.generators.node_schema_generator import NodeSchemaGenerator
            return NodeSchemaGenerator(config_impl)
        else:
            raise ValueError(f"不支持的Schema生成器类型: {generator_type}")