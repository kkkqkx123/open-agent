"""CLI错误处理模块"""

import sys
import traceback
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .help import HelpManager


class CLIErrorHandler:
    """CLI错误处理器"""
    
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.console = Console()
        self.help_manager = HelpManager()
        
        # 错误类型映射
        self.error_mapping = {
            "SessionNotRegisteredError": "SessionNotFound",
            "ServiceNotRegisteredError": "EnvironmentError",
            "ConfigurationError": "EnvironmentError",
            "EnvironmentCheckError": "EnvironmentError",
            "ServiceCreationError": "EnvironmentError",
            "FileNotFoundError": "WorkflowNotFound",
            "ValidationError": "ConfigurationError",
        }
    
    def handle_error(self, error: Exception, context: Optional[str] = None) -> None:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 显示错误面板
        self._display_error_panel(error_type, error_message, context)
        
        # 根据错误类型提供帮助
        mapped_error_type = self.error_mapping.get(error_type, error_type)
        self.help_manager.show_error_help(mapped_error_type)
        
        # 如果是详细模式，显示堆栈跟踪
        if self.verbose:
            self._display_stack_trace(error)
        
        # 根据错误类型决定退出码
        exit_code = self._get_exit_code(error_type)
        sys.exit(exit_code)
    
    def _display_error_panel(self, error_type: str, error_message: str, context: Optional[str]) -> None:
        """显示错误面板"""
        # 构建错误文本
        error_text = Text()
        error_text.append("错误类型: ", style="bold")
        error_text.append(error_type, style="red")
        error_text.append("\n")
        
        if context:
            error_text.append("上下文: ", style="bold")
            error_text.append(context, style="yellow")
            error_text.append("\n")
        
        error_text.append("错误信息: ", style="bold")
        error_text.append(error_message, style="red")
        
        # 创建面板
        panel = Panel(
            error_text,
            title="[bold red]错误[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def _display_stack_trace(self, error: Exception) -> None:
        """显示堆栈跟踪"""
        stack_trace = traceback.format_exc()
        
        panel = Panel(
            stack_trace,
            title="[bold yellow]堆栈跟踪[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def _get_exit_code(self, error_type: str) -> int:
        """获取错误对应的退出码"""
        # 退出码映射
        exit_codes = {
            "SessionNotRegisteredError": 2,
            "ServiceNotRegisteredError": 3,
            "ConfigurationError": 4,
            "EnvironmentCheckError": 5,
            "ServiceCreationError": 6,
            "FileNotFoundError": 7,
            "ValidationError": 8,
            "ClickException": 9,
            "KeyboardInterrupt": 130,  # 标准的SIGINT退出码
        }
        
        return exit_codes.get(error_type, 1)
    
    def handle_warning(self, message: str, context: Optional[str] = None) -> None:
        """处理警告信息
        
        Args:
            message: 警告消息
            context: 警告上下文
        """
        # 构建警告文本
        warning_text = Text()
        warning_text.append("警告: ", style="bold yellow")
        warning_text.append(message, style="yellow")
        
        if context:
            warning_text.append("\n上下文: ", style="bold")
            warning_text.append(context, style="dim")
        
        # 创建面板
        panel = Panel(
            warning_text,
            title="[bold yellow]警告[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def handle_success(self, message: str, context: Optional[str] = None) -> None:
        """处理成功信息
        
        Args:
            message: 成功消息
            context: 成功上下文
        """
        # 构建成功文本
        success_text = Text()
        success_text.append("成功: ", style="bold green")
        success_text.append(message, style="green")
        
        if context:
            success_text.append("\n详情: ", style="bold")
            success_text.append(context, style="dim")
        
        # 创建面板
        panel = Panel(
            success_text,
            title="[bold green]成功[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def handle_info(self, message: str, context: Optional[str] = None) -> None:
        """处理信息
        
        Args:
            message: 信息消息
            context: 信息上下文
        """
        # 构建信息文本
        info_text = Text()
        info_text.append("信息: ", style="bold blue")
        info_text.append(message, style="blue")
        
        if context:
            info_text.append("\n详情: ", style="bold")
            info_text.append(context, style="dim")
        
        # 创建面板
        panel = Panel(
            info_text,
            title="[bold blue]信息[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()


def handle_cli_error(error: Exception, verbose: bool = False, context: Optional[str] = None) -> None:
    """处理CLI错误的便捷函数
    
    Args:
        error: 异常对象
        verbose: 是否显示详细信息
        context: 错误上下文
    """
    handler = CLIErrorHandler(verbose=verbose)
    handler.handle_error(error, context)


def handle_cli_warning(message: str, context: Optional[str] = None) -> None:
    """处理CLI警告的便捷函数
    
    Args:
        message: 警告消息
        context: 警告上下文
    """
    handler = CLIErrorHandler()
    handler.handle_warning(message, context)


def handle_cli_success(message: str, context: Optional[str] = None) -> None:
    """处理CLI成功信息的便捷函数
    
    Args:
        message: 成功消息
        context: 成功上下文
    """
    handler = CLIErrorHandler()
    handler.handle_success(message, context)


def handle_cli_info(message: str, context: Optional[str] = None) -> None:
    """处理CLI信息的便捷函数
    
    Args:
        message: 信息消息
        context: 信息上下文
    """
    handler = CLIErrorHandler()
    handler.handle_info(message, context)
