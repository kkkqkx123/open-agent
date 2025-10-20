"""工作流构建器

负责根据配置构建LangGraph工作流。
"""

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import yaml

from .config import WorkflowConfig
from .registry import NodeRegistry, get_global_registry
from .edges.simple_edge import SimpleEdge
from .edges.conditional_edge import ConditionalEdge
from ...prompts.agent_state import AgentState
from .performance import get_global_optimizer, optimize_workflow_loading


class WorkflowBuilder:
    """工作流构建器"""
    
    def __init__(self, node_registry: Optional[NodeRegistry] = None) -> None:
        """初始化工作流构建器
        
        Args:
            node_registry: 节点注册表，如果为None则使用全局注册表
        """
        self.node_registry = node_registry or get_global_registry()
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        
        # 内置条件函数映射
        self._condition_functions: Dict[str, Callable] = {
            "has_tool_call": self._has_tool_call_condition,
            "no_tool_call": self._no_tool_call_condition,
            "has_tool_calls": self._has_tool_call_condition,
            "no_tool_calls": self._no_tool_call_condition,
            "has_tool_result": self._has_tool_result_condition,
            "has_tool_results": self._has_tool_result_condition,
            "max_iterations_reached": self._max_iterations_reached_condition,
            "has_errors": self._has_errors_condition,
            "no_errors": self._no_errors_condition,
        }
    
    @optimize_workflow_loading
    def load_workflow_config(self, config_path: str) -> WorkflowConfig:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"工作流配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        workflow_config = WorkflowConfig.from_dict(config_data)
        
        # 验证配置
        errors = workflow_config.validate()
        if errors:
            raise ValueError(f"工作流配置验证失败: {'; '.join(errors)}")
        
        # 缓存配置
        self.workflow_configs[workflow_config.name] = workflow_config
        
        return workflow_config
    
    def build_workflow(self, config: WorkflowConfig):
        """根据配置构建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            编译后的工作流
        """
        try:
            from langgraph.graph import StateGraph, END
        except ImportError:
            raise ImportError("LangGraph未安装，无法构建工作流")
        
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 注册节点
        self._register_nodes(workflow, config)
        
        # 添加边
        self._add_edges(workflow, config)
        
        # 设置入口点
        entry_point = config.entry_point or self._determine_entry_point(config)
        workflow.set_entry_point(entry_point)
        
        # 编译工作流
        return workflow.compile()
    
    def _register_nodes(self, workflow, config: WorkflowConfig) -> None:
        """注册节点到工作流
        
        Args:
            workflow: LangGraph工作流
            config: 工作流配置
        """
        for node_name, node_config in config.nodes.items():
            try:
                # 获取节点实例
                node_instance = self.node_registry.get_node_instance(node_config.type)
                
                # 创建节点执行函数
                def create_node_function(node, current_node_name, current_node_config):
                    def node_function(state: AgentState) -> AgentState:
                        result = node.execute(state, current_node_config.config)
                        # 更新状态中的当前步骤
                        state.current_step = current_node_name
                        return result.state
                    return node_function
                
                workflow.add_node(node_name, create_node_function(node_instance, node_name, node_config))
                
            except Exception as e:
                raise ValueError(f"注册节点 '{node_name}' 失败: {e}")
    
    def _add_edges(self, workflow, config: WorkflowConfig) -> None:
        """添加边到工作流
        
        Args:
            workflow: LangGraph工作流
            config: 工作流配置
        """
        for edge_config in config.edges:
            if edge_config.type.value == "simple":
                self._add_simple_edge(workflow, edge_config)
            elif edge_config.type.value == "conditional":
                self._add_conditional_edge(workflow, edge_config)
            else:
                raise ValueError(f"未知的边类型: {edge_config.type.value}")
    
    def _add_simple_edge(self, workflow, edge_config) -> None:
        """添加简单边
        
        Args:
            workflow: LangGraph工作流
            edge_config: 边配置
        """
        workflow.add_edge(edge_config.from_node, edge_config.to_node)
    
    def _add_conditional_edge(self, workflow, edge_config) -> None:
        """添加条件边
        
        Args:
            workflow: LangGraph工作流
            edge_config: 边配置
        """
        if not edge_config.condition:
            raise ValueError(f"条件边 '{edge_config.from_node}' -> '{edge_config.to_node}' 缺少条件表达式")
        
        # 创建条件函数
        condition_func = self._create_condition_function(edge_config.condition)
        
        # 添加条件边
        # 创建条件映射，确保条件函数返回正确的节点名称
        def conditional_wrapper(state: AgentState) -> str:
            if condition_func(state):
                return edge_config.to_node
            # 如果条件不满足，返回END或默认节点
            return "END"
        
        workflow.add_conditional_edges(
            edge_config.from_node,
            conditional_wrapper,
            {edge_config.to_node: edge_config.to_node, "END": "END"}
        )
    
    def _create_condition_function(self, condition: str) -> Callable:
        """创建条件函数
        
        Args:
            condition: 条件表达式
            
        Returns:
            Callable: 条件函数
        """
        if condition in self._condition_functions:
            return self._condition_functions[condition]
        
        # 检查是否为带参数的条件
        if ":" in condition:
            parts = condition.split(":", 1)
            condition_name = parts[0]
            params_str = parts[1]
            
            if condition_name in self._condition_functions:
                base_func = self._condition_functions[condition_name]
                return lambda state: base_func(state, params_str)
        
        # 自定义条件表达式
        return lambda state: self._evaluate_custom_condition(state, condition)
    
    def _determine_entry_point(self, config: WorkflowConfig) -> str:
        """确定入口点
        
        Args:
            config: 工作流配置
            
        Returns:
            str: 入口点节点名称
        """
        # 如果配置了入口点，直接返回
        if config.entry_point:
            return config.entry_point
        
        # 否则，查找没有入边的节点作为入口点
        node_names = set(config.nodes.keys())
        target_nodes = {edge.to_node for edge in config.edges}
        
        entry_candidates = node_names - target_nodes
        if entry_candidates:
            # 返回第一个候选节点
            return list(entry_candidates)[0]
        
        # 如果没有找到，返回第一个节点
        if config.nodes:
            return list(config.nodes.keys())[0]
        
        raise ValueError("无法确定工作流入口点")
    
    # 内置条件函数
    def _has_tool_call_condition(self, state: AgentState, params: str = "") -> bool:
        """检查是否有工具调用"""
        if not state.messages:
            return False
        
        last_message = state.messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return True
        
        # 检查消息内容
        if hasattr(last_message, 'content'):
            content = str(last_message.content)
            return "tool_call" in content.lower() or "调用工具" in content
        
        return False
    
    def _no_tool_call_condition(self, state: AgentState, params: str = "") -> bool:
        """检查是否没有工具调用"""
        return not self._has_tool_call_condition(state, params)
    
    def _has_tool_result_condition(self, state: AgentState, params: str = "") -> bool:
        """检查是否有工具执行结果"""
        return len(state.tool_results) > 0
    
    def _max_iterations_reached_condition(self, state: AgentState, params: str = "") -> bool:
        """检查是否达到最大迭代次数"""
        iteration_count = getattr(state, 'iteration_count', 0)
        max_iterations = getattr(state, 'max_iterations', 10)
        return iteration_count >= max_iterations
    
    def _has_errors_condition(self, state: AgentState, params: str = "") -> bool:
        """检查是否有错误"""
        for result in state.tool_results:
            if not result.success:
                return True
        return False
    
    def _no_errors_condition(self, state: AgentState, params: str = "") -> bool:
        """检查是否没有错误"""
        return not self._has_errors_condition(state, params)
    
    def _evaluate_custom_condition(self, state: AgentState, condition: str) -> bool:
        """评估自定义条件
        
        Args:
            state: 当前状态
            condition: 条件表达式
            
        Returns:
            bool: 条件是否满足
        """
        try:
            # 创建安全的执行环境
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "any": any,
                    "all": all,
                },
                "state": state,
            }
            
            # 执行条件表达式
            result = eval(condition, safe_globals)
            return bool(result)
            
        except Exception:
            # 如果执行失败，返回False
            return False
    
    def register_condition_function(self, name: str, func: Callable) -> None:
        """注册自定义条件函数
        
        Args:
            name: 条件函数名称
            func: 条件函数
        """
        self._condition_functions[name] = func
    
    def list_available_nodes(self) -> List[str]:
        """列出所有可用的节点类型
        
        Returns:
            List[str]: 节点类型列表
        """
        return self.node_registry.list_nodes()
    
    def get_workflow_config(self, name: str) -> Optional[WorkflowConfig]:
        """获取已加载的工作流配置
        
        Args:
            name: 工作流名称
            
        Returns:
            Optional[WorkflowConfig]: 工作流配置，如果不存在则返回None
        """
        return self.workflow_configs.get(name)
    
    def clear_cache(self) -> None:
        """清除缓存的配置"""
        self.workflow_configs.clear()