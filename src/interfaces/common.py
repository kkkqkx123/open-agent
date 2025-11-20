"""通用模块接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from datetime import datetime


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