"""状态机配置适配器

将状态机配置转换为子工作流配置，实现从状态机模式到图工作流模式的映射。
"""

from typing import Dict, Any, List, Optional
from src.interfaces.dependency_injection import get_logger

from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import (
    StateMachineConfig, StateDefinition, StateType, Transition
)

logger = get_logger(__name__)


class StateMachineConfigAdapter:
    """状态机配置适配器
    
    负责将传统的状态机配置转换为基于图的子工作流配置。
    """
    
    def __init__(self):
        """初始化适配器"""
        self._state_type_mapping = {
            StateType.START: "llm_node",
            StateType.END: "llm_node", 
            StateType.PROCESS: "llm_node",
            StateType.DECISION: "llm_node",
            StateType.PARALLEL: "parallel_node",
            StateType.CONDITIONAL: "llm_node"
        }
    
    def convert_to_subworkflow_config(self, state_machine_config: StateMachineConfig) -> Dict[str, Any]:
        """将状态机配置转换为子工作流配置
        
        Args:
            state_machine_config: 状态机配置
            
        Returns:
            Dict[str, Any]: 子工作流配置
        """
        try:
            # 基础配置
            subworkflow_config = {
                "name": f"{state_machine_config.name}_subworkflow",
                "description": f"基于状态机 {state_machine_config.name} 的子工作流",
                "version": state_machine_config.version,
                "max_iterations": 10,
                "states": {},
                "transitions": [],
                "initial_state": self._map_state_to_node(state_machine_config.initial_state)
            }
            
            # 转换状态定义
            for state_name, state_def in state_machine_config.states.items():
                node_config = self._convert_state_to_node(state_name, state_def)
                subworkflow_config["states"][state_name] = node_config
            
            # 转换状态转移
            transitions = self._convert_transitions(state_machine_config.states)
            subworkflow_config["transitions"] = transitions
            
            # 添加循环控制配置
            subworkflow_config["loop_control"] = {
                "max_iterations": 10,
                "termination_states": self._get_termination_states(state_machine_config.states),
                "continue_condition": "not_terminated"
            }
            
            logger.info(f"成功转换状态机配置: {state_machine_config.name}")
            return subworkflow_config
            
        except Exception as e:
            logger.error(f"转换状态机配置失败: {e}")
            raise
    
    def _convert_state_to_node(self, state_name: str, state_def: StateDefinition) -> Dict[str, Any]:
        """将状态定义转换为节点配置
        
        Args:
            state_name: 状态名称
            state_def: 状态定义
            
        Returns:
            Dict[str, Any]: 节点配置
        """
        # 确定节点类型
        node_type = self._determine_node_type(state_def)
        
        # 基础节点配置
        node_config = {
            "type": node_type,
            "description": state_def.description,
            "config": state_def.config.copy() if state_def.config else {}
        }
        
        # 根据节点类型添加特定配置
        if node_type == "llm_node":
            node_config["config"].update(self._get_llm_node_config(state_def))
        elif node_type == "tool_node":
            node_config["config"].update(self._get_tool_node_config(state_def))
        elif node_type == "parallel_node":
            node_config["config"].update(self._get_parallel_node_config(state_def))
        
        # 添加状态机特定信息
        node_config["config"]["state_machine"] = {
            "original_state_name": state_name,
            "state_type": state_def.state_type.value,
            "handler": state_def.handler
        }
        
        return node_config
    
    def _determine_node_type(self, state_def: StateDefinition) -> str:
        """确定节点类型
        
        Args:
            state_def: 状态定义
            
        Returns:
            str: 节点类型
        """
        # 基于状态类型确定节点类型
        base_type = self._state_type_mapping.get(state_def.state_type, "llm_node")
        
        # 检查配置中是否有工具调用需求
        if state_def.config and "tools" in state_def.config:
            return "tool_node"
        
        # 检查是否需要并行处理
        if state_def.state_type == StateType.PARALLEL:
            return "parallel_node"
        
        return base_type
    
    def _get_llm_node_config(self, state_def: StateDefinition) -> Dict[str, Any]:
        """获取LLM节点配置
        
        Args:
            state_def: 状态定义
            
        Returns:
            Dict[str, Any]: LLM节点配置
        """
        config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # 从状态配置中提取LLM相关配置
        if state_def.config:
            for key in ["model", "temperature", "max_tokens", "system_prompt"]:
                if key in state_def.config:
                    config[key] = state_def.config[key]
        
        # 添加状态机特定的系统提示词
        if not config.get("system_prompt"):
            config["system_prompt"] = self._generate_default_system_prompt(state_def)
        
        return config
    
    def _get_tool_node_config(self, state_def: StateDefinition) -> Dict[str, Any]:
        """获取工具节点配置
        
        Args:
            state_def: 状态定义
            
        Returns:
            Dict[str, Any]: 工具节点配置
        """
        config = {
            "timeout": 30,
            "max_parallel_calls": 1,
            "continue_on_error": True
        }
        
        # 从状态配置中提取工具相关配置
        if state_def.config:
            for key in ["tools", "timeout", "max_parallel_calls", "continue_on_error"]:
                if key in state_def.config:
                    config[key] = state_def.config[key]
        
        return config
    
    def _get_parallel_node_config(self, state_def: StateDefinition) -> Dict[str, Any]:
        """获取并行节点配置
        
        Args:
            state_def: 状态定义
            
        Returns:
            Dict[str, Any]: 并行节点配置
        """
        config = {
            "max_concurrent": 3,
            "timeout_ms": 180000
        }
        
        # 从状态配置中提取并行相关配置
        if state_def.config:
            for key in ["max_concurrent", "timeout_ms", "nodes"]:
                if key in state_def.config:
                    config[key] = state_def.config[key]
        
        return config
    
    def _generate_default_system_prompt(self, state_def: StateDefinition) -> str:
        """生成默认系统提示词
        
        Args:
            state_def: 状态定义
            
        Returns:
            str: 系统提示词
        """
        state_type_prompts = {
            StateType.START: "你是工作流的开始节点，请初始化状态并准备执行后续步骤。",
            StateType.END: "你是工作流的结束节点，请总结执行结果并完成工作流。",
            StateType.PROCESS: f"你是处理节点 '{state_def.name}'，请执行相应的处理逻辑。",
            StateType.DECISION: f"你是决策节点 '{state_def.name}'，请根据当前状态做出决策。",
            StateType.CONDITIONAL: f"你是条件节点 '{state_def.name}'，请评估条件并确定下一步。"
        }
        
        return state_type_prompts.get(
            state_def.state_type, 
            f"你是状态机节点 '{state_def.name}'，请执行相应的功能。"
        )
    
    def _convert_transitions(self, states: Dict[str, StateDefinition]) -> List[Dict[str, Any]]:
        """转换状态转移
        
        Args:
            states: 状态定义字典
            
        Returns:
            List[Dict[str, Any]]: 转移配置列表
        """
        transitions = []
        
        for state_name, state_def in states.items():
            for transition in state_def.transitions:
                transition_config = {
                    "from": state_name,
                    "to": transition.target_state,
                    "type": "conditional" if transition.condition else "simple",
                    "description": transition.description
                }
                
                if transition.condition:
                    transition_config["condition"] = self._convert_condition(transition.condition)
                
                transitions.append(transition_config)
        
        return transitions
    
    def _convert_condition(self, condition: str) -> str:
        """转换条件表达式
        
        Args:
            condition: 原始条件表达式
            
        Returns:
            str: 转换后的条件表达式
        """
        # 简单的条件映射
        condition_mapping = {
            "always": "true",
            "never": "false",
            "has_tool_call": "has_tool_call",
            "no_tool_call": "not has_tool_call",
            "has_errors": "has_errors",
            "no_errors": "not has_errors"
        }
        
        return condition_mapping.get(condition.lower(), condition)
    
    def _get_termination_states(self, states: Dict[str, StateDefinition]) -> List[str]:
        """获取终止状态列表
        
        Args:
            states: 状态定义字典
            
        Returns:
            List[str]: 终止状态名称列表
        """
        termination_states = []
        
        for state_name, state_def in states.items():
            if state_def.state_type == StateType.END:
                termination_states.append(state_name)
        
        return termination_states
    
    def _map_state_to_node(self, state_name: str) -> str:
        """将状态名称映射到节点名称
        
        Args:
            state_name: 状态名称
            
        Returns:
            str: 节点名称
        """
        return state_name