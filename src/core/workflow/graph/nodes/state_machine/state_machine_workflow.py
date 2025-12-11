"""基于状态机的工作流实现

提供状态机模式的工作流基类，与基于图的工作流并行支持。
"""

from typing import Dict, Any, Optional, List, Set, Union
from abc import ABC, abstractmethod
from enum import Enum
from src.interfaces.dependency_injection import get_logger

from .workflow_config import WorkflowConfig
from src.core.state import WorkflowState

logger = get_logger(__name__)


class StateType(Enum):
    """状态类型枚举"""
    START = "start"
    END = "end"
    PROCESS = "process"
    DECISION = "decision"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class Transition:
    """状态转移定义"""
    
    def __init__(
        self,
        target_state: str,
        condition: Optional[str] = None,
        description: str = ""
    ):
        self.target_state = target_state
        self.condition = condition  # 转移条件，None表示无条件
        self.description = description


class TransitionRecord:
    """状态转移记录"""
    
    def __init__(
        self,
        from_state: str,
        to_state: str,
        timestamp: str,
        condition: Optional[str] = None
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = timestamp
        self.condition = condition


class StateDefinition:
    """状态定义"""
    
    def __init__(
        self,
        name: str,
        state_type: StateType,
        handler: Optional[str] = None,
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.state_type = state_type
        self.handler = handler  # 状态处理函数名
        self.description = description
        self.config = config or {}
        self.transitions: List[Transition] = []
    
    def add_transition(self, transition: Transition) -> None:
        """添加状态转移"""
        self.transitions.append(transition)


class StateMachineConfig:
    """状态机配置"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        initial_state: str = "initial"
    ):
        self.name = name
        self.description = description
        self.version = version
        self.initial_state = initial_state
        self.states: Dict[str, StateDefinition] = {}
    
    def add_state(self, state: StateDefinition) -> None:
        """添加状态"""
        self.states[state.name] = state
    
    def get_state(self, state_name: str) -> Optional[StateDefinition]:
        """获取状态定义"""
        return self.states.get(state_name)
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        # 检查初始状态是否存在
        if self.initial_state not in self.states:
            errors.append(f"初始状态 '{self.initial_state}' 不存在")
        
        # 检查状态类型
        start_states = [s for s in self.states.values() if s.state_type == StateType.START]
        if len(start_states) != 1:
            errors.append("状态机必须包含且仅包含一个开始状态")
        
        # 检查状态转移
        for state_name, state in self.states.items():
            for transition in state.transitions:
                if transition.target_state not in self.states:
                    errors.append(f"状态 '{state_name}' 的转移目标 '{transition.target_state}' 不存在")
        
        # 检查可达性
        reachable_states = self._get_reachable_states()
        unreachable_states = set(self.states.keys()) - reachable_states
        if unreachable_states:
            errors.append(f"存在不可达状态: {', '.join(unreachable_states)}")
        
        return errors
    
    def _get_reachable_states(self) -> Set[str]:
        """获取从初始状态可达的所有状态"""
        if self.initial_state not in self.states:
            return set()
        
        visited = set()
        stack = [self.initial_state]
        
        while stack:
            current_state = stack.pop()
            if current_state in visited:
                continue
            
            visited.add(current_state)
            state = self.states.get(current_state)
            
            if state:
                for transition in state.transitions:
                    if transition.target_state not in visited:
                        stack.append(transition.target_state)
        
        return visited


class StateMachineWorkflow:
    """基于状态机的工作流基类"""
    
    def __init__(
        self,
        config: WorkflowConfig,
        state_machine_config: StateMachineConfig,
        config_loader: Optional[Any] = None,
        container: Optional[Any] = None,
        **kwargs
    ):
        """初始化状态机工作流
        
        Args:
            config: 工作流配置
            state_machine_config: 状态机配置
            config_loader: 配置加载器
            container: 依赖注入容器
            **kwargs: 额外参数
        """
        self.config = config
        self.config_loader = config_loader
        self.container = container
        self.state_machine_config = state_machine_config
        self.current_state = state_machine_config.initial_state
        self.state_history: List[str] = []
        self.transition_history: List[TransitionRecord] = []
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行状态机工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # 初始化当前状态
        if self.current_state is None:
            self.current_state = self.state_machine_config.initial_state
        
        # 状态机执行循环
        while self.current_state is not None:
            # 获取当前状态定义
            current_state_def = self.state_machine_config.get_state(self.current_state)
            if current_state_def is None:
                logger.error(f"状态 '{self.current_state}' 不存在")
                break
            
            # 执行状态处理
            state = self._process_state(current_state_def, state)
            
            # 检查是否到达终止状态
            if current_state_def.state_type == StateType.END:
                break
            
            # 确定下一个状态
            next_state = self._determine_next_state(current_state_def, state)
            if next_state is None:
                logger.warning(f"状态 '{self.current_state}' 没有有效的转移")
                break
            
            self.current_state = next_state
        
        return state
    
    def _process_state(self, state_def: StateDefinition, state: WorkflowState) -> WorkflowState:
        """处理单个状态
        
        Args:
            state_def: 状态定义
            state: 当前状态
            
        Returns:
            WorkflowState: 处理后的状态
        """
        # 根据状态类型调用相应的处理函数
        handler_name = state_def.handler or f"handle_{state_def.name}"
        
        try:
            # 查找处理函数
            handler = getattr(self, handler_name, None)
            if handler and callable(handler):
                result = handler(state, state_def.config)
                if isinstance(result, dict):
                    # 如果返回字典，合并到state的values中
                    state.values.update(result)
                return state
            else:
                # 默认处理
                return self._default_state_handler(state, state_def)
        except Exception as e:
            logger.error(f"状态 '{state_def.name}' 处理失败: {e}")
            # 记录错误但继续执行
            errors = state.get("errors", [])
            errors.append(f"状态 {state_def.name} 处理失败: {str(e)}")
            state.add_error(f"状态 {state_def.name} 处理失败: {str(e)}")
            return state
    
    def _default_state_handler(self, state: WorkflowState, state_def: StateDefinition) -> WorkflowState:
        """默认状态处理函数
        
        Args:
            state: 当前状态
            state_def: 状态定义
            
        Returns:
            WorkflowState: 处理后的状态
        """
        # 记录状态执行信息
        execution_info = state.get("execution_info", {})
        if not isinstance(execution_info, dict):
            execution_info = {}
        execution_info[state_def.name] = {
            "executed_at": "now",  # 实际应该使用datetime
            "state_type": state_def.state_type.value
        }
        state.set_value("execution_info", execution_info)
        
        # 更新当前状态字段
        state.set_value("current_state", state_def.name)
        
        return state
    
    def _determine_next_state(self, state_def: StateDefinition, state: WorkflowState) -> Optional[str]:
        """确定下一个状态
        
        Args:
            state_def: 当前状态定义
            state: 当前工作流状态
            
        Returns:
            Optional[str]: 下一个状态名，None表示终止
        """
        # 如果没有转移，返回None
        if not state_def.transitions:
            return None
        
        # 评估转移条件
        for transition in state_def.transitions:
            if self._evaluate_transition_condition(transition, state):
                return transition.target_state
        
        # 如果没有条件满足，使用第一个无条件转移
        unconditional_transitions = [t for t in state_def.transitions if t.condition is None]
        if unconditional_transitions:
            return unconditional_transitions[0].target_state
        
        return None
    
    def _evaluate_transition_condition(self, transition: Transition, state: WorkflowState) -> bool:
        """评估转移条件
        
        Args:
            transition: 转移定义
            state: 当前工作流状态
            
        Returns:
            bool: 条件是否满足
        """
        if transition.condition is None:
            return True
        
        # 简单的条件评估实现
        # 实际项目中应该使用更强大的条件引擎
        try:
            # 这里可以扩展为支持更复杂的条件表达式
            condition = transition.condition.lower()
            
            if condition == "always":
                return True
            elif condition == "never":
                return False
            elif condition.startswith("has_"):
                field = condition[4:]
                value = state.get(field)
                return value is not None and bool(value)
            elif condition.startswith("not_has_"):
                field = condition[8:]
                value = state.get(field)
                return value is None or not bool(value)
            
            # 默认返回False
            return False
        except Exception as e:
            logger.warning(f"条件评估失败: {transition.condition}, 错误: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """验证状态机配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors: List[str] = []
        
        # 验证状态机配置
        state_machine_errors = self.state_machine_config.validate()
        errors.extend(state_machine_errors)
        
        return errors
    
    def reset(self) -> None:
        """重置状态机到初始状态"""
        self.current_state = self.state_machine_config.initial_state
    
    def get_current_state_info(self) -> Optional[Dict[str, Any]]:
        """获取当前状态信息
        
        Returns:
            Optional[Dict[str, Any]]: 当前状态信息
        """
        if self.current_state is None:
            return None
        
        state_def = self.state_machine_config.get_state(self.current_state)
        if state_def is None:
            return None
        
        return {
            "name": state_def.name,
            "type": state_def.state_type.value,
            "description": state_def.description,
            "transitions": [
                {
                    "target": t.target_state,
                    "condition": t.condition,
                    "description": t.description
                }
                for t in state_def.transitions
            ]
        }