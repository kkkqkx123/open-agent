"""通用领域接口定义

提供系统中使用的核心接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol, List
from datetime import datetime
from enum import Enum


'''
领域层枚举定义
'''

class AbstractSessionStatus(str, Enum):
    """
    会话状态枚举
    
    定义会话的可能状态，用于会话生命周期管理。
    
    状态流转：
    ACTIVE -> PAUSED -> COMPLETED
    ACTIVE -> FAILED
    ACTIVE/PAUSED/COMPLETED/FAILED -> ARCHIVED
    """
    ACTIVE = "active"      # 活跃状态，会话正在进行
    PAUSED = "paused"      # 暂停状态，会话暂时停止
    COMPLETED = "completed"  # 完成状态，会话正常结束
    FAILED = "failed"      # 失败状态，会话异常结束
    ARCHIVED = "archived"  # 归档状态，会话已归档


'''
领域层抽象实体
'''

class AbstractSessionData(ABC):
    """
    会话数据抽象接口
    
    定义会话数据的基本契约，所有会话相关数据结构应实现此接口。
    这是领域层的核心实体，封装会话的业务概念。
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """
        获取会话ID
        
        Returns:
            str: 唯一的会话标识符
        """
        pass
    
    @property
    @abstractmethod
    def status(self) -> AbstractSessionStatus:
        """
        获取会话状态
        
        Returns:
            AbstractSessionStatus: 当前会话状态
        """
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """
        获取创建时间
        
        Returns:
            datetime: 会话创建时间
        """
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """
        获取更新时间
        
        Returns:
            datetime: 会话最后更新时间
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        
        Returns:
            Dict[str, Any]: 会话数据的字典表示
        """
        pass


'''
领域层基础接口
'''

class ISerializable(ABC):
    """
    可序列化接口
    
    定义领域对象的序列化契约，支持对象的持久化和传输。
    """
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        
        Returns:
            Dict[str, Any]: 对象的字典表示
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ISerializable':
        """
        从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            ISerializable: 新的实例
        """
        pass


class IValidationResult(Protocol):
    """验证结果接口
    
    定义验证结果的标准契约，支持多种实现。
    """
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    metadata: Dict[str, Any]
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        ...
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        ...
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        ...
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        ...
    
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        ...
