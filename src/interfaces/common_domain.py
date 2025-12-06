"""通用领域层接口定义

提供领域层的通用接口，包括核心业务实体和值对象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field


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




'''
通用数据传输对象
'''

@dataclass
class ValidationResult:
    """统一的验证结果数据类"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return len(self.warnings) > 0


@dataclass
class BaseContext:
    """基础上下文数据类"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ExecutionContext(BaseContext):
    """应用层执行上下文"""
    operation_id: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class WorkflowExecutionContext(BaseContext):
    """工作流执行上下文"""
    workflow_id: str = ""
    execution_id: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


class ITimestamped(ABC):
    """
    时间戳接口
    
    定义带有时间戳的领域对象契约。
    """
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """
        获取创建时间
        
        Returns:
            datetime: 创建时间
        """
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """
        获取更新时间
        
        Returns:
            datetime: 更新时间
        """
        pass