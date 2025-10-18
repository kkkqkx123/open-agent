"""基础设施模块集成测试"""

import pytest
import os
import tempfile
import time
from pathlib import Path

from src.infrastructure import (
    DependencyContainer,
    YamlConfigLoader,
    EnvironmentChecker,
    ArchitectureChecker,
    TestContainer
)
from src.infrastructure.exceptions import (
    ServiceNotRegisteredError,
    ConfigurationError
)


class TestInfrastructureIntegration:
    """基础设施模块集成测试"""
    
    def test_container_with_config_loader_integration(self):
        """测试依赖注入容器与配置加载器的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试配置
            config_path = Path(temp_dir) / "configs"
            config_path.mkdir()
            
            global_config = config_path / "global.yaml"
            global_config.write_text("""
log_level: INFO
env: test
debug: true
""")
            
            # 设置依赖注入容器
            container = DependencyContainer()
            container.register_factory(
                YamlConfigLoader,
                lambda: YamlConfigLoader(str(config_path)),
                lifetime="singleton"
            )
            
            # 获取配置加载器并加载配置
            config_loader = container.get(YamlConfigLoader)
            config = config_loader.load("global.yaml")
            
            assert config["log_level"] == "INFO"
            assert config["env"] == "test"
            assert config["debug"] is True
            
            # 验证单例模式
            config_loader2 = container.get(YamlConfigLoader)
            assert config_loader is config_loader2
    
    def test_config_loader_with_env_vars_integration(self):
        """测试配置加载器与环境变量的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 设置环境变量
            os.environ["TEST_API_KEY"] = "test_key_123"
            os.environ["TEST_PORT"] = "8000"
            
            try:
                # 创建带环境变量的配置
                config_path = Path(temp_dir) / "configs"
                config_path.mkdir()
                
                api_config = config_path / "api.yaml"
                api_config.write_text("""
api_key: ${TEST_API_KEY}
port: ${TEST_PORT:9000}
timeout: 30
""")
                
                # 加载配置
                loader = YamlConfigLoader(str(config_path))
                config = loader.load("api.yaml")
                
                assert config["api_key"] == "test_key_123"
                assert config["port"] == "8000"
                assert config["timeout"] == 30
            
            finally:
                # 清理环境变量
                if "TEST_API_KEY" in os.environ:
                    del os.environ["TEST_API_KEY"]
                if "TEST_PORT" in os.environ:
                    del os.environ["TEST_PORT"]
    
    def test_config_hot_reload_integration(self):
        """测试配置热重载功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "configs"
            config_path.mkdir()
            
            test_config = config_path / "test.yaml"
            test_config.write_text("value: original")
            
            loader = YamlConfigLoader(str(config_path))
            
            # 设置变化监听
            changed_configs = {}
            def on_config_change(config_path, config_data):
                changed_configs[config_path] = config_data
            
            loader.watch_for_changes(on_config_change)
            
            # 加载初始配置
            config1 = loader.load("test.yaml")
            assert config1["value"] == "original"
            
            # 修改配置文件
            test_config.write_text("value: updated")
            
            # 手动触发文件变化处理
            loader._handle_file_change(str(test_config))
            
            # 验证变化被检测到
            assert "test.yaml" in changed_configs
            assert changed_configs["test.yaml"]["value"] == "updated"
            
            # 重新加载配置
            config2 = loader.load("test.yaml")
            assert config2["value"] == "updated"
            
            loader.stop_watching()
    
    def test_environment_checker_integration(self):
        """测试环境检查器集成"""
        checker = EnvironmentChecker()
        
        # 执行完整环境检查
        results = checker.check_dependencies()
        
        # 验证检查结果
        assert len(results) > 0
        
        # 检查Python版本
        python_result = next(r for r in results if r.component == "python_version")
        assert python_result.status in ["PASS", "ERROR"]
        
        # 检查必需包
        package_results = [r for r in results if r.component.startswith("package_")]
        assert len(package_results) > 0
        
        # 生成报告
        report = checker.generate_report()
        assert "summary" in report
        assert "details" in report
        assert report["summary"]["total"] == len(results)
    
    def test_architecture_checker_integration(self):
        """测试架构检查器集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试项目结构
            src_path = Path(temp_dir) / "src"
            
            # 创建合规的架构
            self._create_compliant_architecture(src_path)
            
            checker = ArchitectureChecker(str(src_path))
            results = checker.check_architecture()
            
            # 验证检查结果
            assert len(results) >= 2
            
            # 检查层级违规
            layer_result = next(r for r in results if r.component == "architecture_layer")
            assert layer_result.status in ["PASS", "ERROR"]
            
            # 检查循环依赖
            circular_result = next(r for r in results if r.component == "circular_dependency")
            assert circular_result.status in ["PASS", "ERROR"]
            
            # 生成依赖图
            graph = checker.generate_dependency_graph()
            assert "layers" in graph
            assert "import_graph" in graph
            assert "layer_mapping" in graph
    
    def test_test_container_full_integration(self):
        """测试测试容器的完整集成"""
        with TestContainer() as container:
            # 设置基础配置和模块
            container.setup_basic_configs()
            container.setup_basic_modules()
            
            # 测试配置加载
            config_loader = container.get_config_loader()
            global_config = config_loader.load("global.yaml")
            assert global_config["log_level"] == "INFO"
            
            # 测试环境检查
            env_checker = container.get_environment_checker()
            results = env_checker.check_dependencies()
            assert len(results) > 0
            
            # 测试架构检查
            arch_checker = container.get_architecture_checker()
            arch_results = arch_checker.check_architecture()
            assert len(arch_results) >= 2
            
            # 测试依赖注入容器
            di_container = container.get_container()
            assert di_container is not None
    
    def test_multi_environment_dependency_injection(self):
        """测试多环境依赖注入"""
        container = DependencyContainer()
        
        # 定义测试接口和实现
        class IService:
            env: str
        
        class DevService(IService):
            def __init__(self):
                self.env = "development"
        
        class ProdService(IService):
            def __init__(self):
                self.env = "production"
        
        # 注册不同环境的实现
        container.register(IService, DevService, "development")
        container.register(IService, ProdService, "production")
        
        # 测试开发环境
        container.set_environment("development")
        dev_service = container.get(IService)
        assert dev_service.env == "development"
        
        # 测试生产环境
        container.set_environment("production")
        prod_service = container.get(IService)
        assert prod_service.env == "production"
        
        # 测试环境切换
        container.set_environment("development")
        dev_service2 = container.get(IService)
        assert dev_service2.env == "development"
        assert dev_service2 is not dev_service  # 应该是新实例
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试服务未注册错误
        container = DependencyContainer()
        
        with pytest.raises(ServiceNotRegisteredError):
            # 使用类型而不是字符串
            class NonExistentService:
                pass
            container.get(NonExistentService)
        
        # 测试配置文件不存在错误
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = YamlConfigLoader(temp_dir)
            
            with pytest.raises(ConfigurationError):
                loader.load("nonexistent.yaml")
        
        # 测试环境变量不存在错误
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "configs"
            config_path.mkdir()
            
            test_config = config_path / "test.yaml"
            test_config.write_text("value: ${NONEXISTENT_VAR}")
            
            loader = YamlConfigLoader(str(config_path))
            
            with pytest.raises(ConfigurationError):
                loader.load("test.yaml")
    
    def test_performance_integration(self):
        """测试性能集成"""
        with TestContainer() as container:
            container.setup_basic_configs()
            
            config_loader = container.get_config_loader()
            
            # 测试配置加载性能
            start_time = time.time()
            for _ in range(100):
                config_loader.load("global.yaml")
            end_time = time.time()
            
            # 缓存应该使后续加载更快
            avg_time = (end_time - start_time) / 100
            assert avg_time < 0.01  # 平均每次加载应小于10ms
            
            # 测试依赖注入性能
            di_container = container.get_container()
            
            start_time = time.time()
            for _ in range(100):
                di_container.get(YamlConfigLoader)
            end_time = time.time()
            
            # 单例模式应该使获取非常快
            avg_time = (end_time - start_time) / 100
            assert avg_time < 0.001  # 平均每次获取应小于1ms
    
    def _create_compliant_architecture(self, src_path: Path):
        """创建合规的架构结构"""
        # 创建目录结构
        for layer in ["domain", "infrastructure", "application", "presentation"]:
            (src_path / layer).mkdir(parents=True)
            (src_path / layer / "__init__.py").touch()
        
        # 创建领域层
        (src_path / "domain" / "entities.py").write_text("""
from dataclasses import dataclass

@dataclass
class Entity:
    id: str
    name: str
""")
        
        # 创建基础设施层
        (src_path / "infrastructure" / "repository.py").write_text("""
from src.domain.entities import Entity

class Repository:
    def get(self, id: str) -> Entity:
        return Entity(id, "test")
""")
        
        # 创建应用层
        (src_path / "application" / "service.py").write_text("""
from src.domain.entities import Entity
from src.infrastructure.repository import Repository

class ApplicationService:
    def __init__(self, repository: Repository):
        self.repository = repository
    
    def get_entity(self, id: str) -> Entity:
        return self.repository.get(id)
""")
        
        # 创建表现层
        (src_path / "presentation" / "cli.py").write_text("""
from src.application.service import ApplicationService

class CLI:
    def __init__(self, service: ApplicationService):
        self.service = service
""")