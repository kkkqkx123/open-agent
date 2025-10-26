"""LangGraph构建器

提供符合LangGraph最佳实践的图构建功能，支持配置驱动的构建过程。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING
from pathlib import Path
import yaml
import logging
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from src.domain.agent.interfaces import IAgent

from .config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from .state import WorkflowState, AgentState
from src.domain.agent.interfaces import IAgent, IAgentFactory
from .registry import NodeRegistry, get_global_registry
from src.application.workflow.interfaces import IWorkflowBuilder, IWorkflowTemplate
from src.application.workflow.templates.registry import get_global_template_registry

logger = logging.getLogger(__name__)

# 导入LangGraph核心组件
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    logger.warning("LangGraph not available, using fallback implementation")
    LANGGRAPH_AVAILABLE = False


class INodeExecutor(ABC):
    """节点执行器接口"""
    
    @abstractmethod
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """执行节点逻辑"""
        pass


class AgentNodeExecutor(INodeExecutor):
    """Agent节点执行器"""
    
    def __init__(self, agent: IAgent):
        self.agent = agent
    
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """执行Agent节点"""
        # 这里需要异步执行，但在同步上下文中我们需要处理
        import asyncio
        
        try:
            # 获取或创建事件循环
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 执行Agent逻辑
        result = loop.run_until_complete(self.agent.execute(state))
        return result


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
            template_registry: 模板注册表
        """
        self.node_registry = node_registry or get_global_registry()
        self.template_registry = template_registry or get_global_template_registry()
        self._checkpointer_cache: Dict[str, Any] = {}
    
    def build_graph(self, config: GraphConfig) -> Any:
        """构建LangGraph图
        
        Args:
            config: 图配置
            
        Returns:
            编译后的LangGraph图
        """
        if not LANGGRAPH_AVAILABLE:
            logger.error("LangGraph not available, cannot build graph")
            return None
        
        # 验证配置
        errors = config.validate()
        if errors:
            raise ValueError(f"图配置验证失败: {errors}")
        
        # 获取状态类
        state_class = config.get_state_class()
        
        # 创建StateGraph
        builder = StateGraph(state_class)
        
        # 添加节点
        self._add_nodes(builder, config)
        
        # 添加边
        self._add_edges(builder, config)
        
        # 设置入口点
        if config.entry_point:
            builder.add_edge(START, config.entry_point)
        
        # 配置检查点
        checkpointer = self._get_checkpointer(config)
        
        # 编译图
        graph = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=config.interrupt_before,
            interrupt_after=config.interrupt_after
        )
        
        logger.info(f"成功构建图: {config.name}")
        return graph
    
    def _add_nodes(self, builder: Any, config: GraphConfig) -> None:
        """添加节点到图"""
        for node_name, node_config in config.nodes.items():
            # 获取节点函数
            node_function = self._get_node_function(node_config)
            
            if node_function:
                # 根据LangGraph最佳实践添加节点
                if node_config.input_state:
                    # 如果指定了输入状态类型
                    builder.add_node(node_name, node_function, input=node_config.input_state)
                else:
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
                    builder.add_edge(edge.from_node, END)
                else:
                    builder.add_edge(edge.from_node, edge.to_node)
            elif edge.type == EdgeType.CONDITIONAL:
                # 条件边
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
            
            logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")
    
    def _get_node_function(self, node_config: NodeConfig) -> Optional[Callable]:
        """获取节点函数"""
        # 首先从注册表获取
        node_class = self.node_registry.get_node(node_config.function_name)
        if node_class:
            # 创建节点实例
            node_instance = node_class()
            return node_instance.execute
        
        # 然后尝试从模板获取
        template = self.template_registry.get_template(node_config.function_name)
        if template:
            return template.get_node_function()
        
        # 最后尝试作为内置函数
        return self._get_builtin_function(node_config.function_name)
    
    def _get_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取条件函数"""
        # 从注册表获取条件函数
        condition_func = self.node_registry.get_condition_function(condition_name)
        if condition_func:
            return condition_func
        
        # 尝试作为内置条件函数
        return self._get_builtin_condition(condition_name)
    
    def _get_builtin_function(self, function_name: str) -> Optional[Callable]:
        """获取内置函数"""
        builtin_functions = {
            "llm_node": self._create_llm_node,
            "tool_node": self._create_tool_node,
            "analysis_node": self._create_analysis_node,
            "condition_node": self._create_condition_node,
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
            checkpointer = InMemorySaver()
        elif config.checkpointer.startswith("sqlite:"):
            # sqlite:/path/to/db.sqlite
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
    
    def _condition_has_tool_calls(self, state: WorkflowState) -> str:
        """条件：是否有工具调用"""
        return "tool_node" if state.get("tool_calls") else "llm_node"
    
    def _condition_needs_more_info(self, state: WorkflowState) -> str:
        """条件：是否需要更多信息"""
        return "analysis_node" if not state.get("analysis") else "end"
    
    def _condition_is_complete(self, state: WorkflowState) -> str:
        """条件：是否完成"""
        return "end" if state.get("complete") else "continue"
    
    def build_from_yaml(self, yaml_path: str) -> Any:
        """从YAML文件构建图
        
        Args:
            yaml_path: YAML配置文件路径
            
        Returns:
            编译后的LangGraph图
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config = GraphConfig.from_dict(config_data)
        return self.build_graph(config)
    
    def validate_config(self, config: GraphConfig) -> List[str]:
        """验证图配置

        Args:
            config: 图配置

        Returns:
            验证错误列表
        """
        return config.validate()

    def build_workflow(self, config: GraphConfig) -> Any:
        """构建工作流（向后兼容方法）

        Args:
            config: 工作流配置

        Returns:
            编译后的工作流
        """
        return self.build_graph(config)

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
WorkflowBuilder = GraphBuilder