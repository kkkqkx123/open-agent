"""通用类型定义

提供系统中使用的基础枚举和数据类型，避免重复定义。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class BaseStatus(str, Enum):
    """基础状态枚举
    
    定义系统中通用的状态，其他状态枚举应继承此类。
    """
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class BasePriority(str, Enum):
    """基础优先级枚举
    
    定义系统中通用的优先级，其他优先级枚举应继承此类。
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BaseNumericPriority(int, Enum):
    """基础数值优先级枚举
    
    定义系统中通用的数值优先级，用于需要数值比较的场景。
    """
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class OperationResult:
    """操作结果数据传输对象
    
    封装操作执行结果，提供统一的返回格式。
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PagedResult:
    """分页结果数据传输对象
    
    封装分页查询的结果，提供统一的分页信息。
    """
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @property
    def total_pages(self) -> int:
        """计算总页数"""
        return (self.total + self.page_size - 1) // self.page_size