"""对象池状态管理器

提供高性能的状态管理和对象重用功能。
"""

import time
import threading
from typing import Dict, Any, List, Optional, Set, Union
from collections import defaultdict
from dataclasses import dataclass

from .base_manager import BaseStateManager
from .serializer import StateSerializer, StateDiff


@dataclass
class StateUpdate:
    """状态更新"""
    field_path: str
    old_value: Any
    new_value: Any
    timestamp: float


class PoolingStateManager(BaseStateManager):
    """对象池状态管理器
    
    提供以下优化功能：
    1. 增量状态更新
    2. 状态对象池
    3. 内存优化
    4. 并发安全
    """
    
    def __init__(
        self,
        enable_pooling: bool = True,
        max_pool_size: int = 100,
        enable_diff_tracking: bool = True
    ):
        """初始化对象池状态管理器
        
        Args:
            enable_pooling: 是否启用对象池
            max_pool_size: 对象池最大大小
            enable_diff_tracking: 是否启用差异跟踪
        """
        super().__init__()
        self._enable_pooling = enable_pooling
        self._max_pool_size = max_pool_size
        self._enable_diff_tracking = enable_diff_tracking
        
        # 状态对象池
        self._state_pool: Dict[str, Dict[str, Any]] = {}
        self._pool_lock = threading.RLock()
        
        # 差异跟踪
        self._state_history: Dict[str, List[StateUpdate]] = defaultdict(list)
        self._history_lock = threading.RLock()
        self._max_history_size = 50
        
        # 内存优化
        self._compressed_states: Dict[str, Dict[str, Any]] = {}
        self._compression_lock = threading.RLock()
        
        # 序列化器
        self._serializer = StateSerializer(
            max_cache_size=500,
            cache_ttl_seconds=1800,
            enable_diff_serialization=True
        )
        
        # 性能统计
        self._stats = {
            "total_updates": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "memory_saved": 0,
            "diff_applications": 0
        }
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态（使用对象池）
        
        Args:
            state_id: 状态ID
            initial_state: 初始状态
            
        Returns:
            创建的状态
        """
        if not self._enable_pooling:
            import copy
            return copy.deepcopy(initial_state) if initial_state else {}
        
        with self._pool_lock:
            # 检查对象池
            if state_id in self._state_pool:
                self._stats["pool_hits"] += 1
                # 重用现有状态对象
                pooled_state = self._state_pool[state_id]
                # 清空并更新
                pooled_state.clear()
                pooled_state.update(initial_state)
                return pooled_state
            
            self._stats["pool_misses"] += 1
            
            # 创建新状态
            new_state = initial_state.copy() if initial_state else {}
            self._state_pool[state_id] = new_state
            
            # 检查池大小
            if len(self._state_pool) > self._max_pool_size:
                # 移除最久未使用的状态
                oldest_id = next(iter(self._state_pool))
                del self._state_pool[oldest_id]
            
            return new_state
    
    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """增量更新状态
        
        Args:
            state_id: 状态ID
            current_state: 当前状态
            updates: 更新字典
            
        Returns:
            更新后的状态
        """
        start_time = time.time()
        
        # 使用写时复制策略
        if self._enable_diff_tracking:
            new_state = self._apply_incremental_updates(current_state, updates)
            
            # 记录更新历史
            self._record_updates(state_id, current_state, new_state)
        else:
            # 回退到完整复制
            import copy
            new_state = copy.deepcopy(current_state)
            new_state.update(updates)
        
        self._stats["total_updates"] += 1
        
        return new_state
    
    def apply_state_diff(
        self,
        state_id: str,
        base_state: Dict[str, Any],
        diff_data: Union[str, bytes]
    ) -> Dict[str, Any]:
        """应用状态差异
        
        Args:
            state_id: 状态ID
            base_state: 基础状态
            diff_data: 差异数据
            
        Returns:
            应用差异后的状态
        """
        # 使用序列化器的差异应用功能
        new_state = self._serializer.apply_diff(base_state, diff_data)
        
        self._stats["diff_applications"] += 1
        
        # 记录更新历史
        if self._enable_diff_tracking:
            self._record_updates(state_id, base_state, new_state)
        
        return new_state
    
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态对象，如果不存在则返回None
        """
        if state_id in self._state_pool:
            import copy
            return copy.deepcopy(self._state_pool[state_id])
        return None
    
    def compress_state(self, state_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """压缩状态（内存优化）
        
        Args:
            state_id: 状态ID
            state: 要压缩的状态
            
        Returns:
            压缩后的状态
        """
        with self._compression_lock:
            # 使用序列化器的优化功能
            compressed = self._serializer.optimize_state_for_storage(state)
            
            # 存储压缩版本
            self._compressed_states[state_id] = compressed
            
            # 计算内存节省
            original_size = self._estimate_state_size(state)
            compressed_size = self._estimate_state_size(compressed)
            self._stats["memory_saved"] += (original_size - compressed_size)
            
            return compressed
    
    def get_state_history(self, state_id: str, limit: int = 10) -> List[StateUpdate]:
        """获取状态更新历史
        
        Args:
            state_id: 状态ID
            limit: 返回的最大更新数
            
        Returns:
            状态更新列表
        """
        with self._history_lock:
            history = self._state_history.get(state_id, [])
            return history[-limit:] if history else []
    
    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """获取内存使用统计
        
        Returns:
            内存使用统计
        """
        pool_memory = sum(self._estimate_state_size(state) for state in self._state_pool.values())
        compressed_memory = sum(self._estimate_state_size(state) for state in self._compressed_states.values())
        history_memory = len(self._state_history) * self._max_history_size * 100  # 估算
        
        return {
            "pool_size": len(self._state_pool),
            "compressed_states_size": len(self._compressed_states),
            "history_entries": sum(len(h) for h in self._state_history.values()),
            "pool_memory_bytes": pool_memory,
            "compressed_memory_bytes": compressed_memory,
            "history_memory_bytes": history_memory,
            "total_memory_bytes": pool_memory + compressed_memory + history_memory,
            "memory_saved_bytes": self._stats["memory_saved"]
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计信息
        """
        serializer_stats = self._serializer.get_performance_stats()
        
        return {
            "manager_stats": self._stats.copy(),
            "serializer_stats": serializer_stats,
            "pool_efficiency": {
                "hits": self._stats["pool_hits"],
                "misses": self._stats["pool_misses"],
                "hit_rate": f"{(self._stats['pool_hits'] / (self._stats['pool_hits'] + self._stats['pool_misses']) * 100):.2f}%"
                           if (self._stats['pool_hits'] + self._stats['pool_misses']) > 0 else "0%"
            }
        }
    
    def cleanup(self, state_id: Optional[str] = None) -> None:
        """清理资源
        
        Args:
            state_id: 要清理的状态ID，如果为None则清理所有
        """
        if state_id:
            # 清理特定状态
            with self._pool_lock:
                self._state_pool.pop(state_id, None)
            
            with self._compression_lock:
                self._compressed_states.pop(state_id, None)
            
            with self._history_lock:
                self._state_history.pop(state_id, None)
        else:
            # 清理所有状态
            with self._pool_lock:
                self._state_pool.clear()
            
            with self._compression_lock:
                self._compressed_states.clear()
            
            with self._history_lock:
                self._state_history.clear()
            
            # 清理序列化器缓存
            self._serializer.clear_cache()
    
    def _apply_incremental_updates(
        self,
        base_state: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用增量更新
        
        Args:
            base_state: 基础状态
            updates: 更新字典
            
        Returns:
            更新后的状态
        """
        # 创建新状态，只复制需要更新的部分
        import copy
        new_state = copy.deepcopy(base_state)
        
        for key, new_value in updates.items():
            if key in base_state and base_state[key] == new_value:
                # 值相同，跳过
                continue
            
            # 对于列表类型，使用增量更新
            if key in base_state and isinstance(base_state[key], list) and isinstance(new_value, list):
                if len(new_value) > len(base_state[key]):
                    # 只添加新元素
                    new_state[key] = base_state[key] + new_value[len(base_state[key]):]
                else:
                    new_state[key] = new_value
            else:
                new_state[key] = new_value
        
        return new_state
    
    def _record_updates(
        self,
        state_id: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> None:
        """记录状态更新
        
        Args:
            state_id: 状态ID
            old_state: 旧状态
            new_state: 新状态
        """
        with self._history_lock:
            updates = []
            
            # 检查所有字段的变化
            all_keys = set(old_state.keys()) | set(new_state.keys())
            
            for key in all_keys:
                old_value = old_state.get(key)
                new_value = new_state.get(key)
                
                if old_value != new_value:
                    updates.append(StateUpdate(
                        field_path=key,
                        old_value=old_value,
                        new_value=new_value,
                        timestamp=time.time()
                    ))
            
            # 添加到历史记录
            if updates:
                self._state_history[state_id].extend(updates)
                
                # 限制历史记录大小
                if len(self._state_history[state_id]) > self._max_history_size:
                    self._state_history[state_id] = self._state_history[state_id][-self._max_history_size:]
    
    def _estimate_state_size(self, state: Dict[str, Any]) -> int:
        """估算状态大小（字节）
        
        Args:
            state: 状态
            
        Returns:
            估算的大小（字节）
        """
        # 简单的估算方法
        size = 0
        
        # 计算基本字段
        for key, value in state.items():
            size += len(key)  # 键名
            if isinstance(value, str):
                size += len(value)
            elif isinstance(value, (int, float)):
                size += 8
            elif isinstance(value, list):
                size += len(value) * 10  # 粗略估算
            elif isinstance(value, dict):
                size += len(value) * 20  # 粗略估算
            else:
                size += 16  # 其他类型
        
        return size


# 便捷的状态管理函数
def create_optimized_state_manager(
    enable_pooling: bool = True,
    max_pool_size: int = 10,
    enable_diff_tracking: bool = True
) -> 'PoolingStateManager':
    """创建优化的状态管理器（对象池管理器）
    
    Args:
        enable_pooling: 是否启用对象池
        max_pool_size: 对象池最大大小
        enable_diff_tracking: 是否启用差异跟踪
        
    Returns:
        优化的状态管理器实例
    """
    return PoolingStateManager(
        enable_pooling=enable_pooling,
        max_pool_size=max_pool_size,
        enable_diff_tracking=enable_diff_tracking
    )