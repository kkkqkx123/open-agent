"""
统一存储领域模型

定义了统一存储的数据结构和相关模型，包括数据验证和序列化支持。
"""

from typing import Dict, Any, Optional, List, Iterator
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class DataType(str, Enum):
    """数据类型枚举"""
    SESSION = "session"
    THREAD = "thread"
    THREAD_BRANCH = "thread_branch"
    THREAD_SNAPSHOT = "thread_snapshot"
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    CHECKPOINT = "checkpoint"
    CHECKPOINT_VERSION = "checkpoint_version"


class StorageData(BaseModel):
    """统一存储数据模型"""
    id: str = Field(..., description="数据唯一标识")
    type: DataType = Field(..., description="数据类型")
    data: Dict[str, Any] = Field(..., description="实际数据内容")
    session_id: Optional[str] = Field(None, description="关联的会话ID")
    thread_id: Optional[str] = Field(None, description="关联的线程ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True
    
    @validator('updated_at')
    def validate_updated_at(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        """验证更新时间不早于创建时间"""
        if 'created_at' in values and v < values['created_at']:
            raise ValueError("updated_at cannot be earlier than created_at")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageData':
        """从字典创建实例"""
        return cls(**data)
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.now()


class StorageQuery(BaseModel):
    """存储查询模型"""
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    limit: Optional[int] = Field(None, ge=1, description="限制数量")
    offset: Optional[int] = Field(None, ge=0, description="偏移量")
    order_by: Optional[str] = Field(None, description="排序字段")
    order_desc: bool = Field(False, description="是否降序")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageTransaction(BaseModel):
    """存储事务模型"""
    operations: List[Dict[str, Any]] = Field(..., description="操作列表")
    
    def add_save(self, data: Dict[str, Any]) -> None:
        """添加保存操作"""
        self.operations.append({
            "type": "save",
            "data": data
        })
    
    def add_update(self, id: str, updates: Dict[str, Any]) -> None:
        """添加更新操作"""
        self.operations.append({
            "type": "update",
            "id": id,
            "data": updates
        })
    
    def add_delete(self, id: str) -> None:
        """添加删除操作"""
        self.operations.append({
            "type": "delete",
            "id": id
        })
    
    def is_empty(self) -> bool:
        """检查是否为空事务"""
        return len(self.operations) == 0


class StorageStatistics(BaseModel):
    """存储统计模型"""
    total_count: int = Field(..., ge=0, description="总数量")
    total_size: int = Field(..., ge=0, description="总大小（字节）")
    type_distribution: Dict[str, int] = Field(default_factory=dict, description="类型分布")
    oldest_record: Optional[datetime] = Field(None, description="最早记录时间")
    newest_record: Optional[datetime] = Field(None, description="最新记录时间")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageHealth(BaseModel):
    """存储健康状态模型"""
    status: str = Field(..., description="健康状态")
    message: Optional[str] = Field(None, description="状态消息")
    response_time: Optional[float] = Field(None, ge=0, description="响应时间（毫秒）")
    error_count: int = Field(0, ge=0, description="错误计数")
    last_check: datetime = Field(default_factory=datetime.now, description="最后检查时间")
    
    def is_healthy(self) -> bool:
        """检查是否健康"""
        return self.status.lower() == "healthy"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageConfig(BaseModel):
    """存储配置模型"""
    storage_type: str = Field(..., description="存储类型")
    connection_string: Optional[str] = Field(None, description="连接字符串")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="配置参数")
    pool_size: int = Field(10, ge=1, description="连接池大小")
    timeout: int = Field(30, ge=1, description="超时时间（秒）")
    retry_count: int = Field(3, ge=0, description="重试次数")
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取配置参数"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """设置配置参数"""
        self.parameters[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageBatch(BaseModel):
    """存储批处理模型"""
    items: List[Dict[str, Any]] = Field(..., description="批处理项目")
    batch_size: int = Field(100, ge=1, description="批次大小")
    max_retries: int = Field(3, ge=0, description="最大重试次数")
    
    def iter_batches(self) -> Iterator[List[Dict[str, Any]]]:
        """迭代器，按批次返回数据"""
        for i in range(0, len(self.items), self.batch_size):
            yield self.items[i:i + self.batch_size]
    
    def batch_count(self) -> int:
        """获取批次数量"""
        return (len(self.items) + self.batch_size - 1) // self.batch_size


class StorageMigration(BaseModel):
    """存储迁移模型"""
    version: str = Field(..., description="迁移版本")
    description: str = Field(..., description="迁移描述")
    script: str = Field(..., description="迁移脚本")
    dependencies: List[str] = Field(default_factory=list, description="依赖版本")
    rollback_script: Optional[str] = Field(None, description="回滚脚本")
    applied_at: Optional[datetime] = Field(None, description="应用时间")
    
    def is_applied(self) -> bool:
        """检查是否已应用"""
        return self.applied_at is not None
    
    def mark_applied(self) -> None:
        """标记为已应用"""
        self.applied_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()
