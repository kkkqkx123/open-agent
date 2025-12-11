"""配置模块错误处理器

为配置系统提供专门的错误处理和分类策略。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, Callable

from src.infrastructure.error_management import (
    BaseErrorHandler, ErrorCategory, ErrorSeverity,
    register_error_handler
)
from src.interfaces.config import (
    ConfigError, ConfigurationValidationError as ConfigValidationError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationInheritanceError as ConfigInheritanceError,
    ConfigurationParseError as ConfigFormatError,
    ConfigurationEnvironmentError as ConfigEnvironmentError
)

logger = get_logger(__name__)


class ConfigErrorHandler(BaseErrorHandler):
    """配置模块错误处理器
    
    专注于配置错误的分类处理和日志记录，不包含恢复策略。
    恢复策略由 error_recovery.py 模块提供。
    """
    
    def __init__(self) -> None:
        """初始化配置错误处理器"""
        super().__init__(ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH)
        self._handling_strategies: Dict[type, Callable] = {
            ConfigValidationError: self._handle_validation_error,
            ConfigNotFoundError: self._handle_not_found_error,
            ConfigInheritanceError: self._handle_inheritance_error,
            ConfigFormatError: self._handle_format_error,
            ConfigEnvironmentError: self._handle_environment_error,
        }
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误"""
        return isinstance(error, (ConfigError, ConfigValidationError, ConfigNotFoundError,
                                ConfigInheritanceError, ConfigFormatError, ConfigEnvironmentError))
    
    def handle(self, error: Exception, context: Optional[Dict] = None) -> None:
        """处理配置错误"""
        try:
            # 记录错误日志
            self._log_error(error, context)
            
            # 根据错误类型选择处理策略
            error_type = type(error)
            if error_type in self._handling_strategies:
                strategy = self._handling_strategies[error_type]
                strategy(error, context)
            else:
                # 通用配置错误处理
                self._handle_generic_config_error(error, context)
                
        except Exception as handler_error:
            # 错误处理器本身出错，记录但不抛出异常
            logger.error(f"配置错误处理器内部错误: {handler_error}")
    
    def _handle_validation_error(self, error: ConfigValidationError, context: Optional[Dict] = None) -> None:
         """处理配置验证错误"""
         logger.warning(f"配置验证失败: {error}")
         
         # 尝试提供修复建议
         if hasattr(error, 'config_key') and error.config_key:
             logger.info(f"建议检查配置字段: {error.config_key}")
         
         if context and 'config_path' in context:
             logger.info(f"建议检查配置文件: {context['config_path']}")
    
    def _handle_not_found_error(self, error: ConfigNotFoundError, context: Optional[Dict] = None) -> None:
        """处理配置未找到错误"""
        logger.error(f"配置文件未找到: {error}")
        
        # 尝试查找替代配置文件
        if context and 'config_path' in context:
            config_path = context['config_path']
            alternative_paths = self._find_alternative_configs(config_path)
            
            if alternative_paths:
                logger.info(f"找到可能的替代配置文件: {alternative_paths}")
            else:
                logger.warning("未找到替代配置文件")
    
    def _handle_inheritance_error(self, error: ConfigInheritanceError, context: Optional[Dict] = None) -> None:
         """处理配置继承错误"""
         logger.error(f"配置继承失败: {error}")
         
         # 检查父配置路径
         if hasattr(error, 'parent_config') and error.parent_config:
             logger.info(f"建议检查父配置文件: {error.parent_config}")
    
    def _handle_format_error(self, error: ConfigFormatError, context: Optional[Dict] = None) -> None:
        """处理配置格式错误"""
        logger.error(f"配置格式错误: {error}")
        
        # 提供格式修复建议
        if context and 'config_path' in context:
            logger.info(f"建议检查配置文件格式: {context['config_path']}")
            logger.info("常见格式问题: YAML缩进、JSON语法、编码问题")
    
    def _handle_environment_error(self, error: ConfigEnvironmentError, context: Optional[Dict] = None) -> None:
         """处理环境变量错误"""
         logger.error(f"环境变量解析失败: {error}")
         
         # 检查环境变量
         if hasattr(error, 'env_var_name') and error.env_var_name:
             logger.info(f"建议设置环境变量: {error.env_var_name}")
             logger.info(f"示例: export {error.env_var_name}=your_value")
    
    def _handle_generic_config_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """处理通用配置错误"""
        logger.error(f"配置错误: {error}")
        
        # 提供通用建议
        if context and 'config_path' in context:
            logger.info(f"建议检查配置文件: {context['config_path']}")
        
        logger.info("建议检查配置文档或联系管理员")
    
    def _find_alternative_configs(self, config_path: str) -> list:
        """查找替代配置文件"""
        import os
        from pathlib import Path
        
        alternatives = []
        config_dir = os.path.dirname(config_path)
        config_name = os.path.basename(config_path)
        name_without_ext = os.path.splitext(config_name)[0]
        
        # 查找同目录下的其他配置文件
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith(('.yaml', '.yml', '.json')) and file != config_name:
                    if name_without_ext in file or file.startswith('default'):
                        alternatives.append(os.path.join(config_dir, file))
        
        return alternatives
    
    def _log_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """记录配置错误日志"""
        error_info = {
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # 添加配置特定的错误信息
        if isinstance(error, ConfigError):
            if hasattr(error, 'config_path') and error.config_path:
                error_info["config_path"] = error.config_path
            if hasattr(error, 'details') and error.details:
                error_info["error_details"] = error.details
        
        # 根据严重度选择日志级别
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"配置错误: {error_info}")
        elif self.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"配置警告: {error_info}")
        else:
            logger.info(f"配置信息: {error_info}")


# 注册配置错误处理器
def register_config_error_handler() -> None:
    """注册配置错误处理器到全局注册表"""
    config_handler = ConfigErrorHandler()
    
    # 注册各种配置异常的处理器
    register_error_handler(ConfigError, config_handler)
    register_error_handler(ConfigValidationError, config_handler)
    register_error_handler(ConfigNotFoundError, config_handler)
    register_error_handler(ConfigInheritanceError, config_handler)
    register_error_handler(ConfigFormatError, config_handler)
    register_error_handler(ConfigEnvironmentError, config_handler)
    
    logger.info("配置错误处理器已注册到全局注册表")


# 自动注册
register_config_error_handler()