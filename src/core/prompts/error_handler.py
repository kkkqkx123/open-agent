"""
提示词错误处理器

提供分层错误处理和恢复策略，集成到统一错误处理框架中。
"""

from src.services.logger.injection import get_logger
import time
import os
from typing import Type, Dict, Callable, Optional, Any, List
from enum import Enum

from ..common.exceptions import PromptError, PromptLoadError, PromptInjectionError, PromptValidationError, PromptCacheError, PromptNotFoundError
from ..common.error_management import (
    BaseErrorHandler, ErrorCategory, ErrorSeverity,
    ErrorHandlingRegistry, operation_with_retry, operation_with_fallback
)

logger = get_logger(__name__)


class PromptErrorType(Enum):
    """提示词错误类型"""
    LOAD = "load"                     # 加载错误
    INJECTION = "injection"           # 注入错误
    VALIDATION = "validation"         # 验证错误
    CACHE = "cache"                   # 缓存错误
    NOT_FOUND = "not_found"           # 未找到错误
    CONFIGURATION = "configuration"   # 配置错误
    REFERENCE = "reference"           # 引用错误
    CIRCULAR_REFERENCE = "circular_reference"  # 循环引用错误
    PERMISSION = "permission"         # 权限错误
    UNKNOWN = "unknown"               # 未知错误


class PromptErrorHandler(BaseErrorHandler):
    """增强的提示词错误处理器"""
    
    def __init__(self):
        super().__init__(ErrorCategory.PROMPT, ErrorSeverity.MEDIUM)
        self._retry_strategies: Dict[PromptErrorType, Callable] = {}
        self._fallback_strategies: Dict[PromptErrorType, Callable] = {}
        self._recovery_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # 注册默认策略
        self._register_default_strategies()
        
        # 注册到全局注册表
        self._register_to_global_registry()
    
    def _register_to_global_registry(self):
        """注册到全局错误处理注册表"""
        registry = ErrorHandlingRegistry()
        registry.register_handler(PromptError, self)
        registry.register_handler(PromptLoadError, self)
        registry.register_handler(PromptInjectionError, self)
        registry.register_handler(PromptValidationError, self)
        registry.register_handler(PromptCacheError, self)
        registry.register_handler(PromptNotFoundError, self)
    
    def _register_default_strategies(self):
        """注册默认的错误处理策略"""
        # 注册重试策略
        self._retry_strategies[PromptErrorType.LOAD] = self._retry_load
        self._retry_strategies[PromptErrorType.CACHE] = self._retry_cache
        self._retry_strategies[PromptErrorType.REFERENCE] = self._retry_reference
        
        # 注册降级策略
        self._fallback_strategies[PromptErrorType.LOAD] = self._fallback_load
        self._fallback_strategies[PromptErrorType.INJECTION] = self._fallback_injection
        self._fallback_strategies[PromptErrorType.VALIDATION] = self._fallback_validation
        self._fallback_strategies[PromptErrorType.NOT_FOUND] = self._fallback_not_found
    
    
    def can_handle(self, error: Exception) -> bool:
        """判断是否可以处理该错误"""
        return isinstance(error, PromptError)
    
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理提示词错误"""
        if not isinstance(error, PromptError):
            logger.warning(f"非提示词错误，无法处理: {type(error).__name__}")
            return
        
        context = context or {}
        error_type = self._classify_error(error, context)
        
        logger.error(
            f"提示词错误处理: {error_type.value}",
            extra={
                "error_message": str(error),
                "error_type": error_type.value,
                "context": context,
                "error_code": getattr(error, "error_code", None),
                "details": getattr(error, "details", {})
            }
        )
        
        # 尝试恢复
        recovery_result = self._attempt_recovery(error, error_type, context)
        if recovery_result:
            logger.info(f"提示词错误已恢复: {error_type.value}")
        else:
            logger.warning(f"提示词错误无法恢复: {error_type.value}")
    
    def _classify_error(self, error: PromptError, context: Dict[str, Any]) -> PromptErrorType:
        """分类提示词错误"""
        # 根据异常类型分类
        if isinstance(error, PromptLoadError):
            return PromptErrorType.LOAD
        elif isinstance(error, PromptInjectionError):
            return PromptErrorType.INJECTION
        elif isinstance(error, PromptValidationError):
            return PromptErrorType.VALIDATION
        elif isinstance(error, PromptCacheError):
            return PromptErrorType.CACHE
        elif isinstance(error, PromptNotFoundError):
            return PromptErrorType.NOT_FOUND
        
        # 根据错误消息分类
        error_message = str(error).lower()
        
        if "circular" in error_message or "循环" in error_message:
            return PromptErrorType.CIRCULAR_REFERENCE
        elif "reference" in error_message or "引用" in error_message:
            return PromptErrorType.REFERENCE
        elif "permission" in error_message or "权限" in error_message:
            return PromptErrorType.PERMISSION
        elif "config" in error_message or "配置" in error_message:
            return PromptErrorType.CONFIGURATION
        else:
            return PromptErrorType.UNKNOWN
    
    def _attempt_recovery(
        self,
        error: PromptError,
        error_type: PromptErrorType,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """尝试错误恢复"""
        # 首先尝试重试策略
        if error_type in self._retry_strategies:
            try:
                return self._retry_strategies[error_type](error, context)
            except Exception as e:
                logger.warning(f"重试策略失败: {e}")
        
        # 然后尝试降级策略
        if error_type in self._fallback_strategies:
            try:
                return self._fallback_strategies[error_type](error, context)
            except Exception as e:
                logger.warning(f"降级策略失败: {e}")
        
        return None
    
    
    def _retry_load(self, error: PromptLoadError, context: Dict[str, Any]) -> Optional[Any]:
        """加载错误重试策略"""
        prompt_path = getattr(error, 'prompt_path', None) or context.get('prompt_path')
        
        if prompt_path:
            logger.info(f"提示词加载重试: {prompt_path}")
            
            # 检查文件是否存在
            if os.path.exists(prompt_path):
                return {
                    "action": "retry",
                    "strategy": "file_exists",
                    "prompt_path": prompt_path,
                    "reason": "load_retry"
                }
            else:
                # 尝试查找备用路径
                alternative_paths = self._find_alternative_paths(prompt_path)
                if alternative_paths:
                    return {
                        "action": "retry",
                        "strategy": "alternative_path",
                        "prompt_path": alternative_paths[0],
                        "original_path": prompt_path,
                        "reason": "load_retry_alternative"
                    }
        
        return None
    
    def _retry_cache(self, error: PromptCacheError, context: Dict[str, Any]) -> Optional[Any]:
        """缓存错误重试策略"""
        cache_key = getattr(error, 'cache_key', None) or context.get('cache_key')
        
        logger.info(f"提示词缓存重试: {cache_key}")
        
        return {
            "action": "retry",
            "strategy": "cache_bypass",
            "cache_key": cache_key,
            "reason": "cache_retry"
        }
    
    def _retry_reference(self, error: PromptError, context: Dict[str, Any]) -> Optional[Any]:
        """引用错误重试策略"""
        logger.info("提示词引用重试: 重新解析引用")
        
        return {
            "action": "retry",
            "strategy": "reparse_references",
            "reason": "reference_retry"
        }
    
    def _fallback_load(self, error: PromptLoadError, context: Dict[str, Any]) -> Optional[Any]:
        """加载错误降级策略"""
        prompt_name = context.get('prompt_name', 'unknown')
        
        logger.warning(f"提示词加载降级: {prompt_name}")
        
        # 返回默认提示词内容
        default_content = self._get_default_prompt_content(prompt_name)
        
        return {
            "action": "fallback",
            "strategy": "default_content",
            "content": default_content,
            "original_error": str(error),
            "reason": "load_fallback"
        }
    
    def _fallback_injection(self, error: PromptInjectionError, context: Dict[str, Any]) -> Optional[Any]:
        """注入错误降级策略"""
        logger.warning("提示词注入降级: 跳过注入")
        
        return {
            "action": "fallback",
            "strategy": "skip_injection",
            "reason": "injection_fallback"
        }
    
    def _fallback_validation(self, error: PromptValidationError, context: Dict[str, Any]) -> Optional[Any]:
        """验证错误降级策略"""
        logger.warning("提示词验证降级: 跳过验证")
        
        return {
            "action": "fallback",
            "strategy": "skip_validation",
            "validation_errors": getattr(error, 'validation_errors', []),
            "reason": "validation_fallback"
        }
    
    def _fallback_not_found(self, error: PromptNotFoundError, context: Dict[str, Any]) -> Optional[Any]:
        """未找到错误降级策略"""
        prompt_name = context.get('prompt_name', 'unknown')
        
        logger.warning(f"提示词未找到降级: {prompt_name}")
        
        # 返回通用提示词
        generic_content = self._get_generic_prompt_content()
        
        return {
            "action": "fallback",
            "strategy": "generic_content",
            "content": generic_content,
            "prompt_name": prompt_name,
            "reason": "not_found_fallback"
        }
    
    def _find_alternative_paths(self, original_path: str) -> List[str]:
        """查找备用路径"""
        alternatives = []
        
        # 尝试不同的文件扩展名
        base_path = os.path.splitext(original_path)[0]
        for ext in ['.md', '.txt', '.json']:
            alternative = base_path + ext
            if os.path.exists(alternative) and alternative != original_path:
                alternatives.append(alternative)
        
        # 尝试不同的目录
        dirname, basename = os.path.split(original_path)
        if dirname:
            parent_dir = os.path.dirname(dirname)
            if parent_dir:
                alternative = os.path.join(parent_dir, basename)
                if os.path.exists(alternative):
                    alternatives.append(alternative)
        
        return alternatives
    
    def _get_default_prompt_content(self, prompt_name: str) -> str:
        """获取默认提示词内容"""
        default_prompts = {
            "system": "你是一个有用的AI助手。",
            "assistant": "请根据用户的需求提供帮助。",
            "coder": "你是一个编程专家，请帮助解决编程问题。",
            "analyst": "你是一个数据分析专家，请帮助分析数据。"
        }
        
        return default_prompts.get(prompt_name, "你是一个AI助手，请根据用户需求提供帮助。")
    
    def _get_generic_prompt_content(self) -> str:
        """获取通用提示词内容"""
        return "你是一个AI助手，请根据用户需求提供帮助。"
    


def create_default_error_handler() -> PromptErrorHandler:
    """创建默认错误处理器"""
    return PromptErrorHandler()


def handle_prompt_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Optional[Exception]:
    """处理提示词错误的便捷函数"""
    if isinstance(error, PromptError):
        # 使用统一错误处理框架
        error_context = create_prompt_error_context()
        if context:
            error_context.update(context)
        
        registry = ErrorHandlingRegistry()
        registry.handle_error(error, error_context)
        
        # 使用统一框架的恢复机制
        handler = create_default_error_handler()
        error_type = handler._classify_error(error, error_context)
        recovery_result = handler._attempt_recovery(error, error_type, error_context)
        if recovery_result:
            return None
        
        return error
    
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
            "error_code": getattr(error, "error_code", "UNKNOWN"),
            "message": getattr(error, "message", str(error)),
            "details": getattr(error, "details", {})
        }
        
        # 添加验证错误信息
        if hasattr(error, 'validation_errors'):
            error_details["validation_errors"] = getattr(error, 'validation_errors', [])
        
        # 添加路径信息
        if hasattr(error, 'prompt_path'):
            error_details["prompt_path"] = getattr(error, 'prompt_path', None)
        
        if level == "error":
            logger.error(f"提示词错误: {error_details}")
        elif level == "warning":
            logger.warning(f"提示词警告: {error_details}")
        else:
            logger.info(f"提示词信息: {error_details}")
    else:
        logger.error(f"非提示词错误: {error}")


def validate_prompt_content(content: str) -> List[str]:
    """验证提示词内容的便捷函数"""
    return PromptValidator.validate_prompt_content(content)


def validate_prompt_config(config: Dict[str, Any]) -> List[str]:
    """验证提示词配置的便捷函数"""
    return PromptValidator.validate_prompt_config(config)


# 注册提示词错误处理器到全局注册表
def register_prompt_error_handler():
    """注册提示词错误处理器到全局注册表"""
    registry = ErrorHandlingRegistry()
    prompt_handler = PromptErrorHandler()
    
    logger.info("提示词错误处理器已注册到全局注册表")


def create_prompt_error_context(
    prompt_name: Optional[str] = None,
    prompt_path: Optional[str] = None,
    cache_key: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """创建提示词错误上下文"""
    context: Dict[str, Any] = {
        "timestamp": time.time()
    }
    
    if prompt_name:
        context["prompt_name"] = prompt_name
    
    if prompt_path:
        context["prompt_path"] = prompt_path
    
    if cache_key:
        context["cache_key"] = cache_key
    
    context.update(kwargs)
    return context


class PromptValidator:
    """提示词验证器"""
    
    @staticmethod
    def validate_prompt_content(content: str) -> List[str]:
        """验证提示词内容"""
        errors = []
        
        if not content:
            errors.append("提示词内容不能为空")
        
        if isinstance(content, str) and len(content) > 100000:
            errors.append("提示词内容过长（最大100000字符）")
        
        return errors
    
    @staticmethod
    def validate_prompt_config(config: Dict[str, Any]) -> List[str]:
        """验证提示词配置"""
        errors = []
        
        if not isinstance(config, dict):
            errors.append("提示词配置必须是字典类型")
            return errors
        
        if "name" in config and not config["name"]:
            errors.append("提示词名称不能为空")
        
        if "content" in config and not config["content"]:
            errors.append("提示词内容不能为空")
        
        return errors