"""
文件存储配置

定义文件存储的配置参数和验证逻辑。
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class FileStorageConfig(BaseModel):
    """文件存储配置类
    
    定义文件存储的配置参数，包括基础路径、文件格式等。
    """
    
    base_path: str = Field(
        ..., 
        description="文件存储基础路径"
    )
    
    file_format: str = Field(
        "json", 
        description="文件格式：json, pickle, yaml"
    )
    
    directory_structure: str = Field(
        "flat", 
        description="目录结构：flat, by_type, by_date, hierarchical"
    )
    
    enable_compression: bool = Field(
        False, 
        description="是否启用文件压缩"
    )
    
    compression_type: str = Field(
        "gzip", 
        description="压缩类型：gzip, bz2, lzma"
    )
    
    compression_level: int = Field(
        6, 
        ge=1, 
        le=9, 
        description="压缩级别（1-9）"
    )
    
    enable_encryption: bool = Field(
        False, 
        description="是否启用文件加密"
    )
    
    encryption_key: Optional[str] = Field(
        None, 
        description="加密密钥"
    )
    
    enable_file_locking: bool = Field(
        True, 
        description="是否启用文件锁定"
    )
    
    lock_timeout: float = Field(
        30.0, 
        ge=1.0, 
        description="文件锁定超时时间（秒）"
    )
    
    enable_backup: bool = Field(
        True, 
        description="是否启用文件备份"
    )
    
    backup_count: int = Field(
        3, 
        ge=1, 
        description="备份文件数量"
    )
    
    enable_metadata_file: bool = Field(
        True, 
        description="是否启用元数据文件"
    )
    
    metadata_file_name: str = Field(
        ".metadata.json", 
        description="元数据文件名"
    )
    
    enable_indexing: bool = Field(
        True, 
        description="是否启用文件索引"
    )
    
    index_file_name: str = Field(
        ".index.json", 
        description="索引文件名"
    )
    
    auto_create_directories: bool = Field(
        True, 
        description="是否自动创建目录"
    )
    
    max_file_size_mb: Optional[int] = Field(
        None, 
        ge=1, 
        description="最大文件大小（MB），None表示无限制"
    )
    
    cleanup_interval_hours: int = Field(
        24, 
        ge=1, 
        description="清理间隔时间（小时）"
    )
    
    retention_days: int = Field(
        30, 
        ge=1, 
        description="文件保留天数"
    )
    
    enable_sync: bool = Field(
        True, 
        description="是否启用同步写入"
    )
    
    sync_interval: int = Field(
        5, 
        ge=1, 
        description="同步间隔（秒）"
    )
    
    @validator('file_format')
    def validate_file_format(cls, v):
        """验证文件格式"""
        valid_formats = ["json", "pickle", "yaml"]
        if v.lower() not in valid_formats:
            raise ValueError(f"file_format must be one of {valid_formats}")
        return v.lower()
    
    @validator('directory_structure')
    def validate_directory_structure(cls, v):
        """验证目录结构"""
        valid_structures = ["flat", "by_type", "by_date", "hierarchical"]
        if v.lower() not in valid_structures:
            raise ValueError(f"directory_structure must be one of {valid_structures}")
        return v.lower()
    
    @validator('compression_type')
    def validate_compression_type(cls, v):
        """验证压缩类型"""
        valid_types = ["gzip", "bz2", "lzma"]
        if v.lower() not in valid_types:
            raise ValueError(f"compression_type must be one of {valid_types}")
        return v.lower()
    
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
    def from_dict(cls, config: Dict[str, Any]) -> 'FileStorageConfig':
        """从字典创建配置"""
        return cls(**config)
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        extension = f".{self.file_format}"
        
        if self.enable_compression:
            if self.compression_type == "gzip":
                extension += ".gz"
            elif self.compression_type == "bz2":
                extension += ".bz2"
            elif self.compression_type == "lzma":
                extension += ".xz"
        
        return extension
    
    def get_directory_path(self, data_type: Optional[str] = None, date: Optional[str] = None) -> str:
        """获取目录路径"""
        path = self.base_path
        
        if self.directory_structure == "by_type" and data_type:
            path = os.path.join(path, data_type)
        elif self.directory_structure == "by_date" and date:
            path = os.path.join(path, date)
        elif self.directory_structure == "hierarchical" and data_type and date:
            path = os.path.join(path, data_type, date)
        
        return path
    
    def get_file_path(self, id: str, data_type: Optional[str] = None, date: Optional[str] = None) -> str:
        """获取文件路径"""
        directory = self.get_directory_path(data_type, date)
        filename = f"{id}{self.get_file_extension()}"
        return os.path.join(directory, filename)
    
    def get_backup_file_path(self, file_path: str, backup_index: int) -> str:
        """获取备份文件路径"""
        base, ext = os.path.splitext(file_path)
        return f"{base}.backup{backup_index}{ext}"
    
    def get_metadata_file_path(self, directory: str) -> str:
        """获取元数据文件路径"""
        return os.path.join(directory, self.metadata_file_name)
    
    def get_index_file_path(self, directory: str) -> str:
        """获取索引文件路径"""
        return os.path.join(directory, self.index_file_name)