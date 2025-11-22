"""核心历史管理模块

提供历史记录管理的核心实体、接口和基础实现。
"""

from .entities import (
    BaseHistoryRecord,
    LLMRequestRecord,
    LLMResponseRecord,
    TokenUsageRecord,
    CostRecord,
    WorkflowTokenStatistics,
    RecordType
)

from .interfaces import (
    IHistoryStorage,
    ITokenTracker
)

__all__ = [
    # 实体
    "BaseHistoryRecord",
    "LLMRequestRecord", 
    "LLMResponseRecord",
    "TokenUsageRecord",
    "CostRecord",
    "WorkflowTokenStatistics",
    "RecordType",
    
    # 接口
    "IHistoryStorage",
    "ITokenTracker",
]