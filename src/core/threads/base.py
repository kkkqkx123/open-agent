"""Thread基础抽象类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class ThreadBase(ABC):
    """Thread基础抽象类 - 提供Thread实体的基础功能"""
    
    def __init__(self, thread_data: Dict[str, Any]):
        """初始化Thread基础类
        
        Args:
            thread_data: 线程数据
        """
        self._thread_data = thread_data
    
    @property
    def id(self) -> str:
        """获取线程ID"""
        return self._thread_data.get("id", "")
    
    @property
    def status(self) -> str:
        """获取线程状态"""
        return self._thread_data.get("status", "")
    
    @property
    def type(self) -> str:
        """获取线程类型"""
        return self._thread_data.get("type", "main")
    
    @property
    def graph_id(self) -> Optional[str]:
        """获取关联的图ID"""
        return self._thread_data.get("graph_id")
    
    @property
    def parent_thread_id(self) -> Optional[str]:
        """获取父线程ID"""
        return self._thread_data.get("parent_thread_id")
    
    @property
    def source_checkpoint_id(self) -> Optional[str]:
        """获取源检查点ID"""
        return self._thread_data.get("source_checkpoint_id")
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        created_at = self._thread_data.get("created_at")
        if isinstance(created_at, str):
            return datetime.fromisoformat(created_at)
        return created_at or datetime.utcnow()
    
    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        updated_at = self._thread_data.get("updated_at")
        if isinstance(updated_at, str):
            return datetime.fromisoformat(updated_at)
        return updated_at or datetime.utcnow()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取线程元数据"""
        return self._thread_data.get("metadata", {})
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取线程配置"""
        return self._thread_data.get("config", {})
    
    @property
    def state(self) -> Dict[str, Any]:
        """获取线程状态"""
        return self._thread_data.get("state", {})
    
    @property
    def message_count(self) -> int:
        """获取消息计数"""
        return self._thread_data.get("message_count", 0)
    
    @property
    def checkpoint_count(self) -> int:
        """获取检查点计数"""
        return self._thread_data.get("checkpoint_count", 0)
    
    @property
    def branch_count(self) -> int:
        """获取分支计数"""
        return self._thread_data.get("branch_count", 0)
    
    def get_thread_data(self) -> Dict[str, Any]:
        """获取完整的线程数据"""
        return self._thread_data.copy()
    
    def update_thread_data(self, new_data: Dict[str, Any]) -> None:
        """更新线程数据
        
        Args:
            new_data: 新的线程数据
        """
        self._thread_data.update(new_data)
    
    def is_forkable(self) -> bool:
        """检查是否可以派生分支
        
        Returns:
            可以派生返回True，否则返回False
        """
        return self.status in ["active", "paused"]
    
    @abstractmethod
    def validate(self) -> bool:
        """验证线程数据的有效性
        
        Returns:
            数据有效返回True，无效返回False
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            线程数据的字典表示
        """
        pass