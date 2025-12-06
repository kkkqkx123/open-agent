"""
统一错误处理框架

提供统一的错误处理、分类、严重度评估和恢复策略。
"""

from typing import Optional, Dict, Any

from .error_handling_registry import (
    ErrorCategory,
    ErrorSeverity,
    IErrorHandler,
    ErrorHandlingRegistry,
    BaseErrorHandler,
    register_error_handler,
    handle_error,
    operation_with_retry,
    operation_with_fallback,
    safe_execution
)

# 导入各模块的错误处理器
try:
    from .impl.tools import register_tool_error_handler
except (ImportError, ModuleNotFoundError):
    # 如果工具模块不存在，创建一个空的注册函数
    def register_tool_error_handler():
        pass

try:
    from .impl.prompts import register_prompt_error_handler
except (ImportError, ModuleNotFoundError):
    # 如果提示词模块不存在，创建一个空的注册函数
    def register_prompt_error_handler():
        pass

try:
    from .impl.workflow import register_workflow_error_handler
except (ImportError, ModuleNotFoundError):
    # 如果工作流模块不存在，创建一个空的注册函数
    def register_workflow_error_handler():
        pass

# 导入核心模块的错误处理器
try:
    from .impl.state import register_state_error_handler
except (ImportError, ModuleNotFoundError):
    def register_state_error_handler():
        pass

try:
    from .impl.config import register_config_error_handler
except (ImportError, ModuleNotFoundError):
    def register_config_error_handler():
        pass

try:
    from .impl.history import register_history_error_handler
except (ImportError, ModuleNotFoundError):
    def register_history_error_handler():
        pass

try:
    from .impl.storage_adapter import register_storage_error_handler
except (ImportError, ModuleNotFoundError):
    def register_storage_error_handler():
        pass

try:
    from .impl.threads import register_thread_error_handler
except (ImportError, ModuleNotFoundError):
    def register_thread_error_handler():
        pass

try:
    from .impl.sessions import register_session_error_handler
except (ImportError, ModuleNotFoundError):
    def register_session_error_handler():
        pass


def initialize_error_handling():
    """初始化统一错误处理框架
    
    注册所有模块的错误处理器到全局注册表。
    """
    try:
        # 注册工具错误处理器
        register_tool_error_handler()
        
        # 注册提示词错误处理器
        register_prompt_error_handler()
        
        # 注册工作流错误处理器
        register_workflow_error_handler()
        
        # 注册核心模块错误处理器
        register_state_error_handler()
        register_config_error_handler()
        register_history_error_handler()
        register_storage_error_handler()
        register_thread_error_handler()
        register_session_error_handler()
        
        print("统一错误处理框架初始化完成")
        
    except Exception as e:
        print(f"错误处理框架初始化失败: {e}")
        raise


def get_error_handling_registry() -> ErrorHandlingRegistry:
    """获取错误处理注册表实例"""
    return ErrorHandlingRegistry()


# 便捷函数
def handle_module_error(
    error: Exception,
    module_name: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """处理模块错误的便捷函数
    
    Args:
        error: 异常
        module_name: 模块名称
        context: 额外上下文
    """
    import time
    
    error_context = {
        "module_name": module_name,
        "timestamp": time.time()
    }
    
    if context:
        error_context.update(context)
    
    handle_error(error, error_context)


def create_error_context(
    module_name: str,
    operation: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """创建错误上下文的便捷函数
    
    Args:
        module_name: 模块名称
        operation: 操作名称
        **kwargs: 额外上下文
        
    Returns:
        错误上下文字典
    """
    import time
    
    context = {
        "module_name": module_name,
        "timestamp": time.time()
    }
    
    if operation:
        context["operation"] = operation
    
    context.update(kwargs)
    return context


__all__ = [
    # 核心类和枚举
    "ErrorCategory",
    "ErrorSeverity",
    "IErrorHandler",
    "ErrorHandlingRegistry",
    "BaseErrorHandler",
    
    # 主要函数
    "register_error_handler",
    "handle_error",
    "operation_with_retry",
    "operation_with_fallback",
    "safe_execution",
    
    # 初始化和便捷函数
    "initialize_error_handling",
    "get_error_handling_registry",
    "handle_module_error",
    "create_error_context",
    
    # 模块注册函数
    "register_tool_error_handler",
    "register_prompt_error_handler",
    "register_workflow_error_handler",
    "register_state_error_handler",
    "register_config_error_handler",
    "register_history_error_handler",
    "register_storage_error_handler",
    "register_thread_error_handler",
    "register_session_error_handler"
]