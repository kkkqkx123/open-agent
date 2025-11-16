"""
SQLite存储配置

定义SQLite存储的配置参数和验证逻辑。
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class SQLiteStorageConfig(BaseModel):
    """SQLite存储配置类
    
    定义SQLite存储的配置参数，包括数据库路径、连接池等。
    """
    
    database_path: str = Field(
        ..., 
        description="SQLite数据库文件路径"
    )
    
    pool_size: int = Field(
        10, 
        ge=1, 
        le=100, 
        description="连接池大小"
    )
    
    max_overflow: int = Field(
        10, 
        ge=0, 
        le=100, 
        description="连接池最大溢出数量"
    )
    
    pool_timeout: float = Field(
        30.0, 
        ge=1.0, 
        description="获取连接超时时间（秒）"
    )
    
    pool_recycle: int = Field(
        3600, 
        ge=60, 
        description="连接回收时间（秒）"
    )
    
    enable_wal: bool = Field(
        True, 
        description="是否启用WAL模式"
    )
    
    enable_foreign_keys: bool = Field(
        True, 
        description="是否启用外键约束"
    )
    
    journal_mode: str = Field(
        "WAL", 
        description="日志模式：DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF"
    )
    
    synchronous: str = Field(
        "NORMAL", 
        description="同步模式：OFF, NORMAL, FULL, EXTRA"
    )
    
    cache_size: int = Field(
        2000, 
        ge=0, 
        description="缓存页面数"
    )
    
    temp_store: str = Field(
        "MEMORY", 
        description="临时存储位置：DEFAULT, FILE, MEMORY"
    )
    
    mmap_size: int = Field(
        0, 
        ge=0, 
        description="内存映射大小（字节），0表示禁用"
    )
    
    enable_query_logging: bool = Field(
        False, 
        description="是否启用查询日志"
    )
    
    query_timeout: float = Field(
        30.0, 
        ge=1.0, 
        description="查询超时时间（秒）"
    )
    
    enable_auto_vacuum: bool = Field(
        True, 
        description="是否启用自动清理"
    )
    
    vacuum_interval_hours: int = Field(
        24, 
        ge=1, 
        description="自动清理间隔时间（小时）"
    )
    
    enable_backup: bool = Field(
        False, 
        description="是否启用自动备份"
    )
    
    backup_path: Optional[str] = Field(
        None, 
        description="备份文件路径"
    )
    
    backup_interval_hours: int = Field(
        12, 
        ge=1, 
        description="备份间隔时间（小时）"
    )
    
    max_backup_files: int = Field(
        5, 
        ge=1, 
        description="最大备份文件数量"
    )
    
    enable_encryption: bool = Field(
        False, 
        description="是否启用加密"
    )
    
    encryption_key: Optional[str] = Field(
        None, 
        description="加密密钥"
    )
    
    @validator('journal_mode')
    def validate_journal_mode(cls, v):
        """验证日志模式"""
        valid_modes = ["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"]
        if v.upper() not in valid_modes:
            raise ValueError(f"journal_mode must be one of {valid_modes}")
        return v.upper()
    
    @validator('synchronous')
    def validate_synchronous(cls, v):
        """验证同步模式"""
        valid_modes = ["OFF", "NORMAL", "FULL", "EXTRA"]
        if v.upper() not in valid_modes:
            raise ValueError(f"synchronous must be one of {valid_modes}")
        return v.upper()
    
    @validator('temp_store')
    def validate_temp_store(cls, v):
        """验证临时存储位置"""
        valid_modes = ["DEFAULT", "FILE", "MEMORY"]
        if v.upper() not in valid_modes:
            raise ValueError(f"temp_store must be one of {valid_modes}")
        return v.upper()
    
    @validator('backup_path')
    def validate_backup_path(cls, v, values):
        """验证备份路径"""
        if values.get('enable_backup') and not v:
            raise ValueError("backup_path is required when enable_backup is True")
        return v
    
    @validator('encryption_key')
    def validate_encryption_key(cls, v, values):
        """验证加密密钥"""
        if values.get('enable_encryption') and not v:
            raise ValueError("encryption_key is required when enable_encryption is True")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'SQLiteStorageConfig':
        """从字典创建配置"""
        return cls(**config)
    
    def get_connection_string(self) -> str:
        """获取连接字符串"""
        return f"sqlite:///{self.database_path}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """获取连接参数"""
        params = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.enable_query_logging,
            "connect_args": {
                "check_same_thread": False,
                "timeout": self.query_timeout
            }
        }
        
        # 添加SQLite特定参数
        sqlite_params = {}
        
        if self.enable_wal:
            sqlite_params["journal_mode"] = "WAL"
        else:
            sqlite_params["journal_mode"] = self.journal_mode
        
        sqlite_params["synchronous"] = self.synchronous
        sqlite_params["cache_size"] = self.cache_size
        sqlite_params["temp_store"] = self.temp_store
        sqlite_params["mmap_size"] = self.mmap_size
        
        if self.enable_foreign_keys:
            sqlite_params["foreign_keys"] = "ON"
        
        params["connect_args"].update(sqlite_params)
        
        return params
    
    def get_pragmas(self) -> Dict[str, Any]:
        """获取PRAGMA设置"""
        pragmas = {}
        
        if self.enable_wal:
            pragmas["journal_mode"] = "WAL"
        else:
            pragmas["journal_mode"] = self.journal_mode
        
        pragmas["synchronous"] = self.synchronous
        pragmas["cache_size"] = self.cache_size
        pragmas["temp_store"] = self.temp_store
        pragmas["mmap_size"] = self.mmap_size
        
        if self.enable_foreign_keys:
            pragmas["foreign_keys"] = "ON"
        else:
            pragmas["foreign_keys"] = "OFF"
        
        if self.enable_auto_vacuum:
            pragmas["auto_vacuum"] = "INCREMENTAL"
        
        return pragmas