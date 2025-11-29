"""统一图构建器

集成所有功能的统一图构建器，包含基础构建、函数注册表集成和迭代管理功能。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING, cast, Protocol
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
else:
    # 运行时使用Dict作为RunnableConfig的替代
    RunnableConfig = Dict[str, Any]

from src.core.workflow.config.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.core.state import WorkflowState
from src.core.workflow.graph.registry import NodeRegistry, get_global_registry
from src.interfaces.state import IStateLifecycleManager


class FunctionRegistryProtocol(Protocol):
    """函数注册表协议，用于类型检查"""
    
    def get_node_function(self, name: str) -> Optional[Callable]: ...
    def get_condition_function(self, name: str) -> Optional[Callable]: ...

logger = logging.getLogger(__name__)

# 导入LangGraph核心组件
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 导入灵活条件边相关组件
from src.core.workflow.graph.edges.flexible_edge import FlexibleConditionalEdgeFactory


class INodeExecutor(ABC):
    """节点执行器接口"""
    
    @abstractmethod
    def execute(self, node_config: NodeConfig, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """执行节点
        
        Args:
            node_config: 节点配置
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        pass


class GraphBuilder:
    """统一图构建器
    
    集成所有功能的图构建器，支持灵活条件边。
    """
    
    # 属性类型注解
    node_registry: NodeRegistry
    function_registry: Optional[FunctionRegistryProtocol]
    template_registry: Optional[Any]
    enable_function_fallback: bool
    enable_iteration_management: bool
    _checkpointer_cache: Dict[str, Any]
    iteration_manager: Optional[Any]
    route_function_manager: Optional[Any]
    flexible_edge_factory: Optional[FlexibleConditionalEdgeFactory]
    node_function_manager: Optional[Any]
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistryProtocol] = None,
        enable_function_fallback: bool = True,
        enable_iteration_management: bool = True,
        route_function_config_dir: Optional[str] = None,
        node_function_config_dir: Optional[str] = None,
    ) -> None:
        """初始化统一图构建器
        
        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退机制
            enable_iteration_management: 是否启用迭代管理
            route_function_config_dir: 路由函数配置目录
            node_function_config_dir: 节点函数配置目录
        """
        self.node_registry = node_registry or get_global_registry()
        
        # 延迟导入FunctionRegistry避免循环依赖
        if function_registry is not None:
            self.function_registry = function_registry
        else:
            try:
                from src.services.workflow.function_registry import get_global_function_registry
                self.function_registry = get_global_function_registry()
            except ImportError:
                logger.warning("无法导入FunctionRegistry，将不使用函数注册表")
                self.function_registry = None
        self.template_registry: Optional[Any] = None  # 添加缺失的属性，允许任意类型
        self.enable_function_fallback = enable_function_fallback
        self.enable_iteration_management = enable_iteration_management
        self._checkpointer_cache: Dict[str, Any] = {}
        self.iteration_manager: Optional[Any] = None  # IterationManager
        
        # 初始化路由函数管理器 (可选)
        if route_function_config_dir:
            try:
                from src.core.workflow.graph.route_functions import get_route_function_manager
                self.route_function_manager = get_route_function_manager(route_function_config_dir)
                self.flexible_edge_factory = FlexibleConditionalEdgeFactory(self.route_function_manager)
            except ImportError:
                logger.warning("无法导入路由函数管理器，将不使用灵活条件边功能")
                self.route_function_manager = None
                self.flexible_edge_factory = None
        else:
            self.route_function_manager = None
            self.flexible_edge_factory = None
        
        # 初始化节点函数管理器 (可选)
        if node_function_config_dir:
            try:
                from src.core.workflow.graph.node_functions import get_node_function_manager
                self.node_function_manager = get_node_function_manager(node_function_config_dir)
            except ImportError:
                logger.warning("无法导入节点函数管理器，将不使用节点函数组合功能")
                self.node_function_manager = None
        else:
            self.node_function_manager = None
        
        logger.debug(f"统一图构建器初始化完成，函数回退: {enable_function_fallback}, 迭代管理: {enable_iteration_management}")
    
    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateLifecycleManager] = None) -> Any:
        """构建LangGraph图
        
        Args:
            config: 图配置
            state_manager: 状态管理器
            
        Returns:
            编译后的LangGraph图
        """
        # 验证配置
        errors = config.validate()
        if errors:
            raise ValueError(f"图配置验证失败: {errors}")
        
        # 如果启用迭代管理，创建迭代管理器
        if self.enable_iteration_management:
            self.iteration_manager = self._create_iteration_manager(config)
        else:
            self.iteration_manager = None
        
        # 获取状态类
        state_class = config.get_state_class()
        
        # 创建StateGraph
        from langgraph.graph import StateGraph
        # 使用Any类型来避免类型检查问题，因为状态类是动态生成的
        builder = StateGraph(cast(Any, state_class))
        
        # 添加节点
        self._add_nodes(builder, config, state_manager)
        
        # 添加边
        self._add_edges(builder, config)
        
        # 设置入口点
        if config.entry_point:
            from langgraph.graph import START
            builder.add_edge(START, config.entry_point)
        
        # 编译图
        compiled_graph = builder.compile()
        
        logger.debug(f"图构建完成: {config.name}")
        return compiled_graph
    
    def _add_nodes(self, builder: Any, config: GraphConfig, state_manager: Optional[IStateLifecycleManager] = None) -> None:
        """添加节点到图
        
        Args:
            builder: LangGraph构建器
            config: 图配置
            state_manager: 状态管理器
        """
        for node_name, node_config in config.nodes.items():
            node_function = self._get_node_function(node_config, state_manager)
            if node_function:
                builder.add_node(node_name, node_function)
                logger.debug(f"添加节点: {node_name}")
            else:
                logger.warning(f"无法找到节点函数: {node_config.function_name}")
    
    def _add_edges(self, builder: Any, config: GraphConfig) -> None:
        """添加边到图
        
        Args:
            builder: LangGraph构建器
            config: 图配置
        """
        for edge in config.edges:
            if edge.type == EdgeType.SIMPLE:
                self._add_simple_edge(builder, edge)
            elif edge.type == EdgeType.CONDITIONAL:
                self._add_conditional_edge(builder, edge)
            
            logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")
    
    def _add_simple_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加简单边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        from langgraph.graph import END
        
        if edge.to_node == "__end__":
            builder.add_edge(edge.from_node, END)
        else:
            builder.add_edge(edge.from_node, edge.to_node)
    
    def _add_conditional_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加条件边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        try:
            # 检查是否为灵活条件边
            if edge.is_flexible_conditional():
                self._add_flexible_conditional_edge(builder, edge)
            else:
                # 传统条件边
                self._add_legacy_conditional_edge(builder, edge)
        except Exception as e:
            logger.error(f"添加条件边失败 {edge.from_node} -> {edge.to_node}: {e}")
            raise
    
    def _add_flexible_conditional_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加灵活条件边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        try:
            # 检查是否有灵活条件边工厂
            if self.flexible_edge_factory:
                # 创建灵活条件边
                flexible_edge = self.flexible_edge_factory.create_from_config(edge)
                
                # 创建路由函数
                route_function = flexible_edge.create_route_function()
                
                # 添加条件边
                if edge.path_map:
                    builder.add_conditional_edges(
                        edge.from_node,
                        route_function,
                        path_map=edge.path_map
                    )
                else:
                    builder.add_conditional_edges(edge.from_node, route_function)
                     
                logger.debug(f"添加灵活条件边: {edge.from_node}")
            else:
                logger.warning(f"灵活条件边工厂未初始化，跳过灵活条件边: {edge.from_node}")
                # 回退到传统条件边
                self._add_legacy_conditional_edge(builder, edge)
            
        except Exception as e:
            logger.error(f"创建灵活条件边失败: {e}")
            raise
    
    def _add_legacy_conditional_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加传统条件边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        if edge.condition is not None:
            condition_function = self._get_condition_function(edge.condition)
            if condition_function:
                if edge.path_map:
                    builder.add_conditional_edges(
                        edge.from_node, 
                        condition_function,
                        path_map=edge.path_map
                    )
                else:
                    builder.add_conditional_edges(edge.from_node, condition_function)
            else:
                logger.warning(f"无法找到条件函数: {edge.condition}")
        else:
            logger.warning(f"条件边缺少条件表达式: {edge.from_node} -> {edge.to_node}")
    
    def _get_node_function(
        self,
        node_config: NodeConfig,
        state_manager: Optional[IStateLifecycleManager] = None,
    ) -> Optional[Callable]:
        """获取节点函数（统一实现）
        
        优先级：节点内部函数组合 -> 函数注册表 -> 节点注册表 -> 内置函数 -> 父类方法
        
        Args:
            node_config: 节点配置
            state_manager: 状态管理器
            
        Returns:
            Optional[Callable]: 节点函数
        """
        function_name = node_config.function_name
        
        # 0. 检查是否为节点内部函数组合
        if hasattr(node_config, 'composition_name') and node_config.composition_name:
            composition_function = self._create_composition_function(node_config.composition_name)
            if composition_function:
                logger.debug(f"从节点内部函数组合获取节点函数: {node_config.composition_name}")
                return self._wrap_node_function(composition_function, state_manager, node_config.name)
        
        # 1. 优先从函数注册表获取
        if self.function_registry and hasattr(self.function_registry, 'get_node_function'):
            node_function = self.function_registry.get_node_function(function_name)
            if node_function:
                logger.debug(f"从函数注册表获取节点函数: {function_name}")
                return self._wrap_node_function(node_function, state_manager, node_config.name)
        
        # 2. 尝试从节点注册表获取
        if self.node_registry:
            try:
                node_class = self.node_registry.get_node_class(function_name)
                if node_class:
                    node_instance = node_class()
                    logger.debug(f"从节点注册表获取节点函数: {function_name}")
                    return self._wrap_node_function(
                        node_instance.execute, state_manager, node_config.name
                    )
            except ValueError:
                # 节点类型不存在，继续尝试其他方法
                pass
        
        # 3. 尝试从模板注册表获取
        if hasattr(self, 'template_registry') and self.template_registry:
            template = self.template_registry.get_template(function_name)
            if template and hasattr(template, 'get_node_function'):
                node_function = template.get_node_function()
                if node_function:
                    logger.debug(f"从模板注册表获取节点函数: {function_name}")
                    return self._wrap_node_function(node_function, state_manager, node_config.name)
        
        # 4. 尝试从内置函数获取
        builtin_function = self._get_builtin_node_function(function_name)
        if builtin_function:
            logger.debug(f"从内置函数获取节点函数: {function_name}")
            return self._wrap_node_function(builtin_function, state_manager, node_config.name)
        
        # 5. 如果启用回退，尝试内置实现
        if self.enable_function_fallback:
            builtin_functions = {
                "llm_node": self._create_llm_node,
                "tool_node": self._create_tool_node,
                "analysis_node": self._create_analysis_node,
                "condition_node": self._create_condition_node,
                "wait_node": self._create_wait_node,
            }
            fallback_function = builtin_functions.get(function_name)
            if fallback_function:
                logger.debug(f"从内置回退函数获取节点函数: {function_name}")
                return self._wrap_node_function(fallback_function, state_manager, node_config.name)
        
        logger.warning(f"无法找到节点函数: {function_name}")
        return None
    
    def _create_composition_function(self, composition_name: str) -> Optional[Callable]:
        """创建节点内部函数组合函数
        
        Args:
            composition_name: 组合名称
            
        Returns:
            Optional[Callable]: 组合函数，如果不存在返回None
        """
        # 检查是否有节点函数管理器
        if self.node_function_manager and hasattr(self.node_function_manager, 'has_composition') and self.node_function_manager.has_composition(composition_name):
            def composition_function(state: WorkflowState, **kwargs) -> WorkflowState:
                return self.node_function_manager.execute_composition(composition_name, state, **kwargs)
            return composition_function
        return None
    
    def _get_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取条件函数（统一实现）
        
        优先级：路由函数管理器 -> 函数注册表 -> 内置条件 -> 父类方法
        
        Args:
            condition_name: 条件函数名称
            
        Returns:
            Optional[Callable]: 条件函数
        """
        # 1. 优先从路由函数管理器获取
        if self.route_function_manager:
            route_function = self.route_function_manager.get_route_function(condition_name)
            if route_function:
                logger.debug(f"从路由函数管理器获取条件函数: {condition_name}")
                return route_function
        
        # 2. 尝试从函数注册表获取
        if self.function_registry and hasattr(self.function_registry, 'get_condition_function'):
            condition_function = self.function_registry.get_condition_function(
                condition_name
            )
            if condition_function:
                logger.debug(f"从函数注册表获取条件函数: {condition_name}")
                return condition_function
        
        # 3. 尝试从内置函数获取
        builtin_function = self._get_builtin_condition_function(condition_name)
        if builtin_function:
            logger.debug(f"从内置函数获取条件函数: {condition_name}")
            return builtin_function
        
        # 4. 如果启用回退，尝试内置实现
        if self.enable_function_fallback:
            builtin_conditions = {
                "has_tool_calls": self._condition_has_tool_calls,
                "needs_more_info": self._condition_needs_more_info,
                "is_complete": self._condition_is_complete,
            }
            fallback_function = builtin_conditions.get(condition_name)
            if fallback_function:
                logger.debug(f"从内置回退函数获取条件函数: {condition_name}")
                return fallback_function
        
        logger.warning(f"无法找到条件函数: {condition_name}")
        return None
    
    def _wrap_node_function(
        self,
        function: Callable,
        state_manager: Optional[IStateLifecycleManager] = None,
        node_name: str = "unknown",
    ) -> Callable:
        """包装节点函数以支持状态管理和迭代管理
        
        Args:
            function: 原始节点函数
            state_manager: 状态管理器
            node_name: 节点名称
            
        Returns:
            Callable: 包装后的函数
        """
        # 首先包装状态管理
        if state_manager is not None:
            # 如果有状态管理器，使用增强的执行器包装
            try:
                # 尝试导入协作适配器
                collaboration_adapter_path = "src.adapters.workflow.collaboration_adapter"
                try:
                    from src.adapters.workflow.collaboration_adapter import CollaborationStateAdapter
                    
                    def state_wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
                        """状态管理包装的节点函数"""
                        collaboration_adapter = CollaborationStateAdapter(state_manager)
                        
                        def node_executor(domain_state: Any) -> Any:
                            """节点执行函数"""
                            # 将域状态转换为图状态
                            temp_graph_state = collaboration_adapter.state_adapter.to_graph_state(domain_state)
                            # 执行原始函数
                            result = function(temp_graph_state)
                            # 将结果转换回域状态
                            return collaboration_adapter.state_adapter.from_graph_state(result)
                        
                        # 使用协作适配器执行
                        return collaboration_adapter.execute_with_collaboration(state, node_executor)
                    
                    wrapped_function = state_wrapped_function
                except ImportError:
                    logger.warning(f"无法导入协作适配器从 {collaboration_adapter_path}，使用简化的状态包装")
                    raise ImportError()
                    
            except ImportError:
                logger.warning("使用简化的状态包装")
                def state_wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
                    """简化的状态管理包装的节点函数"""
                    def node_executor(domain_state: Any) -> Any:
                        """节点执行函数"""
                        # 执行原始函数
                        result = function(domain_state)
                        return result
                    
                    return node_executor(state)
                
                wrapped_function = state_wrapped_function
        else:
            # 如果没有状态管理器，直接使用原函数
            wrapped_function = function
        
        # 然后包装迭代管理（如果启用）
        if self.enable_iteration_management and self.iteration_manager is not None:
            # 使用类型断言确保iteration_manager不是None
            iteration_manager = self.iteration_manager
            
            def iteration_wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
                """迭代管理包装的节点函数"""
                # 记录开始时间
                start_time = datetime.now()
                
                try:
                    # 检查迭代限制
                    if not iteration_manager.check_limits(state, node_name):
                        logger.info(f"节点 {node_name} 达到迭代限制，提前终止")
                        # 返回表明工作流已完成的状态
                        completed_state = dict(state)
                        completed_state['complete'] = True
                        return completed_state

                    # 执行包装函数
                    result = wrapped_function(state)
                    
                    # 确保结果是字典格式
                    if not isinstance(result, dict):
                        # 如果结果不是字典，尝试将其转换为字典
                        if hasattr(result, '__dict__'):
                            result = result.__dict__
                        else:
                            # 如果无法转换，则使用原始状态
                            result = state
                    
                    # 记录结束时间
                    end_time = datetime.now()
                    
                    # 更新迭代计数
                    # 确保结果中包含原始状态信息
                    if isinstance(state, dict) and isinstance(result, dict):
                        updated_result = {**state, **result}  # 合并原始状态和结果
                    else:
                        updated_result = result
                    
                    updated_result = iteration_manager.record_and_increment(
                        updated_result,
                        node_name,
                        start_time,
                        end_time,
                        status='SUCCESS'
                    )
                    
                    return updated_result
                    
                except Exception as e:
                    logger.error(f"节点 {node_name} 执行失败: {e}")
                    
                    # 记录结束时间
                    end_time = datetime.now()
                    
                    # 即使出错也要记录迭代
                    error_result = dict(state)
                    error_result = iteration_manager.record_and_increment(
                        error_result,
                        node_name,
                        start_time,
                        end_time,
                        status='FAILURE',
                        error=str(e)
                    )
                    
                    # 添加错误信息到状态
                    errors = error_result.get('errors', [])
                    errors.append(f"节点 {node_name} 执行失败: {str(e)}")
                    error_result['errors'] = errors
                    
                    return error_result
            
            return iteration_wrapped_function
        else:
            # 如果不启用迭代管理，直接返回状态包装的函数
            return wrapped_function
    
    def _get_checkpointer(self, config: GraphConfig) -> Optional[Any]:
        """获取检查点
        
        Args:
            config: 图配置
            
        Returns:
            Optional[Any]: 检查点实例
        """
        if not config.checkpointer:
            return None
        
        if config.checkpointer in self._checkpointer_cache:
            return self._checkpointer_cache[config.checkpointer]
        
        checkpointer: Any = None
        if config.checkpointer == "memory":
            from langgraph.checkpoint.memory import InMemorySaver
            checkpointer = InMemorySaver()
        elif config.checkpointer.startswith("sqlite:"):
            # sqlite:/path/to/db.sqlite
            from langgraph.checkpoint.sqlite import SqliteSaver
            db_path = config.checkpointer[7:]  # 移除 "sqlite:" 前缀
            checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")
        
        if checkpointer:
            self._checkpointer_cache[config.checkpointer] = checkpointer
        
        return checkpointer
    
    # 内置节点函数实现
    def _create_llm_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建LLM节点"""
        logger.debug("执行LLM节点")
        
        # 检查是否有消息需要处理
        messages = state.get("messages", [])
        if not messages:
            logger.warning("LLM节点没有收到消息")
            return state
        
        # 获取最后一条消息
        last_message = messages[-1]
        
        # 如果最后一条消息已经是AI回复，则不需要再次调用LLM
        if hasattr(last_message, 'type') and last_message.type == 'ai':
            logger.debug("最后一条消息已经是AI回复，跳过LLM调用")
            return state
        
        try:
            # 尝试获取LLM客户端
            try:
                from src.services.container import get_global_container
                container = get_global_container()
                
                # 检查容器是否有LLM管理器
                if hasattr(container, 'is_registered') and container.is_registered("llm_manager"):
                    llm_manager = container.resolve("llm_manager")
                    
                    # 调用LLM
                    response = llm_manager.generate_response(
                        messages=messages,
                        config=config
                    )
                    
                    # 将响应添加到消息列表
                    updated_messages = messages + [response]
                    state["messages"] = updated_messages
                    
                    logger.debug(f"LLM节点成功生成响应")
                else:
                    logger.warning("LLM管理器未注册，使用模拟响应")
                    # 模拟响应
                    from langchain_core.messages import AIMessage
                    mock_response = AIMessage(content="这是一个模拟的LLM响应")
                    state["messages"] = messages + [mock_response]
            except (ImportError, AttributeError) as e:
                logger.warning(f"无法访问容器或LLM管理器: {e}，使用模拟响应")
                # 模拟响应
                from langchain_core.messages import AIMessage
                mock_response = AIMessage(content="这是一个模拟的LLM响应")
                state["messages"] = messages + [mock_response]
                
        except Exception as e:
            logger.error(f"LLM节点执行失败: {e}")
            # 添加错误信息到状态
            errors = state.get("errors", [])
            errors.append(f"LLM节点执行失败: {str(e)}")
            state["errors"] = errors
        
        return state
    
    def _create_tool_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建工具节点"""
        logger.debug("执行工具节点")
        
        # 检查是否有工具调用
        messages = state.get("messages", [])
        if not messages:
            logger.warning("工具节点没有收到消息")
            return state
        
        last_message = messages[-1]
        
        # 检查是否有工具调用
        tool_calls = getattr(last_message, 'tool_calls', None)
        if not tool_calls:
            logger.debug("没有工具调用需要执行")
            return state
        
        try:
            # 尝试获取工具管理器
            try:
                from src.services.container import get_global_container
                container = get_global_container()
                
                # 检查容器是否有工具管理器
                if hasattr(container, 'is_registered') and container.is_registered("tool_manager"):
                    tool_manager = container.resolve("tool_manager")
                    
                    # 执行工具调用
                    tool_results = []
                    for tool_call in tool_calls:
                        try:
                            result = tool_manager.execute_tool(
                                tool_name=tool_call["name"],
                                tool_args=tool_call["args"],
                                tool_call_id=tool_call["id"]
                            )
                            tool_results.append(result)
                        except Exception as e:
                            logger.error(f"工具调用失败 {tool_call['name']}: {e}")
                            # 创建错误结果
                            from langchain_core.messages import ToolMessage
                            error_result = ToolMessage(
                                content=f"工具执行失败: {str(e)}",
                                tool_call_id=tool_call["id"]
                            )
                            tool_results.append(error_result)
                    
                    # 将工具结果添加到消息列表
                    state["messages"] = messages + tool_results
                    logger.debug(f"工具节点成功执行 {len(tool_results)} 个工具调用")
                else:
                    logger.warning("工具管理器未注册，使用模拟工具响应")
                    # 模拟工具响应
                    from langchain_core.messages import ToolMessage
                    mock_results = []
                    for tool_call in tool_calls:
                        mock_result = ToolMessage(
                            content=f"模拟工具 {tool_call['name']} 的执行结果",
                            tool_call_id=tool_call["id"]
                        )
                        mock_results.append(mock_result)
                    state["messages"] = messages + mock_results
            except (ImportError, AttributeError) as e:
                logger.warning(f"无法访问容器或工具管理器: {e}，使用模拟工具响应")
                # 模拟工具响应
                from langchain_core.messages import ToolMessage
                mock_results = []
                for tool_call in tool_calls:
                    mock_result = ToolMessage(
                        content=f"模拟工具 {tool_call['name']} 的执行结果",
                        tool_call_id=tool_call["id"]
                    )
                    mock_results.append(mock_result)
                state["messages"] = messages + mock_results
                
        except Exception as e:
            logger.error(f"工具节点执行失败: {e}")
            # 添加错误信息到状态
            errors = state.get("errors", [])
            errors.append(f"工具节点执行失败: {str(e)}")
            state["errors"] = errors
        
        return state
    
    def _create_analysis_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建分析节点"""
        logger.debug("执行分析节点")
        
        # 分析消息内容
        messages = state.get("messages", [])
        if not messages:
            logger.warning("分析节点没有收到消息")
            return state
        
        try:
            # 简单的分析逻辑
            analysis_result = {
                "message_count": len(messages),
                "last_message_type": getattr(messages[-1], 'type', 'unknown'),
                "has_tool_calls": bool(getattr(messages[-1], 'tool_calls', None)),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # 将分析结果添加到状态
            state["analysis"] = analysis_result
            logger.debug(f"分析节点完成分析: {analysis_result}")
            
        except Exception as e:
            logger.error(f"分析节点执行失败: {e}")
            # 添加错误信息到状态
            errors = state.get("errors", [])
            errors.append(f"分析节点执行失败: {str(e)}")
            state["errors"] = errors
        
        return state
    
    def _create_condition_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建条件节点"""
        logger.debug("执行条件节点")
        
        try:
            # 简单的条件评估逻辑
            messages = state.get("messages", [])
            
            # 评估条件
            conditions = {
                "has_messages": len(messages) > 0,
                "last_is_ai": len(messages) > 0 and getattr(messages[-1], 'type', None) == 'ai',
                "has_tool_calls": len(messages) > 0 and bool(getattr(messages[-1], 'tool_calls', None)),
                "has_errors": bool(state.get("errors")),
                "is_complete": state.get("complete", False)
            }
            
            # 将条件结果添加到状态
            state["conditions"] = conditions
            logger.debug(f"条件节点完成条件评估: {conditions}")
            
        except Exception as e:
            logger.error(f"条件节点执行失败: {e}")
            # 添加错误信息到状态
            errors = state.get("errors", [])
            errors.append(f"条件节点执行失败: {str(e)}")
            state["errors"] = errors
        
        return state
    
    def _create_wait_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建等待节点"""
        logger.debug("执行等待节点")
        
        try:
            # 简单的等待逻辑
            import time
            
            # 获取等待时间（默认1秒）
            wait_time = state.get("wait_time", 1)
            if isinstance(wait_time, str):
                try:
                    wait_time = float(wait_time)
                except ValueError:
                    wait_time = 1
            
            logger.debug(f"等待节点等待 {wait_time} 秒")
            time.sleep(wait_time)
            
            # 记录等待完成
            state["wait_completed"] = True
            state["wait_timestamp"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"等待节点执行失败: {e}")
            # 添加错误信息到状态
            errors = state.get("errors", [])
            errors.append(f"等待节点执行失败: {str(e)}")
            state["errors"] = errors
        
        return state
    
    # 内置条件函数实现
    def _condition_has_tool_calls(self, state: WorkflowState) -> str:
        """检查是否有工具调用"""
        # 优先使用messages属性
        if hasattr(state, 'messages'):
            messages = state.messages
        else:
            messages = state.get("messages", [])
        
        if not messages:
            return "end"

        last_message = messages[-1]
        
        # 处理字典格式的消息
        if isinstance(last_message, dict):
            # 检查字典中的tool_calls字段
            if last_message.get("tool_calls"):
                return "continue"
            
            # 检查消息内容
            content = str(last_message.get("content", ""))
            return "continue" if "tool_call" in content.lower() or "调用工具" in content else "end"
        
        # 处理LangChain消息对象
        # 检查LangChain消息的tool_calls属性
        if hasattr(last_message, 'tool_calls'):
            tool_calls = getattr(last_message, 'tool_calls', None)
            if tool_calls and len(tool_calls) > 0:
                logger.debug(f"发现工具调用: {tool_calls}")
                return "continue"

        # 检查消息的metadata中的tool_calls
        if hasattr(last_message, 'metadata'):
            metadata = getattr(last_message, 'metadata', {})
            if isinstance(metadata, dict) and metadata.get("tool_calls"):
                return "continue"

        # 检查消息内容
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', ''))
            return "continue" if "tool_call" in content.lower() or "调用工具" in content else "end"

        return "end"

    def _condition_needs_more_info(self, state: WorkflowState) -> str:
        """检查是否需要更多信息"""
        messages = state.get("messages", [])
        
        if not messages:
            return "continue"
        
        last_message = messages[-1]
        
        # 检查最后一条消息是否是AI回复且包含问题
        if hasattr(last_message, 'type') and last_message.type == 'ai':
            content = getattr(last_message, 'content', '')
            
            # 简单的启发式：如果内容包含问号或特定关键词，可能需要更多信息
            question_indicators = ['?', '？', '需要', '请提供', '告诉我', '什么是', '如何']
            if any(indicator in content for indicator in question_indicators):
                return "continue"
        
        # 检查是否有错误
        if state.get("errors"):
            return "continue"
        
        # 检查是否标记为完成
        if state.get("complete", False):
            return "end"
        
        return "continue"

    def _condition_is_complete(self, state: WorkflowState) -> str:
         """检查是否完成"""
         # 检查是否明确标记为完成
         if state.get("complete", False):
             return "end"
         
         # 检查是否有错误
         if state.get("errors"):
             return "error"
         
         # 检查消息数量（简单启发式）
         messages = state.get("messages", [])
         if len(messages) >= 10:  # 假设10条消息后认为可以结束
             return "end"
         
         # 检查最后一条消息是否是结束信号
         if messages:
             last_message = messages[-1]
             if hasattr(last_message, 'content'):
                 content = getattr(last_message, 'content', '')
                 end_indicators = ['结束', '完成', 'finish', 'done', '结束对话']
                 if any(indicator in content.lower() for indicator in end_indicators):
                     return "end"
         
         return "continue"
    
    def _create_iteration_manager(self, config: GraphConfig) -> Any:
        """创建迭代管理器
        
        Args:
            config: 图配置
            
        Returns:
            迭代管理器实例
        """
        # 简化的迭代管理器实现
        class SimpleIterationManager:
            def __init__(self, config: GraphConfig):
                self.config = config
                self.max_iterations = getattr(config, 'max_iterations', 100)
                self.iteration_counts: Dict[str, int] = {}
                self.iteration_records: List[Dict[str, Any]] = []
            
            def check_limits(self, state: Any, node_name: str) -> bool:
                """检查迭代限制"""
                current_count = self.iteration_counts.get(node_name, 0)
                return current_count < self.max_iterations
            
            def record_and_increment(self, state: Dict[str, Any], node_name: str,
                                   start_time: datetime, end_time: datetime,
                                   status: str = 'SUCCESS') -> Dict[str, Any]:
                """记录并增加迭代计数"""
                self.iteration_counts[node_name] = self.iteration_counts.get(node_name, 0) + 1
                
                record = {
                    'node_name': node_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'status': status,
                    'iteration_count': self.iteration_counts[node_name],
                    'duration': (end_time - start_time).total_seconds()
                }
                
                self.iteration_records.append(record)
                return state
        
        return SimpleIterationManager(config)
    
    def _get_builtin_node_function(self, function_name: str) -> Optional[Callable]:
        """获取内置节点函数
        
        Args:
            function_name: 函数名称
            
        Returns:
            Optional[Callable]: 节点函数
        """
        # 简化的内置函数实现
        builtin_functions = {
            "start_node": self._builtin_start_node,
            "end_node": self._builtin_end_node,
            "passthrough_node": self._builtin_passthrough_node,
        }
        return builtin_functions.get(function_name)
    
    def _get_builtin_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取内置条件函数
        
        Args:
            condition_name: 条件函数名称
            
        Returns:
            Optional[Callable]: 条件函数
        """
        # 简化的内置条件函数实现
        builtin_conditions = {
            "always_true": self._builtin_always_true,
            "always_false": self._builtin_always_false,
            "has_messages": self._builtin_has_messages,
        }
        return builtin_conditions.get(condition_name)
    
    def _builtin_start_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """内置开始节点"""
        logger.debug("执行内置开始节点")
        return state
    
    def _builtin_end_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """内置结束节点"""
        logger.debug("执行内置结束节点")
        return state
    
    def _builtin_passthrough_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """内置直通节点"""
        logger.debug("执行内置直通节点")
        return state
    
    def _builtin_always_true(self, state: WorkflowState) -> str:
        """内置条件：总是返回true"""
        return "true"
    
    def _builtin_always_false(self, state: WorkflowState) -> str:
        """内置条件：总是返回false"""
        return "false"
    
    def _builtin_has_messages(self, state: WorkflowState) -> str:
        """内置条件：检查是否有消息"""
        messages = state.get("messages", [])
        return "true" if messages else "false"
    