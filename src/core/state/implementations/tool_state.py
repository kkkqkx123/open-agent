"""工具状态实现

提供工具状态的具体实现，继承自基础状态并实现工具特定功能。
"""

import time
import uuid
from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, Optional
from datetime import datetime

from src.interfaces.state.base import IState
from ..implementations.base_state import BaseStateImpl

# 由于中央接口层没有工具状态特化接口，使用基础接口作为替代
IToolState = IState

# 工具状态类型枚举
from enum import Enum

class StateType(Enum):
    """状态类型枚举"""
    CONNECTION = "connection"
    SESSION = "session"
    BUSINESS = "business"
    CACHE = "cache"


logger = get_logger(__name__)


class ToolState(BaseStateImpl, IToolState):
    """工具状态实现
    
    继承自基础状态实现，添加工具特定的功能。
    """
    
    def __init__(self, **kwargs):
        """初始化工具状态"""
        super().__init__(**kwargs)
        
        # 工具特定字段
        self._context_id: str = kwargs.get('context_id', '')
        self._state_type: StateType = kwargs.get('state_type', StateType.BUSINESS)
        self._tool_type: str = kwargs.get('tool_type', '')
        self._expires_at: Optional[float] = kwargs.get('expires_at')
        self._version: int = kwargs.get('version', 1)
        
        # 如果没有提供context_id，生成一个
        if not self._context_id:
            self._context_id = f"ctx_{uuid.uuid4().hex[:8]}"
    
    # IToolState 接口实现
    def get_context_id(self) -> str:
        """获取上下文ID"""
        return self._context_id
    
    def get_state_type(self) -> StateType:
        """获取状态类型"""
        return self._state_type
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self._expires_at is None:
            return False
        return time.time() > self._expires_at
    
    def set_ttl(self, ttl: int) -> None:
        """设置TTL"""
        self._expires_at = time.time() + ttl
        self._updated_at = datetime.now()
    
    def get_tool_type(self) -> str:
        """获取工具类型"""
        return self._tool_type
    
    def cleanup_expired(self) -> None:
        """清理过期状态"""
        if self.is_expired():
            self._data.clear()
            self._metadata.clear()
            logger.debug(f"清理过期工具状态: {self._id}")
    
    def get_version(self) -> int:
        """获取版本号"""
        return self._version
    
    def increment_version(self) -> None:
        """增加版本号"""
        self._version += 1
        self._updated_at = datetime.now()
    
    # 工具特定方法
    def set_context_id(self, context_id: str) -> None:
        """设置上下文ID"""
        self._context_id = context_id
        self._updated_at = datetime.now()
    
    def set_state_type(self, state_type: StateType) -> None:
        """设置状态类型"""
        self._state_type = state_type
        self._updated_at = datetime.now()
    
    def set_tool_type(self, tool_type: str) -> None:
        """设置工具类型"""
        self._tool_type = tool_type
        self._updated_at = datetime.now()
    
    def set_version(self, version: int) -> None:
        """设置版本号"""
        self._version = version
        self._updated_at = datetime.now()
    
    def get_expires_at(self) -> Optional[float]:
        """获取过期时间"""
        return self._expires_at
    
    def set_expires_at(self, expires_at: float) -> None:
        """设置过期时间"""
        self._expires_at = expires_at
        self._updated_at = datetime.now()
    
    def get_ttl(self) -> Optional[int]:
        """获取剩余TTL"""
        if self._expires_at is None:
            return None
        
        remaining = self._expires_at - time.time()
        return max(0, int(remaining)) if remaining > 0 else 0
    
    def extend_ttl(self, additional_ttl: int) -> None:
        """延长TTL"""
        if self._expires_at is not None:
            self._expires_at += additional_ttl
            self._updated_at = datetime.now()
        else:
            self.set_ttl(additional_ttl)
    
    def is_connection_state(self) -> bool:
        """检查是否为连接状态"""
        return self._state_type == StateType.CONNECTION
    
    def is_session_state(self) -> bool:
        """检查是否为会话状态"""
        return self._state_type == StateType.SESSION
    
    def is_business_state(self) -> bool:
        """检查是否为业务状态"""
        return self._state_type == StateType.BUSINESS
    
    def is_cache_state(self) -> bool:
        """检查是否为缓存状态"""
        return self._state_type == StateType.CACHE
    
    def get_age_seconds(self) -> float:
        """获取状态年龄（秒）"""
        return time.time() - self._created_at.timestamp()
    
    def is_fresh(self, max_age_seconds: int = 300) -> bool:
        """检查是否为新鲜状态"""
        return self.get_age_seconds() <= max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'context_id': self._context_id,
            'state_type': self._state_type.value,
            'tool_type': self._tool_type,
            'expires_at': self._expires_at,
            'version': self._version
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._context_id = data.get("context_id", "")
        instance._state_type = StateType(data.get("state_type", StateType.BUSINESS.value))
        instance._tool_type = data.get("tool_type", "")
        instance._expires_at = data.get("expires_at")
        instance._version = data.get("version", 1)
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
        return (f"ToolState(id={self._id}, context_id={self._context_id}, "
                f"type={self._state_type.value}, tool={self._tool_type})")
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"ToolState(id={self._id}, context_id={self._context_id}, "
                f"state_type={self._state_type.value}, tool_type={self._tool_type}, "
                f"version={self._version}, expired={self.is_expired()})")


class ConnectionState(ToolState):
    """连接状态
    
    专门用于管理工具连接的状态。
    """
    
    def __init__(self, **kwargs):
        """初始化连接状态"""
        kwargs['state_type'] = StateType.CONNECTION
        super().__init__(**kwargs)
        
        # 连接特定字段
        self._connection_status: str = kwargs.get('connection_status', 'disconnected')
        self._connection_params: Dict[str, Any] = kwargs.get('connection_params', {})
        self._last_error: Optional[str] = kwargs.get('last_error')
        self._retry_count: int = kwargs.get('retry_count', 0)
        self._max_retries: int = kwargs.get('max_retries', 3)
    
    def get_connection_status(self) -> str:
        """获取连接状态"""
        return self._connection_status
    
    def set_connection_status(self, status: str) -> None:
        """设置连接状态"""
        self._connection_status = status
        self._updated_at = datetime.now()
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connection_status == 'connected'
    
    def is_disconnected(self) -> bool:
        """检查是否已断开"""
        return self._connection_status == 'disconnected'
    
    def get_connection_params(self) -> Dict[str, Any]:
        """获取连接参数"""
        return self._connection_params.copy()
    
    def set_connection_params(self, params: Dict[str, Any]) -> None:
        """设置连接参数"""
        self._connection_params = params.copy()
        self._updated_at = datetime.now()
    
    def get_last_error(self) -> Optional[str]:
        """获取最后错误"""
        return self._last_error
    
    def set_last_error(self, error: str) -> None:
        """设置最后错误"""
        self._last_error = error
        self._updated_at = datetime.now()
    
    def get_retry_count(self) -> int:
        """获取重试次数"""
        return self._retry_count
    
    def increment_retry_count(self) -> None:
        """增加重试次数"""
        self._retry_count += 1
        self._updated_at = datetime.now()
    
    def reset_retry_count(self) -> None:
        """重置重试次数"""
        self._retry_count = 0
        self._updated_at = datetime.now()
    
    def is_max_retries_reached(self) -> bool:
        """检查是否达到最大重试次数"""
        return self._retry_count >= self._max_retries
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return not self.is_max_retries_reached() and not self.is_connected()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'connection_status': self._connection_status,
            'connection_params': self._connection_params,
            'last_error': self._last_error,
            'retry_count': self._retry_count,
            'max_retries': self._max_retries
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionState':
        """从字典创建状态"""
        # 首先创建父类实例，然后转换为子类类型
        tool_state = ToolState.from_dict(data)
        instance: 'ConnectionState' = cls.__new__(cls)
        
        # 复制父类属性
        instance._id = tool_state._id
        instance._data = tool_state._data
        instance._metadata = tool_state._metadata
        instance._complete = tool_state._complete
        instance._created_at = tool_state._created_at
        instance._updated_at = tool_state._updated_at
        
        # 复制 ToolState 属性
        instance._context_id = tool_state._context_id
        instance._state_type = tool_state._state_type
        instance._tool_type = tool_state._tool_type
        instance._expires_at = tool_state._expires_at
        instance._version = tool_state._version
        
        # 设置 ConnectionState 特定属性
        instance._connection_status = data.get("connection_status", 'disconnected')
        instance._connection_params = data.get("connection_params", {})
        instance._last_error = data.get("last_error")
        instance._retry_count = data.get("retry_count", 0)
        instance._max_retries = data.get("max_retries", 3)
        return instance


class CacheState(ToolState):
    """缓存状态
    
    专门用于管理工具缓存的状态。
    """
    
    def __init__(self, **kwargs):
        """初始化缓存状态"""
        kwargs['state_type'] = StateType.CACHE
        super().__init__(**kwargs)
        
        # 缓存特定字段
        self._cache_key: str = kwargs.get('cache_key', '')
        self._cache_size: int = kwargs.get('cache_size', 0)
        self._hit_count: int = kwargs.get('hit_count', 0)
        self._miss_count: int = kwargs.get('miss_count', 0)
        self._last_access: Optional[float] = kwargs.get('last_access')
    
    def get_cache_key(self) -> str:
        """获取缓存键"""
        return self._cache_key
    
    def set_cache_key(self, key: str) -> None:
        """设置缓存键"""
        self._cache_key = key
        self._updated_at = datetime.now()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return self._cache_size
    
    def set_cache_size(self, size: int) -> None:
        """设置缓存大小"""
        self._cache_size = size
        self._updated_at = datetime.now()
    
    def get_hit_count(self) -> int:
        """获取命中次数"""
        return self._hit_count
    
    def increment_hit_count(self) -> None:
        """增加命中次数"""
        self._hit_count += 1
        self._last_access = time.time()
        self._updated_at = datetime.now()
    
    def get_miss_count(self) -> int:
        """获取未命中次数"""
        return self._miss_count
    
    def increment_miss_count(self) -> None:
        """增加未命中次数"""
        self._miss_count += 1
        self._last_access = time.time()
        self._updated_at = datetime.now()
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self._hit_count + self._miss_count
        return self._hit_count / total if total > 0 else 0.0
    
    def get_last_access(self) -> Optional[float]:
        """获取最后访问时间"""
        return self._last_access
    
    def update_last_access(self) -> None:
        """更新最后访问时间"""
        self._last_access = time.time()
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'cache_key': self._cache_key,
            'cache_size': self._cache_size,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'last_access': self._last_access
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheState':
        """从字典创建状态"""
        # 首先创建父类实例，然后转换为子类类型
        tool_state = ToolState.from_dict(data)
        instance: 'CacheState' = cls.__new__(cls)
        
        # 复制父类属性
        instance._id = tool_state._id
        instance._data = tool_state._data
        instance._metadata = tool_state._metadata
        instance._complete = tool_state._complete
        instance._created_at = tool_state._created_at
        instance._updated_at = tool_state._updated_at
        
        # 复制 ToolState 属性
        instance._context_id = tool_state._context_id
        instance._state_type = tool_state._state_type
        instance._tool_type = tool_state._tool_type
        instance._expires_at = tool_state._expires_at
        instance._version = tool_state._version
        
        # 设置 CacheState 特定属性
        instance._cache_key = data.get("cache_key", "")
        instance._cache_size = data.get("cache_size", 0)
        instance._hit_count = data.get("hit_count", 0)
        instance._miss_count = data.get("miss_count", 0)
        instance._last_access = data.get("last_access")
        return instance