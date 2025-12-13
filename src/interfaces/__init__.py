"""接口层统一导出模块

这个模块提供了所有接口的统一导出，确保接口定义的集中化管理。
"""

# 导出验证相关接口
from .common_domain import IValidationResult

# 导出工具相关接口
from .tool import (
    ITool,
    IToolRegistry,
    IToolFormatter,
    IToolExecutor,
    IToolManager,
    IToolFactory,
    ToolCall,
    ToolResult,
    ValidationType,
    IToolValidator,
    IValidationEngine,
    IValidationReporter,
    IReporterFactory,
    ToolError,
    ToolValidationError,
    ValidationReporterError,
)

__all__ = [
    "IValidationResult",
    # 工具接口
    "ITool",
    "IToolRegistry",
    "IToolFormatter",
    "IToolExecutor",
    "IToolManager",
    "IToolFactory",
    "ToolCall",
    "ToolResult",
    # 验证接口
    "ValidationType",
    "IToolValidator",
    "IValidationEngine",
    "IValidationReporter",
    "IReporterFactory",
    # 异常
    "ToolError",
    "ToolValidationError",
    "ValidationReporterError",
]
