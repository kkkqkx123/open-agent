"""Hook基础类

提供Hook的基础实现。
"""

from abc import ABC
from typing import Dict, Any, List, Optional
from src.interfaces.workflow.hooks import IHook, HookPoint, HookContext, HookExecutionResult
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class BaseHook(IHook):
    """Hook基础类
    
    提供Hook的基础实现，子类只需要实现具体的业务逻辑。
    """
    
    def __init__(self, hook_id: str, name: str, description: str, version: str = "1.0.0"):
        """初始化Hook
        
        Args:
            hook_id: Hook的唯一标识符
            name: Hook名称
            description: Hook描述
            version: Hook版本
        """
        self._hook_id = hook_id
        self._name = name
        self._description = description
        self._version = version
        self._config: Dict[str, Any] = {}
        self._initialized = False
    
    @property
    def hook_id(self) -> str:
        """获取Hook ID"""
        return self._hook_id
    
    @property
    def name(self) -> str:
        """获取Hook名称"""
        return self._name
    
    @property
    def description(self) -> str:
        """获取Hook描述"""
        return self._description
    
    @property
    def version(self) -> str:
        """获取Hook版本"""
        return self._version
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点
        
        Returns:
            List[HookPoint]: 支持的Hook执行点列表
        """
        # 默认支持所有Hook点，子类可以重写
        return [
            HookPoint.BEFORE_EXECUTE,
            HookPoint.AFTER_EXECUTE,
            HookPoint.ON_ERROR,
            HookPoint.BEFORE_COMPILE,
            HookPoint.AFTER_COMPILE
        ]
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化Hook
        
        Args:
            config: Hook配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 验证配置
            errors = self.validate_config(config)
            if errors:
                logger.error(f"Hook {self.name} 配置验证失败: {errors}")
                return False
            
            self._config = config.copy()
            self._initialized = True
            
            logger.debug(f"Hook {self.name} 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Hook {self.name} 初始化失败: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理Hook资源
        
        Returns:
            bool: 清理是否成功
        """
        try:
            self._config.clear()
            self._initialized = False
            
            logger.debug(f"Hook {self.name} 清理完成")
            return True
            
        except Exception as e:
            logger.error(f"Hook {self.name} 清理失败: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """检查Hook是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized
    
    def get_config(self) -> Dict[str, Any]:
        """获取Hook配置
        
        Returns:
            Dict[str, Any]: Hook配置的副本
        """
        return self._config.copy()
    
    def _log_execution(self, hook_point: HookPoint, success: bool = True, error: Optional[Exception] = None) -> None:
        """记录Hook执行日志
        
        Args:
            hook_point: Hook点
            success: 是否成功
            error: 错误信息
        """
        if success:
            logger.debug(f"Hook {self.name} 在 {hook_point.value} 点执行成功")
        else:
            logger.error(f"Hook {self.name} 在 {hook_point.value} 点执行失败: {error}")


class ConfigurableHook(BaseHook):
    """可配置的Hook基础类
    
    提供配置验证和默认值处理功能。
    """
    
    def __init__(self, hook_id: str, name: str, description: str, version: str = "1.0.0"):
        """初始化可配置Hook
        
        Args:
            hook_id: Hook的唯一标识符
            name: Hook名称
            description: Hook描述
            version: Hook版本
        """
        super().__init__(hook_id, name, description, version)
        self._default_config: Dict[str, Any] = {}
    
    def set_default_config(self, config: Dict[str, Any]) -> None:
        """设置默认配置
        
        Args:
            config: 默认配置
        """
        self._default_config = config.copy()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        if key in self._config:
            return self._config[key]
        elif key in self._default_config:
            return self._default_config[key]
        else:
            return default
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置
        
        Args:
            config: Hook配置
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = super().validate_config(config)
        
        # 子类可以重写此方法来添加特定的验证逻辑
        return errors