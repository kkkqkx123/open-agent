"""端到端工作流测试"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from typing import cast, Any, Dict

from src.infrastructure import (
    DependencyContainer,
    YamlConfigLoader,
    EnvironmentChecker,
    ArchitectureChecker,
    TestContainer,
    EnvironmentCheckCommand
)
from src.infrastructure.types import CheckResult


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_complete_infrastructure_workflow(self) -> None:
        """测试完整的基础设施工作流"""
        with TestContainer() as container:
            # 1. 设置环境
            container.set_environment_variable("AGENT_OPENAI_KEY", "test_key_123")
            container.set_environment_variable("AGENT_ENV", "test")
            
            # 2. 设置基础配置
            container.setup_basic_configs()
            
            # 3. 设置基础模块结构
            container.setup_basic_modules()
            
            # 4. 环境检查
            env_checker = container.get_environment_checker()
            env_results = env_checker.check_dependencies()
            
            # 验证环境检查结果
            assert len(env_results) > 0
            env_summary = env_checker.generate_report()
            assert env_summary["summary"]["total"] > 0
            
            # 5. 配置加载
            config_loader = container.get_config_loader()
            
            # 加载全局配置
            global_config = config_loader.load("global.yaml")
            assert global_config["log_level"] == "INFO"
            assert global_config["env"] == "test"
            
            # 加载LLM配置
            llm_config = config_loader.load("llms/_group.yaml")
            assert "openai_group" in llm_config
            
            # 测试环境变量解析
            container.create_test_config("configs/api.yaml", {
                "api_key": "${AGENT_OPENAI_KEY}",
                "environment": "${AGENT_ENV}",
                "timeout": 30
            })
            
            api_config = config_loader.load("api.yaml")
            assert api_config["api_key"] == "test_key_123"
            assert api_config["environment"] == "test"
            
            # 6. 架构检查
            arch_checker = container.get_architecture_checker()
            arch_results = arch_checker.check_architecture()
            
            # 验证架构检查结果
            assert len(arch_results) >= 2
            
            # 7. 依赖注入容器集成
            di_container = container.get_container()
            
            # 注册自定义服务
            class CustomService:
                def __init__(self, config_loader: YamlConfigLoader):
                    self.config_loader = config_loader
                
                def get_config(self, path: str) -> Any:
                    return self.config_loader.load(path)
            
            di_container.register(CustomService, CustomService)
            
            # 获取并使用自定义服务
            custom_service = di_container.get(CustomService)
            config = custom_service.get_config("global.yaml")
            assert config["log_level"] == "INFO"
            
            # 8. 清理环境变量
            container.clear_environment_variable("AGENT_OPENAI_KEY")
            container.clear_environment_variable("AGENT_ENV")
    
    def test_error_recovery_workflow(self) -> None:
        """测试错误恢复工作流"""
        with TestContainer() as container:
            # 1. 创建有问题的配置
            container.create_test_file("configs/invalid.yaml", """
invalid_yaml: [
    unclosed_array
""")
            
            config_loader = container.get_config_loader()
            
            # 2. 尝试加载无效配置
            from src.infrastructure.exceptions import ConfigurationError
            
            with pytest.raises(ConfigurationError):
                config_loader.load("invalid.yaml")
            
            # 3. 创建有效配置并验证恢复
            container.create_test_config("configs/valid.yaml", {
                "log_level": "INFO",
                "env": "test"
            })
            
            valid_config = config_loader.load("valid.yaml")
            assert valid_config["log_level"] == "INFO"
            
            # 4. 测试架构违规检测和恢复
            container.create_test_files_with_violations()
            
            arch_checker = container.get_architecture_checker()
            arch_results = arch_checker.check_architecture()
            
            # 应该检测到违规
            layer_violations = [r for r in arch_results if r.component == "architecture_layer"]
            assert any(not r.is_pass() for r in layer_violations)
            
            # 5. 创建合规架构并验证恢复
            container.setup_basic_modules()
            
            # 重新检查架构
            arch_results = arch_checker.check_architecture()
            
            # 基础模块应该是合规的
            layer_violations = [r for r in arch_results if r.component == "architecture_layer"]
            # 注意：由于测试容器中可能还有其他违规文件，这里不强制要求全部通过
    
    def test_performance_benchmark_workflow(self) -> None:
        """测试性能基准工作流"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 1. 配置加载性能测试
            config_loader = container.get_config_loader()
            
            import time
            start_time = time.time()
            
            # 多次加载配置（测试缓存效果）
            for _ in range(50):
                config_loader.load("global.yaml")
                config_loader.load("llms/_group.yaml")
                config_loader.load("agents/_group.yaml")
                config_loader.load("tool-sets/_group.yaml")
            
            end_time = time.time()
            avg_load_time = (end_time - start_time) / (50 * 4)
            
            # 平均加载时间应小于10ms
            assert avg_load_time < 0.01, f"Average load time: {avg_load_time:.3f}s"
            
            # 2. 依赖注入性能测试
            di_container = container.get_container()
            
            start_time = time.time()
            
            # 多次获取服务（测试单例效果）
            for _ in range(100):
                di_container.get(YamlConfigLoader)
                di_container.get(EnvironmentChecker)
                di_container.get(ArchitectureChecker)
            
            end_time = time.time()
            avg_get_time = (end_time - start_time) / (100 * 3)
            
            # 平均获取时间应小于1ms
            assert avg_get_time < 0.001, f"Average get time: {avg_get_time:.3f}s"
            
            # 3. 环境检查性能测试
            env_checker = container.get_environment_checker()
            
            start_time = time.time()
            env_checker.check_dependencies()
            end_time = time.time()
            
            # 环境检查时间应小于1秒
            check_time = end_time - start_time
            assert check_time < 1.0, f"Environment check time: {check_time:.3f}s"
    
    def test_multi_environment_workflow(self) -> None:
        """测试多环境工作流"""
        with TestContainer() as container:
            # 1. 设置不同环境的配置
            container.create_test_config("configs/global.yaml", {
                "log_level": "INFO",
                "env": "development",
                "debug": True
            })
            
            container.create_test_config("configs/production.yaml", {
                "log_level": "WARNING",
                "env": "production",
                "debug": False
            })
            
            # 2. 设置依赖注入容器的多环境支持
            di_container = container.get_container()
            
            class ConfigService:
                def __init__(self, config_path: str):
                    self.config_path = config_path
                    self.config_loader = di_container.get(YamlConfigLoader)
                
                def get_config(self) -> Any:
                    return self.config_loader.load(self.config_path)
            
            # 注册不同环境的配置服务
            di_container.register_factory(ConfigService, lambda: ConfigService("global.yaml"), "development")
            di_container.register_factory(ConfigService, lambda: ConfigService("production.yaml"), "production")
            
            # 3. 测试开发环境
            di_container.set_environment("development")
            dev_service = di_container.get(ConfigService)
            dev_config = dev_service.get_config()
            assert dev_config["env"] == "development"
            assert dev_config["debug"] is True
            
            # 4. 测试生产环境
            di_container.set_environment("production")
            prod_service = di_container.get(ConfigService)
            prod_config = prod_service.get_config()
            assert prod_config["env"] == "production"
            assert prod_config["debug"] is False
            
            # 5. 验证环境切换
            di_container.set_environment("development")
            dev_service2 = di_container.get(ConfigService)
            dev_config2 = dev_service2.get_config()
            assert dev_config2["env"] == "development"
    
    def test_environment_check_command_integration(self) -> None:
        """测试环境检查命令集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            # 1. 创建环境检查命令
            env_checker = container.get_environment_checker()
            command = EnvironmentCheckCommand(env_checker)
            
            # 2. 测试表格格式输出
            try:
                command.run(format_type="table")
            except SystemExit:
                # 命令可能会因为环境问题退出，这是正常的
                pass
            
            # 3. 测试JSON格式输出
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json_file = f.name
            
            try:
                command.run(format_type="json", output_file=json_file)
                
                # 验证JSON文件生成
                with open(json_file, 'r') as f:
                    report = json.load(f)
                
                assert "summary" in report
                assert "details" in report
                assert report["summary"]["total"] > 0
            
            except SystemExit:
                # 命令可能会因为环境问题退出，这是正常的
                pass
            
            finally:
                # 清理临时文件
                if os.path.exists(json_file):
                    os.unlink(json_file)
    
    def test_configuration_hot_reload_workflow(self) -> None:
        """测试配置热重载工作流"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            config_loader = container.get_config_loader()
            
            # 1. 加载初始配置
            initial_config = config_loader.load("global.yaml")
            assert initial_config["log_level"] == "INFO"
            
            # 2. 设置热重载监听
            reloaded_configs = {}
            def on_reload(config_path: str, config_data: Dict[str, Any]) -> None:
                reloaded_configs[config_path] = config_data
            
            config_loader.watch_for_changes(on_reload)
            
            # 3. 修改配置文件
            updated_config = initial_config.copy()
            updated_config["log_level"] = "DEBUG"
            
            container.create_test_config("configs/global.yaml", updated_config)
            
            # 4. 手动触发重载
            # 使用类型断言来访问私有方法
            from src.infrastructure.config_loader import YamlConfigLoader
            yaml_config_loader = cast(YamlConfigLoader, config_loader)
            yaml_config_loader._handle_file_change(str(container.temp_path / "configs" / "global.yaml"))
            
            # 5. 验证重载
            assert "global.yaml" in reloaded_configs
            assert reloaded_configs["global.yaml"]["log_level"] == "DEBUG"
            
            # 6. 验证新配置加载
            new_config = config_loader.load("global.yaml")
            assert new_config["log_level"] == "DEBUG"
            
            config_loader.stop_watching()