"""
提示词错误处理器

提供分层错误处理和恢复策略
"""

import logging
from typing import Type, Dict, Callable, Optional, Any
from ...core.common.exceptions import PromptError, PromptLoadError, PromptInjectionError, PromptValidationError, PromptCacheError

logger = logging.getLogger(__name__)


class PromptErrorHandler:
    """提示词错误处理器"""
    
    def __init__(self):
        self._error_handlers: Dict[Type[PromptError], Callable] = {}
        self._recovery_strategies: Dict[Type[PromptError], Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        self.register_handler(PromptLoadError, self._handle_load_error)
        self.register_handler(PromptInjectionError, self._handle_injection_error)
        self.register_handler(PromptValidationError, self._handle_validation_error)
        self.register_handler(PromptCacheError, self._handle_cache_error)
        
        # 注册恢复策略
        self.register_recovery_strategy(PromptLoadError, self._recover_load_error)
        self.register_recovery_strategy(PromptCacheError, self._recover_cache_error)
    
    def register_handler(
        self,
        error_type: Type[PromptError],
        handler: Callable
    ):
        """注册错误处理器"""
        self._error_handlers[error_type] = handler
    
    def register_recovery_strategy(
        self,
        error_type: Type[PromptError],
        strategy: Callable
    ):
        """注册恢复策略"""
        self._recovery_strategies[error_type] = strategy
    
    def handle_error(self, error: PromptError) -> Optional[Exception]:
        """处理错误"""
        error_type = type(error)
        handler = self._error_handlers.get(error_type)
        
        if handler:
            try:
                return handler(error)
            except Exception as e:
                logger.error(f"错误处理器失败: {e}")
        
        # 默认处理：记录并返回原错误
        logger.error(f"未处理的提示词错误: {error}")
        return error
    
    def attempt_recovery(self, error: PromptError, context: Dict[str, Any]) -> Optional[Any]:
        """尝试错误恢复"""
        error_type = type(error)
        strategy = self._recovery_strategies.get(error_type)
        
        if strategy:
            try:
                return strategy(error, context)
            except Exception as e:
                logger.error(f"恢复策略失败: {e}")
        
        # 默认恢复：返回None表示无法恢复
        logger.warning(f"没有可用的恢复策略: {error}")
        return None
    
    def _handle_load_error(self, error: PromptLoadError) -> Optional[Exception]:
        """处理加载错误"""
        logger.error(f"提示词加载失败: {error.message}")
        if error.prompt_path:
            logger.error(f"提示词路径: {error.prompt_path}")
        
        # 尝试恢复
        recovery_result = self.attempt_recovery(error, {"prompt_path": error.prompt_path})
        if recovery_result:
            logger.info(f"加载错误已恢复: {recovery_result}")
            return None
        
        return error
    
    def _handle_injection_error(self, error: PromptInjectionError) -> Optional[Exception]:
        """处理注入错误"""
        logger.error(f"提示词注入失败: {error.message}")
        
        # 注入错误通常不应该中断流程，可以尝试使用默认提示词
        logger.warning("尝试使用默认提示词继续")
        return None  # 返回None表示错误已处理，可以继续
    
    def _handle_validation_error(self, error: PromptValidationError) -> Optional[Exception]:
        """处理验证错误"""
        logger.error(f"提示词验证失败: {error.message}")
        for validation_error in error.validation_errors:
            logger.error(f"  - {validation_error}")
        
        # 验证错误通常不应该中断流程，可以跳过验证
        logger.warning("跳过验证继续")
        return None
    
    def _handle_cache_error(self, error: PromptCacheError) -> Optional[Exception]:
        """处理缓存错误"""
        logger.warning(f"提示词缓存错误: {error.message}")
        if error.cache_key:
            logger.warning(f"缓存键: {error.cache_key}")
        
        # 缓存错误通常不应该中断流程
        return None  # 返回None表示错误已处理，可以继续
    
    def _recover_load_error(self, error: PromptLoadError, context: Dict[str, Any]) -> Optional[str]:
        """恢复加载错误"""
        prompt_path = context.get("prompt_path")
        
        # 尝试从备用路径加载
        if prompt_path:
            # 这里可以实现具体的恢复逻辑
            # 例如：尝试不同的文件路径、使用默认内容等
            logger.info(f"尝试恢复加载错误: {prompt_path}")
            
            # 返回默认内容作为恢复结果
            return "# 默认提示词内容\n\n这是默认的提示词内容，用于错误恢复。"
        
        return None
    
    def _recover_cache_error(self, error: PromptCacheError, context: Dict[str, Any]) -> Optional[str]:
        """恢复缓存错误"""
        cache_key = context.get("cache_key") or error.cache_key
        
        # 缓存错误恢复：直接返回None，让系统重新加载
        logger.info(f"缓存错误恢复: {cache_key}")
        return None


def create_default_error_handler() -> PromptErrorHandler:
    """创建默认错误处理器"""
    return PromptErrorHandler()


def handle_prompt_error(error: Exception) -> Optional[Exception]:
    """处理提示词错误的便捷函数"""
    if isinstance(error, PromptError):
        handler = create_default_error_handler()
        return handler.handle_error(error)
    
    # 非提示词错误直接返回
    return error


def should_retry_prompt_error(error: Exception) -> bool:
    """判断提示词错误是否应该重试"""
    if isinstance(error, PromptCacheError):
        return True
    
    if isinstance(error, PromptLoadError):
        return True
    
    return False


def log_prompt_error(error: Exception, level: str = "error") -> None:
    """记录提示词错误"""
    if isinstance(error, PromptError):
        error_details = {
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details
        }
        
        if level == "error":
            logger.error(f"提示词错误: {error_details}")
        elif level == "warning":
            logger.warning(f"提示词警告: {error_details}")
        else:
            logger.info(f"提示词信息: {error_details}")
    else:
        logger.error(f"非提示词错误: {error}")