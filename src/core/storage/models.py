"""
通用存储数据模型

定义了存储系统的通用数据结构和相关模型，移除了领域特定的内容。
"""

from typing import Dict, Any, Optional, List, Iterator, Union
from datetime import datetime
from enum import Enum, auto
from pydantic import BaseModel, Field, field_validator, ConfigDict


class StorageBackendType(str, Enum):
    """存储后端类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"
    REDIS = "redis"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"


class StorageOperationType(str, Enum):
    """存储操作类型枚举"""
    SAVE = "save"
    LOAD = "load"
    DELETE = "delete"
    QUERY = "query"
    BATCH = "batch"
    TRANSACTION = "transaction"


class StorageStatus(str, Enum):
    """存储状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class StorageData(BaseModel):
    """通用存储数据模型"""
    model_config = ConfigDict(use_enum_values=True)
    
    key: str = Field(..., description="数据键")
    value: Dict[str, Any] = Field(..., description="数据值")
    content_type: Optional[str] = Field("application/json", description="内容类型")
    encoding: Optional[str] = Field("utf-8", description="编码格式")
    checksum: Optional[str] = Field(None, description="数据校验和")
    size: Optional[int] = Field(None, description="数据大小（字节）")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @field_validator('updated_at', mode='after')
    @classmethod
    def validate_updated_at(cls, v: datetime, info) -> datetime:
        """验证更新时间不早于创建时间"""
        created_at = info.data.get('created_at')
        if created_at and v < created_at:
            raise ValueError("updated_at cannot be earlier than created_at")
        return v
    
    @field_validator('expires_at', mode='after')
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """验证过期时间不早于创建时间"""
        if v is not None:
            created_at = info.data.get('created_at')
            if created_at and v < created_at:
                raise ValueError("expires_at cannot be earlier than created_at")
        return v
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
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


class StorageOperation(BaseModel):
    """存储操作模型"""
    operation_type: StorageOperationType = Field(..., description="操作类型")
    key: Optional[str] = Field(None, description="操作键")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")
    criteria: Optional[Dict[str, Any]] = Field(None, description="查询条件")
    timestamp: datetime = Field(default_factory=datetime.now, description="操作时间")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作元数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageResult(BaseModel):
    """存储结果模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    operation_id: Optional[str] = Field(None, description="操作ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="结果时间")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="结果元数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageTransaction(BaseModel):
    """存储事务模型"""
    transaction_id: str = Field(..., description="事务ID")
    operations: List[StorageOperation] = Field(default_factory=list, description="操作列表")
    status: str = Field("pending", description="事务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    def add_operation(self, operation: StorageOperation) -> None:
        """添加操作"""
        self.operations.append(operation)
        self.updated_at = datetime.now()
    
    def is_empty(self) -> bool:
        """检查是否为空事务"""
        return len(self.operations) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageStatistics(BaseModel):
    """存储统计模型"""
    total_count: int = Field(..., ge=0, description="总数量")
    total_size: int = Field(..., ge=0, description="总大小（字节）")
    backend_type: StorageBackendType = Field(..., description="后端类型")
    hit_rate: Optional[float] = Field(None, ge=0, le=1, description="命中率")
    avg_response_time: Optional[float] = Field(None, ge=0, description="平均响应时间（毫秒）")
    oldest_record: Optional[datetime] = Field(None, description="最早记录时间")
    newest_record: Optional[datetime] = Field(None, description="最新记录时间")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageHealth(BaseModel):
    """存储健康状态模型"""
    status: StorageStatus = Field(..., description="健康状态")
    message: Optional[str] = Field(None, description="状态消息")
    response_time: Optional[float] = Field(None, ge=0, description="响应时间（毫秒）")
    error_count: int = Field(0, ge=0, description="错误计数")
    last_check: datetime = Field(default_factory=datetime.now, description="最后检查时间")
    backend_type: StorageBackendType = Field(..., description="后端类型")
    
    def is_healthy(self) -> bool:
        """检查是否健康"""
        return self.status == StorageStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageConfig(BaseModel):
    """存储配置模型"""
    backend_type: StorageBackendType = Field(..., description="存储后端类型")
    connection_string: Optional[str] = Field(None, description="连接字符串")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="配置参数")
    pool_size: int = Field(10, ge=1, description="连接池大小")
    timeout: int = Field(30, ge=1, description="超时时间（秒）")
    retry_count: int = Field(3, ge=0, description="重试次数")
    enable_compression: bool = Field(False, description="是否启用压缩")
    enable_encryption: bool = Field(False, description="是否启用加密")
    
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
    operations: List[StorageOperation] = Field(..., description="批处理操作")
    batch_size: int = Field(100, ge=1, description="批次大小")
    max_retries: int = Field(3, ge=0, description="最大重试次数")
    continue_on_error: bool = Field(True, description="遇到错误时是否继续")
    
    def iter_batches(self) -> Iterator[List[StorageOperation]]:
        """迭代器，按批次返回操作"""
        for i in range(0, len(self.operations), self.batch_size):
            yield self.operations[i:i + self.batch_size]
    
    def batch_count(self) -> int:
        """获取批次数量"""
        return (len(self.operations) + self.batch_size - 1) // self.batch_size


class StorageMigration(BaseModel):
    """存储迁移模型"""
    version: str = Field(..., description="迁移版本")
    description: str = Field(..., description="迁移描述")
    script: str = Field(..., description="迁移脚本")
    dependencies: List[str] = Field(default_factory=list, description="依赖版本")
    rollback_script: Optional[str] = Field(None, description="回滚脚本")
    applied_at: Optional[datetime] = Field(None, description="应用时间")
    backend_type: StorageBackendType = Field(..., description="适用的后端类型")
    
    def is_applied(self) -> bool:
        """检查是否已应用"""
        return self.applied_at is not None
    
    def mark_applied(self) -> None:
        """标记为已应用"""
        self.applied_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()


class StorageBackendInfo(BaseModel):
    """存储后端信息模型"""
    name: str = Field(..., description="后端名称")
    backend_type: StorageBackendType = Field(..., description="后端类型")
    status: StorageStatus = Field(..., description="后端状态")
    is_default: bool = Field(False, description="是否为默认后端")
    config: StorageConfig = Field(..., description="后端配置")
    statistics: Optional[StorageStatistics] = Field(None, description="统计信息")
    health: Optional[StorageHealth] = Field(None, description="健康状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_accessed: Optional[datetime] = Field(None, description="最后访问时间")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()
