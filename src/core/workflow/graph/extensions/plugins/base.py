"""插件基类

提供插件系统的基础实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from src.interfaces.dependency_injection import get_logger
from datetime import datetime


class PluginType(Enum):
    """插件类型"""
    START = "start"
    END = "end"
    NODE = "node"
    EDGE = "edge"
    WORKFLOW = "workflow"


class PluginStatus(Enum):
    """插件状态"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginContext:
    """插件上下文"""
    workflow_id: str
    thread_id: Optional[str] = None
    session_id: Optional[str] = None
    execution_start_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginExecutionResult:
    """插件执行结果"""
    plugin_id: str
    status: str
    success: bool
    error: Optional[str] = None
    execution_time: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class IPlugin(ABC):
    """插件接口"""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """插件ID"""
        pass

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """插件类型"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @property
    def status(self) -> PluginStatus:
        """插件状态"""
        return getattr(self, '_status', PluginStatus.INACTIVE)

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def execute(self, context: PluginContext, **kwargs: Any) -> PluginExecutionResult:
        """执行插件
        
        Args:
            context: 插件上下文
            **kwargs: 额外参数
            
        Returns:
            PluginExecutionResult: 执行结果
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass

    def set_status(self, status: PluginStatus) -> None:
        """设置插件状态
        
        Args:
            status: 插件状态
        """
        self._status = status


class BasePlugin(IPlugin):
    """插件基类"""
    
    def __init__(self, plugin_id: str, plugin_type: PluginType, 
                 version: str = "1.0.0", description: str = ""):
        """初始化插件
        
        Args:
            plugin_id: 插件ID
            plugin_type: 插件类型
            version: 插件版本
            description: 插件描述
        """
        self._plugin_id = plugin_id
        self._plugin_type = plugin_type
        self._version = version
        self._description = description
        self._status = PluginStatus.INACTIVE
        self._config: Dict[str, Any] = {}
        self._logger = get_logger(f"plugin.{plugin_id}")

    @property
    def plugin_id(self) -> str:
        """插件ID"""
        return self._plugin_id

    @property
    def plugin_type(self) -> PluginType:
        """插件类型"""
        return self._plugin_type

    @property
    def version(self) -> str:
        """插件版本"""
        return self._version

    @property
    def description(self) -> str:
        """插件描述"""
        return self._description

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            self._config = config or {}
            self._logger.info(f"插件 {self._plugin_id} 初始化成功")
            self.set_status(PluginStatus.ACTIVE)
            return True
        except Exception as e:
            self._logger.error(f"插件 {self._plugin_id} 初始化失败: {e}")
            self.set_status(PluginStatus.ERROR)
            return False

    def cleanup(self) -> None:
        """清理插件资源"""
        try:
            self._logger.info(f"插件 {self._plugin_id} 清理完成")
            self.set_status(PluginStatus.INACTIVE)
        except Exception as e:
            self._logger.error(f"插件 {self._plugin_id} 清理失败: {e}")

    def _create_execution_result(self, success: bool, error: Optional[str] = None,
                            data: Optional[Dict[str, Any]] = None,
                            execution_time: float = 0.0) -> PluginExecutionResult:
        """创建执行结果
        
        Args:
            success: 是否成功
            error: 错误信息
            data: 结果数据
            execution_time: 执行时间
            
        Returns:
            PluginExecutionResult: 执行结果
        """
        return PluginExecutionResult(
            plugin_id=self._plugin_id,
            status="success" if success else "error",
            success=success,
            error=error,
            execution_time=execution_time,
            data=data or {}
        )