"""统一构建策略

提供可复用的构建策略，减少各构建器中的重复构建逻辑。
"""

from typing import Any, Dict, List, Optional, Union, Callable, cast

from src.interfaces.workflow.element_builder import IBuildStrategy, BuildContext, IElementBuilder, INodeBuilder, IEdgeBuilder
from src.interfaces.workflow.config import INodeConfig, IEdgeConfig


class DefaultBuildStrategy(IBuildStrategy):
    """默认构建策略"""
    
    def can_handle(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> bool:
        """默认策略可以处理所有配置"""
        return True
    
    def execute(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Any:
        """执行默认构建逻辑"""
        return builder.build_element(config, context)
    
    def get_strategy_name(self) -> str:
        return "default_build_strategy"


class CachedBuildStrategy(IBuildStrategy):
    """缓存构建策略"""
    
    def __init__(self, cache_key_func: Optional[Callable[..., str]] = None):
        """初始化缓存构建策略
        
        Args:
            cache_key_func: 自定义缓存键生成函数
        """
        self.cache_key_func = cache_key_func
    
    def can_handle(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> bool:
        """检查是否可以使用缓存策略"""
        return True
    
    def execute(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Any:
        """执行缓存构建逻辑"""
        element_type = builder.get_element_type()
        element_name = self._get_element_name(config)
        
        # 生成缓存键
        cache_key = self._generate_cache_key(element_type, element_name, config, context)
        
        # 检查缓存
        cached_result = context.cache.get(cache_key)
        if cached_result is not None:
            if context.logger:
                context.logger.debug(f"从策略缓存获取元素: {cache_key}")
            return cached_result
        
        # 构建元素
        result = builder.build_element(config, context)
        
        # 缓存结果
        context.cache[cache_key] = result
        
        return result
    
    def _get_element_name(self, config: Union[INodeConfig, IEdgeConfig]) -> str:
        """获取元素名称"""
        if isinstance(config, INodeConfig):
            return config.name
        elif isinstance(config, IEdgeConfig):
            return f"{config.from_node}->{config.to_node}"
        else:
            return str(config)
    
    def _generate_cache_key(
        self, 
        element_type: str, 
        element_name: str, 
        config: Union[INodeConfig, IEdgeConfig],
        context: BuildContext
    ) -> str:
        """生成缓存键"""
        if self.cache_key_func:
            return self.cache_key_func(element_type, element_name, config, context)
        
        # 默认缓存键生成逻辑
        return f"{element_type}:{element_name}:{hash(str(config))}"
    
    def get_strategy_name(self) -> str:
        return "cached_build_strategy"


class FunctionResolutionBuildStrategy(IBuildStrategy):
    """函数解析构建策略"""
    
    def can_handle(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> bool:
        """检查是否可以使用函数解析策略"""
        return (
            isinstance(config, INodeConfig) or 
            (isinstance(config, IEdgeConfig) and config.type.value == "conditional")
        ) and context.function_resolver is not None
    
    def execute(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Any:
        """执行函数解析构建逻辑"""
        if isinstance(config, INodeConfig):
            return self._build_node_with_function_resolution(config, context, builder)
        elif isinstance(config, IEdgeConfig):
            return self._build_edge_with_function_resolution(config, context, builder)
        else:
            raise ValueError(f"不支持的配置类型: {type(config)}")
    
    def _build_node_with_function_resolution(
        self, 
        config: INodeConfig, 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Callable:
        """使用函数解析构建节点"""
        if isinstance(builder, INodeBuilder):
            node_function = builder.get_node_function(config, context)
            if node_function:
                return node_function
        
        # 回退到默认构建
        return builder.build_element(config, context)
    
    def _build_edge_with_function_resolution(
        self, 
        config: IEdgeConfig, 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Dict[str, Any]:
        """使用函数解析构建边"""
        edge_data = {
            "config": config,
            "condition_function": None,
            "path_map": config.path_map
        }
        
        if isinstance(builder, IEdgeBuilder):
            condition_function = builder.get_edge_function(config, context)
            if condition_function:
                edge_data["condition_function"] = condition_function
        
        return edge_data
    
    def get_strategy_name(self) -> str:
        return "function_resolution_build_strategy"


class CompositionBuildStrategy(IBuildStrategy):
    """组合构建策略"""
    
    def can_handle(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> bool:
        """检查是否可以使用组合策略"""
        return (
            isinstance(config, INodeConfig) and 
            hasattr(config, 'composition_name') and 
            bool(config.composition_name)
        )
    
    def execute(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Callable:
        """执行组合构建逻辑"""
        if not isinstance(config, INodeConfig):
            raise ValueError("CompositionBuildStrategy只支持INodeConfig")
        
        composition_name = config.composition_name
        
        # 检查是否有节点函数管理器
        if hasattr(context, 'node_function_manager') and context.node_function_manager:
            return self._create_composition_function(composition_name or "", config, context)
        
        # 回退到函数序列构建
        if hasattr(config, 'function_sequence') and config.function_sequence:
            return self._create_function_sequence_composition(config, context)
        
        # 回退到默认构建
        return builder.build_element(config, context)
    
    def _create_composition_function(
        self, 
        composition_name: str, 
        config: INodeConfig,
        context: BuildContext
    ) -> Callable:
        """创建组合函数"""
        if not hasattr(context, 'node_function_manager') or not context.node_function_manager:
            raise ValueError("节点函数管理器未设置")
        
        node_function_manager = context.node_function_manager
        
        def composition_function(state: Any) -> Any:
            return node_function_manager.execute_composition(
                composition_name, state, **config.config
            )
        
        return composition_function
    
    def _create_function_sequence_composition(
        self, 
        config: INodeConfig,
        context: BuildContext
    ) -> Callable:
        """创建函数序列组合"""
        if not context.function_resolver:
            raise ValueError("函数解析器未设置，无法创建函数序列组合")
        
        functions = []
        for func_name in config.function_sequence:
            func = context.function_resolver.get_node_function(func_name, config.__dict__)
            if not func:
                raise ValueError(f"无法找到函数: {func_name}")
            functions.append(func)
        
        def sequence_function(state: Any) -> Any:
            """函数序列执行"""
            current_state = state
            for func in functions:
                current_state = func(current_state)
            return current_state
        
        return sequence_function
    
    def get_strategy_name(self) -> str:
        return "composition_build_strategy"


class ConditionalEdgeBuildStrategy(IBuildStrategy):
    """条件边构建策略"""
    
    def can_handle(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> bool:
        """检查是否可以使用条件边策略"""
        return isinstance(config, IEdgeConfig) and config.type.value == "conditional"
    
    def execute(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Dict[str, Any]:
        """执行条件边构建逻辑"""
        if not isinstance(config, IEdgeConfig):
            raise ValueError("ConditionalEdgeBuildStrategy只支持IEdgeConfig")
        
        # 检查是否为灵活条件边
        if hasattr(config, 'is_flexible_conditional') and config.is_flexible_conditional():
            return self._build_flexible_conditional_edge(config, context, builder)
        else:
            return self._build_legacy_conditional_edge(config, context, builder)
    
    def _build_flexible_conditional_edge(
        self, 
        config: IEdgeConfig, 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Dict[str, Any]:
        """构建灵活条件边"""
        if not hasattr(context, 'flexible_edge_factory') or not context.flexible_edge_factory:
            raise ValueError("灵活条件边工厂未设置")
        
        flexible_edge_factory = context.flexible_edge_factory
        flexible_edge = flexible_edge_factory.create_from_config(config)
        route_function = flexible_edge.create_route_function()
        
        return {
            "config": config,
            "condition_function": route_function,
            "path_map": config.path_map,
            "edge_type": "flexible_conditional"
        }
    
    def _build_legacy_conditional_edge(
        self, 
        config: IEdgeConfig, 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Dict[str, Any]:
        """构建传统条件边"""
        condition_function = None
        
        if config.condition and context.function_resolver:
            condition_function = context.function_resolver.get_condition_function(config.condition)
        
        return {
            "config": config,
            "condition_function": condition_function,
            "path_map": config.path_map,
            "edge_type": "conditional"
        }
    
    def get_strategy_name(self) -> str:
        return "conditional_edge_build_strategy"


class RetryBuildStrategy(IBuildStrategy):
    """重试构建策略"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 0.1):
        """初始化重试构建策略
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def can_handle(self, config: Union[INodeConfig, IEdgeConfig], context: BuildContext) -> bool:
        """重试策略可以处理所有配置，但通常作为包装策略使用"""
        return True
    
    def execute(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Any:
        """执行重试构建逻辑"""
        last_exception: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return builder.build_element(config, context)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    if context.logger:
                        context.logger.warning(f"构建失败，正在重试 ({attempt + 1}/{self.max_retries}): {str(e)}")
                    if self.retry_delay > 0:
                        import time
                        time.sleep(self.retry_delay)
                else:
                    if context.logger:
                        context.logger.error(f"构建失败，已达到最大重试次数: {str(e)}")
        
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("构建失败但没有异常信息")
    
    def get_strategy_name(self) -> str:
        return "retry_build_strategy"


class BuildStrategyRegistry:
    """构建策略注册表"""
    
    def __init__(self):
        self._strategies: Dict[str, IBuildStrategy] = {}
        self._register_default_strategies()
    
    def register_strategy(self, strategy: IBuildStrategy) -> None:
        """注册构建策略"""
        self._strategies[strategy.get_strategy_name()] = strategy
    
    def get_strategy(self, strategy_name: str) -> Optional[IBuildStrategy]:
        """获取构建策略"""
        return self._strategies.get(strategy_name)
    
    def get_all_strategies(self) -> List[IBuildStrategy]:
        """获取所有构建策略"""
        return list(self._strategies.values())
    
    def get_applicable_strategies(
        self, 
        config: Union[INodeConfig, IEdgeConfig], 
        context: BuildContext
    ) -> List[IBuildStrategy]:
        """获取适用的构建策略"""
        applicable = []
        for strategy in self._strategies.values():
            if strategy.can_handle(config, context):
                applicable.append(strategy)
        return applicable
    
    def _register_default_strategies(self) -> None:
        """注册默认构建策略"""
        self.register_strategy(DefaultBuildStrategy())
        self.register_strategy(CachedBuildStrategy())
        self.register_strategy(FunctionResolutionBuildStrategy())
        self.register_strategy(CompositionBuildStrategy())
        self.register_strategy(ConditionalEdgeBuildStrategy())
        self.register_strategy(RetryBuildStrategy())


# 全局构建策略注册表实例
_global_strategy_registry = BuildStrategyRegistry()


def get_strategy_registry() -> BuildStrategyRegistry:
    """获取全局构建策略注册表
    
    Returns:
        BuildStrategyRegistry: 构建策略注册表实例
    """
    return _global_strategy_registry


def register_build_strategy(strategy: IBuildStrategy) -> None:
    """注册构建策略到全局注册表
    
    Args:
        strategy: 构建策略
    """
    _global_strategy_registry.register_strategy(strategy)


def create_retry_strategy(max_retries: int = 3, retry_delay: float = 0.1) -> RetryBuildStrategy:
    """创建重试策略的便捷函数
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟
        
    Returns:
        RetryBuildStrategy: 重试策略
    """
    return RetryBuildStrategy(max_retries=max_retries, retry_delay=retry_delay)


def create_cached_strategy(cache_key_func: Optional[Callable[..., str]] = None) -> CachedBuildStrategy:
    """创建缓存策略的便捷函数
    
    Args:
        cache_key_func: 自定义缓存键生成函数
        
    Returns:
        CachedBuildStrategy: 缓存策略
    """
    return CachedBuildStrategy(cache_key_func=cache_key_func)