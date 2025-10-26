"""增强的工作流构建器

提供更简洁、更灵活的Workflow构建功能，支持配置驱动的构建过程。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.agent.interfaces import IAgent
from pathlib import Path
import yaml
import logging
from abc import ABC, abstractmethod

from .config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from .state import WorkflowState, AgentState
from ...domain.agent.interfaces import IAgent, IAgentFactory
from .registry import NodeRegistry, get_global_registry
from .interfaces import IWorkflowBuilder, IWorkflowTemplate
from .templates.registry import get_global_template_registry

logger = logging.getLogger(__name__)


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
        
        result = loop.run_until_complete(self.agent.execute(state, config))
        # 确保返回WorkflowState类型
        return result  # type: ignore


class WorkflowBuilder(IWorkflowBuilder):
    """增强的工作流构建器
    
    提供更简洁的Workflow构建功能，支持：
    - 配置驱动的构建
    - Agent节点的自动注册
    - 简化的边添加逻辑
    - 模板支持
    """
    
    def __init__(
        self, 
        node_registry: Optional[NodeRegistry] = None,
        agent_factory: Optional[IAgentFactory] = None
    ):
        """初始化增强的工作流构建器
        
        Args:
            agent_factory: Agent工厂实例
            node_registry: 节点注册表实例
        """
        self.agent_factory = agent_factory
        self.node_registry = node_registry or get_global_registry()
        self.workflow_templates: Dict[str, IWorkflowTemplate] = {}
        self._condition_functions: Dict[str, Callable] = {}
        self._node_executors: Dict[str, INodeExecutor] = {}
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        
        # 注册内置条件函数
        self._register_builtin_conditions()
        
        # 自动加载模板
        self._load_templates()
        
        logger.info("EnhancedWorkflowBuilder初始化完成")
    
    def build_from_config(self, config: Union[WorkflowConfig, Dict[str, Any], str]) -> Any:
        """从配置构建工作流
        
        Args:
            config: 工作流配置，可以是WorkflowConfig对象、配置字典或配置文件路径
            
        Returns:
            编译后的工作流
        """
        try:
            from langgraph.graph import StateGraph, END
            self.END = END
        except ImportError:
            raise ImportError("LangGraph未安装，无法构建工作流")
        
        # 解析配置
        workflow_config = self._parse_config(config)
        
        # 验证配置
        errors = workflow_config.validate()
        if errors:
            raise ValueError(f"工作流配置验证失败: {'; '.join(errors)}")
        
        logger.info(f"开始构建工作流: {workflow_config.name}")
        
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 注册节点
        self._register_nodes_enhanced(workflow, workflow_config)
        
        # 添加边
        self._add_edges_enhanced(workflow, workflow_config)
        
        # 设置入口点
        entry_point = workflow_config.entry_point or self._determine_entry_point(workflow_config)
        workflow.set_entry_point(entry_point)
        
        # 编译工作流
        compiled_workflow = workflow.compile()
        
        logger.info(f"工作流构建完成: {workflow_config.name}")
        return compiled_workflow
    
    def build_from_template(
        self, 
        template_name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """从模板构建工作流
        
        Args:
            template_name: 模板名称
            config: 覆盖配置（可选）
            
        Returns:
            编译后的工作流
        """
        if template_name not in self.workflow_templates:
            raise ValueError(f"模板不存在: {template_name}")
        
        template = self.workflow_templates[template_name]
        workflow_config = template.create_template(config or {})
        
        return self.build_from_config(workflow_config)
    
    def register_template(self, name: str, template: IWorkflowTemplate) -> None:
        """注册工作流模板
        
        Args:
            name: 模板名称
            template: 模板实例
        """
        self.workflow_templates[name] = template
        logger.info(f"注册工作流模板: {name}")
    
    def register_condition_function(self, name: str, func: Callable) -> None:
        """注册条件函数
        
        Args:
            name: 条件函数名称
            func: 条件函数
        """
        self._condition_functions[name] = func
        logger.info(f"注册条件函数: {name}")
    
    def register_agent_node(self, node_name: str, agent_config: Dict[str, Any]) -> None:
        """注册Agent节点
        
        Args:
            node_name: 节点名称
            agent_config: Agent配置
        """
        if not self.agent_factory:
            raise ValueError("Agent工厂未设置，无法注册Agent节点")
        
        agent = self.agent_factory.create_agent(agent_config)
        executor = AgentNodeExecutor(agent)
        self._node_executors[node_name] = executor
        
        logger.info(f"注册Agent节点: {node_name}")
    
    def _parse_config(self, config: Union[WorkflowConfig, Dict[str, Any], str]) -> WorkflowConfig:
        """解析配置
        
        Args:
            config: 配置对象、字典或路径
            
        Returns:
            WorkflowConfig: 解析后的配置对象
        """
        if isinstance(config, WorkflowConfig):
            return config
        elif isinstance(config, dict):
            return WorkflowConfig.from_dict(config)
        elif isinstance(config, str):
            return self._load_config_from_file(config)
        else:
            raise ValueError(f"不支持的配置类型: {type(config)}")
    
    def load_workflow_config(self, config_path: str) -> WorkflowConfig:
        """加载工作流配置（向后兼容方法）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        workflow_config = self._load_config_from_file(config_path)
        
        # 缓存配置（与旧版本保持一致）
        self.workflow_configs[workflow_config.name] = workflow_config
        
        return workflow_config
    
    def build_workflow(self, config: WorkflowConfig) -> Any:
        """根据配置构建工作流（向后兼容方法）
        
        Args:
            config: 工作流配置
            
        Returns:
            编译后的工作流
        """
        return self.build_from_config(config)
    
    def _load_config_from_file(self, config_path: str) -> WorkflowConfig:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            WorkflowConfig: 配置对象
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"工作流配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return WorkflowConfig.from_dict(config_data)
    
    def _register_nodes_enhanced(self, workflow: Any, config: WorkflowConfig) -> None:
        """增强的节点注册
        
        Args:
            workflow: LangGraph工作流
            config: 工作流配置
        """
        for node_name, node_config in config.nodes.items():
            try:
                # 检查是否有预注册的节点执行器
                if node_name in self._node_executors:
                    executor = self._node_executors[node_name]
                    workflow.add_node(node_name, self._create_node_function(executor, node_config))
                    logger.debug(f"注册预定义节点: {node_name}")
                    continue
                
                # 检查是否为Agent节点
                if node_config.type == "agent_node":
                    self._register_agent_node_from_config(node_name, node_config)
                    executor = self._node_executors[node_name]
                    workflow.add_node(node_name, self._create_node_function(executor, node_config))
                    logger.debug(f"注册Agent节点: {node_name}")
                    continue
                
                # 使用节点注册表
                node_instance = self.node_registry.get_node_instance(node_config.type)
                workflow.add_node(node_name, self._create_node_function(node_instance, node_config))
                logger.debug(f"注册节点: {node_name} (类型: {node_config.type})")
                
            except Exception as e:
                raise ValueError(f"注册节点 '{node_name}' 失败: {e}")
    
    def _register_agent_node_from_config(self, node_name: str, node_config: NodeConfig) -> None:
        """从配置注册Agent节点
        
        Args:
            node_name: 节点名称
            node_config: 节点配置
        """
        if not self.agent_factory:
            raise ValueError("Agent工厂未设置，无法注册Agent节点")
        
        agent_config = node_config.config.get("agent_config", {})
        agent = self.agent_factory.create_agent(agent_config)
        executor = AgentNodeExecutor(agent)
        self._node_executors[node_name] = executor
    
    def _create_node_function(self, executor: Union[INodeExecutor, Any], node_config: NodeConfig) -> Callable:
        """创建节点执行函数
        
        Args:
            executor: 节点执行器
            node_config: 节点配置
            
        Returns:
            Callable: 节点执行函数
        """
        def node_function(state: WorkflowState) -> Dict[str, Any]:
            try:
                # 执行节点逻辑
                result_state = executor.execute(state, node_config.config)
                
                # 返回状态更新
                return {
                    "messages": result_state.messages,
                    "tool_results": result_state.tool_results,
                    "current_step": result_state.current_step,
                    "max_iterations": result_state.max_iterations,
                    "iteration_count": result_state.iteration_count,
                    "workflow_name": result_state.workflow_name,
                    "errors": result_state.errors,
                    "custom_fields": result_state.custom_fields
                }
            except Exception as e:
                logger.error(f"节点执行失败: {e}")
                # 返回错误状态
                state.add_error({"error": str(e), "node": node_config})
                return {
                    "messages": state.messages,
                    "tool_results": state.tool_results,
                    "current_step": state.current_step,
                    "max_iterations": state.max_iterations,
                    "iteration_count": state.iteration_count,
                    "errors": state.errors
                }
        
        return node_function
    
    def _add_edges_enhanced(self, workflow: Any, config: WorkflowConfig) -> None:
        """增强的边添加逻辑
        
        Args:
            workflow: LangGraph工作流
            config: 工作流配置
        """
        for edge_config in config.edges:
            try:
                if edge_config.type == EdgeType.SIMPLE:
                    self._add_simple_edge_enhanced(workflow, edge_config)
                elif edge_config.type == EdgeType.CONDITIONAL:
                    self._add_conditional_edge_enhanced(workflow, edge_config)
                else:
                    raise ValueError(f"未知的边类型: {edge_config.type}")
            except Exception as e:
                raise ValueError(f"添加边 '{edge_config.from_node}' -> '{edge_config.to_node}' 失败: {e}")
    
    def _add_simple_edge_enhanced(self, workflow: Any, edge_config: EdgeConfig) -> None:
        """添加简单边
        
        Args:
            workflow: LangGraph工作流
            edge_config: 边配置
        """
        workflow.add_edge(edge_config.from_node, edge_config.to_node)
        logger.debug(f"添加简单边: {edge_config.from_node} -> {edge_config.to_node}")
    
    def _add_conditional_edge_enhanced(self, workflow: Any, edge_config: EdgeConfig) -> None:
        """添加条件边
        
        Args:
            workflow: LangGraph工作流
            edge_config: 边配置
        """
        if not edge_config.condition:
            raise ValueError(f"条件边缺少条件表达式: {edge_config.from_node} -> {edge_config.to_node}")
        
        # 创建条件函数
        condition_func = self._create_condition_function(edge_config.condition)
        
        # 创建条件映射
        condition_mapping = {
            edge_config.to_node: edge_config.to_node,
            self.END: self.END
        }
        
        # 添加条件边
        workflow.add_conditional_edges(
            edge_config.from_node,
            condition_func,
            condition_mapping
        )
        
        logger.debug(f"添加条件边: {edge_config.from_node} -> {edge_config.to_node} (条件: {edge_config.condition})")
    
    def _create_condition_function(self, condition: str) -> Callable:
        """创建条件函数
        
        Args:
            condition: 条件表达式
            
        Returns:
            Callable: 条件函数
        """
        # 检查内置条件函数
        if condition in self._condition_functions:
            return self._condition_functions[condition]
        
        # 检查带参数的条件
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
        
        # 查找没有入边的节点作为入口点
        node_names = set(config.nodes.keys())
        target_nodes = {edge.to_node for edge in config.edges}
        
        entry_candidates = node_names - target_nodes
        if entry_candidates:
            return list(entry_candidates)[0]
        
        # 如果没有找到，返回第一个节点
        if config.nodes:
            return list(config.nodes.keys())[0]
        
        raise ValueError("无法确定工作流入口点")
    
    def _register_builtin_conditions(self) -> None:
        """注册内置条件函数"""
        self._condition_functions.update({
            "has_tool_call": self._has_tool_call_condition,
            "no_tool_call": self._no_tool_call_condition,
            "has_tool_calls": self._has_tool_call_condition,
            "no_tool_calls": self._no_tool_call_condition,
            "has_tool_result": self._has_tool_result_condition,
            "has_tool_results": self._has_tool_result_condition,
            "max_iterations_reached": self._max_iterations_reached_condition,
            "has_errors": self._has_errors_condition,
            "no_errors": self._no_errors_condition,
            "plan_completed": self._plan_completed_condition,
        })
    
    # 内置条件函数
    def _has_tool_call_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查是否有工具调用"""
        if not state.messages:
            return False
        
        last_message = state.messages[-1]
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            return True
        
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', ''))
            return "tool_call" in content.lower() or "调用工具" in content
        
        return False
    
    def _no_tool_call_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查是否没有工具调用"""
        return not self._has_tool_call_condition(state, params)
    
    def _has_tool_result_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查是否有工具执行结果"""
        return len(state.tool_results) > 0
    
    def _max_iterations_reached_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查是否达到最大迭代次数"""
        return state.iteration_count >= state.max_iterations
    
    def _has_errors_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查是否有错误"""
        return len(state.errors) > 0 or any(not result.success for result in state.tool_results)
    
    def _no_errors_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查是否没有错误"""
        return not self._has_errors_condition(state, params)
    
    def _plan_completed_condition(self, state: WorkflowState, params: str = "") -> bool:
        """检查计划是否已完成"""
        try:
            if not hasattr(state, 'plan') or not hasattr(state, 'current_step_index'):
                return False
            
            plan = getattr(state, 'plan', [])
            current_step_index = getattr(state, 'current_step_index', 0)
            
            return len(plan) > 0 and current_step_index >= len(plan)
        except Exception:
            return False
    
    def _evaluate_custom_condition(self, state: WorkflowState, condition: str) -> bool:
        """评估自定义条件
        
        Args:
            state: 当前状态
            condition: 条件表达式
            
        Returns:
            bool: 条件是否满足
        """
        try:
            safe_globals = {
                "__builtins__": {
                    "len": len, "str": str, "int": int, "float": float,
                    "bool": bool, "list": list, "dict": dict,
                    "any": any, "all": all,
                },
                "state": state,
            }
            
            result = eval(condition, safe_globals)
            return bool(result)
        except Exception:
            return False
    
    def _load_templates(self) -> None:
        """加载可用模板"""
        try:
            template_registry = get_global_template_registry()
            template_names = template_registry.list_templates()
            
            for template_name in template_names:
                template = template_registry.get_template(template_name)
                if template:
                    self.workflow_templates[template_name] = template
                    logger.debug(f"加载模板: {template_name}")
            
            logger.info(f"加载了 {len(self.workflow_templates)} 个模板")
        except Exception as e:
            logger.error(f"加载模板失败: {e}")
    
    def list_available_templates(self) -> List[str]:
        """列出可用的模板
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self.workflow_templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            Optional[Dict[str, Any]]: 模板信息
        """
        if template_name not in self.workflow_templates:
            return None
        
        template = self.workflow_templates[template_name]
        return {
            "name": template_name,
            "description": getattr(template, 'description', ''),
            "parameters": getattr(template, 'get_parameters', lambda: [])()
        }
    
    def get_workflow_config(self, name: str) -> Optional[WorkflowConfig]:
        """获取已加载的工作流配置（向后兼容方法）
        
        Args:
            name: 工作流名称
            
        Returns:
            Optional[WorkflowConfig]: 工作流配置，如果不存在则返回None
        """
        return self.workflow_configs.get(name)
    
    def clear_cache(self) -> None:
        """清除缓存的配置（向后兼容方法）"""
        self.workflow_configs.clear()
    
    def list_available_nodes(self) -> List[str]:
        """列出所有可用的节点类型（向后兼容方法）
        
        Returns:
            List[str]: 节点类型列表
        """
        return self.node_registry.list_nodes()