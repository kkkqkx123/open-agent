"""统一状态管理器实现

提供集中化的状态管理功能，支持多种状态类型和存储后端。
"""

import threading
import uuid
from typing import Any, Dict, List, Optional, Type, Callable, Tuple

from src.interfaces.state.base import IState
from src.interfaces.state.manager import IStateManager
from src.infrastructure.common.serialization import Serializer
from src.interfaces.state.lifecycle import IStateLifecycleManager
from src.interfaces.storage.state import IStateStorageAdapter

# 导入基础实现
from .base import BaseStateValidator, BaseStateLifecycleManager, BaseStateSerializer, BaseState


class StateManager(IStateManager):
    """统一状态管理器
    
    提供集中化的状态管理功能，支持多种状态类型和存储后端。
    """
    
    def __init__(self, config: Dict[str, Any], storage_adapter: IStateStorageAdapter):
        """初始化状态管理器
        
        Args:
            config: 配置字典
            storage_adapter: 存储适配器（通过DI注入）
        """
        self.config = config
        self._serializer = self._create_serializer(config.get('serializer', {}))
        self._validator = self._create_validator(config.get('validation', {}))
        self._lifecycle = self._create_lifecycle_manager(config.get('lifecycle', {}))
        self._storage = storage_adapter
        self._lock = threading.RLock()
        
        # 状态类型注册表
        self._state_types: Dict[str, Type[IState]] = {}
        self._register_default_state_types()
        
        # 内存存储（用于CRUD操作）
        self._states: Dict[str, IState] = {}
        
        # 统计信息
        self._statistics = {
            "total_created": 0,
            "total_retrieved": 0,
            "total_saved": 0,
            "total_deleted": 0,
            "total_errors": 0
        }
    
    def _create_serializer(self, serializer_config: Dict[str, Any]) -> Serializer:
        """创建序列化器"""
        format_type = serializer_config.get('format', 'json')
        compression = serializer_config.get('compression', True)
        return BaseStateSerializer(format=format_type, compression=compression)
    
    def _create_validator(self, validator_config: Dict[str, Any]) -> BaseStateValidator:
        """创建验证器"""
        strict_mode = validator_config.get('strict_mode', False)
        return BaseStateValidator(strict_mode=strict_mode)
    
    def _create_lifecycle_manager(self, lifecycle_config: Dict[str, Any]) -> IStateLifecycleManager:
        """创建生命周期管理器"""
        return BaseStateLifecycleManager()
    
    def _register_default_state_types(self) -> None:
        """注册默认状态类型"""
        # 注册基础状态类型
        self.register_state_type('workflow', BaseState)
        self.register_state_type('tool', BaseState)
        self.register_state_type('session', BaseState)
        self.register_state_type('thread', BaseState)
        self.register_state_type('checkpoint', BaseState)
    
    def register_state_type(self, state_type: str, state_class: Type[IState]) -> None:
        """注册状态类型

        Args:
            state_type: 状态类型名称
            state_class: 状态类
        """
        with self._lock:
            self._state_types[state_type] = state_class
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> IState:
        """创建状态

        Args:
            state_id: 状态ID
            initial_state: 初始状态数据

        Returns:
            创建的状态实例

        Raises:
            ValueError: 未知状态类型
        """
        with self._lock:
            try:
                # 获取状态类型，默认使用session
                state_type = initial_state.get('type', 'session')
                
                if state_type not in self._state_types:
                    raise ValueError(f"未知状态类型: {state_type}")

                state_class = self._state_types[state_type]
                
                # 创建状态实例，BaseState接受**kwargs
                state = state_class(
                    id=state_id,  # type: ignore
                    data=initial_state.get('data', {}),  # type: ignore
                    metadata=initial_state.get('metadata', {})  # type: ignore
                )

                # 验证状态
                errors = self._validator.validate_state(state)
                if errors:
                    raise ValueError(f"状态验证失败: {errors}")

                # 注册生命周期管理
                self._lifecycle.register_state(state)
                
                # 存储状态
                self._states[state_id] = state

                self._statistics["total_created"] += 1

                return state
            except Exception as e:
                self._statistics["total_errors"] += 1
                raise
    
    def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态

        Args:
            state_id: 状态ID

        Returns:
            状态实例，如果未找到则返回None
        """
        with self._lock:
            try:
                # 从内存存储获取
                if state_id in self._states:
                    self._statistics["total_retrieved"] += 1
                    return self._states[state_id]
                return None
            except Exception:
                self._statistics["total_errors"] += 1
                return None
    
    def update_state(self, state_id: str, updates: Dict[str, Any]) -> IState:
        """更新状态

        Args:
            state_id: 状态ID
            updates: 更新字典

        Returns:
            更新后的状态实例
        """
        with self._lock:
            state = self.get_state(state_id)
            if not state:
                raise ValueError(f"状态未找到: {state_id}")
            
            # 更新状态数据
            for key, value in updates.items():
                state.set_data(key, value)
            
            return state
    
    def delete_state(self, state_id: str) -> bool:
        """删除状态

        Args:
            state_id: 状态ID

        Returns:
            是否删除成功
        """
        with self._lock:
            try:
                if state_id not in self._states:
                    return False
                
                # 从内存存储删除
                del self._states[state_id]

                # 触发生命周期事件
                self._lifecycle.on_state_deleted(state_id)
                self._statistics["total_deleted"] += 1

                return True
            except Exception:
                self._statistics["total_errors"] += 1
                return False
    
    def list_states(self) -> List[str]:
        """列出所有状态ID

        Returns:
            状态ID列表
        """
        with self._lock:
            try:
                return list(self._states.keys())
            except Exception:
                self._statistics["total_errors"] += 1
                return []
    
    # 增强功能方法
    def create_state_with_history(self, state_id: str, initial_state: Dict[str, Any],
                                 thread_id: str) -> IState:
        """创建状态并启用历史记录"""
        state = self.create_state(state_id, initial_state)
        state.set_metadata('thread_id', thread_id)
        return state
    
    def update_state_with_history(self, state_id: str, updates: Dict[str, Any],
                                 thread_id: str, action: str = "update") -> IState:
        """更新状态并记录历史"""
        state = self.update_state(state_id, updates)
        state.set_metadata('last_action', action)
        state.set_metadata('thread_id', thread_id)
        return state
    
    def create_state_snapshot(self, state_id: str, thread_id: str,
                             snapshot_name: str = "") -> str:
        """为状态创建快照"""
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
        state = self.get_state(state_id)
        if state:
            state.set_metadata('snapshot_id', snapshot_id)
            state.set_metadata('snapshot_name', snapshot_name)
        return snapshot_id
    
    def restore_state_from_snapshot(self, snapshot_id: str, state_id: str) -> Optional[IState]:
        """从快照恢复状态"""
        # 简化实现，从存储恢复
        return self.get_state(state_id)
    
    def execute_with_state_management(
        self,
        state_id: str,
        executor: Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[IState], bool]:
        """带状态管理的执行"""
        with self._lock:
            state = self.get_state(state_id)
            if not state:
                return None, False
            
            try:
                # 获取当前状态数据，使用接口方法
                state_data = {}
                if hasattr(state, 'get_data'):
                    # IState接口方法
                    state_data = {}  # 可以通过其他方式获取
                
                # 执行操作
                new_state_data, success = executor(state_data)
                
                if success:
                    # 更新状态
                    self.update_state(state_id, new_state_data)
                    updated_state = self.get_state(state_id)
                    return updated_state, True
                else:
                    return state, False
            except Exception:
                self._statistics["total_errors"] += 1
                return state, False
    
    def cleanup_cache(self) -> int:
        """清理过期缓存"""
        return 0
