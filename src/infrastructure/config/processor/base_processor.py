"""配置处理器基类

定义配置处理器的基础接口和抽象类，提供配置处理的通用框架。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class IConfigProcessor(ABC):
    """配置处理器接口"""
    
    @abstractmethod
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置数据
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取处理器名称
        
        Returns:
            处理器名称
        """
        pass


class BaseConfigProcessor(IConfigProcessor):
    """配置处理器基类
    
    提供配置处理的基础功能。
    """
    
    def __init__(self, name: str):
        """初始化处理器
        
        Args:
            name: 处理器名称
        """
        self.name = name
        self.enabled = True
        
    def get_name(self) -> str:
        """获取处理器名称
        
        Returns:
            处理器名称
        """
        return self.name
    
    def set_enabled(self, enabled: bool) -> None:
        """设置处理器启用状态
        
        Args:
            enabled: 是否启用
        """
        self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """检查处理器是否启用
        
        Returns:
            是否启用
        """
        return self.enabled
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置数据
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        if not self.enabled:
            logger.debug(f"处理器 {self.name} 已禁用，跳过处理")
            return config
        
        logger.debug(f"开始使用处理器 {self.name} 处理配置")
        
        try:
            result = self._process_internal(config, config_path)
            logger.debug(f"处理器 {self.name} 处理完成")
            return result
        except Exception as e:
            logger.error(f"处理器 {self.name} 处理失败: {e}")
            raise
    
    @abstractmethod
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """内部处理逻辑
        
        子类应该重写此方法实现具体的处理逻辑。
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        pass


class ProcessorContext:
    """处理器上下文
    
    提供处理器运行时的上下文信息。
    """
    
    def __init__(self, config_path: str):
        """初始化上下文
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.metadata: Dict[str, Any] = {}
        self.processing_history: list[str] = []
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def add_processing_step(self, processor_name: str) -> None:
        """添加处理步骤
        
        Args:
            processor_name: 处理器名称
        """
        self.processing_history.append(processor_name)
    
    def get_processing_history(self) -> list[str]:
        """获取处理历史
        
        Returns:
            处理历史列表
        """
        return self.processing_history.copy()


class ProcessorResult:
    """处理器结果
    
    封装处理器的处理结果和元数据。
    """
    
    def __init__(self, 
                 config: Dict[str, Any], 
                 success: bool = True,
                 errors: Optional[list[str]] = None,
                 warnings: Optional[list[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """初始化处理结果
        
        Args:
            config: 处理后的配置数据
            success: 是否成功
            errors: 错误列表
            warnings: 警告列表
            metadata: 元数据
        """
        self.config = config
        self.success = success
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
    
    def is_success(self) -> bool:
        """检查是否成功
        
        Returns:
            是否成功
        """
        return self.success
    
    def get_errors(self) -> list[str]:
        """获取错误列表
        
        Returns:
            错误列表
        """
        return self.errors.copy()
    
    def get_warnings(self) -> list[str]:
        """获取警告列表
        
        Returns:
            警告列表
        """
        return self.warnings.copy()
    
    def add_error(self, error: str) -> None:
        """添加错误
        
        Args:
            error: 错误信息
        """
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """添加警告
        
        Args:
            warning: 警告信息
        """
        self.warnings.append(warning)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value