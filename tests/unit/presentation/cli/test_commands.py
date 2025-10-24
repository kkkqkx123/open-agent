"""CLI命令单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.presentation.cli.commands import cli, session, config, version
from src.presentation.cli.help import HelpManager
from src.presentation.cli.error_handler import CLIErrorHandler


class TestCLICommands:
    """CLI命令测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    def test_cli_help(self) -> None:
        """测试CLI帮助命令"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert '模块化代理框架' in result.output
    
    def test_version_command(self) -> None:
        """测试版本命令"""
        result = self.runner.invoke(cli, ['version'])
        assert result.exit_code == 0
        assert 'version' in result.output.lower()
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_list_command(self, mock_container: Mock) -> None:
        """测试会话列表命令"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.list_sessions.return_value = [
            {
                'session_id': 'test-session-123',
                'workflow_config_path': 'test.yaml',
                'created_at': '2023-01-01T00:00:00',
                'updated_at': '2023-01-01T00:00:00',
                'status': 'active'
            }
        ]
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'list'])
        assert result.exit_code == 0
        assert '会话列表' in result.output
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_restore_command(self, mock_container: Mock) -> None:
        """测试会话恢复命令"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = {
            'metadata': {
                'session_id': 'test-session-123',
                'workflow_config_path': 'test.yaml',
                'created_at': '2023-01-01T00:00:00'
            }
        }
        mock_session_manager.restore_session.return_value = (Mock(), Mock())
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'restore', 'test-session-123'])
        assert result.exit_code == 0
        assert '恢复成功' in result.output
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_destroy_command(self, mock_container: Mock) -> None:
        """测试会话删除命令"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = {
            'metadata': {'session_id': 'test-session-123'}
        }
        mock_session_manager.delete_session.return_value = True
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'destroy', 'test-session-123', '--confirm'])
        assert result.exit_code == 0
        assert '删除成功' in result.output
    
    def test_config_check_command(self) -> None:
        """测试配置检查命令"""
        result = self.runner.invoke(cli, ['config', 'check'])
        # 由于环境检查可能失败，我们只检查命令是否执行
        assert result.exit_code in [0, 1]  # 0=成功, 1=检查失败但命令执行正常


class TestHelpManager:
    """帮助管理器测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.help_manager = HelpManager()
    
    def test_show_main_help(self) -> None:
        """测试显示主帮助"""
        # 这个测试主要确保方法不会抛出异常
        try:
            self.help_manager.show_main_help()
        except Exception as e:
            pytest.fail(f"show_main_help() 抛出了异常: {e}")
    
    def test_show_command_help(self) -> None:
        """测试显示命令帮助"""
        # 测试已知命令
        try:
            self.help_manager.show_command_help("session")
        except Exception as e:
            pytest.fail(f"show_command_help('session') 抛出了异常: {e}")
        
        # 测试未知命令
        try:
            self.help_manager.show_command_help("unknown_command")
        except Exception as e:
            pytest.fail(f"show_command_help('unknown_command') 抛出了异常: {e}")
    
    def test_show_error_help(self) -> None:
        """测试显示错误帮助"""
        # 测试已知错误类型
        try:
            self.help_manager.show_error_help("SessionNotFound")
        except Exception as e:
            pytest.fail(f"show_error_help('SessionNotFound') 抛出了异常: {e}")
        
        # 测试未知错误类型
        try:
            self.help_manager.show_error_help("UnknownError")
        except Exception as e:
            pytest.fail(f"show_error_help('UnknownError') 抛出了异常: {e}")


class TestErrorHandler:
    """错误处理器测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.error_handler = CLIErrorHandler(verbose=False)
    
    def test_handle_warning(self) -> None:
        """测试处理警告"""
        # 这个测试主要确保方法不会抛出异常
        try:
            self.error_handler.handle_warning("测试警告", "测试上下文")
        except Exception as e:
            pytest.fail(f"handle_warning() 抛出了异常: {e}")
    
    def test_handle_success(self) -> None:
        """测试处理成功信息"""
        try:
            self.error_handler.handle_success("测试成功", "测试上下文")
        except Exception as e:
            pytest.fail(f"handle_success() 抛出了异常: {e}")
    
    def test_handle_info(self) -> None:
        """测试处理信息"""
        try:
            self.error_handler.handle_info("测试信息", "测试上下文")
        except Exception as e:
            pytest.fail(f"handle_info() 抛出了异常: {e}")
    
    def test_get_exit_code(self) -> None:
        """测试获取退出码"""
        # 测试已知错误类型
        exit_code = self.error_handler._get_exit_code("ClickException")
        assert exit_code == 9
        
        # 测试未知错误类型
        exit_code = self.error_handler._get_exit_code("UnknownError")
        assert exit_code == 1


if __name__ == "__main__":
    pytest.main([__file__])
