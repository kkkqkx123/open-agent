"""
转换上下文

提供转换过程中的上下文信息和状态管理。
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime

from src.services.logger.injection import get_logger
from src.interfaces.llm.converters import IConversionContext


@dataclass
class ConversionContext(IConversionContext):
    """转换上下文
    
    存储转换过程中的所有上下文信息和状态。
    """
    
    # 基础信息
    provider_name: str
    conversion_type: str  # "request", "response", "stream", "format"
    source_format: Optional[str] = None
    target_format: Optional[str] = None
    
    # 转换参数
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 状态信息
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 缓存和优化
    cache_enabled: bool = True
    cache_key: Optional[str] = None
    cache_ttl: Optional[int] = None
    
    # 调试信息
    debug_mode: bool = False
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        self.logger = get_logger(__name__)
        
        # 生成缓存键
        if self.cache_enabled and not self.cache_key:
            self.cache_key = self._generate_cache_key()
    
    def add_error(self, error: str) -> None:
        """添加错误信息
        
        Args:
            error: 错误信息
        """
        self.errors.append(error)
        self.logger.error(f"转换错误: {error}")
    
    def add_warning(self, warning: str) -> None:
        """添加警告信息
        
        Args:
            warning: 警告信息
        """
        self.warnings.append(warning)
        self.logger.warning(f"转换警告: {warning}")
    
    def add_debug_info(self, key: str, value: Any) -> None:
        """添加调试信息
        
        Args:
            key: 调试信息键
            value: 调试信息值
        """
        if self.debug_mode:
            self.debug_info[key] = value
    
    def has_errors(self) -> bool:
        """检查是否有错误
        
        Returns:
            bool: 是否有错误
        """
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """检查是否有警告
        
        Returns:
            bool: 是否有警告
        """
        return len(self.warnings) > 0
    
    def get_duration(self) -> Optional[float]:
        """获取转换持续时间
        
        Returns:
            Optional[float]: 持续时间（秒），如果未结束则返回None
        """
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def mark_completed(self) -> None:
        """标记转换完成"""
        self.end_time = datetime.now()
        
        if self.debug_mode:
            duration = self.get_duration()
            if duration is not None:
                self.add_debug_info("duration_seconds", duration)
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值
        
        Args:
            key: 参数键
            default: 默认值
            
        Returns:
            Any: 参数值
        """
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值
        
        Args:
            key: 参数键
            value: 参数值
        """
        self.parameters[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            Any: 元数据值
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def _generate_cache_key(self) -> str:
        """生成缓存键
        
        Returns:
            str: 缓存键
        """
        import hashlib
        import json
        
        # 构建缓存键的基础数据
        cache_data = {
            "provider": self.provider_name,
            "type": self.conversion_type,
            "source_format": self.source_format,
            "target_format": self.target_format,
            "parameters": self.parameters
        }
        
        # 生成哈希
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()
    
    def create_child_context(self, conversion_type: str, **kwargs: Any) -> "ConversionContext":
        """创建子上下文
        
        Args:
            conversion_type: 子转换类型
            **kwargs: 额外的上下文参数
            
        Returns:
            ConversionContext: 子上下文
        """
        child = ConversionContext(
            provider_name=self.provider_name,
            conversion_type=conversion_type,
            parameters=self.parameters.copy(),
            metadata=self.metadata.copy(),
            cache_enabled=self.cache_enabled,
            debug_mode=self.debug_mode,
            **kwargs
        )
        
        return child
    
    def merge_context(self, other: IConversionContext) -> None:
        """合并另一个上下文
        
        Args:
            other: 另一个上下文
        """
        # 合并错误和警告
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        
        # 合并元数据
        self.metadata.update(other.metadata)
        
        # 合并调试信息
        if (hasattr(other, 'debug_mode') and other.debug_mode and
            hasattr(other, 'debug_info') and hasattr(self, 'debug_info')):
            self.debug_info.update(getattr(other, 'debug_info', {}))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "provider_name": self.provider_name,
            "conversion_type": self.conversion_type,
            "source_format": self.source_format,
            "target_format": self.target_format,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "errors": self.errors,
            "warnings": self.warnings,
            "cache_enabled": self.cache_enabled,
            "cache_key": self.cache_key,
            "debug_mode": self.debug_mode,
            "debug_info": self.debug_info if self.debug_mode else None
        }
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 字符串表示
        """
        return f"ConversionContext(provider={self.provider_name}, type={self.conversion_type})"
    
    def __repr__(self) -> str:
        """详细字符串表示
        
        Returns:
            str: 详细字符串表示
        """
        return (f"ConversionContext(provider_name='{self.provider_name}', "
                f"conversion_type='{self.conversion_type}', "
                f"source_format='{self.source_format}', "
                f"target_format='{self.target_format}', "
                f"errors={len(self.errors)}, "
                f"warnings={len(self.warnings)})")