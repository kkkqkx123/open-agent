"""Checkpoint配置数据模型

提供Checkpoint所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CheckpointClientConfig(BaseModel):
    """Checkpoint配置数据模型
    
    包含Checkpoint所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """
    
    enabled: bool = Field(True, description="是否启用checkpoint功能")
    storage_type: str = Field("sqlite", description="存储类型：sqlite, memory")
    auto_save: bool = Field(True, description="是否自动保存")
    save_interval: int = Field(5, description="每N步保存一次")
    max_checkpoints: int = Field(100, description="最大保存的checkpoint数量")
    retention_days: int = Field(30, description="保留天数")
    trigger_conditions: List[str] = Field(
        default_factory=lambda: ["tool_call", "state_change"], 
        description="触发保存的条件"
    )
    db_path: Optional[str] = Field(None, description="SQLite数据库路径")
    compression: bool = Field(False, description="是否压缩存储")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointClientConfig":
        """从字典创建配置"""
        return cls(**data)


__all__ = [
    "CheckpointClientConfig"
]