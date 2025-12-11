"""状态机子工作流模板

实现基于子工作流的状态机，复用现有的LLM节点、工具节点和触发器机制。
"""

from typing import Dict, Any, List, Optional
from src.interfaces.dependency_injection import get_logger

from ..base import BaseWorkflowTemplate
from .config_adapter import StateMachineConfigAdapter
from .state_mapper import StateMachineStateMapper
from src.interfaces.workflow.core import IWorkflow
from ...value_objects import StepType, TransitionType
from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import (
    StateMachineConfig, StateType
)

logger = get_logger(__name__)


class StateMachineSubWorkflowTemplate(BaseWorkflowTemplate):
    """状态机子工作流模板
    
    将传统状态机转换为基于图的子工作流，实现LLM-工具-LLM的循环结构。
    """
    
    def __init__(self) -> None:
        """初始化状态机子工作流模板"""
        super().__init__()
        self._name = "state_machine_subworkflow"
        self._description = "状态机子工作流模板，支持LLM-工具-LLM循环结构"
        self._category = "state_machine"
        self._version = "1.0"
        
        # 初始化适配器和映射器
        self._config_adapter = StateMachineConfigAdapter()
        self._state_mapper = StateMachineStateMapper()
        
        # 模板参数
        self._parameters = [
            {
                "name": "state_machine_config",
                "type": "object",
                "description": "状态机配置对象",
                "required": True
            },
            {
                "name": "max_iterations",
                "type": "integer",
                "description": "最大迭代次数",
                "required": False,
                "default": 10,
                "min": 1,
                "max": 50
            },
            {
                "name": "llm_client",
                "type": "string",
                "description": "LLM客户端标识",
                "required": False,
                "default": "default"
            },
            {
                "name": "tool_manager",
                "type": "string",
                "description": "工具管理器标识",
                "required": False,
                "default": "default"
            },
            {
                "name": "enable_loop_control",
                "type": "boolean",
                "description": "是否启用循环控制",
                "required": False,
                "default": True
            },
            {
                "name": "termination_states",
                "type": "array",
                "description": "终止状态列表",
                "required": False,
                "default": [],
                "items": {
                    "type": "string"
                }
            }
        ]
    
    def _build_workflow_structure(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建状态机子工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        try:
            # 获取状态机配置
            state_machine_config = config.get("state_machine_config")
            if not state_machine_config:
                raise ValueError("状态机配置不能为空")
            
            # 转换为子工作流配置
            subworkflow_config = self._config_adapter.convert_to_subworkflow_config(state_machine_config)
            
            # 合并用户配置
            subworkflow_config.update({
                "max_iterations": config.get("max_iterations", 10),
                "llm_client": config.get("llm_client", "default"),
                "tool_manager": config.get("tool_manager", "default"),
                "enable_loop_control": config.get("enable_loop_control", True),
                "termination_states": config.get("termination_states", [])
            })
            
            # 构建工作流结构
            self._build_nodes(workflow, subworkflow_config)
            self._build_transitions(workflow, subworkflow_config)
            self._setup_loop_control(workflow, subworkflow_config)
            
            # 设置入口点
            initial_state = subworkflow_config.get("initial_state", "start")
            workflow.set_entry_point(initial_state)
            
            logger.info(f"构建状态机子工作流结构完成: {workflow.name}")
            
        except Exception as e:
            logger.error(f"构建状态机子工作流失败: {e}")
            raise
    
    def _build_nodes(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建工作流节点
        
        Args:
            workflow: 工作流实例
            config: 子工作流配置
        """
        states = config.get("states", {})
        llm_client = config.get("llm_client", "default")
        tool_manager = config.get("tool_manager", "default")
        
        for state_name, node_config in states.items():
            node_type = node_config.get("type", "llm_node")
            node_description = node_config.get("description", f"状态机节点: {state_name}")
            node_specific_config = node_config.get("config", {})
            
            # 根据节点类型创建步骤
            if node_type == "llm_node":
                step = self._create_llm_step(
                    workflow, state_name, node_description, 
                    node_specific_config, llm_client
                )
            elif node_type == "tool_node":
                step = self._create_tool_step(
                    workflow, state_name, node_description,
                    node_specific_config, tool_manager
                )
            elif node_type == "parallel_node":
                step = self._create_parallel_step(
                    workflow, state_name, node_description,
                    node_specific_config, llm_client
                )
            else:
                # 默认创建LLM节点
                step = self._create_llm_step(
                    workflow, state_name, node_description,
                    node_specific_config, llm_client
                )
            
            # 添加节点到工作流（注意：IWorkflow接口应该支持add_step）
            if hasattr(workflow, 'add_step'):
                workflow.add_step(step)  # type: ignore
    
    def _create_llm_step(self, workflow: IWorkflow, step_id: str, description: str,
                        config: Dict[str, Any], llm_client: str):
        """创建LLM步骤
        
        Args:
            workflow: 工作流实例
            step_id: 步骤ID
            description: 步骤描述
            config: 节点配置
            llm_client: LLM客户端标识
            
        Returns:
            WorkflowStep: 工作流步骤
        """
        # 合并LLM配置
        llm_config = {
            "llm_client": llm_client,
            "model": config.get("model", "gpt-4"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1000),
            "system_prompt": config.get("system_prompt", ""),
            "next_node": self._determine_next_node(config)
        }
        
        # 添加状态机特定配置
        if "state_machine" in config:
            llm_config["state_machine"] = config["state_machine"]
        
        return self._create_step(
            step_id=step_id,
            step_name=step_id,
            step_type=StepType.ANALYSIS,
            description=description,
            config=llm_config
        )
    
    def _create_tool_step(self, workflow: IWorkflow, step_id: str, description: str,
                         config: Dict[str, Any], tool_manager: str):
        """创建工具步骤
        
        Args:
            workflow: 工作流实例
            step_id: 步骤ID
            description: 步骤描述
            config: 节点配置
            tool_manager: 工具管理器标识
            
        Returns:
            WorkflowStep: 工作流步骤
        """
        # 合并工具配置
        tool_config = {
            "tool_manager": tool_manager,
            "timeout": config.get("timeout", 30),
            "max_parallel_calls": config.get("max_parallel_calls", 1),
            "continue_on_error": config.get("continue_on_error", True),
            "tools": config.get("tools", []),
            "next_node": self._determine_next_node(config)
        }
        
        # 添加状态机特定配置
        if "state_machine" in config:
            tool_config["state_machine"] = config["state_machine"]
        
        return self._create_step(
            step_id=step_id,
            step_name=step_id,
            step_type=StepType.EXECUTION,
            description=description,
            config=tool_config
        )
    
    def _create_parallel_step(self, workflow: IWorkflow, step_id: str, description: str,
                            config: Dict[str, Any], llm_client: str):
        """创建并行步骤
        
        Args:
            workflow: 工作流实例
            step_id: 步骤ID
            description: 步骤描述
            config: 节点配置
            llm_client: LLM客户端标识
            
        Returns:
            WorkflowStep: 工作流步骤
        """
        # 合并并行配置
        parallel_config = {
            "max_concurrent": config.get("max_concurrent", 3),
            "timeout_ms": config.get("timeout_ms", 180000),
            "nodes": config.get("nodes", {}),
            "default_nodes": config.get("default_nodes", {}),
            "llm_client": llm_client,
            "next_node": self._determine_next_node(config)
        }
        
        # 添加状态机特定配置
        if "state_machine" in config:
            parallel_config["state_machine"] = config["state_machine"]
        
        return self._create_step(
            step_id=step_id,
            step_name=step_id,
            step_type=StepType.PARALLEL,
            description=description,
            config=parallel_config
        )
    
    def _determine_next_node(self, config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点
        
        Args:
            config: 节点配置
            
        Returns:
            Optional[str]: 下一个节点名称
        """
        # 如果配置中指定了下一个节点，直接返回
        if "next_node" in config:
            return config["next_node"]
        
        # 根据状态机配置确定下一个节点
        state_machine_info = config.get("state_machine", {})
        original_state_name = state_machine_info.get("original_state_name")
        
        if original_state_name:
            # 这里可以根据状态机逻辑确定下一个节点
            # 暂时返回None，让转换条件来决定
            return None
        
        return None
    
    def _build_transitions(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建工作流转换
        
        Args:
            workflow: 工作流实例
            config: 子工作流配置
        """
        transitions = config.get("transitions", [])
        
        for transition_config in transitions:
            from_step = transition_config.get("from")
            to_step = transition_config.get("to")
            transition_type = TransitionType.CONDITIONAL if transition_config.get("condition") else TransitionType.SIMPLE
            condition = transition_config.get("condition")
            description = transition_config.get("description", "")
            
            transition = self._create_transition(
                transition_id=f"{from_step}_to_{to_step}",
                from_step=from_step,
                to_step=to_step,
                transition_type=transition_type,
                condition=condition,
                description=description
            )
            
            # 添加转换到工作流（注意：IWorkflow接口应该支持add_transition）
            if hasattr(workflow, 'add_transition'):
                workflow.add_transition(transition)  # type: ignore
    
    def _setup_loop_control(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """设置循环控制
        
        Args:
            workflow: 工作流实例
            config: 子工作流配置
        """
        if not config.get("enable_loop_control", True):
            return
        
        max_iterations = config.get("max_iterations", 10)
        termination_states = config.get("termination_states", [])
        
        # 创建循环控制节点
        loop_control_step = self._create_step(
            step_id="loop_control",
            step_name="loop_control",
            step_type=StepType.CONTROL,
            description="循环控制节点",
            config={
                "max_iterations": max_iterations,
                "termination_states": termination_states,
                "continue_condition": "should_continue"
            }
        )
        if hasattr(workflow, 'add_step'):
            workflow.add_step(loop_control_step)  # type: ignore
        
        # 为每个非终止状态添加到循环控制的转换
        states = config.get("states", {})
        for state_name, node_config in states.items():
            if state_name not in termination_states:
                # 检查是否已经有从该状态出发的转换
                has_existing_transitions = any(
                    t.get("from") == state_name 
                    for t in config.get("transitions", [])
                )
                
                if not has_existing_transitions:
                    # 添加默认转换到循环控制
                    transition = self._create_transition(
                        transition_id=f"{state_name}_to_loop_control",
                        from_step=state_name,
                        to_step="loop_control",
                        transition_type=TransitionType.SIMPLE,
                        description="默认循环控制转换"
                    )
                    if hasattr(workflow, 'add_transition'):
                        workflow.add_transition(transition)  # type: ignore
        
        # 添加循环控制的条件转换
        for state_name, node_config in states.items():
            if state_name not in termination_states:
                # 继续循环的转换
                continue_transition = self._create_transition(
                    transition_id=f"loop_control_to_{state_name}",
                    from_step="loop_control",
                    to_step=state_name,
                    transition_type=TransitionType.CONDITIONAL,
                    condition="should_continue",
                    description="继续执行状态机"
                )
                if hasattr(workflow, 'add_transition'):
                    workflow.add_transition(continue_transition)  # type: ignore
        
        # 添加终止转换
        if termination_states:
            for termination_state in termination_states:
                terminate_transition = self._create_transition(
                    transition_id=f"loop_control_to_{termination_state}",
                    from_step="loop_control",
                    to_step=termination_state,
                    transition_type=TransitionType.CONDITIONAL,
                    condition="should_terminate",
                    description="终止状态机执行"
                )
                if hasattr(workflow, 'add_transition'):
                    workflow.add_transition(terminate_transition)  # type: ignore
    
    def create_from_state_machine_config(self, state_machine_config: StateMachineConfig,
                                      name: str, description: str = "",
                                      **kwargs) -> IWorkflow:
        """从状态机配置创建工作流
        
        Args:
            state_machine_config: 状态机配置
            name: 工作流名称
            description: 工作流描述
            **kwargs: 额外参数
            
        Returns:
            IWorkflow: 工作流实例
        """
        # 准备配置参数
        config = {
            "state_machine_config": state_machine_config,
            "name": name,
            "description": description or f"基于状态机 {state_machine_config.name} 的子工作流"
        }
        config.update(kwargs)
        
        # 创建工作流
        return self.create_workflow(name, description, config)