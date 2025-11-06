"""迭代相关类型定义

定义迭代管理中使用的类型结构。
"""

from typing import TypedDict, List, Dict, Optional
from datetime import datetime


class IterationRecord(TypedDict):
    """单次迭代记录"""
    node_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    status: str  # 'SUCCESS', 'FAILURE', etc.
    error: Optional[str]


class NodeIterationStats(TypedDict):
    """节点级别的迭代统计"""
    count: int
    total_duration: float
    errors: int


class IterationHistory(TypedDict):
    """迭代历史记录列表"""
    iterations: List[IterationRecord]