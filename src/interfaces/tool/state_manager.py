"""
工具状态管理器接口定义

定义了有状态工具所需的状态管理接口。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import time
import uuid


class StateType(Enum):
    """状态类型枚举"""
    CONNECTION = "connection"
    SESSION = "session"
    BUSINESS = "business"
    CACHE = "cache"


@dataclass
class StateEntry:
    """状态条目"""
    state_id: str
    context_id: str
    state_type: StateType
    data: Dict[str, Any]
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    version: int = 1
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class IToolStateManager(ABC):
    """工具状态管理器接口"""
    
    @abstractmethod
    def create_context(self, context_id: str, tool_type: str) -> str:
        """创建工具上下文"""
        pass
    
    @abstractmethod
    def get_state(self, context_id: str, state_type: StateType) -> Optional[Dict[str, Any]]:
        """获取状态数据"""
        pass
    
    @abstractmethod
    def set_state(self, context_id: str, state_type: StateType, state_data: Dict[str, Any], 
                  ttl: Optional[int] = None) -> bool:
        """设置状态数据"""
        pass
    
    @abstractmethod
    def update_state(self, context_id: str, state_type: StateType, updates: Dict[str, Any]) -> bool:
        """更新状态数据"""
        pass
    
    @abstractmethod
    def delete_state(self, context_id: str, state_type: StateType) -> bool:
        """删除状态"""
        pass
    
    @abstractmethod
    def cleanup_context(self, context_id: str) -> bool:
        """清理上下文"""
        pass
    
    @abstractmethod
    def list_contexts(self, tool_type: Optional[str] = None) -> List[str]:
        """列出上下文"""
        pass
    
    @abstractmethod
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        pass