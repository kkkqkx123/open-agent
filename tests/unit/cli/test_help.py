"""CLI帮助管理器单元测试"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO

from src.presentation.cli.help import HelpManager


class TestHelpManager:
    """帮助管理器测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.help_manager = HelpManager()
    
    def test_init(self) -> None:
        """测试初始化"""
        assert hasattr(self.help_manager, 'console')
    
    def test_show_main_help(self) -> None:
        """测试显示主帮助"""
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_main_help()
            
            # 验证print被调用
            mock_print.assert_called_once()
    
    def test_show_command_help_known_command(self) -> None:
        """测试显示已知命令的帮助"""
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_command_help("session")
            
            # 验证print被调用
            mock_print.assert_called_once()
    
    def test_show_command_help_unknown_command(self) -> None:
        """测试显示未知命令的帮助"""
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_command_help("unknown_command")
            
            # 验证print被调用两次（错误信息和帮助提示）
            assert mock_print.call_count == 2
    
    def test_show_command_help_all_known_commands(self) -> None:
        """测试显示所有已知命令的帮助"""
        known_commands = ["session", "config", "run", "version"]
        
        for command in known_commands:
            with patch('rich.console.Console.print') as mock_print:
                self.help_manager.show_command_help(command)
                
                # 验证print被调用
                mock_print.assert_called_once()
    
    def test_show_error_help_known_error(self) -> None:
        """测试显示已知错误的帮助"""
        known_errors = ["SessionNotFound", "WorkflowNotFound", "EnvironmentError"]
        
        for error_type in known_errors:
            with patch('rich.console.Console.print') as mock_print:
                self.help_manager.show_error_help(error_type)
                
                # 验证print被调用
                mock_print.assert_called_once()
    
    def test_show_error_help_unknown_error(self) -> None:
        """测试显示未知错误的帮助"""
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_error_help("UnknownError")
            
            # 验证print被调用两次（错误信息和帮助提示）
            assert mock_print.call_count == 2
    
    def test_show_quick_start(self) -> None:
        """测试显示快速开始指南"""
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_quick_start()
            
            # 验证print被调用
            mock_print.assert_called_once()
    
    def test_help_texts_content(self) -> None:
        """测试帮助文本内容"""
        # 测试主帮助文本包含关键内容
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_main_help()
            
            # 获取调用参数
            call_args = mock_print.call_args[0][0]
            # 验证是Markdown对象
            from rich.markdown import Markdown
            assert isinstance(call_args, Markdown)
    
    def test_command_help_content(self) -> None:
        """测试命令帮助内容"""
        # 测试session命令帮助
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_command_help("session")
            
            # 获取调用参数
            call_args = mock_print.call_args[0][0]
            # 验证是Markdown对象
            from rich.markdown import Markdown
            assert isinstance(call_args, Markdown)
    
    def test_error_help_content(self) -> None:
        """测试错误帮助内容"""
        # 测试SessionNotFound错误帮助
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_error_help("SessionNotFound")
            
            # 获取调用参数
            call_args = mock_print.call_args[0][0]
            # 验证是Markdown对象
            from rich.markdown import Markdown
            assert isinstance(call_args, Markdown)
    
    def test_quick_start_content(self) -> None:
        """测试快速开始指南内容"""
        with patch('rich.console.Console.print') as mock_print:
            self.help_manager.show_quick_start()
            
            # 获取调用参数
            call_args = mock_print.call_args[0][0]
            # 验证是Markdown对象
            from rich.markdown import Markdown
            assert isinstance(call_args, Markdown)


class TestHelpManagerIntegration:
    """帮助管理器集成测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.help_manager = HelpManager()
    
    def test_all_methods_execute_without_error(self) -> None:
        """测试所有方法都能正常执行而不抛出异常"""
        methods = [
            ('show_main_help', []),
            ('show_command_help', ['session']),
            ('show_command_help', ['unknown']),
            ('show_error_help', ['SessionNotFound']),
            ('show_error_help', ['UnknownError']),
            ('show_quick_start', []),
        ]
        
        for method_name, args in methods:
            try:
                method = getattr(self.help_manager, method_name)
                method(*args)
            except Exception as e:
                pytest.fail(f"{method_name}{args} 抛出了异常: {e}")
    
    def test_help_text_structure(self) -> None:
        """测试帮助文本结构"""
        # 验证所有帮助文本都包含必要的结构元素
        from rich.markdown import Markdown
        
        with patch('rich.console.Console.print') as mock_print:
            # 测试主帮助
            self.help_manager.show_main_help()
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Markdown)
            
            # 测试命令帮助
            self.help_manager.show_command_help("session")
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Markdown)
            
            # 测试错误帮助
            self.help_manager.show_error_help("SessionNotFound")
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Markdown)
            
            # 测试快速开始
            self.help_manager.show_quick_start()
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Markdown)


if __name__ == "__main__":
    pytest.main([__file__])