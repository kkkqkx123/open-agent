"""统一DI框架测试"""

import pytest
import logging
from typing import Dict, Any

from src.services.configuration.unified_di_framework import (
    UnifiedDIFramework,
    get_global_framework,
    initialize_framework,
    shutdown_framework
)
from src.services.configuration.base_configurator import BaseModuleConfigurator
from src.interfaces.configuration import IModuleConfigurator, ValidationResult
from src.interfaces.container import IDependencyContainer, ILifecycleAware
from src.core.common.types import ServiceLifetime

logger = logging.getLogger(__name__)


# 测试服务类
class TestService(ILifecycleAware):
    """测试服务"""
    
    def __init__(self, name: str = "test"):
        self.name = name
        self._initialized = False
    
    def initialize(self) -> None:
        self._initialized = True
        logger.info(f"TestService {self.name} initialized")
    
    def start(self) -> None:
        logger.info(f"TestService {self.name} started")
    
    def stop(self) -> None:
        logger.info(f"TestService {self.name} stopped")
    
    def dispose(self) -> None:
        self._initialized = False
        logger.info(f"TestService {self.name} disposed")


class TestConfigurator(BaseModuleConfigurator):
    """测试配置器"""
    
    def __init__(self):
        super().__init__("test")
        self.set_priority(1)
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置测试服务"""
        enabled = config.get("enabled", True)
        if not enabled:
            logger.info("Test module disabled")
            return
        
        service_name = config.get("service_name", "default")
        
        # 注册测试服务
        def test_service_factory() -> TestService:
            return TestService(service_name)
        
        container.register_factory(
            TestService,
            test_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info(f"Test service configured with name: {service_name}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "service_name": "default_test",
            "version": "1.0.0"
        }
    
    def get_required_fields(self) -> list:
        return ["enabled"]
    
    def get_field_types(self) -> dict:
        return {
            "enabled": bool,
            "service_name": str,
            "version": str
        }


class TestModuleConfigurator(IModuleConfigurator):
    """独立测试模块配置器"""
    
    def configure(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置模块"""
        enabled = config.get("enabled", True)
        if not enabled:
            return
        
        # 注册服务
        container.register(
            TestService,
            TestService,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        errors = []
        
        if not isinstance(config.get("enabled", True), bool):
            errors.append("enabled must be boolean")
        
        return ValidationResult(len(errors) == 0, errors, [])
    
    def get_default_config(self) -> Dict[str, Any]:
        return {"enabled": True}
    
    def get_dependencies(self) -> list:
        return []
    
    def get_priority(self) -> int:
        return 10


class TestUnifiedDIFramework:
    """统一DI框架测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 确保框架是新的
        shutdown_framework()
    
    def teardown_method(self):
        """测试后清理"""
        shutdown_framework()
    
    def test_framework_initialization(self):
        """测试框架初始化"""
        framework = UnifiedDIFramework()
        container = framework.initialize()
        
        assert container is not None
        assert framework.get_container() is container
        assert framework.get_configuration_manager() is not None
        assert framework.get_template_manager() is not None
        assert framework.get_lifecycle_manager() is not None
    
    def test_module_configurator_registration(self):
        """测试模块配置器注册"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        configurator = TestConfigurator()
        framework.register_configurator("test", configurator)
        
        # 配置模块
        config = {"enabled": True, "service_name": "test_service"}
        framework.configure_module("test", config)
        
        # 验证服务已注册
        container = framework.get_container()
        service = container.get(TestService)
        assert service is not None
        assert service.name == "test_service"
    
    def test_configuration_validation(self):
        """测试配置验证"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        configurator = TestConfigurator()
        framework.register_configurator("test", configurator)
        
        # 测试有效配置
        valid_config = {"enabled": True, "service_name": "valid"}
        framework.configure_module("test", valid_config)
        
        # 测试无效配置
        invalid_config = {"enabled": "invalid"}  # 应该是布尔值
        with pytest.raises(ValueError):
            framework.configure_module("test", invalid_config)
    
    def test_template_configuration(self):
        """测试模板配置"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        # 注册模板
        from src.services.configuration.template_system import ConfigurationTemplate
        
        template_content = {
            "test": {
                "enabled": True,
                "service_name": "${SERVICE_NAME:template_service}"
            }
        }
        
        template = ConfigurationTemplate("test_template", template_content)
        framework.get_template_manager().register_template(template)
        
        # 注册配置器
        configurator = TestConfigurator()
        framework.register_configurator("test", configurator)
        
        # 从模板配置
        variables = {"SERVICE_NAME": "from_template"}
        framework.configure_from_template("test_template", variables)
        
        # 验证配置
        container = framework.get_container()
        service = container.get(TestService)
        assert service is not None
        assert service.name == "from_template"
    
    def test_lifecycle_management(self):
        """测试生命周期管理"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        configurator = TestConfigurator()
        framework.register_configurator("test", configurator)
        
        config = {"enabled": True, "service_name": "lifecycle_test"}
        framework.configure_module("test", config)
        
        # 获取生命周期管理器
        lifecycle_manager = framework.get_lifecycle_manager()
        
        # 手动注册服务到生命周期管理器
        container = framework.get_container()
        service = container.get(TestService)
        lifecycle_manager.register_service("test_service", service)
        
        # 测试生命周期操作
        assert lifecycle_manager.initialize_service("test_service") is True
        assert lifecycle_manager.start_service("test_service") is True
        assert lifecycle_manager.stop_service("test_service") is True
        assert lifecycle_manager.dispose_service("test_service") is True
    
    def test_dependency_analysis(self):
        """测试依赖分析"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        # 获取依赖分析结果
        analysis = framework.get_container().analyze_dependencies()
        
        assert analysis is not None
        assert isinstance(analysis.dependency_graph, dict)
        assert isinstance(analysis.circular_dependencies, list)
        assert isinstance(analysis.max_dependency_depth, int)
    
    def test_service_tracking(self):
        """测试服务追踪"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        configurator = TestConfigurator()
        framework.register_configurator("test", configurator)
        
        config = {"enabled": True, "service_name": "tracking_test"}
        framework.configure_module("test", config)
        
        # 获取服务
        container = framework.get_container()
        service = container.get(TestService)
        
        # 获取服务追踪器
        tracker = container.get_service_tracker()
        
        # 验证服务被追踪
        tracked_services = tracker.get_tracked_services()
        assert TestService in tracked_services
        assert service in tracked_services[TestService]
    
    def test_framework_status(self):
        """测试框架状态"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        configurator = TestConfigurator()
        framework.register_configurator("test", configurator)
        
        config = {"enabled": True, "service_name": "status_test"}
        framework.configure_module("test", config)
        
        # 获取框架状态
        status = framework.get_framework_status()
        
        assert status["initialized"] is True
        assert "container_metrics" in status
        assert "configuration_status" in status
        assert "lifecycle_statistics" in status
        assert "dependency_analysis" in status
    
    def test_optimization_suggestions(self):
        """测试优化建议"""
        framework = UnifiedDIFramework()
        framework.initialize()
        
        # 获取优化建议
        suggestions = framework.optimize_configuration()
        
        assert "suggestions" in suggestions
        assert "total_impact_score" in suggestions
        assert "high_priority_count" in suggestions
        assert isinstance(suggestions["suggestions"], list)
    
    def test_global_framework_functions(self):
        """测试全局框架函数"""
        # 初始化全局框架
        container = initialize_framework()
        assert container is not None
        
        # 注册配置器
        configurator = TestConfigurator()
        register_module_configurator("test", configurator)
        
        # 配置模块
        config = {"enabled": True, "service_name": "global_test"}
        framework = get_global_framework()
        framework.configure_module("test", config)
        
        # 获取服务
        service = get_service(TestService)
        assert service is not None
        assert service.name == "global_test"
        
        # 获取框架状态
        status = get_framework_status()
        assert status["initialized"] is True
        
        # 关闭框架
        shutdown_framework()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])