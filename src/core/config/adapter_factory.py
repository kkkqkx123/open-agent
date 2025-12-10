"""
适配器工厂 - 负责创建和管理模块特定配置适配器
"""

from src.services.logger.injection import get_logger
from typing import Dict, Type, Any
from .adapters import (
    BaseConfigAdapter,
    LLMConfigAdapter,
    WorkflowConfigAdapter,
    ToolConfigAdapter,
    StateConfigAdapter
)
from .config_manager import ConfigManager
from src.interfaces.config import ConfigError, ConfigurationValidationError as ConfigValidationError
from src.infrastructure.error_management import handle_error

logger = get_logger(__name__)


class AdapterFactory:
    """适配器工厂类"""
    
    def __init__(self, base_manager: ConfigManager):
        """
        初始化适配器工厂
        
        Args:
            base_manager: 基础配置管理器
        """
        self.base_manager = base_manager
        self._adapters: Dict[str, BaseConfigAdapter] = {}
        self._adapter_types: Dict[str, Type[BaseConfigAdapter]] = {
            'llm': LLMConfigAdapter,
            'workflow': WorkflowConfigAdapter,
            'tools': ToolConfigAdapter,
            'state': StateConfigAdapter,
        }
    
    def get_adapter(self, module_type: str) -> BaseConfigAdapter:
        """
        获取指定模块类型的适配器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置适配器实例
            
        Raises:
            ConfigValidationError: 模块类型验证失败
            ConfigError: 适配器创建失败
        """
        adapter_class: Type[BaseConfigAdapter] | None = None
        try:
            # 输入验证
            if not module_type:
                raise ConfigValidationError("模块类型不能为空")
            
            if not isinstance(module_type, str):
                raise ConfigValidationError(
                    f"模块类型必须是字符串，实际类型: {type(module_type).__name__}"
                )
            
            # 检查是否已缓存
            if module_type in self._adapters:
                return self._adapters[module_type]
            
            # 检查模块类型是否支持
            if module_type not in self._adapter_types:
                supported_types = list(self._adapter_types.keys())
                raise ConfigValidationError(
                    f"不支持的模块类型: {module_type}",
                    details={
                        "module_type": module_type,
                        "supported_types": supported_types
                    }
                )
            
            # 创建适配器实例
            adapter_class = self._adapter_types[module_type]
            
            # 验证适配器类
            if not issubclass(adapter_class, BaseConfigAdapter):
                raise ConfigError(
                    f"适配器类 {adapter_class.__name__} 必须继承自 BaseConfigAdapter"
                )
            
            # 创建实例
            adapter = adapter_class(self.base_manager)
            
            # 验证创建的实例
            if not hasattr(adapter, 'get_config'):
                raise ConfigError(
                    f"适配器 {adapter_class.__name__} 缺少必需的 get_config 方法"
                )
            
            # 缓存适配器
            self._adapters[module_type] = adapter
            
            logger.info(f"成功创建 {module_type} 适配器: {adapter_class.__name__}")
            return adapter
            
        except ConfigValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "module_type": module_type,
                "adapter_class": adapter_class.__name__ if adapter_class else None,
                "operation": "get_adapter",
                "factory_class": self.__class__.__name__
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise ConfigError(
                f"获取适配器失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e
    
    def register_adapter_type(self, module_type: str, adapter_class: Type[BaseConfigAdapter]) -> None:
        """
        注册新的适配器类型
        
        Args:
            module_type: 模块类型
            adapter_class: 适配器类
            
        Raises:
            ConfigValidationError: 输入验证失败
            ConfigError: 注册失败
        """
        try:
            # 输入验证
            if not module_type:
                raise ConfigValidationError("模块类型不能为空")
            
            if not isinstance(module_type, str):
                raise ConfigValidationError(
                    f"模块类型必须是字符串，实际类型: {type(module_type).__name__}"
                )
            
            if not adapter_class:
                raise ConfigValidationError("适配器类不能为None")
            
            if not isinstance(adapter_class, type):
                raise ConfigValidationError(
                    f"适配器必须是类类型，实际类型: {type(adapter_class).__name__}"
                )
            
            # 验证适配器类继承关系
            if not issubclass(adapter_class, BaseConfigAdapter):
                raise ConfigValidationError(
                    f"适配器类 {adapter_class.__name__} 必须继承自 BaseConfigAdapter"
                )
            
            # 检查是否已存在
            if module_type in self._adapter_types:
                existing_class = self._adapter_types[module_type]
                logger.warning(
                    f"覆盖已存在的适配器类型 {module_type}: "
                    f"{existing_class.__name__} -> {adapter_class.__name__}"
                )
            
            # 注册适配器类型
            self._adapter_types[module_type] = adapter_class
            
            # 如果已有实例，需要重新创建
            if module_type in self._adapters:
                try:
                    self._adapters[module_type] = adapter_class(self.base_manager)
                    logger.info(f"重新创建 {module_type} 适配器实例")
                except Exception as e:
                    # 如果重新创建失败，移除缓存并记录错误
                    del self._adapters[module_type]
                    raise ConfigError(
                        f"重新创建适配器实例失败: {e}",
                        details={
                            "module_type": module_type,
                            "adapter_class": adapter_class.__name__
                        }
                    ) from e
            
            logger.info(f"成功注册适配器类型: {module_type} -> {adapter_class.__name__}")
            
        except ConfigValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "module_type": module_type,
                "adapter_class": adapter_class.__name__ if adapter_class else None,
                "operation": "register_adapter_type",
                "factory_class": self.__class__.__name__
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise ConfigError(
                f"注册适配器类型失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e
    
    def create_adapter(self, module_type: str) -> BaseConfigAdapter:
        """
        创建新的适配器实例（不缓存）
        
        Args:
            module_type: 模块类型
            
        Returns:
            新的配置适配器实例
            
        Raises:
            ConfigValidationError: 模块类型验证失败
            ConfigError: 适配器创建失败
        """
        adapter_class: Type[BaseConfigAdapter] | None = None
        try:
            # 输入验证
            if not module_type:
                raise ConfigValidationError("模块类型不能为空")
            
            if not isinstance(module_type, str):
                raise ConfigValidationError(
                    f"模块类型必须是字符串，实际类型: {type(module_type).__name__}"
                )
            
            # 检查模块类型是否支持
            if module_type not in self._adapter_types:
                supported_types = list(self._adapter_types.keys())
                raise ConfigValidationError(
                    f"不支持的模块类型: {module_type}",
                    details={
                        "module_type": module_type,
                        "supported_types": supported_types
                    }
                )
            
            # 创建适配器实例
            adapter_class = self._adapter_types[module_type]
            adapter = adapter_class(self.base_manager)
            
            # 验证创建的实例
            if not isinstance(adapter, BaseConfigAdapter):
                raise ConfigError(
                    f"创建的适配器实例类型不正确: {type(adapter).__name__}"
                )
            
            logger.debug(f"成功创建 {module_type} 适配器实例: {adapter_class.__name__}")
            return adapter
            
        except ConfigValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "module_type": module_type,
                "adapter_class": adapter_class.__name__ if adapter_class else None,
                "operation": "create_adapter",
                "factory_class": self.__class__.__name__
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise ConfigError(
                f"创建适配器失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e