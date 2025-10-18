"""测试容器单元测试"""

import pytest
import tempfile
import yaml
import os
from pathlib import Path
from typing import Any

from src.infrastructure.test_container import TestContainer
from src.infrastructure import IConfigLoader, IEnvironmentChecker, ArchitectureChecker


class TestTestContainer:
    """测试容器测试"""
    
    def test_init_with_temp_dir(self) -> None:
        """测试使用临时目录初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            container = TestContainer(temp_dir)
            
            assert container.temp_dir == temp_dir
            assert container.temp_path == Path(temp_dir)
            assert container.container is not None
    
    def test_init_without_temp_dir(self) -> None:
        """测试不指定临时目录初始化"""
        container = TestContainer()
        
        assert container.temp_dir is not None
        assert container.temp_path.exists()
        assert container.container is not None
    
    def test_get_container(self) -> None:
        """测试获取依赖注入容器"""
        container = TestContainer()
        di_container = container.get_container()
        
        assert di_container is not None
        assert di_container is container.container
    
    def test_create_test_config(self) -> None:
        """测试创建测试配置文件"""
        container = TestContainer()
        
        config_data = {
            "log_level": "DEBUG",
            "env": "test"
        }
        
        container.create_test_config("configs/test.yaml", config_data)
        
        config_file = container.temp_path / "configs" / "test.yaml"
        assert config_file.exists()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = yaml.safe_load(f)
        
        assert loaded_config["log_level"] == "DEBUG"
        assert loaded_config["env"] == "test"
    
    def test_create_test_file(self) -> None:
        """测试创建测试文件"""
        container = TestContainer()
        
        content = "test file content"
        container.create_test_file("test_dir/test_file.txt", content)
        
        test_file = container.temp_path / "test_dir" / "test_file.txt"
        assert test_file.exists()
        
        with open(test_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        assert file_content == content
    
    def test_create_test_module(self) -> None:
        """测试创建测试模块"""
        container = TestContainer()
        
        content = """
def test_function():
    return "test"
"""
        
        container.create_test_module("src/test_module.py", content)
        
        module_file = container.temp_path / "src" / "test_module.py"
        assert module_file.exists()
        
        # 检查__init__.py文件是否创建
        init_file = container.temp_path / "src" / "__init__.py"
        assert init_file.exists()
        
        with open(module_file, 'r', encoding='utf-8') as f:
            module_content = f.read()
        
        assert "test_function" in module_content
    
    def test_get_config_loader(self) -> None:
        """测试获取配置加载器"""
        container = TestContainer()
        
        config_loader = container.get_config_loader()
        assert config_loader is not None
        assert isinstance(config_loader, IConfigLoader)
    
    def test_get_environment_checker(self) -> None:
        """测试获取环境检查器"""
        container = TestContainer()
        
        env_checker = container.get_environment_checker()
        assert env_checker is not None
        assert isinstance(env_checker, IEnvironmentChecker)
    
    def test_get_architecture_checker(self) -> None:
        """测试获取架构检查器"""
        container = TestContainer()
        
        arch_checker = container.get_architecture_checker()
        assert arch_checker is not None
        assert isinstance(arch_checker, ArchitectureChecker)
    
    def test_setup_basic_configs(self) -> None:
        """测试设置基础配置文件"""
        container = TestContainer()
        
        container.setup_basic_configs()
        
        # 检查全局配置文件
        global_config = container.temp_path / "configs" / "global.yaml"
        assert global_config.exists()
        
        with open(global_config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert config["log_level"] == "INFO"
        assert config["env"] == "test"
        assert len(config["log_outputs"]) == 1
        
        # 检查LLM组配置文件
        llm_group_config = container.temp_path / "configs" / "llms" / "_group.yaml"
        assert llm_group_config.exists()
        
        with open(llm_group_config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert "openai_group" in config
        assert "base_url" in config["openai_group"]
        
        # 检查Agent组配置文件
        agent_group_config = container.temp_path / "configs" / "agents" / "_group.yaml"
        assert agent_group_config.exists()
        
        # 检查工具集组配置文件
        tool_group_config = container.temp_path / "configs" / "tool-sets" / "_group.yaml"
        assert tool_group_config.exists()
    
    def test_setup_basic_modules(self) -> None:
        """测试设置基础模块结构"""
        container = TestContainer()
        
        container.setup_basic_modules()
        
        # 检查领域层模块
        domain_init = container.temp_path / "src" / "domain" / "__init__.py"
        domain_entities = container.temp_path / "src" / "domain" / "entities.py"
        assert domain_init.exists()
        assert domain_entities.exists()
        
        # 检查基础设施层模块
        infra_init = container.temp_path / "src" / "infrastructure" / "__init__.py"
        infra_repo = container.temp_path / "src" / "infrastructure" / "repository.py"
        assert infra_init.exists()
        assert infra_repo.exists()
        
        # 检查应用层模块
        app_init = container.temp_path / "src" / "application" / "__init__.py"
        app_service = container.temp_path / "src" / "application" / "service.py"
        assert app_init.exists()
        assert app_service.exists()
        
        # 检查表现层模块
        pres_init = container.temp_path / "src" / "presentation" / "__init__.py"
        pres_cli = container.temp_path / "src" / "presentation" / "cli.py"
        assert pres_init.exists()
        assert pres_cli.exists()
    
    def test_cleanup(self) -> None:
        """测试清理测试环境"""
        container = TestContainer()
        
        # 创建一些文件
        container.create_test_file("test.txt", "test")
        assert container.temp_path.exists()
        
        # 清理
        container.cleanup()
        assert not container.temp_path.exists()
    
    def test_context_manager(self) -> None:
        """测试上下文管理器"""
        with TestContainer() as container:
            # 创建一些文件
            container.create_test_file("test.txt", "test")
            assert container.temp_path.exists()
        
        # 退出上下文后应该自动清理
        assert not container.temp_path.exists()
    
    def test_set_environment_variable(self) -> None:
        """测试设置环境变量"""
        container = TestContainer()
        
        # 设置环境变量
        container.set_environment_variable("TEST_VAR", "test_value")
        
        # 验证环境变量已设置
        import os
        assert os.environ.get("TEST_VAR") == "test_value"
        
        # 清理
        container.clear_environment_variable("TEST_VAR")
        assert os.environ.get("TEST_VAR") is None
    
    def test_clear_environment_variable(self) -> None:
        """测试清除环境变量"""
        import os
        
        # 设置环境变量
        os.environ["TEST_VAR"] = "test_value"
        assert os.environ.get("TEST_VAR") == "test_value"
        
        # 使用容器清除
        container = TestContainer()
        container.clear_environment_variable("TEST_VAR")
        assert os.environ.get("TEST_VAR") is None
    
    def test_create_test_files_with_violations(self) -> None:
        """测试创建有架构违规的测试文件"""
        container = TestContainer()
        
        container.create_test_files_with_violations()
        
        # 检查违规文件是否创建
        domain_violation = container.temp_path / "src" / "domain" / "violation.py"
        assert domain_violation.exists()
        
        infra_violation = container.temp_path / "src" / "infrastructure" / "violation.py"
        assert infra_violation.exists()
        
        module_a = container.temp_path / "src" / "module_a.py"
        assert module_a.exists()
        
        module_b = container.temp_path / "src" / "module_b.py"
        assert module_b.exists()
        
        # 检查违规内容
        with open(domain_violation, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "from src.infrastructure.repository" in content
        
        with open(infra_violation, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "from src.application.service" in content
    
    def test_integration_with_config_loader(self) -> None:
        """测试与配置加载器的集成"""
        container = TestContainer()
        container.setup_basic_configs()
        
        config_loader = container.get_config_loader()
        
        # 加载全局配置
        global_config = config_loader.load("global.yaml")
        assert global_config["log_level"] == "INFO"
        assert global_config["env"] == "test"
        
        # 加载LLM组配置
        llm_config = config_loader.load("llms/_group.yaml")
        assert "openai_group" in llm_config
    
    def test_integration_with_environment_checker(self) -> None:
        """测试与环境检查器的集成"""
        container = TestContainer()
        container.setup_basic_configs()
        
        env_checker = container.get_environment_checker()
        
        # 检查配置文件
        results = env_checker.check_config_files()
        assert len(results) > 0
        
        # 应该有配置文件的检查结果
        config_results = [r for r in results if r.component.startswith("config_file_")]
        assert len(config_results) > 0
    
    def test_integration_with_architecture_checker(self) -> None:
        """测试与架构检查器的集成"""
        container = TestContainer()
        container.setup_basic_modules()
        
        arch_checker = container.get_architecture_checker()
        
        # 检查架构
        results = arch_checker.check_architecture()
        assert len(results) >= 2  # 至少有层级检查和循环依赖检查