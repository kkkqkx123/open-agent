"""统一状态管理器实现

提供集中化的状态管理功能，支持多种状态类型和存储后端。
"""

import threading
import uuid
from src.services.logger import get_logger
from typing import Any, Dict, List, Optional, Type, Callable

from ..interfaces.base import (
    IState, IStateManager, IStateValidator,
    IStateCache, IStateStorageAdapter
)
from src.interfaces.state.serializer import IStateSerializer
from src.interfaces.state.lifecycle import IStateLifecycleManager
from .base import BaseStateSerializer, BaseStateValidator, BaseStateLifecycleManager


logger = get_logger(__name__)


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
        self._cache = self._create_cache(config.get('cache', {}))
        self._storage = storage_adapter
        self._lock = threading.RLock()
        
        # 状态类型注册表
        self._state_types: Dict[str, Type[IState]] = {}
        self._register_default_state_types()
        
        # 统计信息
        self._statistics = {
            "total_created": 0,
            "total_retrieved": 0,
            "total_saved": 0,
            "total_deleted": 0,
            "total_errors": 0
        }
    
    def _create_serializer(self, serializer_config: Dict[str, Any]) -> IStateSerializer:
        """创建序列化器"""
        format_type = serializer_config.get('format', 'json')
        compression = serializer_config.get('compression', True)
        return BaseStateSerializer(format=format_type, compression=compression)
    
    def _create_validator(self, validator_config: Dict[str, Any]) -> IStateValidator:
        """创建验证器"""
        strict_mode = validator_config.get('strict_mode', False)
        return BaseStateValidator(strict_mode=strict_mode)
    
    def _create_lifecycle_manager(self, lifecycle_config: Dict[str, Any]) -> IStateLifecycleManager:
        """创建生命周期管理器"""
        return BaseStateLifecycleManager()
    
    def _create_cache(self, cache_config: Dict[str, Any]) -> IStateCache:
        """创建缓存"""
        if cache_config.get('enabled', True):
            from .cache_adapter import StateCacheAdapter
            return StateCacheAdapter(
                cache_name=cache_config.get('name', 'state'),
                max_size=cache_config.get('max_size', 1000),
                ttl=cache_config.get('ttl', 300),
                enable_serialization=cache_config.get('enable_serialization', False)
            )
        else:
            from .cache_adapter import NoOpCacheAdapter
            return NoOpCacheAdapter()
    

    def _register_default_state_types(self) -> None:
        """注册默认状态类型"""
        # 延迟导入避免循环依赖
        from ..implementations.workflow_state import WorkflowState
        from ..implementations.tool_state import ToolState
        from ..implementations.session_state import SessionState
        from ..implementations.thread_state import ThreadState
        from ..implementations.checkpoint_state import CheckpointState
        
        self.register_state_type('workflow', WorkflowState)
        self.register_state_type('tool', ToolState)
        self.register_state_type('session', SessionState)
        self.register_state_type('thread', ThreadState)
        self.register_state_type('checkpoint', CheckpointState)
    
    def register_state_type(self, state_type: str, state_class: Type[IState]) -> None:
        """注册状态类型
        
        Args:
            state_type: 状态类型名称
            state_class: 状态类
        """
        with self._lock:
            self._state_types[state_type] = state_class
            logger.debug(f"注册状态类型: {state_type} -> {state_class.__name__}")
    
    async def create_state(self, state_type: str, **kwargs: Any) -> IState:
        """创建状态
        
        Args:
            state_type: 状态类型
            **kwargs: 状态参数
            
        Returns:
            创建的状态实例
            
        Raises:
            ValueError: 未知状态类型
        """
        with self._lock:
            try:
                if state_type not in self._state_types:
                    raise ValueError(f"未知状态类型: {state_type}")
                
                state_class = self._state_types[state_type]
                
                # 生成ID（如果未提供）
                if 'id' not in kwargs:
                    kwargs['id'] = f"{state_type}_{uuid.uuid4().hex[:8]}"
                
                state = state_class(**kwargs)
                
                # 验证状态
                errors = self._validator.validate_state(state)
                if errors:
                    raise ValueError(f"状态验证失败: {errors}")
                
                # 注册生命周期管理
                self._lifecycle.register_state(state)
                
                # 保存到存储
                await self.save_state(state)
                
                self._statistics["total_created"] += 1
                logger.debug(f"创建状态: {state.get_id()} (类型: {state_type})")
                
                return state
            except Exception as e:
                self._statistics["total_errors"] += 1
                logger.error(f"创建状态失败: {e}")
                raise
    
    async def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态实例，如果未找到则返回None
        """
        with self._lock:
            try:
                # 先从缓存获取
                cached_state = self._cache.get(state_id)
                if cached_state:
                    self._statistics["total_retrieved"] += 1
                    return cached_state
                
                # 从存储获取
                state_data = await self._storage.get(state_id)
                if not state_data:
                    return None
                
                # 反序列化
                state = self._serializer.deserialize(state_data)
                
                # 缓存状态
                self._cache.put(state_id, state)
                
                self._statistics["total_retrieved"] += 1
                logger.debug(f"获取状态: {state_id}")
                
                return state
            except Exception as e:
                self._statistics["total_errors"] += 1
                logger.error(f"获取状态失败: {e}")
                return None
    
    async def save_state(self, state: IState) -> bool:
        """保存状态
        
        Args:
            state: 状态实例
            
        Returns:
            是否保存成功
        """
        with self._lock:
            try:
                # 获取状态ID
                state_id = state.get_id()
                if not state_id:
                    logger.error("无法保存状态：状态ID为空")
                    self._statistics["total_errors"] += 1
                    return False
                
                # 验证状态
                errors = self._validator.validate_state(state)
                if errors:
                    logger.warning(f"状态验证警告: {errors}")
                
                # 序列化状态
                serialized_data = self._serializer.serialize(state)
                
                # 保存到存储
                success = await self._storage.save(state_id, serialized_data)
                
                if success:
                    # 更新缓存
                    self._cache.put(state_id, state)
                    
                    # 触发生命周期事件
                    self._lifecycle.on_state_saved(state)
                    
                    self._statistics["total_saved"] += 1
                    logger.debug(f"保存状态: {state.get_id()}")
                
                return success
            except Exception as e:
                self._statistics["total_errors"] += 1
                self._lifecycle.on_state_error(state, e)
                logger.error(f"保存状态失败: {e}")
                return False
    
    async def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            是否删除成功
        """
        with self._lock:
            try:
                # 从存储删除
                success = await self._storage.delete(state_id)
                
                if success:
                    # 从缓存删除
                    self._cache.delete(state_id)
                    
                    # 触发生命周期事件
                    self._lifecycle.on_state_deleted(state_id)
                    
                    self._statistics["total_deleted"] += 1
                    logger.debug(f"删除状态: {state_id}")
                
                return success
            except Exception as e:
                self._statistics["total_errors"] += 1
                logger.error(f"删除状态失败: {e}")
                return False
    
    async def list_states(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """列出状态ID
        
        Args:
            filters: 过滤条件
            
        Returns:
            状态ID列表
        """
        with self._lock:
            try:
                return await self._storage.list(filters)
            except Exception as e:
                self._statistics["total_errors"] += 1
                logger.error(f"列出状态失败: {e}")
                return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                **self._statistics,
                "cache_stats": self._cache.get_statistics() if hasattr(self._cache, 'get_statistics') else {},
                "storage_stats": await self._storage.get_statistics(),
                "lifecycle_stats": self._lifecycle.get_statistics(),
                "registered_state_types": list(self._state_types.keys())
            }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            try:
                self._cache.clear()
            except Exception as e:
                logger.warning(f"清空缓存失败: {e}")
            logger.debug("清空状态缓存")
    
    async def cleanup_expired_states(self) -> int:
        """清理过期状态
        
        Returns:
            清理的状态数量
        """
        with self._lock:
            cleaned_count = 0
            
            try:
                # 获取所有状态
                state_ids = await self.list_states()
                
                for state_id in state_ids:
                    state = await self.get_state(state_id)
                    if state:
                        # 检查状态是否有is_expired方法或检查更新时间
                        is_expired = False
                        if hasattr(state, 'is_expired'):
                            try:
                                is_expired = getattr(state, 'is_expired')()
                            except Exception:
                                is_expired = False
                        
                        if is_expired and await self.delete_state(state_id):
                            cleaned_count += 1
                
                logger.info(f"清理了 {cleaned_count} 个过期状态")
                return cleaned_count
            except Exception as e:
                self._statistics["total_errors"] += 1
                logger.error(f"清理过期状态失败: {e}")
                return 0