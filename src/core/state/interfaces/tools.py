"""工具状态特化接口定义

定义专门用于工具状态管理的接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

from .base import IState


class StateType(Enum):
    """状态类型枚举"""
    CONNECTION = "connection"
    SESSION = "session"
    BUSINESS = "business"
    CACHE = "cache"


class IToolState(IState):
    """工具状态接口
    
    继承自基础状态接口，添加工具特定的功能。
    这个接口专门用于工具状态管理。
    """
    
    @abstractmethod
    def get_context_id(self) -> str:
        """获取上下文ID"""
        pass
    
    @abstractmethod
    def get_state_type(self) -> StateType:
        """获取状态类型"""
        pass
    
    @abstractmethod
    def is_expired(self) -> bool:
        """检查是否过期"""
        pass
    
    @abstractmethod
    def set_ttl(self, ttl: int) -> None:
        """设置TTL"""
        pass
    
    @abstractmethod
    def get_tool_type(self) -> str:
        """获取工具类型"""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> None:
        """清理过期状态"""
        pass
    
    @abstractmethod
    def get_version(self) -> int:
        """获取版本号"""
        pass
    
    @abstractmethod
    def increment_version(self) -> None:
        """增加版本号"""
        pass


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
    
    @abstractmethod
    def cleanup_expired_states(self) -> int:
        """清理过期状态，返回清理的数量"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass


class IToolStateBuilder(ABC):
    """工具状态构建器接口"""
    
    @abstractmethod
    def with_context_id(self, context_id: str) -> 'IToolStateBuilder':
        """设置上下文ID"""
        pass
    
    @abstractmethod
    def with_state_type(self, state_type: StateType) -> 'IToolStateBuilder':
        """设置状态类型"""
        pass
    
    @abstractmethod
    def with_tool_type(self, tool_type: str) -> 'IToolStateBuilder':
        """设置工具类型"""
        pass
    
    @abstractmethod
    def with_ttl(self, ttl: int) -> 'IToolStateBuilder':
        """设置TTL"""
        pass
    
    @abstractmethod
    def with_version(self, version: int) -> 'IToolStateBuilder':
        """设置版本号"""
        pass
    
    @abstractmethod
    def with_data(self, data: Dict[str, Any]) -> 'IToolStateBuilder':
        """设置状态数据"""
        pass
    
    @abstractmethod
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IToolStateBuilder':
        """设置元数据"""
        pass
    
    @abstractmethod
    def build(self) -> IToolState:
        """构建工具状态"""
        pass