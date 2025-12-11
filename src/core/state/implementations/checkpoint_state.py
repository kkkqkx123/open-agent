"""检查点状态实现

提供检查点状态的具体实现，继承自基础状态并实现检查点特定功能。
"""

import uuid
from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from src.interfaces.state.base import IState
from ..implementations.base_state import BaseStateImpl

# 由于中央接口层没有检查点状态特化接口，使用基础接口作为替代
ICheckpointState = IState


logger = get_logger(__name__)


class CheckpointState(BaseStateImpl, ICheckpointState):
    """检查点状态实现
    
    继承自基础状态实现，添加检查点特定的功能。
    """
    
    def __init__(self, **kwargs):
        """初始化检查点状态"""
        super().__init__(**kwargs)
        
        # 检查点特定字段
        self._thread_id: Optional[str] = kwargs.get('thread_id')
        self._checkpoint_data: Dict[str, Any] = kwargs.get('checkpoint_data', {})
        self._step_number: int = kwargs.get('step_number', 0)
        self._node_name: Optional[str] = kwargs.get('node_name')
        self._config_snapshot: Dict[str, Any] = kwargs.get('config_snapshot', {})
        self._pending_writes: List[Dict[str, Any]] = kwargs.get('pending_writes', [])
        self._validation_errors: List[str] = kwargs.get('validation_errors', [])
        self._checkpoint_type: str = kwargs.get('checkpoint_type', 'manual')  # manual, auto, error
    
    # ICheckpointState 接口实现
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID"""
        return self._thread_id
    
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID"""
        self._thread_id = thread_id
        self._updated_at = datetime.now()
    
    def get_checkpoint_data(self) -> Dict[str, Any]:
        """获取检查点数据"""
        return self._checkpoint_data.copy()
    
    def set_checkpoint_data(self, checkpoint_data: Dict[str, Any]) -> None:
        """设置检查点数据"""
        self._checkpoint_data = checkpoint_data.copy()
        self._updated_at = datetime.now()
    
    def update_checkpoint_data(self, updates: Dict[str, Any]) -> None:
        """更新检查点数据"""
        self._checkpoint_data.update(updates)
        self._updated_at = datetime.now()
    
    def get_step_number(self) -> int:
        """获取步骤编号"""
        return self._step_number
    
    def set_step_number(self, step_number: int) -> None:
        """设置步骤编号"""
        self._step_number = step_number
        self._updated_at = datetime.now()
    
    def increment_step_number(self) -> None:
        """增加步骤编号"""
        self._step_number += 1
        self._updated_at = datetime.now()
    
    def get_node_name(self) -> Optional[str]:
        """获取节点名称"""
        return self._node_name
    
    def set_node_name(self, node_name: str) -> None:
        """设置节点名称"""
        self._node_name = node_name
        self._updated_at = datetime.now()
    
    def is_checkpoint_valid(self) -> bool:
        """检查检查点是否有效"""
        # 基本验证：必须有线程ID和检查点数据
        if not self._thread_id:
            return False
        
        if not self._checkpoint_data:
            return False
        
        # 检查是否有验证错误
        if self._validation_errors:
            return False
        
        return True
    
    def validate_checkpoint(self) -> List[str]:
        """验证检查点，返回错误列表"""
        errors = []
        
        # 验证必需字段
        if not self._thread_id:
            errors.append("缺少线程ID")
        
        if not self._checkpoint_data:
            errors.append("缺少检查点数据")
        
        if self._step_number < 0:
            errors.append("步骤编号不能为负数")
        
        # 验证检查点数据结构
        if self._checkpoint_data:
            required_keys = ['state', 'context']
            for key in required_keys:
                if key not in self._checkpoint_data:
                    errors.append(f"检查点数据缺少必需字段: {key}")
        
        # 验证配置快照
        if self._config_snapshot and not isinstance(self._config_snapshot, dict):
            errors.append("配置快照必须是字典类型")
        
        # 验证待写入操作
        for i, write_op in enumerate(self._pending_writes):
            if not isinstance(write_op, dict):
                errors.append(f"待写入操作 {i} 必须是字典类型")
            elif 'key' not in write_op:
                errors.append(f"待写入操作 {i} 缺少key字段")
            elif 'value' not in write_op:
                errors.append(f"待写入操作 {i} 缺少value字段")
        
        self._validation_errors = errors.copy()
        return errors
    
    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照"""
        return self._config_snapshot.copy()
    
    def set_config_snapshot(self, config_snapshot: Dict[str, Any]) -> None:
        """设置配置快照"""
        self._config_snapshot = config_snapshot.copy()
        self._updated_at = datetime.now()
    
    def get_pending_writes(self) -> List[Dict[str, Any]]:
        """获取待写入操作"""
        return self._pending_writes.copy()
    
    def add_pending_write(self, write_op: Dict[str, Any]) -> None:
        """添加待写入操作"""
        self._pending_writes.append(write_op.copy())
        self._updated_at = datetime.now()
    
    def clear_pending_writes(self) -> None:
        """清除待写入操作"""
        self._pending_writes.clear()
        self._updated_at = datetime.now()
    
    # 检查点特定方法
    def get_checkpoint_type(self) -> str:
        """获取检查点类型"""
        return self._checkpoint_type
    
    def set_checkpoint_type(self, checkpoint_type: str) -> None:
        """设置检查点类型"""
        self._checkpoint_type = checkpoint_type
        self._updated_at = datetime.now()
    
    def is_manual_checkpoint(self) -> bool:
        """检查是否为手动检查点"""
        return self._checkpoint_type == 'manual'
    
    def is_auto_checkpoint(self) -> bool:
        """检查是否为自动检查点"""
        return self._checkpoint_type == 'auto'
    
    def is_error_checkpoint(self) -> bool:
        """检查是否为错误检查点"""
        return self._checkpoint_type == 'error'
    
    def get_validation_errors(self) -> List[str]:
        """获取验证错误"""
        return self._validation_errors.copy()
    
    def has_validation_errors(self) -> bool:
        """检查是否有验证错误"""
        return len(self._validation_errors) > 0
    
    def clear_validation_errors(self) -> None:
        """清除验证错误"""
        self._validation_errors.clear()
        self._updated_at = datetime.now()
    
    def get_checkpoint_size(self) -> int:
        """获取检查点大小（字节）"""
        import sys
        size = sys.getsizeof(self._checkpoint_data)
        size += sys.getsizeof(self._config_snapshot)
        size += sys.getsizeof(self._pending_writes)
        return size
    
    def get_checkpoint_age(self) -> float:
        """获取检查点年龄（秒）"""
        return (datetime.now() - self._created_at).total_seconds()
    
    def is_recent_checkpoint(self, max_age_seconds: int = 3600) -> bool:
        """检查是否为最近创建的检查点"""
        return self.get_checkpoint_age() <= max_age_seconds
    
    def get_checkpoint_info(self) -> Dict[str, Any]:
        """获取检查点信息"""
        return {
            "id": self._id,
            "thread_id": self._thread_id,
            "step_number": self._step_number,
            "node_name": self._node_name,
            "checkpoint_type": self._checkpoint_type,
            "is_valid": self.is_checkpoint_valid(),
            "validation_errors": len(self._validation_errors),
            "pending_writes": len(self._pending_writes),
            "checkpoint_size": self.get_checkpoint_size(),
            "age_seconds": self.get_checkpoint_age(),
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat()
        }
    
    def merge_pending_writes(self) -> Dict[str, Any]:
        """合并待写入操作
        
        Returns:
            合并后的写入操作字典
        """
        merged = {}
        for write_op in self._pending_writes:
            key = write_op.get('key')
            value = write_op.get('value')
            if key is not None:
                merged[key] = value
        return merged
    
    def apply_pending_writes(self, target_dict: Dict[str, Any]) -> None:
        """将待写入操作应用到目标字典
        
        Args:
            target_dict: 目标字典
        """
        for write_op in self._pending_writes:
            key = write_op.get('key')
            value = write_op.get('value')
            if key is not None:
                target_dict[key] = value
    
    def create_checkpoint_summary(self) -> Dict[str, Any]:
        """创建检查点摘要
        
        Returns:
            检查点摘要
        """
        return {
            "checkpoint_id": self._id,
            "thread_id": self._thread_id,
            "step": self._step_number,
            "node": self._node_name,
            "type": self._checkpoint_type,
            "data_keys": list(self._checkpoint_data.keys()),
            "config_keys": list(self._config_snapshot.keys()),
            "pending_writes_count": len(self._pending_writes),
            "has_errors": self.has_validation_errors(),
            "created_at": self._created_at.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'thread_id': self._thread_id,
            'checkpoint_data': self._checkpoint_data,
            'step_number': self._step_number,
            'node_name': self._node_name,
            'config_snapshot': self._config_snapshot,
            'pending_writes': self._pending_writes,
            'validation_errors': self._validation_errors,
            'checkpoint_type': self._checkpoint_type
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._thread_id = data.get("thread_id")
        instance._checkpoint_data = data.get("checkpoint_data", {})
        instance._step_number = data.get("step_number", 0)
        instance._node_name = data.get("node_name")
        instance._config_snapshot = data.get("config_snapshot", {})
        instance._pending_writes = data.get("pending_writes", [])
        instance._validation_errors = data.get("validation_errors", [])
        instance._checkpoint_type = data.get("checkpoint_type", "manual")
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
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"CheckpointState(id={self._id}, thread_id={self._thread_id}, "
                f"step={self._step_number}, node={self._node_name})")
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"CheckpointState(id={self._id}, thread_id={self._thread_id}, "
                f"step={self._step_number}, node={self._node_name}, "
                f"type={self._checkpoint_type}, valid={self.is_checkpoint_valid()})")


class AutoCheckpointState(CheckpointState):
    """自动检查点状态
    
    专门用于自动生成的检查点。
    """
    
    def __init__(self, **kwargs):
        """初始化自动检查点状态"""
        kwargs['checkpoint_type'] = 'auto'
        super().__init__(**kwargs)
        
        # 自动检查点特定字段
        self._trigger_reason: str = kwargs.get('trigger_reason', '')
        self._trigger_data: Dict[str, Any] = kwargs.get('trigger_data', {})
        self._auto_checkpoint_interval: int = kwargs.get('auto_checkpoint_interval', 0)
        self._next_auto_checkpoint: Optional[datetime] = kwargs.get('next_auto_checkpoint')
    
    def get_trigger_reason(self) -> str:
        """获取触发原因"""
        return self._trigger_reason
    
    def set_trigger_reason(self, reason: str) -> None:
        """设置触发原因"""
        self._trigger_reason = reason
        self._updated_at = datetime.now()
    
    def get_trigger_data(self) -> Dict[str, Any]:
        """获取触发数据"""
        return self._trigger_data.copy()
    
    def set_trigger_data(self, data: Dict[str, Any]) -> None:
        """设置触发数据"""
        self._trigger_data = data.copy()
        self._updated_at = datetime.now()
    
    def get_auto_checkpoint_interval(self) -> int:
        """获取自动检查点间隔"""
        return self._auto_checkpoint_interval
    
    def set_auto_checkpoint_interval(self, interval: int) -> None:
        """设置自动检查点间隔"""
        self._auto_checkpoint_interval = interval
        self._updated_at = datetime.now()
    
    def get_next_auto_checkpoint(self) -> Optional[datetime]:
        """获取下次自动检查点时间"""
        return self._next_auto_checkpoint
    
    def set_next_auto_checkpoint(self, next_time: datetime) -> None:
        """设置下次自动检查点时间"""
        self._next_auto_checkpoint = next_time
        self._updated_at = datetime.now()
    
    def is_time_for_auto_checkpoint(self) -> bool:
        """检查是否到了自动检查点时间"""
        if not self._next_auto_checkpoint:
            return False
        return datetime.now() >= self._next_auto_checkpoint
    
    def schedule_next_auto_checkpoint(self) -> None:
        """安排下次自动检查点"""
        if self._auto_checkpoint_interval > 0:
            self._next_auto_checkpoint = datetime.now() + timedelta(seconds=self._auto_checkpoint_interval)
            self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'trigger_reason': self._trigger_reason,
            'trigger_data': self._trigger_data,
            'auto_checkpoint_interval': self._auto_checkpoint_interval,
            'next_auto_checkpoint': self._next_auto_checkpoint.isoformat() if self._next_auto_checkpoint else None
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoCheckpointState':
        """从字典创建状态"""
        # 首先创建父类实例，然后转换为子类类型
        checkpoint_state = CheckpointState.from_dict(data)
        instance: 'AutoCheckpointState' = cls.__new__(cls)
        
        # 复制父类属性
        instance._id = checkpoint_state._id
        instance._data = checkpoint_state._data
        instance._metadata = checkpoint_state._metadata
        instance._complete = checkpoint_state._complete
        instance._created_at = checkpoint_state._created_at
        instance._updated_at = checkpoint_state._updated_at
        
        # 复制 CheckpointState 属性
        instance._thread_id = checkpoint_state._thread_id
        instance._checkpoint_data = checkpoint_state._checkpoint_data
        instance._step_number = checkpoint_state._step_number
        instance._node_name = checkpoint_state._node_name
        instance._config_snapshot = checkpoint_state._config_snapshot
        instance._pending_writes = checkpoint_state._pending_writes
        instance._validation_errors = checkpoint_state._validation_errors
        instance._checkpoint_type = checkpoint_state._checkpoint_type
        
        # 设置 AutoCheckpointState 特定属性
        instance._trigger_reason = data.get("trigger_reason", "")
        instance._trigger_data = data.get("trigger_data", {})
        instance._auto_checkpoint_interval = data.get("auto_checkpoint_interval", 0)
        
        # 处理时间
        next_checkpoint_str = data.get("next_auto_checkpoint")
        if next_checkpoint_str:
            instance._next_auto_checkpoint = datetime.fromisoformat(next_checkpoint_str)
        else:
            instance._next_auto_checkpoint = None
        
        return instance