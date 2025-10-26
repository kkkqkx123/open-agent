"""Checkpoint配置模型

定义checkpoint系统的配置数据结构。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class CheckpointConfig:
    """Checkpoint配置类
    
    定义checkpoint系统的各种配置选项。
    """
    enabled: bool = True
    storage_type: str = "sqlite"  # "sqlite" | "memory"
    auto_save: bool = True
    save_interval: int = 5  # 每5步保存一次
    max_checkpoints: int = 100
    retention_days: int = 30
    trigger_conditions: List[str] = field(default_factory=lambda: ["tool_call", "state_change"])
    db_path: Optional[str] = None  # SQLite数据库路径
    compression: bool = False  # 是否压缩存储
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointConfig":
        """从字典创建配置
        
        Args:
            data: 配置字典
            
        Returns:
            CheckpointConfig: 配置对象
        """
        return cls(
            enabled=data.get("enabled", True),
            storage_type=data.get("storage_type", "sqlite"),
            auto_save=data.get("auto_save", True),
            save_interval=data.get("save_interval", 5),
            max_checkpoints=data.get("max_checkpoints", 100),
            retention_days=data.get("retention_days", 30),
            trigger_conditions=data.get("trigger_conditions", ["tool_call", "state_change"]),
            db_path=data.get("db_path"),
            compression=data.get("compression", False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "enabled": self.enabled,
            "storage_type": self.storage_type,
            "auto_save": self.auto_save,
            "save_interval": self.save_interval,
            "max_checkpoints": self.max_checkpoints,
            "retention_days": self.retention_days,
            "trigger_conditions": self.trigger_conditions,
            "db_path": self.db_path,
            "compression": self.compression
        }
    
    def validate(self) -> List[str]:
        """验证配置的有效性
        
        Returns:
            List[str]: 错误信息列表，如果配置有效则返回空列表
        """
        errors = []
        
        if self.storage_type not in ["sqlite", "memory"]:
            errors.append(f"不支持的存储类型: {self.storage_type}")
        
        if self.save_interval <= 0:
            errors.append("保存间隔必须大于0")
        
        if self.max_checkpoints <= 0:
            errors.append("最大checkpoint数量必须大于0")
        
        if self.retention_days <= 0:
            errors.append("保留天数必须大于0")
        
        if self.storage_type == "sqlite" and not self.db_path:
            errors.append("SQLite存储需要指定数据库路径")
        
        return errors


@dataclass
class CheckpointMetadata:
    """Checkpoint元数据
    
    存储checkpoint的附加信息。
    """
    checkpoint_id: str
    session_id: str
    workflow_id: str
    step_count: int = 0
    node_name: Optional[str] = None
    trigger_reason: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointMetadata":
        """从字典创建元数据
        
        Args:
            data: 元数据字典
            
        Returns:
            CheckpointMetadata: 元数据对象
        """
        return cls(
            checkpoint_id=data["checkpoint_id"],
            session_id=data["session_id"],
            workflow_id=data["workflow_id"],
            step_count=data.get("step_count", 0),
            node_name=data.get("node_name"),
            trigger_reason=data.get("trigger_reason"),
            tags=data.get("tags", []),
            custom_data=data.get("custom_data", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 元数据字典
        """
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "step_count": self.step_count,
            "node_name": self.node_name,
            "trigger_reason": self.trigger_reason,
            "tags": self.tags,
            "custom_data": self.custom_data
        }