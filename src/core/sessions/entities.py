"""Session实体定义"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class SessionMetadata(BaseModel):
    """会话元数据模型"""
    
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic配置"""
        extra = "allow"


class Session(BaseModel):
    """会话实体模型"""
    
    id: str = Field(..., description="会话唯一标识")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="会话状态")
    graph_id: Optional[str] = Field(None, description="关联的图ID")
    thread_id: Optional[str] = Field(None, description="关联的线程ID")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    # 元数据
    metadata: SessionMetadata = Field(default_factory=SessionMetadata, description="会话元数据")
    
    # 配置和状态
    config: Dict[str, Any] = Field(default_factory=dict, description="会话配置")
    state: Dict[str, Any] = Field(default_factory=dict, description="会话状态")
    
    # 统计信息
    message_count: int = Field(default=0, description="消息数量")
    checkpoint_count: int = Field(default=0, description="检查点数量")
    
    class Config:
        """Pydantic配置"""
        extra = "allow"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.utcnow()
    
    def increment_message_count(self) -> None:
        """增加消息计数"""
        self.message_count += 1
        self.update_timestamp()
    
    def increment_checkpoint_count(self) -> None:
        """增加检查点计数"""
        self.checkpoint_count += 1
        self.update_timestamp()
    
    def can_transition_to(self, new_status: SessionStatus) -> bool:
        """检查是否可以转换到指定状态
        
        Args:
            new_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        # 定义状态转换规则
        valid_transitions = {
            SessionStatus.ACTIVE: [SessionStatus.PAUSED, SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.ARCHIVED],
            SessionStatus.PAUSED: [SessionStatus.ACTIVE, SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.ARCHIVED],
            SessionStatus.COMPLETED: [SessionStatus.ACTIVE, SessionStatus.ARCHIVED],
            SessionStatus.FAILED: [SessionStatus.ACTIVE, SessionStatus.ARCHIVED],
            SessionStatus.ARCHIVED: [SessionStatus.ACTIVE]  # 可以重新激活归档的会话
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status: SessionStatus) -> bool:
        """转换会话状态
        
        Args:
            new_status: 目标状态
            
        Returns:
            转换成功返回True，失败返回False
        """
        if not self.can_transition_to(new_status):
            return False
        
        self.status = new_status
        self.update_timestamp()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """从字典创建实例"""
        return cls(**data)