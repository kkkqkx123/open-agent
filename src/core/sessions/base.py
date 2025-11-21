"""Session基础抽象类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class SessionBase(ABC):
    """Session基础抽象类 - 提供Session实体的基础功能"""
    
    def __init__(self, session_data: Dict[str, Any]):
        """初始化Session基础类
        
        Args:
            session_data: 会话数据
        """
        self._session_data = session_data
    
    @property
    def id(self) -> str:
        """获取会话ID"""
        return self._session_data.get("id", "")
    
    @property
    def status(self) -> str:
        """获取会话状态"""
        return self._session_data.get("status", "")
    
    @property
    def graph_id(self) -> Optional[str]:
        """获取关联的图ID"""
        return self._session_data.get("graph_id")
    
    @property
    def thread_id(self) -> Optional[str]:
        """获取关联的线程ID"""
        return self._session_data.get("thread_id")
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        created_at = self._session_data.get("created_at")
        if isinstance(created_at, str):
            return datetime.fromisoformat(created_at)
        return created_at or datetime.utcnow()
    
    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        updated_at = self._session_data.get("updated_at")
        if isinstance(updated_at, str):
            return datetime.fromisoformat(updated_at)
        return updated_at or datetime.utcnow()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取会话元数据"""
        return self._session_data.get("metadata", {})
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取会话配置"""
        return self._session_data.get("config", {})
    
    @property
    def state(self) -> Dict[str, Any]:
        """获取会话状态"""
        return self._session_data.get("state", {})
    
    @property
    def message_count(self) -> int:
        """获取消息计数"""
        return self._session_data.get("message_count", 0)
    
    @property
    def checkpoint_count(self) -> int:
        """获取检查点计数"""
        return self._session_data.get("checkpoint_count", 0)
    
    def get_session_data(self) -> Dict[str, Any]:
        """获取完整的会话数据"""
        return self._session_data.copy()
    
    def update_session_data(self, new_data: Dict[str, Any]) -> None:
        """更新会话数据
        
        Args:
            new_data: 新的会话数据
        """
        self._session_data.update(new_data)
    
    @abstractmethod
    def validate(self) -> bool:
        """验证会话数据的有效性
        
        Returns:
            数据有效返回True，无效返回False
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            会话数据的字典表示
        """
        pass