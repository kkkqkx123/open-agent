"""状态机状态映射器

负责在状态机状态和工作流状态之间进行转换，确保状态信息的一致性。
"""

from typing import Dict, Any, List, Optional
from src.interfaces.dependency_injection import get_logger

from src.interfaces.state.base import IState
from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import (
    StateMachineConfig, StateDefinition
)

logger = get_logger(__name__)


class StateMachineStateMapper:
    """状态机状态映射器
    
    负责状态机状态与工作流状态之间的双向映射。
    """
    
    def __init__(self) -> None:
        """初始化状态映射器"""
        self._state_history_key = "state_machine_state_history"
        self._current_state_key = "state_machine_current_state"
        self._iteration_count_key = "state_machine_iteration_count"
        self._termination_flag_key = "state_machine_terminated"
    
    def initialize_workflow_state(self, workflow_state: IState, 
                               state_machine_config: StateMachineConfig) -> IState:
        """初始化工作流状态
        
        Args:
            workflow_state: 工作流状态
            state_machine_config: 状态机配置
            
        Returns:
            WorkflowState: 初始化后的工作流状态
        """
        # 设置初始状态
        workflow_state.set_data(self._current_state_key, state_machine_config.initial_state)
        
        # 初始化状态历史
        workflow_state.set_data(self._state_history_key, [state_machine_config.initial_state])
        
        # 初始化迭代计数
        workflow_state.set_data(self._iteration_count_key, 0)
        
        # 初始化终止标志
        workflow_state.set_data(self._termination_flag_key, False)
        
        # 存储状态机配置信息
        workflow_state.set_data("state_machine_config", {
            "name": state_machine_config.name,
            "initial_state": state_machine_config.initial_state,
            "states": list(state_machine_config.states.keys())
        })
        
        logger.debug(f"初始化状态机状态: {state_machine_config.initial_state}")
        return workflow_state
    
    def update_current_state(self, workflow_state: IState, 
                           new_state: str, state_def: Optional[StateDefinition] = None) -> IState:
        """更新当前状态
        
        Args:
            workflow_state: 工作流状态
            new_state: 新状态名称
            state_def: 状态定义（可选）
            
        Returns:
            WorkflowState: 更新后的工作流状态
        """
        # 更新当前状态
        workflow_state.set_data(self._current_state_key, new_state)
        
        # 更新状态历史
        state_history = workflow_state.get_data(self._state_history_key, [])
        state_history.append(new_state)
        workflow_state.set_data(self._state_history_key, state_history)
        
        # 增加迭代计数
        iteration_count = workflow_state.get_data(self._iteration_count_key, 0)
        workflow_state.set_data(self._iteration_count_key, iteration_count + 1)
        
        # 存储状态定义信息
        if state_def:
            workflow_state.set_data(f"state_def_{new_state}", {
                "name": state_def.name,
                "type": state_def.state_type.value,
                "description": state_def.description,
                "config": state_def.config
            })
        
        logger.debug(f"更新状态机状态: {new_state}")
        return workflow_state
    
    def get_current_state(self, workflow_state: IState) -> Optional[str]:
        """获取当前状态
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            Optional[str]: 当前状态名称
        """
        return workflow_state.get_data(self._current_state_key)  # type: ignore
    
    def get_state_history(self, workflow_state: IState) -> List[str]:
        """获取状态历史
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            List[str]: 状态历史列表
        """
        return workflow_state.get_data(self._state_history_key, [])  # type: ignore
    
    def get_iteration_count(self, workflow_state: IState) -> int:
        """获取迭代计数
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            int: 迭代次数
        """
        return workflow_state.get_data(self._iteration_count_key, 0)  # type: ignore
    
    def is_terminated(self, workflow_state: IState) -> bool:
        """检查是否已终止
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            bool: 是否已终止
        """
        return workflow_state.get_data(self._termination_flag_key, False)  # type: ignore
    
    def set_terminated(self, workflow_state: IState, terminated: bool = True) -> IState:
        """设置终止标志
        
        Args:
            workflow_state: 工作流状态
            terminated: 是否终止
            
        Returns:
            WorkflowState: 更新后的工作流状态
        """
        workflow_state.set_data(self._termination_flag_key, terminated)
        if terminated:
            logger.info("状态机已终止")
        return workflow_state
    
    def should_continue(self, workflow_state: IState, 
                      max_iterations: int = 10) -> bool:
        """判断是否应该继续执行
        
        Args:
            workflow_state: 工作流状态
            max_iterations: 最大迭代次数
            
        Returns:
            bool: 是否应该继续
        """
        # 检查是否已终止
        if self.is_terminated(workflow_state):
            return False
        
        # 检查迭代次数
        iteration_count = self.get_iteration_count(workflow_state)
        if iteration_count >= max_iterations:
            logger.warning(f"达到最大迭代次数: {max_iterations}")
            return False
        
        return True
    
    def evaluate_transition_condition(self, workflow_state: IState, 
                                  condition: Optional[str]) -> bool:
        """评估转移条件
        
        Args:
            workflow_state: 工作流状态
            condition: 条件表达式
            
        Returns:
            bool: 条件是否满足
        """
        if not condition:
            return True
        
        try:
            # 简单的条件评估
            condition_lower = condition.lower()
            
            # 检查工具调用
            if condition_lower == "has_tool_call":
                return self._has_tool_call(workflow_state)
            elif condition_lower == "not has_tool_call":
                return not self._has_tool_call(workflow_state)
            
            # 检查错误
            elif condition_lower == "has_errors":
                return self._has_errors(workflow_state)
            elif condition_lower == "not has_errors":
                return not self._has_errors(workflow_state)
            
            # 检查特定状态
            elif condition_lower.startswith("state_is_"):
                target_state = condition_lower[9:]  # 移除 "state_is_" 前缀
                current_state = self.get_current_state(workflow_state)
                return current_state == target_state
            
            # 检查状态历史
            elif condition_lower.startswith("visited_"):
                target_state = condition_lower[8:]  # 移除 "visited_" 前缀
                state_history = self.get_state_history(workflow_state)
                return target_state in state_history
            
            # 布尔值
            elif condition_lower == "true":
                return True
            elif condition_lower == "false":
                return False
            
            # 默认返回False
            else:
                logger.warning(f"未知的条件表达式: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"评估转移条件失败: {condition}, 错误: {e}")
            return False
    
    def _has_tool_call(self, workflow_state: IState) -> bool:
        """检查是否有工具调用
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            bool: 是否有工具调用
        """
        # 检查消息中是否有工具调用
        messages = workflow_state.get_data("messages", [])
        if messages:
            last_message = messages[-1]
            
            # 使用类型安全的接口检查工具调用
            if hasattr(last_message, 'has_tool_calls') and callable(last_message.has_tool_calls):
                return bool(last_message.has_tool_calls())
            
            # 检查字典格式（后备方案）
            elif isinstance(last_message, dict) and "tool_calls" in last_message:
                return len(last_message["tool_calls"]) > 0
        
        return False
    
    def _has_errors(self, workflow_state: IState) -> bool:
        """检查是否有错误
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            bool: 是否有错误
        """
        # 检查错误列表
        errors = workflow_state.get_data("errors", [])
        if errors:
            return True
        
        # 检查工具执行错误
        tool_results = workflow_state.get_data("tool_results", [])
        for result in tool_results:
            if not result.get("success", True):
                return True
        
        return False
    
    def get_state_execution_info(self, workflow_state: IState) -> Dict[str, Any]:
        """获取状态执行信息
        
        Args:
            workflow_state: 工作流状态
            
        Returns:
            Dict[str, Any]: 状态执行信息
        """
        return {
            "current_state": self.get_current_state(workflow_state),
            "state_history": self.get_state_history(workflow_state),
            "iteration_count": self.get_iteration_count(workflow_state),
            "terminated": self.is_terminated(workflow_state),
            "has_tool_call": self._has_tool_call(workflow_state),
            "has_errors": self._has_errors(workflow_state)
        }
    
    def reset_state(self, workflow_state: IState, 
                  initial_state: str) -> IState:
        """重置状态机状态
        
        Args:
            workflow_state: 工作流状态
            initial_state: 初始状态
            
        Returns:
            WorkflowState: 重置后的工作流状态
        """
        workflow_state.set_data(self._current_state_key, initial_state)
        workflow_state.set_data(self._state_history_key, [initial_state])
        workflow_state.set_data(self._iteration_count_key, 0)
        workflow_state.set_data(self._termination_flag_key, False)
        
        logger.debug(f"重置状态机状态到: {initial_state}")
        return workflow_state