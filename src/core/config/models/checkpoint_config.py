"""Checkpoint配置模型"""

from typing import List, Optional
from pydantic import Field, field_validator

from .base import BaseConfig


class CheckpointConfig(BaseConfig):
    """Checkpoint配置模型"""
    
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
    
    @field_validator("storage_type")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        """验证存储类型"""
        allowed_types = ["sqlite", "memory"]
        if v not in allowed_types:
            raise ValueError(f"存储类型必须是以下之一: {allowed_types}")
        return v
    
    @field_validator("save_interval")
    @classmethod
    def validate_save_interval(cls, v: int) -> int:
        """验证保存间隔"""
        if v <= 0:
            raise ValueError("保存间隔必须大于0")
        return v
    
    @field_validator("max_checkpoints")
    @classmethod
    def validate_max_checkpoints(cls, v: int) -> int:
        """验证最大checkpoint数量"""
        if v <= 0:
            raise ValueError("最大checkpoint数量必须大于0")
        return v
    
    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, v: int) -> int:
        """验证保留天数"""
        if v <= 0:
            raise ValueError("保留天数必须大于0")
        return v
    
    @field_validator("trigger_conditions")
    @classmethod
    def validate_trigger_conditions(cls, v: List[str]) -> List[str]:
        """验证触发条件"""
        if not v:
            raise ValueError("触发条件不能为空")
        return v
    
    def get_db_path(self) -> str:
        """获取数据库路径，如果未配置则返回默认路径"""
        if self.db_path:
            return self.db_path
        
        # 根据环境返回默认路径
        import os
        if "test" in os.environ.get("PYTEST_CURRENT_TEST", ""):
            return "storage/test/checkpoints.db"
        else:
            return "storage/checkpoints.db"