"""
配置管理器 - 统一的配置管理入口

提供基础的配置管理功能，专注于配置加载和处理。
"""

from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar

import logging
from src.interfaces.config import IConfigLoader, IConfigProcessor, IConfigValidator, IUnifiedConfigManager, IConfigInheritanceHandler
from src.interfaces.common_domain import ValidationResult
from src.interfaces.config import (
    ConfigError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationValidationError as ConfigValidationError
)
from .processor import ConfigProcessorChain
from .validation import BaseConfigValidator

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Any)


class ConfigManager(IUnifiedConfigManager):
    """配置管理器 - 提供基础的配置管理功能"""
    
    def __init__(self, config_loader: IConfigLoader, processor_chain: Optional[ConfigProcessorChain] = None, base_path: Optional[Path] = None, inheritance_handler: Optional[IConfigInheritanceHandler] = None):
        """初始化配置管理器
        
        Args:
            config_loader: 配置加载器（通过依赖注入）
            processor_chain: 配置处理器链（可选）
            base_path: 配置文件基础路径（可选）
            inheritance_handler: 继承处理器（可选）
        """
        self.base_path = base_path or Path("configs")
        
        # 通过依赖注入使用配置加载器
        self.loader = config_loader
        
        # 初始化处理器链（如果未提供则创建默认的）
        if processor_chain is None:
            self.processor_chain = ConfigProcessorChain()
        else:
            self.processor_chain = processor_chain
        
        # 继承处理器（用于工作流配置等）
        self._inheritance_handler = inheritance_handler
        
        # 模块特定验证器注册表
        self._module_validators: Dict[str, IConfigValidator] = {}
        
        # 默认验证器
        self._default_validator = BaseConfigValidator("DefaultValidator")
        
        logger.info("配置管理器初始化完成")
    
    def load_config(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """加载并处理配置
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
            
        Returns:
            配置数据
        """
        try:
            # 加载原始配置
            logger.debug(f"加载配置文件: {config_path}")
            raw_config = self.loader.load(config_path)
            
            # 处理配置（继承、环境变量、引用）
            logger.debug(f"处理配置: {config_path}")
            processed_config = self.processor_chain.process(raw_config, config_path)
            
            # 使用模块特定验证器验证配置
            validator = self._get_validator(module_type)
            logger.debug(f"验证配置: {config_path}")
            validation_result = validator.validate(processed_config)
            
            if not validation_result.is_valid:
                error_msg = f"配置验证失败 {config_path}: " + "; ".join(validation_result.errors)
                logger.error(error_msg)
                raise ConfigValidationError(error_msg)
            
            logger.info(f"配置加载成功: {config_path}")
            return processed_config
            
        except ConfigNotFoundError:
            raise
        except Exception as e:
            logger.error(f"配置加载失败 {config_path}: {e}")
            if isinstance(e, (ConfigError, ConfigValidationError)):
                raise
            raise ConfigError(f"配置加载失败: {e}") from e
    
    def load_config_with_module(self, config_path: str, module_type: str) -> Dict[str, Any]:
        """加载模块特定配置
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型
            
        Returns:
            配置数据
        """
        return self.load_config(config_path, module_type=module_type)
    
    def save_config(self, config: Dict[str, Any], config_path: str) -> None:
        """保存配置文件
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "save_config is not implemented in core layer. Use services layer."
        )
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "get_config is not implemented in core layer. Use services layer."
        )
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "set_config is not implemented in core layer. Use services layer."
        )
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        return self._default_validator.validate(config)
    
    def register_module_validator(self, module_type: str, validator: IConfigValidator) -> None:
        """注册模块特定验证器
        
        Args:
            module_type: 模块类型
            validator: 验证器
        """
        self._module_validators[module_type] = validator
        logger.info(f"已注册模块验证器: {module_type}")
    
    def get_module_config(self, module_type: str) -> Dict[str, Any]:
        """获取模块配置
        
        Args:
            module_type: 模块类型
            
        Returns:
            模块配置
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "get_module_config is not implemented in core layer. Use services layer."
        )
    
    def reload_module_configs(self, module_type: str) -> None:
        """重新加载模块配置
        
        Args:
            module_type: 模块类型
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "reload_module_configs is not implemented in core layer. Use services layer."
        )
    
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            重新加载的配置数据
        """
        # 基础实现，直接重新加载
        return self.load_config(config_path)
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有缓存
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "invalidate_cache is not implemented in core layer. Use services layer."
        )
    
    def _get_validator(self, module_type: Optional[str]) -> IConfigValidator:
        """获取模块特定的验证器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置验证器
        """
        if module_type and module_type in self._module_validators:
            return self._module_validators[module_type]
        
        # 返回默认验证器
        return self._default_validator
