"""基础状态实现

提供状态管理系统的基类实现，包含通用功能和默认行为。
"""

import json
import pickle
import zlib
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime

from ..interfaces.base import IState, IStateSerializer, IStateValidator, IStateLifecycleManager
from ..interfaces.workflow import IWorkflowState
from ..interfaces.tools import IToolState, StateType
from ..interfaces.sessions import ISessionState
from ..interfaces.threads import IThreadState
from ..interfaces.checkpoints import ICheckpointState


logger = logging.getLogger(__name__)


class BaseState(IState):
    """基础状态实现
    
    提供状态的基本功能实现。
    """
    
    def __init__(self, **kwargs):
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
    
    def serialize(self, state: IState) -> Union[str, bytes]:
        """序列化状态到字符串或字节"""
        try:
            state_dict = state.to_dict()
            
            if self.format == "json":
                data = json.dumps(state_dict, ensure_ascii=False, default=self._json_serializer).encode('utf-8')
            else:  # pickle
                data = pickle.dumps(state_dict)
            
            if self.compression:
                data = zlib.compress(data)
            
            if self.format == "json" and not self.compression:
                return data.decode('utf-8')
            
            return data
        except Exception as e:
            logger.error(f"序列化状态失败: {e}")
            raise
    
    def deserialize(self, data: Union[str, bytes]) -> IState:
        """从字符串或字节反序列化状态"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            if self.compression:
                data = zlib.decompress(data)
            
            if self.format == "json":
                state_dict = json.loads(data.decode('utf-8'))
            else:  # pickle
                state_dict = pickle.loads(data)
            
            # 创建一个简单的状态实现
            return BaseState.from_dict(state_dict)
        except Exception as e:
            logger.error(f"反序列化状态失败: {e}")
            raise
    
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
    
    def __init__(self):
        """初始化生命周期管理器"""
        self._states: Dict[str, IState] = {}
        self._statistics = {
            "total_registered": 0,
            "total_unregistered": 0,
            "total_saved": 0,
            "total_deleted": 0,
            "total_errors": 0
        }
    
    def register_state(self, state: IState) -> None:
        """注册状态"""
        state_id = state.get_id()
        if state_id:
            self._states[state_id] = state
            self._statistics["total_registered"] += 1
    
    def unregister_state(self, state_id: str) -> None:
        """注销状态"""
        if state_id in self._states:
            del self._states[state_id]
            self._statistics["total_unregistered"] += 1
    
    def on_state_saved(self, state: IState) -> None:
        """状态保存事件"""
        self._statistics["total_saved"] += 1
    
    def on_state_deleted(self, state_id: str) -> None:
        """状态删除事件"""
        self.unregister_state(state_id)
        self._statistics["total_deleted"] += 1
    
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