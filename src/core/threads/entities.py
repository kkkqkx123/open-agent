"""Thread实体定义"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ThreadStatus(str, Enum):
    """线程状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused" 
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    BRANCHED = "branched"  # 已分支状态


class ThreadType(str, Enum):
    """线程类型枚举"""
    MAIN = "main"          # 主线线程
    BRANCH = "branch"      # 分支线程
    SNAPSHOT = "snapshot"  # 快照线程
    FORK = "fork"         # 派生线程


class ThreadMetadata(BaseModel):
    """线程元数据模型"""
    
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic配置"""
        extra = "allow"


class Thread(BaseModel):
    """线程实体模型"""
    
    id: str = Field(..., description="线程唯一标识")
    status: ThreadStatus = Field(default=ThreadStatus.ACTIVE, description="线程状态")
    type: ThreadType = Field(default=ThreadType.MAIN, description="线程类型")
    
    # 关联关系
    graph_id: Optional[str] = Field(None, description="关联的图ID")
    parent_thread_id: Optional[str] = Field(None, description="父线程ID")
    source_checkpoint_id: Optional[str] = Field(None, description="源检查点ID")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    # 元数据
    metadata: ThreadMetadata = Field(default_factory=ThreadMetadata, description="线程元数据")
    
    # 配置和状态
    config: Dict[str, Any] = Field(default_factory=dict, description="线程配置")
    state: Dict[str, Any] = Field(default_factory=dict, description="线程状态")
    
    # 统计信息
    message_count: int = Field(default=0, description="消息数量")
    checkpoint_count: int = Field(default=0, description="检查点数量")
    branch_count: int = Field(default=0, description="分支数量")
    
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
    
    def increment_branch_count(self) -> None:
        """增加分支计数"""
        self.branch_count += 1
        self.update_timestamp()
    
    def can_transition_to(self, new_status: ThreadStatus) -> bool:
        """检查是否可以转换到指定状态
        
        Args:
            new_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        # 定义状态转换规则
        valid_transitions = {
            ThreadStatus.ACTIVE: [ThreadStatus.PAUSED, ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.ARCHIVED, ThreadStatus.BRANCHED],
            ThreadStatus.PAUSED: [ThreadStatus.ACTIVE, ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.ARCHIVED],
            ThreadStatus.COMPLETED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED],
            ThreadStatus.FAILED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED],
            ThreadStatus.ARCHIVED: [ThreadStatus.ACTIVE],  # 可以重新激活归档的线程
            ThreadStatus.BRANCHED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED]  # 分支状态可以重新激活或归档
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status: ThreadStatus) -> bool:
        """转换线程状态
        
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
    
    def is_forkable(self) -> bool:
        """检查是否可以派生分支
        
        Returns:
            可以派生返回True，否则返回False
        """
        return self.status in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Thread":
        """从字典创建实例"""
        return cls(**data)


class ThreadBranch(BaseModel):
    """线程分支实体模型"""
    
    id: str = Field(..., description="分支唯一标识")
    thread_id: str = Field(..., description="所属线程ID")
    parent_thread_id: str = Field(..., description="父线程ID")
    source_checkpoint_id: str = Field(..., description="源检查点ID")
    
    branch_name: str = Field(..., description="分支名称")
    branch_type: str = Field(default="user", description="分支类型")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="分支元数据")
    
    class Config:
        """Pydantic配置"""
        extra = "allow"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadBranch":
        """从字典创建实例"""
        return cls(**data)


class ThreadSnapshot(BaseModel):
    """线程快照实体模型"""
    
    id: str = Field(..., description="快照唯一标识")
    thread_id: str = Field(..., description="所属线程ID")
    
    snapshot_name: str = Field(..., description="快照名称")
    description: Optional[str] = Field(None, description="快照描述")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    
    # 状态快照
    state_snapshot: Dict[str, Any] = Field(default_factory=dict, description="状态快照")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="快照元数据")
    
    # 统计信息
    message_count: int = Field(default=0, description="消息数量")
    checkpoint_count: int = Field(default=0, description="检查点数量")
    
    class Config:
        """Pydantic配置"""
        extra = "allow"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadSnapshot":
        """从字典创建实例"""
        return cls(**data)