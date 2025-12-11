"""统一元素构建器工厂

提供统一的元素构建器创建和管理功能。
"""

from typing import Any, Dict, List, Optional, Type, Union
import logging

from src.interfaces.workflow.element_builder import (
    IElementBuilder, INodeBuilder, IEdgeBuilder,
    IElementBuilderFactory, BuildContext
)
from src.interfaces.workflow.config import INodeConfig, IEdgeConfig
from src.interfaces.logger import ILogger
from .base_builder import BaseNodeBuilder, BaseEdgeBuilder, BaseElementBuilder
from .validation_rules import get_validation_registry
from .build_strategies import get_strategy_registry


class ElementBuilderFactory(IElementBuilderFactory):
    """统一元素构建器工厂
    
    负责创建和管理所有类型的元素构建器。
    """
    
    def __init__(self, logger: Optional[Union[logging.Logger, ILogger]] = None):
        """初始化元素构建器工厂
        
        Args:
            logger: 日志记录器
        """
        # 使用基础设施层的日志服务
        if logger is None:
            from src.interfaces.dependency_injection import get_logger
            self.logger = get_logger(self.__class__.__name__)
        else:
            self.logger = logger
            
        self._builder_classes: Dict[str, Type[IElementBuilder]] = {}
        self._builder_instances: Dict[str, IElementBuilder] = {}
        self._node_builder_classes: Dict[str, Type[INodeBuilder]] = {}
        self._edge_builder_classes: Dict[str, Type[IEdgeBuilder]] = {}
        self._validation_registry = get_validation_registry()
        self._strategy_registry = get_strategy_registry()
        
        # 注册默认构建器类
        self._register_default_builder_classes()
    
    def create_builder(self, element_type: str, context: BuildContext) -> IElementBuilder:
        """创建元素构建器
        
        Args:
            element_type: 元素类型
            context: 构建上下文
            
        Returns:
            IElementBuilder: 元素构建器实例
        """
        # 检查是否有缓存的实例
        cache_key = f"{element_type}:{id(context)}"
        if cache_key in self._builder_instances:
            return self._builder_instances[cache_key]
        
        # 获取构建器类
        builder_class = self._builder_classes.get(element_type)
        if not builder_class:
            raise ValueError(f"不支持的元素类型: {element_type}")
        
        # 创建构建器实例
        builder = self._create_builder_instance(builder_class, context)
        
        # 配置构建器
        self._configure_builder(builder, context)
        
        # 缓存实例
        self._builder_instances[cache_key] = builder
        
        self.logger.debug(f"创建{element_type}构建器: {builder_class.__name__}")
        return builder
    
    def get_supported_types(self) -> List[str]:
        """获取支持的元素类型"""
        return list(self._builder_classes.keys())
    
    def get_supported_node_types(self) -> List[str]:
        """获取支持的节点类型"""
        return list(self._node_builder_classes.keys())
    
    def get_supported_edge_types(self) -> List[str]:
        """获取支持的边类型"""
        return list(self._edge_builder_classes.keys())
    
    def register_builder(self, element_type: str, builder_class: Type[IElementBuilder]) -> None:
        """注册元素构建器
        
        Args:
            element_type: 元素类型
            builder_class: 构建器类
        """
        if not issubclass(builder_class, IElementBuilder):
            raise ValueError(f"构建器类必须实现 IElementBuilder 接口: {builder_class}")
        
        self._builder_classes[element_type] = builder_class
        
        # 如果是专门的节点或边构建器，也注册到对应的字典中
        if issubclass(builder_class, INodeBuilder):
            self._node_builder_classes[element_type] = builder_class
        if issubclass(builder_class, IEdgeBuilder):
            self._edge_builder_classes[element_type] = builder_class
        
        self.logger.debug(f"注册{element_type}构建器类: {builder_class.__name__}")
    
    def register_node_builder(self, node_type: str, builder_class: Type[INodeBuilder]) -> None:
        """注册节点构建器
        
        Args:
            node_type: 节点类型
            builder_class: 节点构建器类
        """
        if not issubclass(builder_class, INodeBuilder):
            raise ValueError(f"节点构建器类必须实现 INodeBuilder 接口: {builder_class}")
        
        self._node_builder_classes[node_type] = builder_class
        self._builder_classes[node_type] = builder_class  # 同时注册到通用字典
        
        self.logger.debug(f"注册节点构建器类: {node_type} -> {builder_class.__name__}")
    
    def register_edge_builder(self, edge_type: str, builder_class: Type[IEdgeBuilder]) -> None:
        """注册边构建器
        
        Args:
            edge_type: 边类型
            builder_class: 边构建器类
        """
        if not issubclass(builder_class, IEdgeBuilder):
            raise ValueError(f"边构建器类必须实现 IEdgeBuilder 接口: {builder_class}")
        
        self._edge_builder_classes[edge_type] = builder_class
        self._builder_classes[edge_type] = builder_class  # 同时注册到通用字典
        
        self.logger.debug(f"注册边构建器类: {edge_type} -> {builder_class.__name__}")
    
    def register_builder_instance(self, element_type: str, builder: IElementBuilder) -> None:
        """注册元素构建器实例
        
        Args:
            element_type: 元素类型
            builder: 构建器实例
        """
        if not isinstance(builder, IElementBuilder):
            raise ValueError(f"必须实现 IElementBuilder 接口: {type(builder)}")
        
        self._builder_instances[element_type] = builder
        self.logger.debug(f"注册{element_type}构建器实例: {type(builder).__name__}")
    
    def create_all_builders(self, context: BuildContext) -> Dict[str, IElementBuilder]:
        """创建所有支持的构建器
        
        Args:
            context: 构建上下文
            
        Returns:
            Dict[str, IElementBuilder]: 元素类型到构建器的映射
        """
        builders = {}
        for element_type in self.get_supported_types():
            try:
                builders[element_type] = self.create_builder(element_type, context)
            except Exception as e:
                self.logger.error(f"创建{element_type}构建器失败: {e}")
        
        return builders
    
    def clear_cache(self) -> None:
        """清除缓存的构建器实例"""
        self._builder_instances.clear()
        self.logger.debug("清除构建器实例缓存")
    
    def create_node_builder(self, node_type: str, context: BuildContext) -> INodeBuilder:
        """创建节点构建器
        
        Args:
            node_type: 节点类型
            context: 构建上下文
            
        Returns:
            INodeBuilder: 节点构建器实例
        """
        builder_class = self._node_builder_classes.get(node_type)
        if not builder_class:
            raise ValueError(f"不支持的节点类型: {node_type}")
        
        builder = self._create_builder_instance(builder_class, context)
        if not isinstance(builder, INodeBuilder):
            raise ValueError(f"构建器类必须实现 INodeBuilder 接口: {type(builder)}")
        
        return builder
    
    def create_edge_builder(self, edge_type: str, context: BuildContext) -> IEdgeBuilder:
        """创建边构建器
        
        Args:
            edge_type: 边类型
            context: 构建上下文
            
        Returns:
            IEdgeBuilder: 边构建器实例
        """
        builder_class = self._edge_builder_classes.get(edge_type)
        if not builder_class:
            raise ValueError(f"不支持的边类型: {edge_type}")
        
        builder = self._create_builder_instance(builder_class, context)
        if not isinstance(builder, IEdgeBuilder):
            raise ValueError(f"构建器类必须实现 IEdgeBuilder 接口: {type(builder)}")
        
        return builder
    
    def _create_builder_instance(self, builder_class: Type[IElementBuilder], context: BuildContext) -> IElementBuilder:
        """创建构建器实例
        
        Args:
            builder_class: 构建器类
            context: 构建上下文
            
        Returns:
            IElementBuilder: 构建器实例
        """
        # 尝试使用上下文信息创建实例
        try:
            # 检查构建器类是否支持这些参数（通过检查是否是BaseElementBuilder的子类）
            if issubclass(builder_class, BaseElementBuilder):
                return builder_class(
                    logger=context.logger,
                    enable_caching=getattr(context, 'enable_caching', True),
                    enable_validation=getattr(context, 'enable_validation', True)
                )
            else:
                # 对于其他类型的构建器，使用默认构造函数
                return builder_class()
        except TypeError:
            # 如果构造函数不接受这些参数，使用默认构造函数
            return builder_class()
    
    def _configure_builder(self, builder: IElementBuilder, context: BuildContext) -> None:
        """配置构建器
        
        Args:
            builder: 构建器实例
            context: 构建上下文
        """
        # 添加验证规则（BaseElementBuilder类型的构建器）
        if isinstance(builder, BaseElementBuilder):
            validation_rules = self._validation_registry.get_rules_for_config_type(type(None))
            for rule in validation_rules:
                builder.add_validation_rule(rule)
        
        # 添加构建策略（BaseElementBuilder类型的构建器）
        if isinstance(builder, BaseElementBuilder):
            # 这里可以根据上下文添加特定的策略
            strategies = self._strategy_registry.get_all_strategies()
            for strategy in strategies:
                builder.add_build_strategy(strategy)
    
    def _register_default_builder_classes(self) -> None:
        """注册默认构建器类"""
        # 注册基础构建器类
        self.register_node_builder("node", BaseNodeBuilder)
        self.register_edge_builder("edge", BaseEdgeBuilder)


class ConfigurableElementBuilderFactory(ElementBuilderFactory):
    """可配置的元素构建器工厂
    
    支持通过配置自定义构建器行为。
    """
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[Union[logging.Logger, ILogger]] = None
    ):
        """初始化可配置元素构建器工厂
        
        Args:
            config: 工厂配置
            logger: 日志记录器
        """
        super().__init__(logger)
        self.config = config or {}
        self._apply_configuration()
    
    def _apply_configuration(self) -> None:
        """应用配置"""
        # 注册自定义构建器
        custom_builders = self.config.get("custom_builders", {})
        for element_type, builder_class_path in custom_builders.items():
            try:
                builder_class = self._import_class(builder_class_path)
                self.register_builder(element_type, builder_class)
            except Exception as e:
                self.logger.error(f"注册自定义构建器失败 {element_type}: {e}")
        
        # 配置验证规则
        validation_config = self.config.get("validation", {})
        if validation_config.get("enabled", True):
            self._configure_validation_rules(validation_config)
        
        # 配置构建策略
        strategy_config = self.config.get("strategies", {})
        if strategy_config.get("enabled", True):
            self._configure_build_strategies(strategy_config)
    
    def _import_class(self, class_path: str) -> Type[Any]:
        """导入类
        
        Args:
            class_path: 类路径，格式为 "module.Class"
            
        Returns:
            Type: 导入的类
        """
        module_path, class_name = class_path.rsplit('.', 1)
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    
    def _configure_validation_rules(self, validation_config: Dict[str, Any]) -> None:
        """配置验证规则
        
        Args:
            validation_config: 验证配置
        """
        # 这里可以根据配置添加或移除验证规则
        disabled_rules = validation_config.get("disabled_rules", [])
        for rule_name in disabled_rules:
            rule = self._validation_registry.get_rule(rule_name)
            if rule:
                # 从所有构建器中移除该规则
                self.logger.debug(f"禁用验证规则: {rule_name}")
    
    def _configure_build_strategies(self, strategy_config: Dict[str, Any]) -> None:
        """配置构建策略
        
        Args:
            strategy_config: 策略配置
        """
        # 这里可以根据配置添加或移除构建策略
        disabled_strategies = strategy_config.get("disabled_strategies", [])
        for strategy_name in disabled_strategies:
            strategy = self._strategy_registry.get_strategy(strategy_name)
            if strategy:
                # 从所有构建器中移除该策略
                self.logger.debug(f"禁用构建策略: {strategy_name}")


class ElementBuilderManager:
    """元素构建器管理器
    
    管理多个构建器工厂实例，支持多环境配置。
    """
    
    def __init__(self, logger: Optional[Union[logging.Logger, ILogger]] = None):
        """初始化元素构建器管理器
        
        Args:
            logger: 日志记录器
        """
        # 使用基础设施层的日志服务
        if logger is None:
            from src.interfaces.dependency_injection import get_logger
            self.logger = get_logger(self.__class__.__name__)
        else:
            self.logger = logger
            
        self._factories: Dict[str, ElementBuilderFactory] = {}
        self._default_factory_name = "default"
        
        # 创建默认工厂
        self._factories[self._default_factory_name] = ElementBuilderFactory(logger)
    
    def get_factory(self, factory_name: Optional[str] = None) -> ElementBuilderFactory:
        """获取构建器工厂
        
        Args:
            factory_name: 工厂名称，如果为None则返回默认工厂
            
        Returns:
            ElementBuilderFactory: 构建器工厂实例
        """
        factory_name = factory_name or self._default_factory_name
        factory = self._factories.get(factory_name)
        if not factory:
            raise ValueError(f"构建器工厂不存在: {factory_name}")
        return factory
    
    def register_factory(self, factory_name: str, factory: ElementBuilderFactory) -> None:
        """注册构建器工厂
        
        Args:
            factory_name: 工厂名称
            factory: 构建器工厂实例
        """
        self._factories[factory_name] = factory
        self.logger.debug(f"注册构建器工厂: {factory_name}")
    
    def create_factory(
        self, 
        factory_name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> ElementBuilderFactory:
        """创建并注册构建器工厂
        
        Args:
            factory_name: 工厂名称
            config: 工厂配置
            
        Returns:
            ElementBuilderFactory: 创建的构建器工厂实例
        """
        factory = ConfigurableElementBuilderFactory(config, self.logger)
        self.register_factory(factory_name, factory)
        return factory
    
    def get_supported_types(self, factory_name: Optional[str] = None) -> List[str]:
        """获取支持的元素类型
        
        Args:
            factory_name: 工厂名称，如果为None则使用默认工厂
            
        Returns:
            List[str]: 支持的元素类型列表
        """
        factory = self.get_factory(factory_name)
        return factory.get_supported_types()
    
    def clear_all_caches(self) -> None:
        """清除所有工厂的缓存"""
        for factory in self._factories.values():
            factory.clear_cache()
        self.logger.debug("清除所有构建器工厂缓存")


# 全局元素构建器管理器实例
_global_builder_manager = ElementBuilderManager()


def get_builder_manager() -> ElementBuilderManager:
    """获取全局元素构建器管理器
    
    Returns:
        ElementBuilderManager: 元素构建器管理器实例
    """
    return _global_builder_manager


def get_builder_factory(factory_name: Optional[str] = None) -> ElementBuilderFactory:
    """获取构建器工厂的便捷函数
    
    Args:
        factory_name: 工厂名称
        
    Returns:
        ElementBuilderFactory: 构建器工厂实例
    """
    return _global_builder_manager.get_factory(factory_name)


def create_element_builder(
    element_type: str,
    context: BuildContext,
    factory_name: Optional[str] = None
) -> IElementBuilder:
    """创建元素构建器的便捷函数
    
    Args:
        element_type: 元素类型
        context: 构建上下文
        factory_name: 工厂名称
        
    Returns:
        IElementBuilder: 元素构建器实例
    """
    factory = get_builder_factory(factory_name)
    return factory.create_builder(element_type, context)


def create_node_builder(
    node_type: str,
    context: BuildContext,
    factory_name: Optional[str] = None
) -> INodeBuilder:
    """创建节点构建器的便捷函数
    
    Args:
        node_type: 节点类型
        context: 构建上下文
        factory_name: 工厂名称
        
    Returns:
        INodeBuilder: 节点构建器实例
    """
    factory = get_builder_factory(factory_name)
    return factory.create_node_builder(node_type, context)


def create_edge_builder(
    edge_type: str,
    context: BuildContext,
    factory_name: Optional[str] = None
) -> IEdgeBuilder:
    """创建边构建器的便捷函数
    
    Args:
        edge_type: 边类型
        context: 构建上下文
        factory_name: 工厂名称
        
    Returns:
        IEdgeBuilder: 边构建器实例
    """
    factory = get_builder_factory(factory_name)
    return factory.create_edge_builder(edge_type, context)


def register_element_builder(element_type: str, builder_class: Type[IElementBuilder]) -> None:
    """注册元素构建器的便捷函数
    
    Args:
        element_type: 元素类型
        builder_class: 构建器类
    """
    default_factory = get_builder_factory()
    default_factory.register_builder(element_type, builder_class)


def register_node_builder(node_type: str, builder_class: Type[INodeBuilder]) -> None:
    """注册节点构建器的便捷函数
    
    Args:
        node_type: 节点类型
        builder_class: 节点构建器类
    """
    default_factory = get_builder_factory()
    default_factory.register_node_builder(node_type, builder_class)


def register_edge_builder(edge_type: str, builder_class: Type[IEdgeBuilder]) -> None:
    """注册边构建器的便捷函数
    
    Args:
        edge_type: 边类型
        builder_class: 边构建器类
    """
    default_factory = get_builder_factory()
    default_factory.register_edge_builder(edge_type, builder_class)