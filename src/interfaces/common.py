"""通用模块接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from src.core.logger.handlers.base_handler import BaseHandler
    from src.services.logger.redactor import LogRedactor


# 会话状态定义
class AbstractSessionStatus(str, Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    
    # 类变量标记，允许子类化（若需要）
    # 默认情况下，使用此类直接作为状态，无需继承


class AbstractSessionData(ABC):
    """会话数据抽象接口"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """会话ID"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> AbstractSessionStatus:
        """会话状态"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass


class AbstractThreadData(ABC):
    """线程数据抽象接口"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """线程ID"""
        pass
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """关联的会话ID"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass


class AbstractThreadBranchData(ABC):
    """线程分支数据抽象接口"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """分支ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """关联的线程ID"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass


class AbstractThreadSnapshotData(ABC):
    """线程快照数据抽象接口"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """快照ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> str:
        """关联的线程ID"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass


class IConfigLoader(ABC):
    """配置加载器接口"""
    
    @property
    @abstractmethod
    def base_path(self) -> Path:
        """获取配置基础路径"""
        pass
    
    @abstractmethod
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Returns:
            配置数据
        """
        pass
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件（简化接口）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置数据
        """
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载所有配置"""
        pass
    
    @abstractmethod
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听配置变化
        
        Args:
            callback: 变化回调函数
        """
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass
    
    @abstractmethod
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量
        
        Args:
            config: 配置数据
            
        Returns:
            解析后的配置
        """
        pass
    
    @abstractmethod
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置数据或None
        """
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], config_path: str, config_type: Optional[str] = None) -> None:
        """保存配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            config_type: 配置类型（可选）
        """
        pass
    
    @abstractmethod
    def list_configs(self, config_type: Optional[str] = None) -> List[str]:
        """列出配置文件
        
        Args:
            config_type: 配置类型（可选）
            
        Returns:
            配置文件路径列表
        """
        pass
    
    @abstractmethod
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            路径是否有效
        """
        pass
    
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件（内部方法）
        
        Args:
            file_path: 文件路径
        """
        pass


class IConfigInheritanceHandler(ABC):
    """配置继承处理器接口"""
    
    @abstractmethod
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """解析配置继承关系
        
        Args:
            config: 原始配置
            base_path: 基础路径
            
        Returns:
            解析后的配置
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any], schema: Optional[object] = None) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        pass


class ISerializable(ABC):
    """可序列化接口"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ISerializable':
        """从字典创建实例"""
        pass


class ICacheable(ABC):
    """可缓存接口"""
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """获取缓存键"""
        pass
    
    @abstractmethod
    def get_cache_ttl(self) -> int:
        """获取缓存TTL"""
        pass


class ITimestamped(ABC):
    """时间戳接口"""
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        pass


class IStorage(ABC):
    """统一存储接口"""
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any]) -> list[Dict[str, Any]]:
        """列出数据"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据"""
        pass


class ServiceLifetime(str, Enum):
    """服务生命周期枚举"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ILogger(ABC):
    """日志记录器接口"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        pass
    
    @abstractmethod
    def add_handler(self, handler: 'BaseHandler') -> None:
        """添加日志处理器"""
        pass

    @abstractmethod
    def remove_handler(self, handler: 'BaseHandler') -> None:
        """移除日志处理器"""
        pass

    @abstractmethod
    def set_redactor(self, redactor: 'LogRedactor') -> None:
        """设置日志脱敏器"""
        pass