"""
内存存储配置

定义内存存储的配置参数和验证逻辑。
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class MemoryStorageConfig(BaseModel):
    """内存存储配置类
    
    定义内存存储的配置参数，包括最大容量、过期策略等。
    """
    
    max_size: Optional[int] = Field(
        None, 
        ge=1, 
        description="最大存储条目数量，None表示无限制"
    )
    
    max_memory_mb: Optional[int] = Field(
        None, 
        ge=1, 
        description="最大内存使用量（MB），None表示无限制"
    )
    
    enable_ttl: bool = Field(
        False, 
        description="是否启用TTL（生存时间）"
    )
    
    default_ttl_seconds: int = Field(
        3600, 
        ge=1, 
        description="默认TTL时间（秒）"
    )
    
    cleanup_interval_seconds: int = Field(
        300, 
        ge=1, 
        description="清理过期数据的间隔时间（秒）"
    )
    
    enable_compression: bool = Field(
        False, 
        description="是否启用数据压缩"
    )
    
    compression_threshold: int = Field(
        1024, 
        ge=1, 
        description="压缩阈值（字节），大于此值的数据将被压缩"
    )
    
    enable_metrics: bool = Field(
        True, 
        description="是否启用性能指标收集"
    )
    
    enable_persistence: bool = Field(
        False, 
        description="是否启用持久化（保存到文件）"
    )
    
    persistence_path: Optional[str] = Field(
        None, 
        description="持久化文件路径"
    )
    
    persistence_interval_seconds: int = Field(
        600, 
        ge=1, 
        description="持久化间隔时间（秒）"
    )
    
    @validator('persistence_path')
    def validate_persistence_path(cls, v, values):
        """验证持久化路径"""
        if values.get('enable_persistence') and not v:
            raise ValueError("persistence_path is required when enable_persistence is True")
        return v
    
    @validator('max_memory_mb')
    def validate_max_memory_mb(cls, v, values):
        """验证最大内存限制"""
        if v is not None and v < 1:
            raise ValueError("max_memory_mb must be at least 1")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'MemoryStorageConfig':
        """从字典创建配置"""
        return cls(**config)
    
    def get_backend_config(self) -> Dict[str, Any]:
        """获取后端配置"""
        return {
            "max_size": self.max_size,
            "max_memory_mb": self.max_memory_mb,
            "enable_ttl": self.enable_ttl,
            "default_ttl_seconds": self.default_ttl_seconds,
            "cleanup_interval_seconds": self.cleanup_interval_seconds,
            "enable_compression": self.enable_compression,
            "compression_threshold": self.compression_threshold,
            "enable_metrics": self.enable_metrics,
            "enable_persistence": self.enable_persistence,
            "persistence_path": self.persistence_path,
            "persistence_interval_seconds": self.persistence_interval_seconds
        }