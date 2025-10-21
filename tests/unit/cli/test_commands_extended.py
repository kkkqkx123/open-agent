"""CLI命令扩展单元测试"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from pathlib import Path

from src.presentation.cli.commands import (
    cli, session, config, version, help_command, quickstart, run,
    session_list, session_restore, session_destroy, config_check,
    _print_sessions_table, setup_container
)
from src.infrastructure.exceptions import (
    ServiceNotRegisteredError,
    ConfigurationError,
    EnvironmentCheckError
)


class TestCLICommandsExtended:
    """CLI命令扩展测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    def test_cli_group_creation(self) -> None:
        """测试CLI组创建"""
        assert cli.name == "模块化代理框架"
        assert cli.help is not None
        assert "模块化代理框架命令行工具" in cli.help
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_list_json_format(self, mock_container: Mock) -> None:
        """测试会话列表JSON格式输出"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.list_sessions.return_value = [
            {
                'metadata': {
                    'session_id': 'test-session-123',
                    'workflow_config_path': 'test.yaml',
                    'created_at': '2023-01-01T00:00:00.000Z',
                    'updated_at': '2023-01-01T01:00:00.000Z',
                    'status': 'active'
                }
            }
        ]
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'list', '--format', 'json'])
        assert result.exit_code == 0
        
        # 验证JSON输出
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]['metadata']['session_id'] == 'test-session-123'
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_list_empty(self, mock_container: Mock) -> None:
        """测试空会话列表"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.list_sessions.return_value = []
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'list'])
        assert result.exit_code == 0
        assert '无会话' in result.output
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_list_with_exception(self, mock_container: Mock) -> None:
        """测试会话列表异常处理"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.list_sessions.side_effect = Exception("列表获取失败")
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'list'])
        assert result.exit_code != 0
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_restore_not_found(self, mock_container: Mock) -> None:
        """测试恢复不存在的会话"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = None
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'restore', 'nonexistent'])
        assert result.exit_code != 0
        assert '不存在' in result.output
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_restore_with_exception(self, mock_container: Mock) -> None:
        """测试恢复会话异常处理"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.side_effect = Exception("恢复失败")
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'restore', 'session123'])
        assert result.exit_code != 0
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_destroy_without_confirm(self, mock_container: Mock) -> None:
        """测试删除会话不确认"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = {
            'metadata': {'session_id': 'test-session-123'}
        }
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        # 模拟用户不确认
        with patch('click.confirm', return_value=False):
            result = self.runner.invoke(cli, ['session', 'destroy', 'test-session-123'])
            assert result.exit_code == 0
            assert '操作已取消' in result.output
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_destroy_failure(self, mock_container: Mock) -> None:
        """测试删除会话失败"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = {
            'metadata': {'session_id': 'test-session-123'}
        }
        mock_session_manager.delete_session.return_value = False
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'destroy', 'test-session-123', '--confirm'])
        assert result.exit_code != 0
        assert '删除失败' in result.output
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_destroy_not_found(self, mock_container: Mock) -> None:
        """测试删除不存在的会话"""
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = None
        
        mock_container_instance = Mock()
        mock_container_instance.get.return_value = mock_session_manager
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'destroy', 'nonexistent', '--confirm'])
        assert result.exit_code != 0
        assert '不存在' in result.output
    
    def test_config_check_json_output(self) -> None:
        """测试配置检查JSON输出"""
        with patch('src.presentation.cli.commands.EnvironmentCheckCommand') as mock_command:
            mock_cmd = Mock()
            mock_command.return_value = mock_cmd
            
            result = self.runner.invoke(cli, [
                'config', 'check', 
                '--format', 'json', 
                '--output', 'test_output.json'
            ])
            
            mock_cmd.run.assert_called_once_with(
                format_type='json', 
                output_file='test_output.json'
            )
    
    def test_config_check_with_exception(self) -> None:
        """测试配置检查异常处理"""
        with patch('src.presentation.cli.commands.EnvironmentCheckCommand') as mock_command:
            mock_cmd = Mock()
            mock_cmd.run.side_effect = Exception("检查失败")
            mock_command.return_value = mock_cmd
            
            result = self.runner.invoke(cli, ['config', 'check'])
            assert result.exit_code != 0
    
    def test_version_command_file_not_found(self) -> None:
        """测试版本命令文件不存在"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('src.presentation.cli.commands.handle_cli_warning') as mock_warning:
                result = self.runner.invoke(cli, ['version'])
                assert result.exit_code == 0
                assert '版本' in result.output
                mock_warning.assert_called_once()
    
    def test_version_command_invalid_toml(self) -> None:
        """测试版本命令无效TOML"""
        with patch('builtins.open', side_effect=Exception("TOML解析错误")):
            with patch('src.presentation.cli.commands.handle_cli_warning') as mock_warning:
                result = self.runner.invoke(cli, ['version'])
                assert result.exit_code == 0
                assert '版本' in result.output
                mock_warning.assert_called_once()
    
    def test_help_command_with_argument(self) -> None:
        """测试带参数的帮助命令"""
        with patch('src.presentation.cli.commands.help_manager') as mock_manager:
            result = self.runner.invoke(cli, ['help', 'session'])
            assert result.exit_code == 0
            mock_manager.show_command_help.assert_called_once_with('session')
    
    def test_help_command_without_argument(self) -> None:
        """测试不带参数的帮助命令"""
        with patch('src.presentation.cli.commands.help_manager') as mock_manager:
            result = self.runner.invoke(cli, ['help'])
            assert result.exit_code == 0
            mock_manager.show_main_help.assert_called_once()
    
    def test_quickstart_command(self) -> None:
        """测试快速开始命令"""
        with patch('src.presentation.cli.commands.help_manager') as mock_manager:
            result = self.runner.invoke(cli, ['quickstart'])
            assert result.exit_code == 0
            mock_manager.show_quick_start.assert_called_once()
    
    def test_run_command_with_config(self) -> None:
        """测试带配置的运行命令"""
        # 创建一个临时配置文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: config\n")
            temp_config_path = f.name
        
        try:
            with patch('src.presentation.tui.app.TUIApp') as mock_tui:
                mock_app = Mock()
                mock_tui.return_value = mock_app
                
                result = self.runner.invoke(cli, ['run', '--config', temp_config_path])
                
                # 验证TUIApp被调用
                mock_tui.assert_called_once()
                # 获取调用参数并验证
                call_args = mock_tui.call_args
                assert call_args is not None
                # 验证传入的路径参数
                assert isinstance(call_args[0][0], Path)
        finally:
            # 清理临时文件
            os.unlink(temp_config_path)
    
    def test_run_command_tui_exception(self) -> None:
        """测试运行命令TUI异常"""
        with patch('src.presentation.tui.app.TUIApp') as mock_tui:
            mock_app = Mock()
            mock_app.run.side_effect = Exception("TUI启动失败")
            mock_tui.return_value = mock_app
            
            result = self.runner.invoke(cli, ['run'])
            assert result.exit_code != 0


class TestPrintSessionsTable:
    """打印会话表格测试"""
    
    def test_print_sessions_table_with_data(self) -> None:
        """测试打印有数据的会话表格"""
        sessions = [
            {
                'metadata': {
                    'session_id': 'test-session-123',
                    'workflow_config_path': 'test.yaml',
                    'created_at': '2023-01-01T00:00:00.000Z',
                    'updated_at': '2023-01-01T01:00:00.000Z',
                    'status': 'active'
                }
            }
        ]
        
        with patch('src.presentation.cli.commands.console.print') as mock_print:
            _print_sessions_table(sessions)
            mock_print.assert_called_once()
    
    def test_print_sessions_table_empty(self) -> None:
        """测试打印空会话表格"""
        sessions = []
        
        with patch('src.presentation.cli.commands.console.print') as mock_print:
            _print_sessions_table(sessions)
            mock_print.assert_called_once()
    
    def test_print_sessions_table_missing_metadata(self) -> None:
        """测试打印缺少元数据的会话表格"""
        sessions = [
            {'id': 'test'},  # 缺少metadata
            {
                'metadata': {
                    'session_id': 'test-session-456',
                    # 缺少其他字段
                }
            }
        ]
        
        with patch('src.presentation.cli.commands.console.print') as mock_print:
            _print_sessions_table(sessions)
            mock_print.assert_called_once()


class TestSetupContainer:
    """设置容器测试"""
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_setup_container_registers_services(self, mock_container: Mock) -> None:
        """测试设置容器注册服务"""
        mock_container_instance = Mock()
        mock_container_instance.has_service.return_value = False
        mock_container.return_value = mock_container_instance
        
        with patch('src.infrastructure.config_loader.YamlConfigLoader') as mock_loader:
            with patch('src.session.store.FileSessionStore') as mock_store:
                with patch('src.session.git_manager.create_git_manager') as mock_git:
                    with patch('src.workflow.manager.WorkflowManager') as mock_workflow:
                        with patch('src.session.manager.SessionManager') as mock_session:
                            setup_container()
                            
                            # 验证所有服务都被注册
                            assert mock_container_instance.register_instance.call_count >= 5
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_setup_container_skips_existing_services(self, mock_container: Mock) -> None:
        """测试设置容器跳过已存在的服务"""
        mock_container_instance = Mock()
        mock_container_instance.has_service.return_value = True  # 所有服务都已存在
        mock_container.return_value = mock_container_instance
        
        setup_container()
        
        # 验证没有尝试注册任何服务
        mock_container_instance.register_instance.assert_not_called()


class TestCLICommandsErrorHandling:
    """CLI命令错误处理测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_list_with_service_error(self, mock_container: Mock) -> None:
        """测试会话列表服务错误"""
        # 模拟服务未注册错误
        mock_container_instance = Mock()
        mock_container_instance.get.side_effect = ServiceNotRegisteredError("服务未注册")
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'list'])
        assert result.exit_code != 0
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_list_with_config_error(self, mock_container: Mock) -> None:
        """测试会话列表配置错误"""
        # 模拟配置错误
        mock_container_instance = Mock()
        mock_container_instance.get.side_effect = ConfigurationError("配置错误")
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'list'])
        assert result.exit_code != 0
    
    @patch('src.presentation.cli.commands.get_global_container')
    def test_session_restore_with_session_error(self, mock_container: Mock) -> None:
        """测试会话恢复会话错误"""
        # 模拟会话未注册错误
        mock_container_instance = Mock()
        mock_container_instance.get.side_effect = ServiceNotRegisteredError("会话未注册")
        mock_container.return_value = mock_container_instance
        
        result = self.runner.invoke(cli, ['session', 'restore', 'session123'])
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])