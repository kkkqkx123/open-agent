"""LLM管理器状态机实现

负责管理LLM管理器的状态转换。
"""

from src.interfaces.dependency_injection import get_logger
from enum import Enum
from typing import Callable, Dict, Optional, Any

logger = get_logger(__name__)


class LLMManagerState(Enum):
    """LLM管理器状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    RECOVERING = "recovering"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


class StateTransitionError(Exception):
    """状态转换错误"""
    pass


class StateMachine:
    """状态机实现
    
    管理LLM管理器的状态转换，确保状态转换的合法性和一致性。
    """
    
    def __init__(self):
        """初始化状态机"""
        self._current_state = LLMManagerState.UNINITIALIZED
        self._state_history: list[LLMManagerState] = [self._current_state]
        self._state_data: Dict[LLMManagerState, Dict[str, Any]] = {}
        self._transitions: Dict[LLMManagerState, Dict[LLMManagerState, Callable]] = {
            LLMManagerState.UNINITIALIZED: {
                LLMManagerState.INITIALIZING: self._on_start_initialization,
                LLMManagerState.SHUTTING_DOWN: self._on_start_shutdown,
            },
            LLMManagerState.INITIALIZING: {
                LLMManagerState.READY: self._on_initialization_complete,
                LLMManagerState.ERROR: self._on_initialization_failed,
                LLMManagerState.SHUTTING_DOWN: self._on_start_shutdown,
            },
            LLMManagerState.READY: {
                LLMManagerState.ERROR: self._on_error,
                LLMManagerState.RECOVERING: self._on_start_recovery,
                LLMManagerState.SHUTTING_DOWN: self._on_start_shutdown,
            },
            LLMManagerState.ERROR: {
                LLMManagerState.RECOVERING: self._on_start_recovery,
                LLMManagerState.SHUTTING_DOWN: self._on_start_shutdown,
            },
            LLMManagerState.RECOVERING: {
                LLMManagerState.READY: self._on_recovery_complete,
                LLMManagerState.ERROR: self._on_recovery_failed,
                LLMManagerState.SHUTTING_DOWN: self._on_start_shutdown,
            },
            LLMManagerState.SHUTTING_DOWN: {
                LLMManagerState.SHUTDOWN: self._on_shutdown_complete,
                LLMManagerState.ERROR: self._on_shutdown_failed,
            },
            LLMManagerState.SHUTDOWN: {
                # 终态，不允许转换
            },
        }
        
        # 状态转换回调
        self._transition_callbacks: Dict[str, Callable] = {}
    
    @property
    def current_state(self) -> LLMManagerState:
        """获取当前状态"""
        return self._current_state
    
    @property
    def state_history(self) -> list[LLMManagerState]:
        """获取状态历史"""
        return self._state_history.copy()
    
    def can_transition_to(self, new_state: LLMManagerState) -> bool:
        """
        检查是否可以转换到新状态
        
        Args:
            new_state: 目标状态
            
        Returns:
            bool: 是否可以转换
        """
        return new_state in self._transitions.get(self._current_state, {})
    
    def get_allowed_transitions(self) -> list[LLMManagerState]:
        """
        获取当前状态允许的转换
        
        Returns:
            list[LLMManagerState]: 允许转换的状态列表
        """
        return list(self._transitions.get(self._current_state, {}).keys())
    
    def transition_to(self, new_state: LLMManagerState, *args, **kwargs) -> bool:
        """
        转换到新状态
        
        Args:
            new_state: 目标状态
            *args: 传递给状态处理函数的位置参数
            **kwargs: 传递给状态处理函数的关键字参数
            
        Returns:
            bool: 转换是否成功
            
        Raises:
            StateTransitionError: 状态转换失败
        """
        if not self.can_transition_to(new_state):
            raise StateTransitionError(f"不能从 {self._current_state.value} 转换到 {new_state.value}")
        
        old_state = self._current_state
        
        try:
            # 调用状态转换处理函数
            transition_handler = self._transitions[self._current_state][new_state]
            if transition_handler:
                transition_handler(*args, **kwargs)
            
            # 更新状态
            self._current_state = new_state
            self._state_history.append(new_state)
            
            logger.info(f"状态转换: {old_state.value} -> {new_state.value}")
            
            # 调用注册的回调
            self._call_transition_callbacks(old_state, new_state, *args, **kwargs)
            
            return True
            
        except Exception as e:
            logger.error(f"状态转换失败: {old_state.value} -> {new_state.value}, 错误: {e}")
            raise StateTransitionError(f"状态转换失败: {e}") from e
    
    def set_state_data(self, state: LLMManagerState, key: str, value: Any) -> None:
        """
        设置状态数据
        
        Args:
            state: 状态
            key: 键
            value: 值
        """
        if state not in self._state_data:
            self._state_data[state] = {}
        self._state_data[state][key] = value
    
    def get_state_data(self, state: LLMManagerState, key: str, default: Any = None) -> Any:
        """
        获取状态数据
        
        Args:
            state: 状态
            key: 键
            default: 默认值
            
        Returns:
            Any: 状态数据
        """
        return self._state_data.get(state, {}).get(key, default)
    
    def register_transition_callback(self, name: str, callback: Callable) -> None:
        """
        注册状态转换回调
        
        Args:
            name: 回调名称
            callback: 回调函数
        """
        self._transition_callbacks[name] = callback
    
    def unregister_transition_callback(self, name: str) -> None:
        """
        注销状态转换回调
        
        Args:
            name: 回调名称
        """
        if name in self._transition_callbacks:
            del self._transition_callbacks[name]
    
    def _call_transition_callbacks(self, old_state: LLMManagerState, new_state: LLMManagerState, *args, **kwargs) -> None:
        """
        调用状态转换回调
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            *args: 位置参数
            **kwargs: 关键字参数
        """
        for name, callback in self._transition_callbacks.items():
            try:
                callback(old_state, new_state, *args, **kwargs)
            except Exception as e:
                logger.warning(f"状态转换回调 {name} 执行失败: {e}")
    
    # 状态处理函数
    def _on_start_initialization(self) -> None:
        """开始初始化时的处理"""
        logger.debug("开始初始化LLM管理器")
        self.set_state_data(LLMManagerState.INITIALIZING, "start_time", logger.info)
    
    def _on_initialization_complete(self) -> None:
        """初始化完成时的处理"""
        logger.debug("LLM管理器初始化完成")
        self.set_state_data(LLMManagerState.READY, "ready_time", logger.info)
    
    def _on_initialization_failed(self, error: Exception) -> None:
        """初始化失败时的处理"""
        logger.error(f"LLM管理器初始化失败: {error}")
        self.set_state_data(LLMManagerState.ERROR, "error", error)
        self.set_state_data(LLMManagerState.ERROR, "error_time", logger.info)
    
    def _on_error(self, error: Exception) -> None:
        """发生错误时的处理"""
        logger.error(f"LLM管理器发生错误: {error}")
        self.set_state_data(LLMManagerState.ERROR, "error", error)
        self.set_state_data(LLMManagerState.ERROR, "error_time", logger.info)
    
    def _on_start_recovery(self) -> None:
        """开始恢复时的处理"""
        logger.info("开始恢复LLM管理器")
        self.set_state_data(LLMManagerState.RECOVERING, "recovery_start_time", logger.info)
    
    def _on_recovery_complete(self) -> None:
        """恢复完成时的处理"""
        logger.info("LLM管理器恢复完成")
        self.set_state_data(LLMManagerState.READY, "recovery_time", logger.info)
    
    def _on_recovery_failed(self, error: Exception) -> None:
        """恢复失败时的处理"""
        logger.error(f"LLM管理器恢复失败: {error}")
        self.set_state_data(LLMManagerState.ERROR, "recovery_error", error)
        self.set_state_data(LLMManagerState.ERROR, "error_time", logger.info)
    
    def _on_start_shutdown(self) -> None:
        """开始关闭时的处理"""
        logger.info("开始关闭LLM管理器")
        self.set_state_data(LLMManagerState.SHUTTING_DOWN, "shutdown_start_time", logger.info)
    
    def _on_shutdown_complete(self) -> None:
        """关闭完成时的处理"""
        logger.info("LLM管理器关闭完成")
        self.set_state_data(LLMManagerState.SHUTDOWN, "shutdown_time", logger.info)
    
    def _on_shutdown_failed(self, error: Exception) -> None:
        """关闭失败时的处理"""
        logger.error(f"LLM管理器关闭失败: {error}")
        self.set_state_data(LLMManagerState.ERROR, "shutdown_error", error)
        self.set_state_data(LLMManagerState.ERROR, "error_time", logger.info)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        获取状态摘要
        
        Returns:
            Dict[str, Any]: 状态摘要
        """
        return {
            "current_state": self._current_state.value,
            "state_history": [state.value for state in self._state_history],
            "allowed_transitions": [state.value for state in self.get_allowed_transitions()],
            "state_data": {
                state.value: data for state, data in self._state_data.items() if data
            },
        }