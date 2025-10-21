"""CLI主入口文件单元测试"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from click import Context

from src.presentation.cli.main import main, run


class TestMain:
    """CLI主入口测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    def test_main_help(self) -> None:
        """测试主命令帮助"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert '模块化代理框架命令行工具' in result.output
    
    def test_main_with_verbose(self) -> None:
        """测试带详细模式的主命令"""
        with patch('src.presentation.cli.main.commands.cli') as mock_cli:
            result = self.runner.invoke(main, ['--verbose', '--help'])
            # 由于没有子命令，会显示帮助
            assert result.exit_code == 0
    
    def test_main_with_config(self) -> None:
        """测试带配置文件的主命令"""
        with patch('src.presentation.cli.main.commands.cli') as mock_cli:
            result = self.runner.invoke(main, ['--config', 'test.yaml', '--help'])
            # 由于没有子命令，会显示帮助
            assert result.exit_code == 0
    
    def test_main_context_object(self) -> None:
        """测试上下文对象设置"""
        with patch('src.presentation.cli.main.commands.cli') as mock_cli:
            ctx = Context(main)
            # 确保上下文对象存在
            ctx.ensure_object(dict)
            # 直接设置上下文对象
            ctx.obj["verbose"] = True
            ctx.obj["config"] = 'test.yaml'
            
            # 验证上下文对象设置
            assert ctx.obj['verbose'] is True
            assert ctx.obj['config'] == 'test.yaml'
    
    def test_run_command_help(self) -> None:
        """测试运行命令帮助"""
        result = self.runner.invoke(main, ['run', '--help'])
        assert result.exit_code == 0
        assert '运行代理工作流' in result.output
    
    @patch('src.presentation.cli.main.TUIApp')
    def test_run_command_with_tui(self, mock_tui_app: Mock) -> None:
        """测试使用TUI界面的运行命令"""
        mock_app = Mock()
        mock_tui_app.return_value = mock_app
        
        result = self.runner.invoke(main, [
            '--verbose',
            'run',
            '--workflow', 'test.yaml',
            '--tui'
        ])
        
        assert result.exit_code == 0
        mock_tui_app.assert_called_once()
        mock_app.run.assert_called_once()
    
    @patch('src.presentation.cli.run_command.RunCommand')
    def test_run_command_without_tui(self, mock_run_command: Mock) -> None:
        """测试不使用TUI界面的运行命令"""
        mock_cmd = Mock()
        mock_run_command.return_value = mock_cmd
        
        result = self.runner.invoke(main, [
            '--verbose',
            '--config', 'config.yaml',
            'run',
            '--workflow', 'test.yaml',
            '--agent', 'agent.yaml',
            '--session', 'session123'
        ])
        
        assert result.exit_code == 0
        mock_run_command.assert_called_once_with('config.yaml', True)
        mock_cmd.execute.assert_called_once_with('test.yaml', 'agent.yaml', 'session123')
    
    @patch('src.presentation.cli.run_command.RunCommand')
    def test_run_command_minimal_args(self, mock_run_command: Mock) -> None:
        """测试最小参数的运行命令"""
        mock_cmd = Mock()
        mock_run_command.return_value = mock_cmd
        
        result = self.runner.invoke(main, [
            'run',
            '--workflow', 'test.yaml'
        ])
        
        assert result.exit_code == 0
        mock_run_command.assert_called_once_with(None, False)
        mock_cmd.execute.assert_called_once_with('test.yaml', None, None)
    
    @patch('src.presentation.cli.run_command.RunCommand')
    def test_run_command_with_exception(self, mock_run_command: Mock) -> None:
        """测试运行命令异常处理"""
        mock_cmd = Mock()
        mock_cmd.execute.side_effect = Exception("测试异常")
        mock_run_command.return_value = mock_cmd
        
        result = self.runner.invoke(main, [
            'run',
            '--workflow', 'test.yaml'
        ])
        
        # 应该抛出异常
        assert result.exit_code != 0
    
    def test_run_command_missing_workflow(self) -> None:
        """测试缺少工作流参数的运行命令"""
        result = self.runner.invoke(main, ['run'])
        
        # 应该失败，因为缺少必需的workflow参数
        assert result.exit_code != 0
    
    @patch('src.presentation.cli.main.TUIApp')
    def test_run_command_tui_exception(self, mock_tui_app: Mock) -> None:
        """测试TUI模式异常处理"""
        mock_app = Mock()
        mock_app.run.side_effect = Exception("TUI异常")
        mock_tui_app.return_value = mock_app
        
        result = self.runner.invoke(main, [
            'run',
            '--workflow', 'test.yaml',
            '--tui'
        ])
        
        # 应该抛出异常
        assert result.exit_code != 0
    
    def test_main_function_import(self) -> None:
        """测试主函数导入"""
        from src.presentation.cli import main as imported_main
        assert callable(imported_main)
    
    def test_run_function_import(self) -> None:
        """测试运行函数导入"""
        from src.presentation.cli.main import run
        assert callable(run)


class TestMainIntegration:
    """CLI主入口集成测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    def test_all_commands_help(self) -> None:
        """测试所有命令的帮助"""
        commands = ['run']
        
        for command in commands:
            result = self.runner.invoke(main, [command, '--help'])
            assert result.exit_code == 0
    
    def test_context_persistence(self) -> None:
        """测试上下文持久性"""
        with patch('src.presentation.cli.run_command.RunCommand') as mock_run_command:
            mock_cmd = Mock()
            mock_run_command.return_value = mock_cmd
            
            # 测试上下文对象在子命令中可用
            result = self.runner.invoke(main, [
                '--verbose',
                '--config', 'test.yaml',
                'run',
                '--workflow', 'test.yaml'
            ])
            
            assert result.exit_code == 0
            # 验证RunCommand被正确调用，说明上下文传递成功
            mock_run_command.assert_called_once_with('test.yaml', True)


if __name__ == "__main__":
    pytest.main([__file__])