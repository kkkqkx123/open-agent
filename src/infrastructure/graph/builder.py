"""LangGraph构建器

提供符合LangGraph最佳实践的图构建功能，支持配置驱动的构建过程。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING, cast
from pathlib import Path
import yaml
import logging
import asyncio
import concurrent.futures
import time
import threading
from abc import ABC, abstractmethod


if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
else:
    # 运行时使用Dict作为RunnableConfig的替代
    RunnableConfig = Dict[str, Any]

from .config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from .state import WorkflowState, LCBaseMessage
from .registry import NodeRegistry, get_global_registry
from .adapters import get_state_adapter
from src.domain.state.interfaces import IStateCollaborationManager
from .adapters.state_adapter import GraphAgentState

logger = logging.getLogger(__name__)

# 导入LangGraph核心组件
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver


class INodeExecutor(ABC):
    """节点执行器接口"""
    
    @abstractmethod
    def execute(self, state: WorkflowState, config: "Optional[RunnableConfig]" = None) -> WorkflowState:
        """执行节点逻辑"""
        pass


class NodeWithAdapterExecutor(INodeExecutor):
    """带适配器的节点执行器 - 将图状态与域状态进行转换"""
    
    def __init__(self, node_instance):
        self.node = node_instance
    
    def execute(self, state: WorkflowState, config: "Optional[RunnableConfig]" = None) -> WorkflowState:
        # 确保config不为None
        if config is None:
            config = {}
            
        # 1. 图状态转域状态
        state_adapter = get_state_adapter()
        domain_state = state_adapter.from_graph_state(state)
        
        # 2. 调用节点原始逻辑
        result = self.node.execute(domain_state, config)
        
        # 3. 将结果中的域状态转回图状态
        return cast(WorkflowState, state_adapter.to_graph_state(result.state))


class EnhancedNodeWithAdapterExecutor(INodeExecutor):
    """增强的节点执行器 - 重构版本"""
    
    def __init__(self, node_instance, state_manager: IStateCollaborationManager):
        self.node = node_instance
        from .adapters.collaboration_adapter import CollaborationStateAdapter
        self.collaboration_adapter = CollaborationStateAdapter(state_manager)
    
    def execute(self, state: WorkflowState, config: "Optional[RunnableConfig]" = None) -> WorkflowState:
        """执行节点逻辑，集成状态管理功能"""
        
        # 确保config不为None
        if config is None:
            config = {}
        
        def node_executor(domain_state: Any) -> Any:
            """节点执行函数"""
            # 将域状态转换为图状态供节点使用
            temp_graph_state = self.collaboration_adapter.state_adapter.to_graph_state(domain_state)
            
            # 执行原始节点逻辑
            result_graph_state = self.node.execute(temp_graph_state, config)
            
            # 将结果转换回域状态
            return self.collaboration_adapter.state_adapter.from_graph_state(result_graph_state)
        
        # 使用协作适配器执行
        return cast(WorkflowState, self.collaboration_adapter.execute_with_collaboration(state, node_executor))


class GraphBuilder:
    """LangGraph构建器 - 符合最佳实践"""
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        template_registry: Optional[Any] = None
    ) -> None:
        """初始化图构建器
        
        Args:
            node_registry: 节点注册表
            template_registry: 模板注册表（可选，用于扩展）
        """
        self.node_registry = node_registry or get_global_registry()
        self.template_registry = template_registry
        self._checkpointer_cache: Dict[str, Any] = {}
    
    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateCollaborationManager] = None) -> Any:
        """构建LangGraph图
        
        Args:
            config: 图配置
            
        Returns:
            编译后的LangGraph图
        """
        # 验证配置
        errors = config.validate()
        if errors:
            raise ValueError(f"图配置验证失败: {errors}")
        
        # 获取状态类
        state_class = config.get_state_class()
        
        # 创建StateGraph
        from langgraph.graph import StateGraph
        builder = StateGraph(state_class)
        
        # 添加节点
        self._add_nodes(builder, config, state_manager)
        
        # 添加边
        self._add_edges(builder, config)
        
        # 设置入口点
        if config.entry_point:
            from langgraph.graph import START
            builder.add_edge(START, config.entry_point)
        
        # 配置检查点
        checkpointer = self._get_checkpointer(config)
        
        # 编译图 - 支持异步执行
        graph = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=config.interrupt_before,
            interrupt_after=config.interrupt_after
        )
        
        logger.info(f"成功构建图: {config.name}")
        return graph
    
    def _add_nodes(self, builder: Any, config: GraphConfig, state_manager: Optional[IStateCollaborationManager] = None) -> None:
        """添加节点到图"""
        for node_name, node_config in config.nodes.items():
            # 获取节点函数
            node_function = self._get_node_function(node_config, state_manager)
            
            if node_function:
                # 根据LangGraph最佳实践添加节点
                # 修复LangGraph API调用，移除input参数，因为StateGraph不支持此参数
                builder.add_node(node_name, node_function)
                
                logger.debug(f"添加节点: {node_name}")
            else:
                logger.warning(f"无法找到节点函数: {node_config.function_name}")
    
    def _add_edges(self, builder: Any, config: GraphConfig) -> None:
        """添加边到图"""
        for edge in config.edges:
            if edge.type == EdgeType.SIMPLE:
                # 简单边
                if edge.to_node == "__end__":
                    from langgraph.graph import END
                    builder.add_edge(edge.from_node, END)
                else:
                    builder.add_edge(edge.from_node, edge.to_node)
            elif edge.type == EdgeType.CONDITIONAL:
                # 条件边
                if edge.condition is not None:  # 修复类型问题
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
            
            logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")
    
    def _get_node_function(self, node_config: NodeConfig, state_manager: Optional[IStateCollaborationManager] = None) -> Optional[Callable]:
        """获取节点函数"""
        # 首先从注册表获取
        try:
            node_class = self.node_registry.get_node_class(node_config.function_name)  # 修复方法名
            if node_class:
                # 创建节点实例
                node_instance = node_class()
                # 使用适配器包装节点，使其能够处理状态转换
                if state_manager:
                    # 如果提供了状态管理器，使用增强的执行器
                    adapter_wrapper = EnhancedNodeWithAdapterExecutor(node_instance, state_manager)
                else:
                    # 否则使用普通的执行器
                    adapter_wrapper = NodeWithAdapterExecutor(node_instance)
                return adapter_wrapper.execute
        except ValueError:
            # 节点类型不存在，继续尝试其他方法
            pass
        
        # 尝试从模板获取（如果提供了模板注册表）
        if self.template_registry and hasattr(self.template_registry, 'get_template'):
            try:
                template = self.template_registry.get_template(node_config.function_name)
                if template and hasattr(template, 'get_node_function'):
                    return template.get_node_function()
            except (AttributeError, ValueError):
                # 模板不存在或没有get_node_function方法，继续尝试其他方法
                pass
        
        # 最后尝试作为内置函数
        return self._get_builtin_function(node_config.function_name)
    
    def _get_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取条件函数"""
        # 检查节点注册表是否有条件函数
        # 注意：NodeRegistry 中没有 get_condition_function 方法，所以跳过这部分
        # 尝试作为内置条件函数
        return self._get_builtin_condition(condition_name)
    
    def _get_builtin_function(self, function_name: str) -> Optional[Callable]:
        """获取内置函数"""
        builtin_functions = {
            "llm_node": self._create_llm_node,
            "tool_node": self._create_tool_node,
            "analysis_node": self._create_analysis_node,
            "condition_node": self._create_condition_node,
            "wait_node": self._create_wait_node,
        }
        return builtin_functions.get(function_name)
    
    def _get_builtin_condition(self, condition_name: str) -> Optional[Callable]:
        """获取内置条件函数"""
        builtin_conditions = {
            "has_tool_calls": self._condition_has_tool_calls,
            "needs_more_info": self._condition_needs_more_info,
            "is_complete": self._condition_is_complete,
        }
        return builtin_conditions.get(condition_name)
    
    def _get_checkpointer(self, config: GraphConfig) -> Optional[Any]:
        """获取检查点"""
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
    
    def _create_llm_node(self, state: WorkflowState) -> Dict[str, Any]:
        """创建LLM节点"""
        # 这里应该调用实际的LLM服务
        # 简化实现
        return {"messages": state.get("messages", []) + [{"role": "assistant", "content": "LLM响应"}]}
    
    def _create_tool_node(self, state: WorkflowState) -> Dict[str, Any]:
        """创建工具节点"""
        # 这里应该调用实际的工具服务
        # 简化实现
        return {"tool_results": state.get("tool_calls", [])}
    
    def _create_analysis_node(self, state: WorkflowState) -> Dict[str, Any]:
        """创建分析节点"""
        # 这里应该执行实际的分析逻辑
        # 简化实现
        return {"analysis": "分析结果"}
    
    def _create_condition_node(self, state: WorkflowState) -> Dict[str, Any]:
        """创建条件节点"""
        # 这里应该执行实际的条件判断
        # 简化实现
        return {"condition_result": True}
    
    def _create_wait_node(self, state: WorkflowState) -> Dict[str, Any]:
        """创建等待节点"""
        # 这里应该执行实际的等待逻辑
        # 简化实现 - 返回等待状态
        return {
            "is_waiting": True,
            "wait_start_time": state.get("wait_start_time", time.time()),
            "messages": state.get("messages", []) + [{"role": "system", "content": "等待中..."}]
        }
    
    def _condition_has_tool_calls(self, state: WorkflowState) -> str:
        """条件：是否有工具调用"""
        return "tool_node" if state.get("tool_calls") else "llm_node"
    
    def _condition_needs_more_info(self, state: WorkflowState) -> str:
        """条件：是否需要更多信息"""
        return "analysis_node" if not state.get("analysis") else "end"
    
    def _condition_is_complete(self, state: WorkflowState) -> str:
        """条件：是否完成"""
        return "end" if state.get("complete") else "continue"
    
    def build_from_yaml(self, yaml_path: str, state_manager: Optional[IStateCollaborationManager] = None) -> Any:
        """从YAML文件构建图
        
        Args:
            yaml_path: YAML配置文件路径
            
        Returns:
            编译后的LangGraph图
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config = GraphConfig.from_dict(config_data)
        return self.build_graph(config, state_manager)
    
    def validate_config(self, config: GraphConfig) -> List[str]:
        """验证图配置

        Args:
            config: 图配置

        Returns:
            验证错误列表
        """
        return config.validate()

    def load_workflow_config(self, config_path: str) -> GraphConfig:
        """加载工作流配置

        Args:
            config_path: 配置文件路径

        Returns:
            工作流配置
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        return GraphConfig.from_dict(config_data)


# 为了向后兼容，保留旧的类名
# 注意：这里不再直接创建别名，而是通过工厂函数来避免循环导入
def get_workflow_builder(*args, **kwargs):
    """获取工作流构建器实例（向后兼容）"""
    return GraphBuilder(*args, **kwargs)