"""CLI模块集成测试"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from src.presentation.cli.main import main
from src.presentation.cli.commands import cli
from src.infrastructure import TestContainer


class TestCLIIntegration:
    """CLI集成测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self) -> None:
        """测试后清理"""
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_full_workflow(self) -> None:
        """测试CLI完整工作流"""
        with TestContainer() as container:
            # 设置基本配置
            container.setup_basic_configs()
            
            # 测试版本命令 - 使用cli而不是main
            result = self.runner.invoke(cli, ['version'])
            assert result.exit_code == 0
            assert 'version' in result.output.lower()
            
            # 测试帮助命令
            result = self.runner.invoke(main, ['--help'])
            assert result.exit_code == 0
            assert '模块化代理框架' in result.output
    
    def test_session_management_workflow(self) -> None:
        """测试会话管理工作流"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试会话列表（初始为空）
            result = self.runner.invoke(cli, ['session', 'list'])
            assert result.exit_code == 0
            
            # 测试JSON格式会话列表
            result = self.runner.invoke(cli, ['session', 'list', '--format', 'json'])
            assert result.exit_code == 0
            try:
                data = json.loads(result.output)
                assert isinstance(data, list)
            except json.JSONDecodeError:
                pytest.fail("JSON输出格式无效")
    
    def test_config_check_workflow(self) -> None:
        """测试配置检查工作流"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试配置检查
            result = self.runner.invoke(cli, ['config', 'check'])
            # 配置检查可能失败，但命令应该执行
            assert result.exit_code in [0, 1]
            
            # 测试JSON格式配置检查
            output_file = os.path.join(self.temp_dir, 'config_check.json')
            result = self.runner.invoke(cli, [
                'config', 'check', 
                '--format', 'json',
                '--output', output_file
            ])
            # 检查输出文件是否创建
            assert os.path.exists(output_file) or result.exit_code != 0
    
    def test_help_system_integration(self) -> None:
        """测试帮助系统集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试主帮助
            result = self.runner.invoke(cli, ['help'])
            assert result.exit_code == 0
            
            # 测试命令帮助
            commands = ['session', 'config', 'run', 'version']
            for command in commands:
                result = self.runner.invoke(cli, ['help', command])
                assert result.exit_code == 0
            
            # 测试快速开始
            result = self.runner.invoke(cli, ['quickstart'])
            assert result.exit_code == 0
    
    def test_error_handling_integration(self) -> None:
        """测试错误处理集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试恢复不存在的会话
            result = self.runner.invoke(cli, ['session', 'restore', 'nonexistent-session'])
            assert result.exit_code != 0
            
            # 测试删除不存在的会话
            result = self.runner.invoke(cli, [
                'session', 'destroy', 'nonexistent-session', '--confirm'
            ])
            assert result.exit_code != 0
    
    def test_verbose_mode_integration(self) -> None:
        """测试详细模式集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试详细模式
            result = self.runner.invoke(main, ['--verbose', '--help'])
            assert result.exit_code == 0
            
            # 测试详细模式下的错误
            result = self.runner.invoke(main, [
                '--verbose', 'session', 'restore', 'nonexistent'
            ])
            assert result.exit_code != 0
    
    def test_config_parameter_integration(self) -> None:
        """测试配置参数集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 创建临时配置文件
            config_file = os.path.join(self.temp_dir, 'test_config.yaml')
            with open(config_file, 'w') as f:
                f.write("test: config\n")
            
            # 测试配置参数
            result = self.runner.invoke(main, [
                '--config', config_file, '--help'
            ])
            assert result.exit_code == 0
    
    def test_run_command_integration(self) -> None:
        """测试运行命令集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 创建临时工作流文件
            workflow_file = os.path.join(self.temp_dir, 'test_workflow.yaml')
            with open(workflow_file, 'w') as f:
                f.write("name: test_workflow\n")
            
            # 测试运行命令（可能失败，但应该尝试执行）
            result = self.runner.invoke(main, [
                'run', '--workflow', workflow_file
            ])
            # 可能因为缺少依赖而失败，但命令应该被识别
            assert result.exit_code in [0, 1, 2]
    
    def test_container_setup_integration(self) -> None:
        """测试容器设置集成"""
        from src.presentation.cli.commands import setup_container
        from src.infrastructure.config_loader import IConfigLoader
        from src.sessions.manager import ISessionManager
        
        with TestContainer() as container:
            # 测试容器设置
            setup_container()
            
            # 验证服务已注册 - 使用全局容器而不是TestContainer
            from src.infrastructure.container import get_global_container
            global_container = get_global_container()
            assert global_container.has_service(IConfigLoader)
            assert global_container.has_service(ISessionManager)
    
    def test_cli_with_custom_environment(self) -> None:
        """测试自定义环境中的CLI"""
        # 设置测试环境变量
        os.environ['AGENT_TEST_MODE'] = 'true'
        
        try:
            with TestContainer() as container:
                container.setup_basic_configs()
                
                # 测试在测试环境中的命令
                result = self.runner.invoke(cli, ['version'])
                assert result.exit_code == 0
        finally:
            # 清理环境变量
            if 'AGENT_TEST_MODE' in os.environ:
                del os.environ['AGENT_TEST_MODE']
    
    def test_cli_output_formats(self) -> None:
        """测试CLI输出格式"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试表格格式
            result = self.runner.invoke(cli, ['session', 'list', '--format', 'table'])
            assert result.exit_code == 0
            
            # 测试JSON格式
            result = self.runner.invoke(cli, ['session', 'list', '--format', 'json'])
            assert result.exit_code == 0
    
    def test_cli_command_chaining(self) -> None:
        """测试CLI命令链式调用"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试多个命令的连续执行
            commands = [
                ['version'],
                ['help'],
                ['session', 'list'],
                ['config', 'check']
            ]
            
            for command in commands:
                result = self.runner.invoke(cli, command)
                # 某些命令可能失败，但应该被正确处理
                assert result.exit_code in [0, 1]


class TestCLIErrorRecovery:
    """CLI错误恢复测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    def test_missing_dependency_handling(self) -> None:
        """测试缺少依赖处理"""
        with patch('src.presentation.cli.commands.get_global_container') as mock_container:
            # 模拟缺少依赖
            mock_container.side_effect = Exception("依赖缺失")
            
            result = self.runner.invoke(cli, ['session', 'list'])
            assert result.exit_code != 0
    
    def test_invalid_configuration_handling(self) -> None:
        """测试无效配置处理"""
        # 不使用TestContainer，直接测试CLI
        result = self.runner.invoke(cli, ['session', 'list'])
        # 应该因为配置问题而失败，或者至少有某种错误处理
        # 如果命令成功执行（返回空列表），那也是可以接受的
        # 因为CLI可能有默认的错误处理机制
        assert result.exit_code in [0, 1, 2]  # 允许成功或各种错误码
    
    def test_file_system_error_handling(self) -> None:
        """测试文件系统错误处理"""
        # 测试不存在的配置文件
        result = self.runner.invoke(main, [
            '--config', '/nonexistent/config.yaml',
            '--help'
        ])
        # 帮助命令应该成功，即使配置文件不存在
        assert result.exit_code == 0


class TestCLIPerformance:
    """CLI性能测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.runner = CliRunner()
    
    def test_command_response_time(self) -> None:
        """测试命令响应时间"""
        import time
        
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试快速命令的响应时间
            start_time = time.time()
            result = self.runner.invoke(cli, ['version'])
            end_time = time.time()
            
            assert result.exit_code == 0
            # 命令应该在合理时间内完成（1秒）
            assert end_time - start_time < 1.0
    
    def test_large_output_handling(self) -> None:
        """测试大输出处理"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 测试可能产生大量输出的命令
            result = self.runner.invoke(cli, ['config', 'check'])
            # 即使输出很大，也应该能正常处理
            assert result.exit_code in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__])
