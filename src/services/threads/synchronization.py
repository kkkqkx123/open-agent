"""线程同步和状态复制服务"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
import copy

class SyncStrategy(str, Enum):
    """同步策略枚举"""
    OVERWRITE = "overwrite"           # 覆盖策略
    MERGE = "merge"                   # 合并策略

class ReplicationStrategy(str, Enum):
    """复制策略枚举"""
    FULL_COPY = "full_copy"           # 完整复制
    SELECTIVE_COPY = "selective_copy" # 选择性复制
    REFERENCE_ONLY = "reference_only" # 仅引用
    INCREMENTAL = "incremental"       # 增量复制

class ConflictType(str, Enum):
    """冲突类型枚举"""
    VALUE_CONFLICT = "value_conflict"           # 值冲突
    STRUCTURE_CONFLICT = "structure_conflict"   # 结构冲突
    TYPE_CONFLICT = "type_conflict"             # 类型冲突
    REFERENCE_CONFLICT = "reference_conflict"   # 引用冲突

class ConflictResolution(str, Enum):
    """冲突解决方式枚举"""
    KEEP_SOURCE = "keep_source"         # 保持源值
    KEEP_TARGET = "keep_target"         # 保持目标值
    MERGE_VALUES = "merge_values"       # 合并值
    LATEST_WINS = "latest_wins"         # 最新获胜
    MANUAL_RESOLVE = "manual_resolve"   # 手动解决
    CUSTOM_HANDLER = "custom_handler"   # 自定义处理

@dataclass
class StateConflict:
    """状态冲突"""
    field_path: str                     # 字段路径
    conflict_type: ConflictType         # 冲突类型
    source_value: Any                   # 源值
    target_value: Any                   # 目标值
    source_timestamp: datetime          # 源时间戳
    target_timestamp: datetime          # 目标时间戳
    resolution: Optional[ConflictResolution] = None  # 解决方案
    resolved_value: Optional[Any] = None  # 解决后的值

@dataclass
class SyncResult:
    """同步结果"""
    success: bool                       # 是否成功
    synced_thread_ids: List[str]        # 已同步的线程ID
    conflicts: List[StateConflict]      # 冲突列表
    resolved_conflicts: List[StateConflict]  # 已解决的冲突
    failed_thread_ids: List[str]        # 失败的线程ID
    sync_metadata: Dict[str, Any]       # 同步元数据
    sync_timestamp: datetime             # 同步时间戳

class IConflictDetector(ABC):
    """冲突检测器接口"""
    
    @abstractmethod
    async def detect_conflicts(
        self,
        source_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> List[StateConflict]:
        """检测状态冲突"""
        pass

class IConflictResolver(ABC):
    """冲突解决器接口"""
    
    @abstractmethod
    async def resolve_conflicts(
        self,
        conflicts: List[StateConflict],
        strategy: ConflictResolution
    ) -> List[StateConflict]:
        """解决冲突"""
        pass

class IStateReplicator(ABC):
    """状态复制器接口"""
    
    @abstractmethod
    async def replicate_state(
        self,
        source_state: Dict[str, Any],
        target_thread_id: str,
        strategy: ReplicationStrategy,
        permissions: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """复制状态到目标线程"""
        pass
    
    @abstractmethod
    async def validate_state_compatibility(
        self,
        source_state: Dict[str, Any],
        target_thread_id: str
    ) -> bool:
        """验证状态兼容性"""
        pass

class IStateMerger(ABC):
    """状态合并器接口"""
    
    @abstractmethod
    async def merge_states(
        self,
        states: List[Dict[str, Any]],
        strategy: SyncStrategy,
        resolved_conflicts: List[StateConflict]
    ) -> Dict[str, Any]:
        """合并状态"""
        pass

class ConflictDetector(IConflictDetector):
    """冲突检测器实现"""
    
    async def detect_conflicts(
        self,
        source_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> List[StateConflict]:
        """检测状态冲突"""
        conflicts = []
        
        # 获取所有字段的并集
        all_fields = set(source_state.keys()) | set(target_state.keys())
        
        for field in all_fields:
            source_value = source_state.get(field)
            target_value = target_state.get(field)
            
            # 检测值冲突
            if self._has_value_conflict(source_value, target_value):
                conflicts.append(StateConflict(
                    field_path=field,
                    conflict_type=ConflictType.VALUE_CONFLICT,
                    source_value=source_value,
                    target_value=target_value,
                    source_timestamp=self._extract_timestamp(source_value),
                    target_timestamp=self._extract_timestamp(target_value)
                ))
            
            # 检测类型冲突
            elif self._has_type_conflict(source_value, target_value):
                conflicts.append(StateConflict(
                    field_path=field,
                    conflict_type=ConflictType.TYPE_CONFLICT,
                    source_value=source_value,
                    target_value=target_value,
                    source_timestamp=datetime.now(),
                    target_timestamp=datetime.now()
                ))
            
            # 检测结构冲突
            elif self._has_structure_conflict(source_value, target_value):
                conflicts.append(StateConflict(
                    field_path=field,
                    conflict_type=ConflictType.STRUCTURE_CONFLICT,
                    source_value=source_value,
                    target_value=target_value,
                    source_timestamp=datetime.now(),
                    target_timestamp=datetime.now()
                ))
        
        return conflicts
    
    def _has_value_conflict(self, source_value: Any, target_value: Any) -> bool:
        """检查是否有值冲突"""
        if source_value is None and target_value is None:
            return False
        if source_value is None or target_value is None:
            return True
        
        # 对于基本类型，直接比较
        if isinstance(source_value, (str, int, float, bool)):
            return bool(source_value != target_value)
        
        # 对于复杂类型，需要深度比较
        return bool(str(source_value) != str(target_value))
    
    def _has_type_conflict(self, source_value: Any, target_value: Any) -> bool:
        """检查是否有类型冲突"""
        if source_value is None or target_value is None:
            return False
        
        return type(source_value) != type(target_value)
    
    def _has_structure_conflict(self, source_value: Any, target_value: Any) -> bool:
        """检查是否有结构冲突"""
        if not isinstance(source_value, dict) or not isinstance(target_value, dict):
            return False
        
        source_keys = set(source_value.keys())
        target_keys = set(target_value.keys())
        
        # 检查键的差异
        return source_keys != target_keys
    
    def _extract_timestamp(self, value: Any) -> datetime:
        """提取时间戳"""
        if isinstance(value, dict) and "timestamp" in value:
            if isinstance(value["timestamp"], str):
                return datetime.fromisoformat(value["timestamp"])
            if isinstance(value["timestamp"], datetime):
                return value["timestamp"]
        return datetime.now()

class ConflictResolver(IConflictResolver):
    """冲突解决器实现"""
    
    async def resolve_conflicts(
        self,
        conflicts: List[StateConflict],
        strategy: ConflictResolution
    ) -> List[StateConflict]:
        """解决冲突"""
        resolved_conflicts = []
        
        for conflict in conflicts:
            if strategy == ConflictResolution.KEEP_SOURCE:
                conflict.resolution = ConflictResolution.KEEP_SOURCE
                conflict.resolved_value = conflict.source_value
            elif strategy == ConflictResolution.KEEP_TARGET:
                conflict.resolution = ConflictResolution.KEEP_TARGET
                conflict.resolved_value = conflict.target_value
            elif strategy == ConflictResolution.LATEST_WINS:
                if conflict.source_timestamp > conflict.target_timestamp:
                    conflict.resolution = ConflictResolution.KEEP_SOURCE
                    conflict.resolved_value = conflict.source_value
                else:
                    conflict.resolution = ConflictResolution.KEEP_TARGET
                    conflict.resolved_value = conflict.target_value
            elif strategy == ConflictResolution.MERGE_VALUES:
                conflict.resolution = ConflictResolution.MERGE_VALUES
                conflict.resolved_value = await self._merge_values(conflict)
            else:
                # 对于其他策略，保持未解决状态
                pass
            
            resolved_conflicts.append(conflict)
        
        return resolved_conflicts
    
    async def _merge_values(self, conflict: StateConflict) -> Any:
        """合并值"""
        if isinstance(conflict.source_value, dict) and isinstance(conflict.target_value, dict):
            # 合并字典
            merged = conflict.source_value.copy()
            merged.update(conflict.target_value)
            return merged
        elif isinstance(conflict.source_value, list) and isinstance(conflict.target_value, list):
            # 合并列表
            return list(set(conflict.source_value + conflict.target_value))
        else:
            # 对于其他类型，返回源值
            return conflict.source_value

class StateReplicator(IStateReplicator):
    """状态复制器实现"""
    
    def __init__(self) -> None:
        pass
    
    async def replicate_state(
        self,
        source_state: Dict[str, Any],
        target_thread_id: str,
        strategy: ReplicationStrategy,
        permissions: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """复制状态到目标线程"""
        
        if strategy == ReplicationStrategy.FULL_COPY:
            return await self._full_copy(source_state)
        elif strategy == ReplicationStrategy.SELECTIVE_COPY:
            return await self._selective_copy(source_state)
        elif strategy == ReplicationStrategy.REFERENCE_ONLY:
            return await self._reference_copy(source_state)
        elif strategy == ReplicationStrategy.INCREMENTAL:
            return await self._incremental_copy(source_state, target_thread_id)
        else:
            raise ValueError(f"Unsupported replication strategy: {strategy}")
    
    async def validate_state_compatibility(
        self,
        source_state: Dict[str, Any],
        target_thread_id: str
    ) -> bool:
        """验证状态兼容性"""
        # 简化实现，实际应用中需要更复杂的兼容性检查
        required_fields = ["thread_id", "state", "config"]
        
        for field in required_fields:
            if field not in source_state:
                return False
        
        return True
    
    async def _full_copy(
        self,
        source_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """完整复制状态"""
        # 深拷贝状态数据
        copied_state = copy.deepcopy(source_state)
        
        # 添加复制元数据
        copied_state["_replication_metadata"] = {
            "strategy": ReplicationStrategy.FULL_COPY.value,
            "replicated_at": datetime.now().isoformat()
        }
        
        return copied_state
    
    async def _selective_copy(
        self,
        source_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """选择性复制状态"""
        # 简化实现：复制所有非元数据字段
        copied_state = {}
        for field, value in source_state.items():
            if not field.startswith("_"):
                copied_state[field] = value
        
        # 添加复制元数据
        copied_state["_replication_metadata"] = {
            "strategy": ReplicationStrategy.SELECTIVE_COPY.value,
            "replicated_at": datetime.now().isoformat()
        }
        
        return copied_state
    
    async def _reference_copy(self, source_state: Dict[str, Any]) -> Dict[str, Any]:
        """仅引用复制"""
        return {
            "_reference": {
                "source_thread_id": source_state.get("thread_id"),
                "checkpoint_id": source_state.get("checkpoint_id"),
                "reference_created_at": datetime.now().isoformat()
            }
        }
    
    async def _incremental_copy(
        self,
        source_state: Dict[str, Any],
        target_thread_id: str
    ) -> Dict[str, Any]:
        """增量复制"""
        return {
            **source_state,
            "_replication_metadata": {
                "strategy": ReplicationStrategy.INCREMENTAL.value,
                "replicated_at": datetime.now().isoformat(),
                "target_thread_id": target_thread_id
            }
        }
    

class StateMerger(IStateMerger):
    """状态合并器实现"""
    
    async def merge_states(
        self,
        states: List[Dict[str, Any]],
        strategy: SyncStrategy,
        resolved_conflicts: List[StateConflict]
    ) -> Dict[str, Any]:
        """合并状态"""
        if not states:
            return {}
        
        if strategy == SyncStrategy.OVERWRITE:
            # 覆盖策略：使用最后一个状态
            return states[-1].copy()
        
        elif strategy == SyncStrategy.MERGE:
            # 合并策略：简单合并所有状态
            merged = {}
            for state in states:
                merged.update(state)
            return merged
        
        else:
            # 默认策略：使用第一个状态
            return states[0].copy()