"""基础状态实现

提供状态管理系统的基类实现，包含通用功能和默认行为。
"""

import json
import pickle
import zlib
import uuid
from src.interfaces.dependency_injection import get_logger
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime

from src.interfaces.state.base import IState
from src.infrastructure.common.serialization import Serializer, SerializationError
from src.interfaces.state.lifecycle import IStateLifecycleManager
from src.interfaces.state.history import IStateHistoryManager
from src.interfaces.state.snapshot import IStateSnapshotManager
from ..entities import StateSnapshot, StateHistoryEntry, StateStatistics, StateDiff

# 由于中央接口层没有验证器接口，我们需要创建这个接口
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 类型检查时使用这个接口，但实际运行时使用基础接口
    class IStateValidator:
        """状态验证器接口（临时定义）"""
        def validate_state(self, state: IState) -> List[str]:
            return []
        def validate_state_data(self, data: Dict[str, Any]) -> List[str]:
            return []
else:
    # 运行时使用基础类作为替代
    IStateValidator = object  # 临时使用object作为占位符


logger = get_logger(__name__)


class BaseState(IState):
    """基础状态实现
    
    提供状态的基本功能实现。
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化基础状态"""
        self._data: Dict[str, Any] = kwargs.get('data', {})
        self._metadata: Dict[str, Any] = kwargs.get('metadata', {})
        self._id: Optional[str] = kwargs.get('id')
        self._created_at: datetime = kwargs.get('created_at', datetime.now())
        self._updated_at: datetime = kwargs.get('updated_at', datetime.now())
        self._complete: bool = kwargs.get('complete', False)
    
    # IState 接口实现
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置状态数据"""
        self._data[key] = value
        self._updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
        self._updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._id
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._id = id
        self._updated_at = datetime.now()
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        return self._updated_at
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return self._complete
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._complete = True
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data": self._data,
            "metadata": self._metadata,
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "complete": self._complete
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 处理时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        return instance


class BaseStateSerializer(Serializer):
    """基础状态序列化器实现
    
    提供JSON和Pickle两种序列化格式的支持。
    """
    
    def __init__(self, format: str = "json", compression: bool = True, enable_cache: bool = False, cache_size: int = 1000):
        """初始化序列化器
        
        Args:
            format: 序列化格式，支持 "json" 或 "pickle"
            compression: 是否启用压缩
            enable_cache: 是否启用缓存
            cache_size: 缓存大小限制
        """
        # 初始化父类Serializer
        super().__init__(enable_cache=enable_cache, cache_size=cache_size)
        
        self.format = format
        self.compression = compression
        
        if format not in ["json", "pickle"]:
            raise ValueError(f"不支持的序列化格式: {format}")
    
    def serialize(self, data: Any, format: str = None, enable_cache: bool = True, **kwargs: Any) -> Union[str, bytes]:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            format: 序列化格式，如果为None则使用默认格式
            enable_cache: 是否启用缓存
            **kwargs: 其他参数
            
        Returns:
            序列化后的数据
        """
        # 使用默认格式
        actual_format = format or self.format
        
        # 如果是IState对象，先转换为字典
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        
        try:
            if actual_format == "json":
                result = json.dumps(data, ensure_ascii=False, default=self._json_serializer)
            else:  # pickle
                result = pickle.dumps(data)
            
            if self.compression:
                if isinstance(result, str):
                    result = result.encode('utf-8')
                result = zlib.compress(result)
            
            # 如果是JSON且未压缩，返回字符串
            if actual_format == "json" and not self.compression:
                return result
            
            return result
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            raise SerializationError(f"序列化失败: {e}") from e
    
    def deserialize(self, data: Union[str, bytes], format: str = None, enable_cache: bool = True, **kwargs: Any) -> Any:
        """反序列化数据
        
        Args:
            data: 要反序列化的数据
            format: 数据格式，如果为None则使用默认格式
            enable_cache: 是否启用缓存
            **kwargs: 其他参数
            
        Returns:
            反序列化后的数据
        """
        # 使用默认格式
        actual_format = format or self.format
        
        try:
            if self.compression:
                data = zlib.decompress(data)
            
            if actual_format == "json":
                if isinstance(data, bytes):
                    result = json.loads(data.decode('utf-8'))
                else:
                    result = json.loads(data)
            else:  # pickle
                result = pickle.loads(data)
            
            # 如果数据包含状态信息，尝试转换为BaseState
            if isinstance(result, dict) and 'data' in result and 'metadata' in result:
                return BaseState.from_dict(result)
            
            return result
        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            raise SerializationError(f"反序列化失败: {e}") from e
    
    def serialize_state(self, state: dict) -> bytes:
        """序列化状态字典到字节
        
        Args:
            state: 状态字典
            
        Returns:
            序列化后的字节数据
        """
        result = self.serialize(state, format=self.format, enable_cache=False)
        if isinstance(result, str):
            result = result.encode('utf-8')
        return result
    
    def deserialize_state(self, data: bytes) -> dict:
        """从字节反序列化状态字典
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            反序列化后的状态字典
        """
        result = self.deserialize(data, format=self.format, enable_cache=False)
        return result if isinstance(result, dict) else {'data': result}
    
    def compress_data(self, data: bytes) -> bytes:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的数据
        """
        return zlib.compress(data)
    
    def decompress_data(self, compressed_data: bytes) -> bytes:
        """解压缩数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压缩后的数据
        """
        return zlib.decompress(compressed_data)
    
    def _json_serializer(self, obj: Any) -> Any:
        """JSON序列化器，处理特殊类型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)


class BaseStateValidator(IStateValidator):
    """基础状态验证器实现"""
    
    def __init__(self, strict_mode: bool = False):
        """初始化验证器
        
        Args:
            strict_mode: 是否启用严格模式
        """
        self.strict_mode = strict_mode
    
    def validate_state(self, state: IState) -> List[str]:
        """验证状态，返回错误列表"""
        errors = []
        
        # 基础验证
        if not state.get_id():
            errors.append("状态ID不能为空")
        
        if state.get_created_at() > state.get_updated_at():
            errors.append("创建时间不能晚于更新时间")
        
        # 验证状态数据
        state_dict = state.to_dict()
        errors.extend(self.validate_state_data(state_dict))
        
        return errors
    
    def validate_state_data(self, data: Dict[str, Any]) -> List[str]:
        """验证状态数据"""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("状态数据必须是字典类型")
            return errors
        
        # 检查必需字段
        required_fields = ["data", "metadata", "created_at", "updated_at"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        if "data" in data and not isinstance(data["data"], dict):
            errors.append("data字段必须是字典类型")
        
        if "metadata" in data and not isinstance(data["metadata"], dict):
            errors.append("metadata字段必须是字典类型")
        
        return errors


class BaseStateLifecycleManager(IStateLifecycleManager):
    """基础状态生命周期管理器实现"""
    
    def __init__(self) -> None:
        """初始化生命周期管理器"""
        self._states: Dict[str, IState] = {}
        self._statistics = {
            "total_registered": 0,
            "total_unregistered": 0,
            "total_saved": 0,
            "total_deleted": 0,
            "total_errors": 0,
            "total_initialized": 0,
            "total_cleaned": 0
        }
    
    def initialize_state(self, state: IState) -> None:
        """初始化状态"""
        state_id = state.get_id()
        if state_id:
            self._states[state_id] = state
            self._statistics["total_initialized"] += 1
            logger.debug(f"初始化状态: {state_id}")
    
    def cleanup_state(self, state: IState) -> None:
        """清理状态"""
        state_id = state.get_id()
        if state_id and state_id in self._states:
            del self._states[state_id]
            self._statistics["total_cleaned"] += 1
            logger.debug(f"清理状态: {state_id}")
    
    def validate_state(self, state: IState) -> List[str]:
        """验证状态"""
        errors = []
        
        # 基础验证
        if not state.get_id():
            errors.append("状态ID不能为空")
        
        if state.get_created_at() > state.get_updated_at():
            errors.append("创建时间不能晚于更新时间")
        
        return errors
    
    def register_state(self, state: IState) -> None:
        """注册状态"""
        state_id = state.get_id()
        if state_id:
            self._states[state_id] = state
            self._statistics["total_registered"] += 1
            logger.debug(f"注册状态: {state_id}")
    
    def unregister_state(self, state_id: str) -> None:
        """注销状态"""
        if state_id in self._states:
            del self._states[state_id]
            self._statistics["total_unregistered"] += 1
            logger.debug(f"注销状态: {state_id}")
    
    def on_state_saved(self, state: IState) -> None:
        """状态保存事件"""
        self._statistics["total_saved"] += 1
        logger.debug(f"状态保存事件: {state.get_id()}")
    
    def on_state_deleted(self, state_id: str) -> None:
        """状态删除事件"""
        self.unregister_state(state_id)
        self._statistics["total_deleted"] += 1
        logger.debug(f"状态删除事件: {state_id}")
    
    def on_state_error(self, state: IState, error: Exception) -> None:
        """状态错误事件"""
        self._statistics["total_errors"] += 1
        logger.error(f"状态错误: {error}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._statistics,
            "currently_registered": len(self._states)
        }


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
    
    def _create_history_entry(self, thread_id: str, old_state: Dict[str, Any],
                            new_state: Dict[str, Any], action: str) -> StateHistoryEntry:
        """创建历史记录条目"""
        state_diff = self._calculate_state_diff(old_state, new_state)
        
        return StateHistoryEntry(
            history_id=self._generate_history_id(),
            thread_id=thread_id,
            timestamp=datetime.now().isoformat(),
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
    
    def __init__(self, max_snapshots_per_thread: int = 50):
        """初始化快照管理器
        
        Args:
            max_snapshots_per_thread: 每个线程的最大快照数量
        """
        self.max_snapshots_per_thread = max_snapshots_per_thread
    
    def _generate_snapshot_id(self) -> str:
        """生成快照ID"""
        return str(uuid.uuid4())
    
    def _create_snapshot(self, thread_id: str, domain_state: Dict[str, Any],
                        snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> StateSnapshot:
        """创建快照对象"""
        return StateSnapshot(
            snapshot_id=self._generate_snapshot_id(),
            thread_id=thread_id,
            domain_state=domain_state,
            timestamp=datetime.now().isoformat(),
            snapshot_name=snapshot_name,
            metadata=metadata or {}
        )


class BaseStateManager:
    """基础状态管理器实现
    
    提供状态管理的通用功能，作为具体实现的基类。
    """
    
    def __init__(self, serializer: Optional[Serializer] = None):
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