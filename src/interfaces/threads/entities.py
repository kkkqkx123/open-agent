"""线程实体接口定义

定义线程管理中使用的实体接口，遵循分层架构原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..common_domain import ISerializable


class IThread(ISerializable, ABC):
    """线程接口
    
    定义线程的基本契约，用于跨层传递线程数据。
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """线程ID"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """线程状态"""
        pass
    
    @property
    @abstractmethod
    def type(self) -> str:
        """线程类型"""
        pass
    
    @property
    @abstractmethod
    def graph_id(self) -> Optional[str]:
        """关联的图ID"""
        pass
    
    @property
    @abstractmethod
    def parent_thread_id(self) -> Optional[str]:
        """父线程ID"""
        pass
    
    @property
    @abstractmethod
    def source_checkpoint_id(self) -> Optional[str]:
        """源检查点ID"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """线程元数据"""
        pass
    
    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        """线程配置"""
        pass
    
    @property
    @abstractmethod
    def state(self) -> Dict[str, Any]:
        """线程状态"""
        pass
    
    @property
    @abstractmethod
    def message_count(self) -> int:
        """消息数量"""
        pass
    
    @property
    @abstractmethod
    def checkpoint_count(self) -> int:
        """检查点数量"""
        pass
    
    @property
    @abstractmethod
    def branch_count(self) -> int:
        """分支数量"""
        pass
    
    @abstractmethod
    def can_transition_to(self, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        pass
    
    @abstractmethod
    def transition_to(self, new_status: str) -> bool:
        """转换线程状态"""
        pass
    
    @abstractmethod
    def is_forkable(self) -> bool:
        """检查是否可以派生分支"""
        pass


class IThreadBranch(ISerializable, ABC):
    """线程分支接口
    
    定义线程分支的基本契约。
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """分支ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """所属线程ID"""
        pass
    
    @property
    @abstractmethod
    def parent_thread_id(self) -> str:
        """父线程ID"""
        pass
    
    @property
    @abstractmethod
    def source_checkpoint_id(self) -> str:
        """源检查点ID"""
        pass
    
    @property
    @abstractmethod
    def branch_name(self) -> str:
        """分支名称"""
        pass
    
    @property
    @abstractmethod
    def branch_type(self) -> str:
        """分支类型"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """分支元数据"""
        pass


class IThreadSnapshot(ISerializable, ABC):
    """线程快照接口
    
    定义线程快照的基本契约。
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """快照ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """所属线程ID"""
        pass
    
    @property
    @abstractmethod
    def snapshot_name(self) -> str:
        """快照名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """快照描述"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def state_snapshot(self) -> Dict[str, Any]:
        """状态快照"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """快照元数据"""
        pass
    
    @property
    @abstractmethod
    def message_count(self) -> int:
        """消息数量"""
        pass
    
    @property
    @abstractmethod
    def checkpoint_count(self) -> int:
        """检查点数量"""
        pass