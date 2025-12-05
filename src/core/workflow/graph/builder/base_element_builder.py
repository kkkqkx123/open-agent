"""统一元素构建器基类

提供所有元素构建器的通用实现，减少代码重复。
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union, Callable
from src.services.logger.injection import get_logger

from src.interfaces.workflow.element_builder import (
    IElementBuilder, INodeBuilder, IEdgeBuilder, 
    BuildContext, BuildResult, IValidationRule, IBuildStrategy
)
from src.core.workflow.config.config import NodeConfig, EdgeConfig


class BaseElementBuilder(IElementBuilder, ABC):
    """统一元素构建器基类
    
    提供所有元素构建器的通用功能实现。
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        enable_caching: bool = True,
        enable_validation: bool = True
    ):
        """初始化基础元素构建器
        
        Args:
            logger: 日志记录器
            enable_caching: 是否启用缓存
            enable_validation: 是否启用验证
        """
        self.logger = logger or get_logger(self.__class__.__name__)
        self.enable_caching = enable_caching
        self.enable_validation = enable_validation
        self._validation_rules: List[IValidationRule] = []
        self._build_strategies: List[IBuildStrategy] = []
        
        # 注册默认验证规则
        self._register_default_validation_rules()
        
        # 注册默认构建策略
        self._register_default_build_strategies()
    
    def build_element(
        self, 
        config: Union[NodeConfig, EdgeConfig], 
        context: BuildContext
    ) -> Any:
        """构建元素的通用实现
        
        Args:
            config: 元素配置
            context: 构建上下文
            
        Returns:
            Any: 构建的元素实例
        """
        element_name = self._get_element_name(config)
        element_type = self.get_element_type()
        
        # 检查缓存
        if self.enable_caching and self.should_cache(config):
            cached_result = context.get_cached_result(element_type, element_name)
            if cached_result is not None:
                self.logger.debug(f"从缓存获取{element_type}: {element_name}")
                context.record_build_result(BuildResult.SUCCESS, f"从缓存获取{element_type}: {element_name}")
                return cached_result
        
        try:
            # 验证配置
            if self.enable_validation:
                validation_errors = self.validate_config(config, context)
                if validation_errors:
                    error_msg = f"{element_type} {element_name} 配置验证失败: {', '.join(validation_errors)}"
                    self.logger.error(error_msg)
                    context.record_build_result(BuildResult.ERROR, error_msg)
                    raise ValueError(error_msg)
            
            # 执行构建策略
            element = self._execute_build_strategies(config, context)
            
            # 缓存结果
            if self.enable_caching and self.should_cache(config):
                context.cache_result(element_type, element_name, element)
            
            context.record_build_result(BuildResult.SUCCESS, f"成功构建{element_type}: {element_name}")
            return element
            
        except Exception as e:
            error_msg = f"构建{element_type} {element_name} 失败: {str(e)}"
            self.logger.error(error_msg)
            context.record_build_result(BuildResult.ERROR, error_msg)
            raise
    
    def validate_config(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> List[str]:
        """验证配置的通用实现
        
        Args:
            config: 元素配置
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        all_errors = []
        
        # 基础验证
        base_errors = self._validate_base_config(config, context)
        all_errors.extend(base_errors)
        
        # 执行验证规则
        for rule in self._get_sorted_validation_rules():
            try:
                rule_errors = rule.validate(config, context)
                all_errors.extend(rule_errors)
            except Exception as e:
                error_msg = f"验证规则 {rule.get_rule_name()} 执行失败: {str(e)}"
                self.logger.warning(error_msg)
                all_errors.append(error_msg)
        
        # 子类特定验证
        specific_errors = self._validate_specific_config(config, context)
        all_errors.extend(specific_errors)
        
        return all_errors
    
    def add_to_graph(
        self, 
        element: Any, 
        builder: Any, 
        config: Union[NodeConfig, EdgeConfig],
        context: BuildContext
    ) -> None:
        """将元素添加到图的通用实现
        
        Args:
            element: 构建的元素实例
            builder: LangGraph构建器
            config: 元素配置
            context: 构建上下文
        """
        element_name = self._get_element_name(config)
        element_type = self.get_element_type()
        
        try:
            self._add_element_to_graph(element, builder, config, context)
            context.record_build_result(BuildResult.SUCCESS, f"成功添加{element_type}到图: {element_name}")
        except Exception as e:
            error_msg = f"添加{element_type} {element_name} 到图失败: {str(e)}"
            self.logger.error(error_msg)
            context.record_build_result(BuildResult.ERROR, error_msg)
            raise
    
    def add_validation_rule(self, rule: IValidationRule) -> None:
        """添加验证规则
        
        Args:
            rule: 验证规则
        """
        self._validation_rules.append(rule)
        self.logger.debug(f"添加验证规则: {rule.get_rule_name()}")
    
    def add_build_strategy(self, strategy: IBuildStrategy) -> None:
        """添加构建策略
        
        Args:
            strategy: 构建策略
        """
        self._build_strategies.append(strategy)
        self.logger.debug(f"添加构建策略: {strategy.get_strategy_name()}")
    
    def _get_element_name(self, config: Union[NodeConfig, EdgeConfig]) -> str:
        """获取元素名称
        
        Args:
            config: 元素配置
            
        Returns:
            str: 元素名称
        """
        if isinstance(config, NodeConfig):
            return config.name
        elif isinstance(config, EdgeConfig):
            return f"{config.from_node}->{config.to_node}"
        else:
            return str(config)
    
    def _validate_base_config(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> List[str]:
        """基础配置验证
        
        Args:
            config: 元素配置
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not config:
            errors.append("配置不能为空")
            return errors
        
        # 检查是否可以构建
        if not self.can_build(config):
            element_type = self.get_element_type()
            errors.append(f"不支持的{element_type}配置类型")
        
        return errors
    
    def _execute_build_strategies(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> Any:
        """执行构建策略
        
        Args:
            config: 元素配置
            context: 构建上下文
            
        Returns:
            Any: 构建结果
        """
        # 查找适用的构建策略
        for strategy in self._build_strategies:
            if strategy.can_handle(config, context):
                self.logger.debug(f"使用构建策略: {strategy.get_strategy_name()}")
                return strategy.execute(config, context, self)
        
        # 如果没有适用的策略，使用默认构建方法
        self.logger.debug("使用默认构建方法")
        return self._build_element_impl(config, context)
    
    def _get_sorted_validation_rules(self) -> List[IValidationRule]:
        """获取按优先级排序的验证规则
        
        Returns:
            List[IValidationRule]: 排序后的验证规则列表
        """
        return sorted(self._validation_rules, key=lambda rule: rule.get_priority())
    
    @abstractmethod
    def _build_element_impl(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> Any:
        """构建元素的具体实现（子类必须实现）
        
        Args:
            config: 元素配置
            context: 构建上下文
            
        Returns:
            Any: 构建的元素实例
        """
        pass
    
    @abstractmethod
    def _add_element_to_graph(self, element: Any, builder: Any, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> None:
        """将元素添加到图的具体实现（子类必须实现）
        
        Args:
            element: 构建的元素实例
            builder: LangGraph构建器
            config: 元素配置
            context: 构建上下文
        """
        pass
    
    @abstractmethod
    def _validate_specific_config(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> List[str]:
        """子类特定的配置验证（子类必须实现）
        
        Args:
            config: 元素配置
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    def _register_default_validation_rules(self) -> None:
        """注册默认验证规则（子类可以重写）"""
        pass
    
    def _register_default_build_strategies(self) -> None:
        """注册默认构建策略（子类可以重写）"""
        pass


class BaseNodeBuilder(BaseElementBuilder, INodeBuilder):
    """基础节点构建器
    
    为所有节点构建器提供通用功能。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "node"
    
    def can_build(self, config: Union[NodeConfig, EdgeConfig]) -> bool:
        """检查是否可以构建节点"""
        return isinstance(config, NodeConfig)
    
    def get_supported_config_types(self) -> List[type]:
        """获取支持的配置类型"""
        return [NodeConfig]
    
    def get_node_function(
        self, 
        config: NodeConfig, 
        context: BuildContext
    ) -> Optional[Callable]:
        """获取节点函数的默认实现
        
        Args:
            config: 节点配置
            context: 构建上下文
            
        Returns:
            Optional[Callable]: 节点函数
        """
        if not context.function_resolver:
            self.logger.warning("函数解析器未设置，无法获取节点函数")
            return None
        
        function_name = config.function_name
        node_function = context.function_resolver.get_node_function(function_name, config.__dict__)
        
        if node_function:
            # 包装节点函数
            wrapped_function = self.wrap_node_function(node_function, config, context)
            return wrapped_function
        
        return None
    
    def wrap_node_function(
        self, 
        function: Callable, 
        config: NodeConfig,
        context: BuildContext
    ) -> Callable:
        """包装节点函数的默认实现
        
        Args:
            function: 原始节点函数
            config: 节点配置
            context: 构建上下文
            
        Returns:
            Callable: 包装后的函数
        """
        # 如果有状态管理器，添加状态管理包装
        if context.state_manager:
            function = self._wrap_with_state_management(function, config, context)
        
        # 可以添加其他包装逻辑，如迭代管理、监控等
        return function
    
    def _wrap_with_state_management(
        self, 
        function: Callable, 
        config: NodeConfig,
        context: BuildContext
    ) -> Callable:
        """使用状态管理包装函数
        
        Args:
            function: 原始函数
            config: 节点配置
            context: 构建上下文
            
        Returns:
            Callable: 包装后的函数
        """
        def state_wrapped_function(state: Any) -> Any:
            """状态管理包装的节点函数"""
            if context.state_manager:
                return context.state_manager.execute_with_state(
                    config.name, function, state
                )
            return function(state)
        
        return state_wrapped_function

    def _build_element_impl(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> Any:
        """构建节点元素的具体实现
        
        Args:
            config: 节点配置
            context: 构建上下文
            
        Returns:
            Any: 构建的节点函数
        """
        if isinstance(config, NodeConfig):
            # 获取节点函数
            node_function = self.get_node_function(config, context)
            if node_function:
                return node_function
            else:
                # 如果无法获取函数，返回一个默认函数
                def default_node_function(state):
                    self.logger.warning(f"无法获取节点 {config.name} 的函数，使用默认函数")
                    return state
                return default_node_function
        else:
            raise ValueError(f"节点构建器无法处理非节点配置: {type(config)}")
    
    def _add_element_to_graph(self, element: Any, builder: Any, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> None:
        """将节点添加到图
        
        Args:
            element: 节点函数
            builder: LangGraph构建器
            config: 节点配置
            context: 构建上下文
        """
        if isinstance(config, NodeConfig):
            builder.add_node(config.name, element)
    
    def _validate_specific_config(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> List[str]:
        """节点特定的配置验证
        
        Args:
            config: 节点配置
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if isinstance(config, NodeConfig):
            if not config.name:
                errors.append("节点名称不能为空")
            
            if not config.function_name:
                errors.append("节点函数名称不能为空")
        
        return errors


class BaseEdgeBuilder(BaseElementBuilder, IEdgeBuilder):
    """基础边构建器
    
    为所有边构建器提供通用功能。
    """
    
    def get_element_type(self) -> str:
        """获取元素类型"""
        return "edge"
    
    def can_build(self, config: Union[NodeConfig, EdgeConfig]) -> bool:
        """检查是否可以构建边"""
        return isinstance(config, EdgeConfig)
    
    def get_supported_config_types(self) -> List[type]:
        """获取支持的配置类型"""
        return [EdgeConfig]
    
    def get_edge_function(
        self, 
        config: EdgeConfig, 
        context: BuildContext
    ) -> Optional[Callable]:
        """获取边函数的默认实现
        
        Args:
            config: 边配置
            context: 构建上下文
            
        Returns:
            Optional[Callable]: 边函数
        """
        if not context.function_resolver:
            self.logger.warning("函数解析器未设置，无法获取边函数")
            return None
        
        if config.condition:
            condition_function = context.function_resolver.get_condition_function(config.condition)
            return condition_function
        
        return None
    
    def _add_element_to_graph(self, element: Any, builder: Any, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> None:
        """将边添加到图
        
        Args:
            element: 边函数
            builder: LangGraph构建器
            config: 边配置
            context: 构建上下文
        """
        if isinstance(config, EdgeConfig):
            if element:
                builder.add_conditional_edges(config.from_node, element)
            else:
                builder.add_edge(config.from_node, config.to_node)
    
    def _build_element_impl(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> Any:
        """构建边元素的具体实现
        
        Args:
            config: 边配置
            context: 构建上下文
            
        Returns:
            Any: 构建的边函数
        """
        if isinstance(config, EdgeConfig):
            # 获取边函数（主要用于条件边）
            edge_function = self.get_edge_function(config, context)
            if edge_function:
                return edge_function
            else:
                # 如果是简单边，返回 None（表示直接连接）
                if config.type.value == "simple":
                    return None
                else:
                    # 如果无法获取条件函数，返回默认函数
                    def default_edge_function(state):
                        self.logger.warning(f"无法获取边 {config.from_node}->{config.to_node} 的函数，使用默认函数")
                        return config.to_node  # 简单返回目标节点
                    return default_edge_function
        else:
            raise ValueError(f"边构建器无法处理非边配置: {type(config)}")
    
    def _validate_specific_config(self, config: Union[NodeConfig, EdgeConfig], context: BuildContext) -> List[str]:
        """边特定的配置验证
        
        Args:
            config: 边配置
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if isinstance(config, EdgeConfig):
            if not config.from_node:
                errors.append("边起始节点不能为空")
            
            if config.type.value == "simple" and not config.to_node:
                errors.append("简单边必须指定目标节点")
            
            if config.type.value == "conditional" and not config.condition and not hasattr(config, 'route_function'):
                errors.append("条件边必须指定条件表达式或路由函数")
        
        return errors
