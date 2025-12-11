"""基于子工作流的状态机节点

重构后的状态机节点，使用子工作流实现LLM-工具-LLM循环结构。
"""

from typing import Dict, Any, Optional, cast
from src.interfaces.dependency_injection import get_logger

from src.core.workflow.graph.decorators import node
from src.infrastructure.graph.nodes.async_node import AsyncNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.base import IState
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.workflow.core import IWorkflowRegistry
from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import StateMachineConfig
from src.core.workflow.templates.state_machine import StateMachineSubWorkflowTemplate
from src.core.workflow.templates.state_machine.state_mapper import StateMachineStateMapper

logger = get_logger(__name__)


@node("state_machine_subworkflow_node")
class StateMachineSubWorkflowNode(AsyncNode):
    """基于子工作流的状态机节点
    
    使用子工作流实现状态机逻辑，复用现有的LLM节点、工具节点和触发器机制。
    """
    
    def __init__(self,
                 workflow_registry: Optional[IWorkflowRegistry] = None,
                 state_machine_template: Optional[StateMachineSubWorkflowTemplate] = None):
        """初始化状态机子工作流节点
        
        Args:
            workflow_registry: 工作流注册表
            state_machine_template: 状态机子工作流模板
        """
        self._workflow_registry = workflow_registry
        self._state_machine_template = state_machine_template or StateMachineSubWorkflowTemplate()
        self._state_mapper = StateMachineStateMapper()
    
    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "state_machine_subworkflow_node"
    
    async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行状态机子工作流
        
        Args:
            state: 当前工作流状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        try:
            # 获取状态机配置
            state_machine_config = self._get_state_machine_config(config)
            if not state_machine_config:
                raise ValueError("状态机配置不能为空")
            
            # 创建子工作流
            subworkflow = self._create_subworkflow(state_machine_config, config)
            
            # 初始化状态机状态
            workflow_state = self._state_mapper.initialize_workflow_state(state, state_machine_config)
            
            # 执行子工作流
            result_state = await self._execute_subworkflow(subworkflow, workflow_state, config)
            
            # 确定下一步
            next_node = self._determine_next_node(result_state, config)
            
            # 构建结果元数据
            result_metadata = {
                "state_machine_name": state_machine_config.name,
                "execution_info": self._state_mapper.get_state_execution_info(result_state),
                "subworkflow_id": subworkflow.workflow_id,
                "iterations": self._state_mapper.get_iteration_count(result_state)
            }
            
            return NodeExecutionResult(
                state=result_state,
                next_node=next_node,
                metadata=result_metadata
            )
            
        except Exception as e:
            logger.error(f"状态机子工作流执行失败: {e}")
            raise
    
    def _get_state_machine_config(self, config: Dict[str, Any]) -> Optional[StateMachineConfig]:
        """获取状态机配置
        
        Args:
            config: 节点配置
            
        Returns:
            Optional[StateMachineConfig]: 状态机配置
        """
        # 方式1: 直接传入状态机配置对象
        if "state_machine_config" in config:
            return config["state_machine_config"]
        
        # 方式2: 从配置文件加载
        if "config_file" in config:
            return self._load_config_from_file(config["config_file"])
        
        # 方式3: 从配置字典构建
        if "config_data" in config:
            return self._build_config_from_dict(config["config_data"])
        
        # 方式4: 使用默认配置
        if "use_default" in config and config["use_default"]:
            return self._create_default_config()
        
        return None
    
    def _load_config_from_file(self, config_file: str) -> Optional[StateMachineConfig]:
        """从文件加载状态机配置
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            Optional[StateMachineConfig]: 状态机配置
        """
        try:
            from src.core.workflow.graph.nodes.state_machine.state_machine_config_loader import load_state_machine_workflow
            workflow = load_state_machine_workflow(config_file)
            return workflow.state_machine_config
        except Exception as e:
            logger.error(f"从文件加载状态机配置失败: {config_file}, 错误: {e}")
            return None
    
    def _build_config_from_dict(self, config_data: Dict[str, Any]) -> Optional[StateMachineConfig]:
        """从字典构建状态机配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            Optional[StateMachineConfig]: 状态机配置
        """
        try:
            from src.core.workflow.graph.nodes.state_machine.state_machine_config_loader import create_state_machine_workflow_from_dict
            workflow = create_state_machine_workflow_from_dict(config_data)
            return workflow.state_machine_config
        except Exception as e:
            logger.error(f"从字典构建状态机配置失败: {e}")
            return None
    
    def _create_default_config(self) -> StateMachineConfig:
        """创建默认状态机配置
        
        Returns:
            StateMachineConfig: 默认状态机配置
        """
        from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import (
            StateMachineConfig, StateDefinition, StateType, Transition
        )
        
        # 创建简单的默认状态机
        config = StateMachineConfig(
            name="default_state_machine",
            description="默认状态机配置",
            version="1.0.0",
            initial_state="start"
        )
        
        # 添加开始状态
        start_state = StateDefinition(
            name="start",
            state_type=StateType.START,
            description="开始状态",
            config={"system_prompt": "请开始处理任务"}
        )
        start_state.add_transition(Transition("process"))
        config.add_state(start_state)
        
        # 添加处理状态
        process_state = StateDefinition(
            name="process",
            state_type=StateType.PROCESS,
            description="处理状态",
            config={"system_prompt": "请处理当前任务"}
        )
        process_state.add_transition(Transition("end"))
        config.add_state(process_state)
        
        # 添加结束状态
        end_state = StateDefinition(
            name="end",
            state_type=StateType.END,
            description="结束状态"
        )
        config.add_state(end_state)
        
        return config
    
    def _create_subworkflow(self, state_machine_config: StateMachineConfig, 
                          node_config: Dict[str, Any]) -> IWorkflow:
        """创建子工作流
        
        Args:
            state_machine_config: 状态机配置
            node_config: 节点配置
            
        Returns:
            IWorkflow: 子工作流实例
        """
        # 准备子工作流配置
        subworkflow_config = {
            "state_machine_config": state_machine_config,
            "max_iterations": node_config.get("max_iterations", 10),
            "llm_client": node_config.get("llm_client", "default"),
            "tool_manager": node_config.get("tool_manager", "default"),
            "enable_loop_control": node_config.get("enable_loop_control", True),
            "termination_states": node_config.get("termination_states", [])
        }
        
        # 创建子工作流
        workflow_name = f"{state_machine_config.name}_subworkflow"
        workflow_description = f"基于状态机 {state_machine_config.name} 的子工作流"
        
        return self._state_machine_template.create_workflow(
            name=workflow_name,
            description=workflow_description,
            config=subworkflow_config
        )
    
    async def _execute_subworkflow(self, subworkflow: IWorkflow, 
                                 workflow_state: IState,
                                 config: Dict[str, Any]) -> IState:
        """执行子工作流
        
        Args:
            subworkflow: 子工作流实例
            workflow_state: 工作流状态
            config: 节点配置
            
        Returns:
            WorkflowState: 执行后的状态
        """
        try:
            # 获取最大迭代次数
            max_iterations = config.get("max_iterations", 10)
            
            # 执行子工作流循环
            while self._state_mapper.should_continue(workflow_state, max_iterations):
                # 获取当前状态
                current_state = self._state_mapper.get_current_state(workflow_state)
                if not current_state:
                    logger.warning("当前状态为空，终止执行")
                    break
                
                # 执行当前状态的节点
                step_result = await self._execute_current_step(subworkflow, workflow_state, current_state)
                
                # 更新状态
                workflow_state = step_result.state
                
                # 检查是否需要终止
                if self._should_terminate(workflow_state, config):
                    self._state_mapper.set_terminated(workflow_state, True)
                    break
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"执行子工作流失败: {e}")
            raise
    
    async def _execute_current_step(self, subworkflow: IWorkflow, 
                                 workflow_state: IState,
                                 current_state: str) -> NodeExecutionResult:
        """执行当前步骤
        
        Args:
            subworkflow: 子工作流实例
            workflow_state: 工作流状态
            current_state: 当前状态
            
        Returns:
            NodeExecutionResult: 步骤执行结果
        """
        try:
            from src.interfaces.state import IWorkflowState
            
            # 获取当前步骤
            step = subworkflow.get_node(current_state)
            if not step:
                raise ValueError(f"步骤不存在: {current_state}")
            
            # 获取节点配置（从节点对象获取）
            step_config = getattr(step, 'config', {}) if hasattr(step, 'config') else {}
            
            # 强制类型转换为 IWorkflowState（假设 IState 兼容 IWorkflowState）
            wf_state = cast(IWorkflowState, workflow_state)
            
            # 执行步骤（INode 接口要求）
            result = await step.execute_async(wf_state, step_config)
            
            return result
            
        except Exception as e:
            logger.error(f"执行步骤失败: {current_state}, 错误: {e}")
            raise
    
    def _should_terminate(self, workflow_state: IState, 
                         config: Dict[str, Any]) -> bool:
        """判断是否应该终止
        
        Args:
            workflow_state: 工作流状态
            config: 节点配置
            
        Returns:
            bool: 是否应该终止
        """
        # 检查终止状态
        termination_states = config.get("termination_states", [])
        current_state = self._state_mapper.get_current_state(workflow_state)
        
        if current_state in termination_states:
            return True
        
        # 检查终止条件
        termination_conditions = config.get("termination_conditions", [])
        for condition in termination_conditions:
            if self._state_mapper.evaluate_transition_condition(workflow_state, condition):
                return True
        
        return False
    
    def _determine_next_node(self, result_state: IState, 
                           config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点
        
        Args:
            result_state: 执行结果状态
            config: 节点配置
            
        Returns:
            Optional[str]: 下一个节点名称
        """
        # 如果配置中指定了下一个节点，直接返回
        if "next_node" in config:
            return config["next_node"]
        
        # 根据执行结果确定下一个节点
        execution_info = self._state_mapper.get_state_execution_info(result_state)
        
        # 如果已终止，返回配置的终止后节点
        if execution_info["terminated"]:
            return config.get("termination_node", "__end__")
        
        # 如果有错误，返回错误处理节点
        if execution_info["has_errors"]:
            return config.get("error_node", "error_handler")
        
        # 默认返回None，让工作流引擎决定
        return None
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "state_machine_config": {
                    "type": "object",
                    "description": "状态机配置对象"
                },
                "config_file": {
                    "type": "string",
                    "description": "状态机配置文件路径"
                },
                "config_data": {
                    "type": "object",
                    "description": "状态机配置数据"
                },
                "use_default": {
                    "type": "boolean",
                    "description": "是否使用默认配置",
                    "default": False
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "最大迭代次数",
                    "default": 10,
                    "min": 1,
                    "max": 50
                },
                "llm_client": {
                    "type": "string",
                    "description": "LLM客户端标识",
                    "default": "default"
                },
                "tool_manager": {
                    "type": "string",
                    "description": "工具管理器标识",
                    "default": "default"
                },
                "enable_loop_control": {
                    "type": "boolean",
                    "description": "是否启用循环控制",
                    "default": True
                },
                "termination_states": {
                    "type": "array",
                    "description": "终止状态列表",
                    "default": [],
                    "items": {
                        "type": "string"
                    }
                },
                "termination_conditions": {
                    "type": "array",
                    "description": "终止条件列表",
                    "default": [],
                    "items": {
                        "type": "string"
                    }
                },
                "next_node": {
                    "type": "string",
                    "description": "下一个节点ID"
                },
                "termination_node": {
                    "type": "string",
                    "description": "终止后节点ID"
                },
                "error_node": {
                    "type": "string",
                    "description": "错误处理节点ID"
                }
            },
            "required": []
        }