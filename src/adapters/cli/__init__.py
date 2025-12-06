"""CLI适配器模块

提供命令行界面适配器功能。
"""

from .env_check_command import EnvironmentCheckCommand
from .architecture_command import ArchitectureCommand
from .environment import EnvironmentChecker, IEnvironmentChecker
from .architecture_check import ArchitectureChecker
from .commands import cli
from .error_handling import (
    CLIErrorHandler,
    handle_cli_error,
    handle_cli_warning,
    handle_cli_success,
    handle_cli_info
)
from .help import HelpManager
from .main import main
from .run_command import RunCommand
from .dependency_analyzer_tool import (
    StaticDependencyAnalyzer,
    DependencyAnalysisResult,
    CircularDependency
)
from .dependency_analysis_command import DependencyAnalysisCommand

__all__ = [
    "EnvironmentCheckCommand",
    "ArchitectureCommand",
    "EnvironmentChecker",
    "IEnvironmentChecker",
    "ArchitectureChecker",
    "cli",
    "CLIErrorHandler",
    "handle_cli_error",
    "handle_cli_warning",
    "handle_cli_success",
    "handle_cli_info",
    "HelpManager",
    "main",
    "RunCommand",
    "StaticDependencyAnalyzer",
    "DependencyAnalysisResult",
    "CircularDependency",
    "DependencyAnalysisCommand",
]