"""CLI错误处理器单元测试"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from src.presentation.cli.error_handler import (
    CLIErrorHandler,
    handle_cli_error,
    handle_cli_warning,
    handle_cli_success,
    handle_cli_info
)


class TestCLIErrorHandler:
    """CLI错误处理器测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.error_handler = CLIErrorHandler(verbose=False)
    
    def test_init(self) -> None:
        """测试初始化"""
        assert self.error_handler.verbose is False
        assert hasattr(self.error_handler, 'console')
        assert hasattr(self.error_handler, 'help_manager')
        assert isinstance(self.error_handler.error_mapping, dict)
    
    def test_init_verbose(self) -> None:
        """测试详细模式初始化"""
        handler = CLIErrorHandler(verbose=True)
        assert handler.verbose is True
    
    def test_error_mapping(self) -> None:
        """测试错误类型映射"""
        expected_mapping = {
            "SessionNotRegisteredError": "SessionNotFound",
            "ServiceNotRegisteredError": "EnvironmentError",
            "ConfigurationError": "EnvironmentError",
            "EnvironmentCheckError": "EnvironmentError",
            "ServiceCreationError": "EnvironmentError",
            "FileNotFoundError": "WorkflowNotFound",
            "ValidationError": "ConfigurationError",
        }
        assert self.error_handler.error_mapping == expected_mapping
    
    @patch('sys.exit')
    def test_handle_error_with_known_error(self, mock_exit: Mock) -> None:
        """测试处理已知错误"""
        error = FileNotFoundError("文件未找到")
        context = "测试上下文"
        
        with patch.object(self.error_handler, '_display_error_panel') as mock_panel:
            with patch.object(self.error_handler.help_manager, 'show_error_help') as mock_help:
                self.error_handler.handle_error(error, context)
                
                mock_panel.assert_called_once_with("FileNotFoundError", "文件未找到", context)
                mock_help.assert_called_once_with("WorkflowNotFound")
                mock_exit.assert_called_once_with(7)
    
    @patch('sys.exit')
    def test_handle_error_with_unknown_error(self, mock_exit: Mock) -> None:
        """测试处理未知错误"""
        error = RuntimeError("未知错误")
        
        with patch.object(self.error_handler, '_display_error_panel') as mock_panel:
            with patch.object(self.error_handler.help_manager, 'show_error_help') as mock_help:
                self.error_handler.handle_error(error)
                
                mock_panel.assert_called_once_with("RuntimeError", "未知错误", None)
                mock_help.assert_called_once_with("RuntimeError")
                mock_exit.assert_called_once_with(1)
    
    @patch('sys.exit')
    def test_handle_error_verbose_mode(self, mock_exit: Mock) -> None:
        """测试详细模式下的错误处理"""
        handler = CLIErrorHandler(verbose=True)
        error = ValueError("测试错误")
        
        with patch.object(handler, '_display_error_panel'):
            with patch.object(handler.help_manager, 'show_error_help'):
                with patch.object(handler, '_display_stack_trace') as mock_stack:
                    handler.handle_error(error)
                    
                    mock_stack.assert_called_once_with(error)
    
    def test_display_error_panel(self) -> None:
        """测试显示错误面板"""
        # 使用StringIO捕获控制台输出
        console_output = StringIO()
        
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler._display_error_panel("TestError", "测试错误", "测试上下文")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_display_stack_trace(self) -> None:
        """测试显示堆栈跟踪"""
        error = ValueError("测试错误")
        
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler._display_stack_trace(error)
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_get_exit_code_known_errors(self) -> None:
        """测试获取已知错误的退出码"""
        test_cases = [
            ("SessionNotRegisteredError", 2),
            ("ServiceNotRegisteredError", 3),
            ("ConfigurationError", 4),
            ("EnvironmentCheckError", 5),
            ("ServiceCreationError", 6),
            ("FileNotFoundError", 7),
            ("ValidationError", 8),
            ("ClickException", 9),
            ("KeyboardInterrupt", 130),
        ]
        
        for error_type, expected_code in test_cases:
            exit_code = self.error_handler._get_exit_code(error_type)
            assert exit_code == expected_code
    
    def test_get_exit_code_unknown_error(self) -> None:
        """测试获取未知错误的退出码"""
        exit_code = self.error_handler._get_exit_code("UnknownError")
        assert exit_code == 1
    
    def test_handle_warning(self) -> None:
        """测试处理警告"""
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler.handle_warning("测试警告", "测试上下文")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_handle_warning_without_context(self) -> None:
        """测试处理无上下文的警告"""
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler.handle_warning("测试警告")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_handle_success(self) -> None:
        """测试处理成功信息"""
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler.handle_success("测试成功", "测试上下文")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_handle_success_without_context(self) -> None:
        """测试处理无上下文的成功信息"""
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler.handle_success("测试成功")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_handle_info(self) -> None:
        """测试处理信息"""
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler.handle_info("测试信息", "测试上下文")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2
    
    def test_handle_info_without_context(self) -> None:
        """测试处理无上下文的信息"""
        with patch('rich.console.Console.print') as mock_print:
            self.error_handler.handle_info("测试信息")
            
            # 验证print被调用了两次（面板和空行）
            assert mock_print.call_count == 2


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    @patch('sys.exit')
    def test_handle_cli_error(self, mock_exit: Mock) -> None:
        """测试CLI错误处理便捷函数"""
        error = ValueError("测试错误")
        
        with patch('src.presentation.cli.error_handler.CLIErrorHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            handle_cli_error(error, verbose=True, context="测试上下文")
            
            mock_handler_class.assert_called_once_with(verbose=True)
            mock_handler.handle_error.assert_called_once_with(error, "测试上下文")
    
    def test_handle_cli_warning(self) -> None:
        """测试CLI警告处理便捷函数"""
        with patch('src.presentation.cli.error_handler.CLIErrorHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            handle_cli_warning("测试警告", "测试上下文")
            
            mock_handler_class.assert_called_once_with()
            mock_handler.handle_warning.assert_called_once_with("测试警告", "测试上下文")
    
    def test_handle_cli_success(self) -> None:
        """测试CLI成功处理便捷函数"""
        with patch('src.presentation.cli.error_handler.CLIErrorHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            handle_cli_success("测试成功", "测试上下文")
            
            mock_handler_class.assert_called_once_with()
            mock_handler.handle_success.assert_called_once_with("测试成功", "测试上下文")
    
    def test_handle_cli_info(self) -> None:
        """测试CLI信息处理便捷函数"""
        with patch('src.presentation.cli.error_handler.CLIErrorHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            handle_cli_info("测试信息", "测试上下文")
            
            mock_handler_class.assert_called_once_with()
            mock_handler.handle_info.assert_called_once_with("测试信息", "测试上下文")


if __name__ == "__main__":
    pytest.main([__file__])