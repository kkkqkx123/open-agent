"""
工具系统接口模块
"""

from .base import (
    ITool,
    IToolRegistry,
    IToolFormatter,
    IToolExecutor,
    IToolManager,
    IToolFactory,
    ToolCall,
    ToolResult,
)

from .config import (
    ToolConfig,
    NativeToolConfig,
    RestToolConfig,
    MCPToolConfig,
)

from .state_manager import (
    IToolStateManager,
    StateEntry,
    StateType,
)

from .validator import (
    ValidationType,
    IToolValidator,
    IValidationEngine,
)

from .reporter import (
    IValidationReporter,
    IReporterFactory,
)

from .exceptions import (
    ToolError,
    ToolRegistrationError,
    ToolExecutionError,
    ToolValidationError,
    ToolNotFoundError,
    ToolConfigurationError,
    ToolTimeoutError,
    ToolPermissionError,
    ToolDependencyError,
    ToolResourceError,
    ValidationReporterError,
)

__all__ = [
    # 基础接口
    "ITool",
    "IToolRegistry",
    "IToolFormatter",
    "IToolExecutor",
    "IToolManager",
    "IToolFactory",
    "ToolCall",
    "ToolResult",
    
    # 配置接口
    "ToolConfig",
    "NativeToolConfig",
    "RestToolConfig",
    "MCPToolConfig",
    
    # 状态管理接口
    "IToolStateManager",
    "StateEntry",
    "StateType",
    
    # 验证接口
    "ValidationType",
    "IToolValidator",
    "IValidationEngine",
    
    # 报告器接口
    "IValidationReporter",
    "IReporterFactory",
    
    # 异常
    "ToolError",
    "ToolRegistrationError",
    "ToolExecutionError",
    "ToolValidationError",
    "ToolNotFoundError",
    "ToolConfigurationError",
    "ToolTimeoutError",
    "ToolPermissionError",
    "ToolDependencyError",
    "ToolResourceError",
    "ValidationReporterError",
]