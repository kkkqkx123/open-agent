"""状态管理基础实现类

提供状态管理系统的基类实现，包含通用功能和默认行为。
"""

import json
import pickle
import zlib
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from src.interfaces.state.history import IStateHistoryManager
from src.interfaces.state.snapshot import IStateSnapshotManager
from src.interfaces.state.serializer import IStateSerializer
from src.interfaces.state.interfaces import IState
from src.core.state.entities import StateSnapshot, StateHistoryEntry, StateStatistics, StateDiff


logger = logging.getLogger(__name__)


class BaseStateSerializer(IStateSerializer):
    """基础状态序列化器实现
    
    提供JSON和Pickle两种序列化格式的支持。
    """
    
    def __init__(self, format: str = "json", compression: bool = True):
        """初始化序列化器
        
        Args:
            format: 序列化格式，支持 "json" 或 "pickle"
            compression: 是否启用压缩
        """
        self.format = format
        self.compression = compression
        
        if format not in ["json", "pickle"]:
            raise ValueError(f"不支持的序列化格式: {format}")
    
    def serialize_state(self, state: Dict[str, Any]) -> bytes:
        """序列化状态"""
        try:
            if self.format == "json":
                data = json.dumps(state, ensure_ascii=False, default=self._json_serializer).encode('utf-8')
            else:  # pickle
                data = pickle.dumps(state)
            
            if self.compression:
                data = self.compress_data(data)
            
            return data
        except Exception as e:
            logger.error(f"序列化状态失败: {e}")
            raise
    
    def deserialize_state(self, data: bytes) -> Dict[str, Any]:
        """反序列化状态"""
        try:
            if self.compression:
                data = self.decompress_data(data)
            
            if self.format == "json":
                result = json.loads(data.decode('utf-8'))
                if not isinstance(result, dict):
                    raise ValueError("JSON反序列化结果不是字典类型")
                return result
            else:  # pickle
                result = pickle.loads(data)
                if not isinstance(result, dict):
                    raise ValueError("Pickle反序列化结果不是字典类型")
                return result
        except Exception as e:
            logger.error(f"反序列化状态失败: {e}")
            raise
    
    def compress_data(self, data: bytes) -> bytes:
        """压缩数据"""
        return zlib.compress(data)
    
    def decompress_data(self, compressed_data: bytes) -> bytes:
        """解压缩数据"""
        return zlib.decompress(compressed_data)
    
    def _json_serializer(self, obj: Any) -> Any:
        """JSON序列化器，处理特殊类型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def serialize(self, state: IState) -> Union[str, bytes]:
        """序列化状态到字符串或字节
        
        Args:
            state: 要序列化的状态
            
        Returns:
            序列化的状态数据
        """
        state_dict = state.to_dict()
        serialized_bytes = self.serialize_state(state_dict)
        
        if self.format == "json" and not self.compression:
            return serialized_bytes.decode('utf-8')
        
        return serialized_bytes
    
    def deserialize(self, data: Union[str, bytes]) -> IState:
        """从字符串或字节反序列化状态
        
        Args:
            data: 序列化的状态数据
            
        Returns:
            反序列化的状态实例
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        state_dict = self.deserialize_state(data)
        
        # 创建一个简单的状态实现
        from datetime import datetime
        
        class SimpleState(IState):
            def __init__(self, data: Dict[str, Any]):
                self._data = data
                self._metadata = data.get("metadata", {})
                self._id = data.get("id")
                self._created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
                self._updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
                self._complete = data.get("complete", False)
            
            def get_data(self, key: str, default: Any = None) -> Any:
                return self._data.get(key, default)
            
            def set_data(self, key: str, value: Any) -> None:
                self._data[key] = value
                self._updated_at = datetime.now()
            
            def get_metadata(self, key: str, default: Any = None) -> Any:
                return self._metadata.get(key, default)
            
            def set_metadata(self, key: str, value: Any) -> None:
                self._metadata[key] = value
            
            def get_id(self) -> Optional[str]:
                return self._id
            
            def set_id(self, id: str) -> None:
                self._id = id
                self._data["id"] = id
            
            def get_created_at(self) -> datetime:
                return self._created_at
            
            def get_updated_at(self) -> datetime:
                return self._updated_at
            
            def is_complete(self) -> bool:
                return self._complete
            
            def mark_complete(self) -> None:
                self._complete = True
                self._data["complete"] = True
                self._updated_at = datetime.now()
            
            def to_dict(self) -> Dict[str, Any]:
                return {
                    **self._data,
                    "metadata": self._metadata,
                    "created_at": self._created_at.isoformat(),
                    "updated_at": self._updated_at.isoformat(),
                    "complete": self._complete
                }
            
            @classmethod
            def from_dict(cls, data: Dict[str, Any]) -> 'SimpleState':
                return cls(data)
        
        return SimpleState(state_dict)


class BaseStateHistoryManager(IStateHistoryManager):
    """基础状态历史管理器实现
    
    提供历史记录管理的通用功能。
    """
    
    def __init__(self, max_history_size: int = 1000):
        """初始化历史管理器
        
        Args:
            max_history_size: 最大历史记录数量
        """
        self.max_history_size = max_history_size
    
    def _generate_history_id(self) -> str:
        """生成历史记录ID"""
        return str(uuid.uuid4())
    
    def _calculate_state_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态差异"""
        diff = StateDiff.calculate(old_state, new_state)
        return diff.to_dict()
    
    def _apply_state_diff(self, current_state: Dict[str, Any], diff: Dict[str, Any]) -> Dict[str, Any]:
        """应用状态差异"""
        state_diff = StateDiff.from_dict(diff)
        return state_diff.apply_to_state(current_state)
    
    def _create_history_entry(self, agent_id: str, old_state: Dict[str, Any], 
                            new_state: Dict[str, Any], action: str) -> StateHistoryEntry:
        """创建历史记录条目"""
        state_diff = self._calculate_state_diff(old_state, new_state)
        
        return StateHistoryEntry(
            history_id=self._generate_history_id(),
            agent_id=agent_id,
            timestamp=datetime.now(),
            action=action,
            state_diff=state_diff,
            metadata={
                "old_state_keys": list(old_state.keys()),
                "new_state_keys": list(new_state.keys())
            }
        )


class BaseStateSnapshotManager(IStateSnapshotManager):
    """基础状态快照管理器实现
    
    提供快照管理的通用功能。
    """
    
    def __init__(self, max_snapshots_per_agent: int = 50):
        """初始化快照管理器
        
        Args:
            max_snapshots_per_agent: 每个代理的最大快照数量
        """
        self.max_snapshots_per_agent = max_snapshots_per_agent
    
    def _generate_snapshot_id(self) -> str:
        """生成快照ID"""
        return str(uuid.uuid4())
    
    def _create_snapshot(self, agent_id: str, domain_state: Dict[str, Any], 
                        snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> StateSnapshot:
        """创建快照对象"""
        return StateSnapshot(
            snapshot_id=self._generate_snapshot_id(),
            agent_id=agent_id,
            domain_state=domain_state,
            timestamp=datetime.now(),
            snapshot_name=snapshot_name,
            metadata=metadata or {}
        )


class BaseStateManager:
    """基础状态管理器实现
    
    提供状态管理的通用功能，作为具体实现的基类。
    """
    
    def __init__(self, serializer: Optional[IStateSerializer] = None):
        """初始化状态管理器
        
        Args:
            serializer: 状态序列化器
        """
        self._serializer = serializer or BaseStateSerializer()
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def _validate_state_id(self, state_id: str) -> None:
        """验证状态ID"""
        if not state_id or not isinstance(state_id, str):
            raise ValueError("状态ID必须是非空字符串")
    
    def _validate_state_data(self, state: Dict[str, Any]) -> None:
        """验证状态数据"""
        if not isinstance(state, dict):
            raise ValueError("状态数据必须是字典类型")
    
    def _generate_state_id(self) -> str:
        """生成状态ID"""
        return f"state_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
    
    def _clone_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """克隆状态数据"""
        return state.copy()
    
    def _merge_states(self, base_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """合并状态数据"""
        merged = base_state.copy()
        merged.update(updates)
        return merged
    
    def get_statistics(self) -> StateStatistics:
        """获取状态统计信息"""
        return StateStatistics(
            total_states=len(self._states),
            last_updated=datetime.now()
        )


class StateValidationMixin:
    """状态验证混入类
    
    提供状态验证的通用方法。
    """
    
    def validate_state_structure(self, state: Dict[str, Any]) -> List[str]:
        """验证状态结构
        
        Args:
            state: 要验证的状态
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not isinstance(state, dict):
            errors.append("状态必须是字典类型")
            return errors
        
        # 检查必需字段
        required_fields = ["id"]
        for field in required_fields:
            if field not in state:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        if "id" in state and not isinstance(state["id"], str):
            errors.append("状态ID必须是字符串类型")
        
        if "metadata" in state and not isinstance(state["metadata"], dict):
            errors.append("元数据必须是字典类型")
        
        return errors
    
    def validate_state_completeness(self, state: Dict[str, Any]) -> List[str]:
        """验证状态完整性
        
        Args:
            state: 要验证的状态
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 基础结构验证
        errors.extend(self.validate_state_structure(state))
        
        # 完整性检查
        if "created_at" in state:
            try:
                datetime.fromisoformat(state["created_at"])
            except (ValueError, TypeError):
                errors.append("创建时间格式无效")
        
        if "updated_at" in state:
            try:
                datetime.fromisoformat(state["updated_at"])
            except (ValueError, TypeError):
                errors.append("更新时间格式无效")
        
        return errors