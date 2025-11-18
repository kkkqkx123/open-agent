"""统一图构建器

集成所有功能的统一图构建器，包含基础构建、函数注册表集成和迭代管理功能。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING, cast
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
from src.core.workflow.states.workflow import WorkflowState
from src.core.workflow.states.base import LCBaseMessage
from src.core.workflow.graph.registry import NodeRegistry, get_global_registry
from src.domain.state.interfaces import IStateLifecycleManager
from src.services.workflow.function_registry import (
    FunctionRegistry,
    get_global_function_registry,
)

logger = logging.getLogger(__name__)

# 导入LangGraph核心组件
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver


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


class UnifiedGraphBuilder:
    """统一图构建器
    
    集成所有功能的图构建器，支持灵活条件边。
    """
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistry] = None,
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
        self.function_registry = function_registry or get_global_function_registry()
        self.template_registry: Optional[Any] = None  # 添加缺失的属性，允许任意类型
        self.enable_function_fallback = enable_function_fallback
        self.enable_iteration_management = enable_iteration_management
        self._checkpointer_cache: Dict[str, Any] = {}
        self.iteration_manager: Optional[Any] = None  # IterationManager
        
        # 初始化路由函数管理器 (可选)
        # self.route_function_manager = get_route_function_manager(route_function_config_dir)
        # self.flexible_edge_factory = FlexibleConditionalEdgeFactory(self.route_function_manager)
        
        # 初始化节点函数管理器 (可选)
        # self.node_function_manager = get_node_function_manager(node_function_config_dir)
        
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
        # if self.enable_iteration_management:
        #     self.iteration_manager = IterationManager(config)
        # else:
        #     self.iteration_manager = None
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
            # 灵活条件边功能暂未启用
            logger.debug(f"灵活条件边功能暂未启用: {edge.from_node}")
            # 创建灵活条件边
            # flexible_edge = self.flexible_edge_factory.create_from_config(edge)
            # 
            # 创建路由函数
            # route_function = flexible_edge.create_route_function()
            # 
            # 添加条件边
            # if edge.path_map:
            #     builder.add_conditional_edges(
            #         edge.from_node,
            #         route_function,
            #         path_map=edge.path_map
            #     )
            # else:
            #     builder.add_conditional_edges(edge.from_node, route_function)
                
            logger.debug(f"添加灵活条件边: {edge.from_node}")
            
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
        if self.function_registry:
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
        if self.template_registry:
            template = self.template_registry.get_template(function_name)
            if template and hasattr(template, 'get_node_function'):
                node_function = template.get_node_function()
                if node_function:
                    logger.debug(f"从模板注册表获取节点函数: {function_name}")
                    return self._wrap_node_function(node_function, state_manager, node_config.name)
        
        # 4. 尝试从内置函数获取
        # rest_function = get_rest_node_function(function_name)
        # if rest_function:
        #     logger.debug(f"从内置函数获取节点函数: {function_name}")
        #     return self._wrap_node_function(rest_function, state_manager, node_config.name)
        
        # 5. 如果启用回退，尝试内置实现
        if self.enable_function_fallback:
            rest_functions = {
                "llm_node": self._create_llm_node,
                "tool_node": self._create_tool_node,
                "analysis_node": self._create_analysis_node,
                "condition_node": self._create_condition_node,
                "wait_node": self._create_wait_node,
            }
            fallback_function = rest_functions.get(function_name)
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
        # 组合函数功能暂未启用
        # if self.node_function_manager.has_composition(composition_name):
        #     def composition_function(state: WorkflowState, **kwargs) -> WorkflowState:
        #         return self.node_function_manager.execute_composition(composition_name, state, **kwargs)
        #     return composition_function
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
        # route_function = self.route_function_manager.get_route_function(condition_name)
        # if route_function:
        #     logger.debug(f"从路由函数管理器获取条件函数: {condition_name}")
        #     return route_function
        
        # 2. 尝试从函数注册表获取
        if self.function_registry:
            condition_function = self.function_registry.get_condition_function(
                condition_name
            )
            if condition_function:
                logger.debug(f"从函数注册表获取条件函数: {condition_name}")
                return condition_function
        
        # 3. 尝试从内置函数获取
        # rest_function = get_rest_condition_function(condition_name)
        # if rest_function:
        #     logger.debug(f"从内置函数获取条件函数: {condition_name}")
        #     return rest_function
        
        # 4. 如果启用回退，尝试内置实现
        if self.enable_function_fallback:
            rest_conditions = {
                "has_tool_calls": self._condition_has_tool_calls,
                "needs_more_info": self._condition_needs_more_info,
                "is_complete": self._condition_is_complete,
            }
            fallback_function = rest_conditions.get(condition_name)
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
            # from .adapters.collaboration_adapter import CollaborationStateAdapter
            
            def state_wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
                """状态管理包装的节点函数"""
                # collaboration_adapter = CollaborationStateAdapter(state_manager)
                
                def node_executor(domain_state: Any) -> Any:
                    """节点执行函数"""
                    # 将域状态转换为图状态
                    # temp_graph_state = collaboration_adapter.state_adapter.to_graph_state(domain_state)
                    # 执行原始函数
                    result = function(domain_state)
                    # 将结果转换回域状态
                    # return collaboration_adapter.state_adapter.from_graph_state(result)
                    return result
                
                # 使用协作适配器执行
                # return collaboration_adapter.execute_with_collaboration(state, node_executor)
                return node_executor(state)
            
            wrapped_function = state_wrapped_function
        else:
            # 如果没有状态管理器，直接使用原函数
            wrapped_function = function
        
        # 然后包装迭代管理（如果启用）
        # if self.enable_iteration_management and self.iteration_manager is not None:
        #     # 使用类型断言确保iteration_manager不是None
        #     iteration_manager = self.iteration_manager
        #     
        #     def iteration_wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
        #         """迭代管理包装的节点函数"""
        #         # 记录开始时间
        #         start_time = datetime.now()
        #         
        #         try:
        #             # 检查迭代限制
        #             if not iteration_manager.check_limits(state, node_name):
        #                 logger.info(f"节点 {node_name} 达到迭代限制，提前终止")
        #                 # 返回表明工作流已完成的状态
        #                 completed_state = dict(state)
        #                 completed_state['complete'] = True
        #                 return completed_state
        #
        #             # 执行包装函数
        #             result = wrapped_function(state)
        #             
        #             # 确保结果是字典格式
        #             if not isinstance(result, dict):
        #                 # 如果结果不是字典，尝试将其转换为字典
        #                 if hasattr(result, '__dict__'):
        #                     result = result.__dict__
        #                 else:
        #                     # 如果无法转换，则使用原始状态
        #                     result = state
        #             
        #             # 记录结束时间
        #             end_time = datetime.now()
        #             
        #             # 更新迭代计数
        #             # 确保结果中包含原始状态信息
        #             if isinstance(state, dict) and isinstance(result, dict):
        #                 updated_result = {**state, **result}  # 合并原始状态和结果
        #             else:
        #                 updated_result = result
        #             
        #             # updated_result = iteration_manager.record_and_increment(
        #             #     updated_result,
        #             #     node_name,
        #             #     start_time,
        #             #     end_time,
        #             #     status='SUCCESS'
        #             # )
        #             
        #             return updated_result
        #             
        #         except Exception as e:
        #             logger.error(f"节点 {node_name} 执行失败: {e}")
        #             
        #             # 记录结束时间
        #             end_time = datetime.now()
        #             
        #             # 即使出错也要记录迭代
        #             error_result = dict(state)
        #             # error_result = iteration_manager.record_and_increment(
        #             #     error_result,
        #             #     node_name,
        #             #     start_time,
        #             #     end_time,
        #             #     status='FAILURE',
        #             #     error=str(e)
        #             # )
        #             
        #             # 添加错误信息到状态
        #             errors = error_result.get('errors', [])
        #             errors.append(f"节点 {node_name} 执行失败: {str(e)}")
        #             error_result['errors'] = errors
        #             
        #             return error_result
        #     
        #     return iteration_wrapped_function
        # else:
        #     # 如果不启用迭代管理，直接返回状态包装的函数
        #     return wrapped_function
        
        # 迭代管理功能暂未启用，直接返回状态包装的函数
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
        
        checkpointer = None
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
        # 这里应该实现LLM节点的具体逻辑
        logger.debug("执行LLM节点")
        return state
    
    def _create_tool_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建工具节点"""
        # 这里应该实现工具节点的具体逻辑
        logger.debug("执行工具节点")
        return state
    
    def _create_analysis_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建分析节点"""
        # 这里应该实现分析节点的具体逻辑
        logger.debug("执行分析节点")
        return state
    
    def _create_condition_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建条件节点"""
        # 这里应该实现条件节点的具体逻辑
        logger.debug("执行条件节点")
        return state
    
    def _create_wait_node(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """创建等待节点"""
        # 这里应该实现等待节点的具体逻辑
        logger.debug("执行等待节点")
        return state
    
    # 内置条件函数实现
    def _condition_has_tool_calls(self, state: WorkflowState) -> str:
        """检查是否有工具调用"""
        messages = state.get("messages", [])
        if not messages:
            return "end"

        last_message = messages[-1]
        # 检查LangChain消息的tool_calls属性
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
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
        # 这里应该实现具体的条件逻辑
        return "continue"

    def _condition_is_complete(self, state: WorkflowState) -> str:
         """检查是否完成"""
         # 这里应该实现具体的条件逻辑
         return "end"


# 为向后兼容性创建别名
GraphBuilder = UnifiedGraphBuilder