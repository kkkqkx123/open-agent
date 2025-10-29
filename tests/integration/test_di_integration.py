"""依赖注入集成测试

测试组件间协作和整体系统功能。
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.infrastructure.di_config import DIConfig, create_container, get_global_container, reset_global_container
from src.infrastructure.lifecycle_manager import LifecycleManager, get_global_lifecycle_manager, reset_global_lifecycle_manager
from src.infrastructure.container import IDependencyContainer, ServiceLifetime
from src.infrastructure.config_loader import IConfigLoader
from src.application.workflow.manager import IWorkflowManager
from src.application.sessions.manager import ISessionManager


class TestDIIntegration:
    """依赖注入集成测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """配置目录"""
        config_dir = temp_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        
        # 创建基本配置文件
        global_config = config_dir / "global.yaml"
        global_config.write_text("""
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

secrets:
  openai_api_key: "test_key"
        """)
        
        application_config = config_dir / "application.yaml"
        application_config.write_text("""
version: "1.0"
application:
  environment: test
  config_path: "configs"

assembly:
  components:
    - name: "workflow_manager"
      type: "IWorkflowManager"
      implementation: "WorkflowManager"
    - name: "session_manager"
      type: "ISessionManager"
      implementation: "SessionManager"

dependencies:
  workflow_manager:
    - "IConfigLoader"
    - "NodeRegistry"
  session_manager:
    - "IWorkflowManager"
    - "ISessionStore"
        """)
        
        return config_dir
    
    def test_di_config_initialization(self, config_dir):
        """测试DI配置初始化"""
        di_config = DIConfig()
        
        assert di_config.container is not None
        assert di_config._config_loader is None
        assert di_config._node_registry is None
        assert di_config._session_store is None
    
    def test_configure_core_services(self, config_dir):
        """测试配置核心服务"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        assert container is not None
        assert container.get_environment() == "test"
        
        # 验证核心服务已注册
        assert container.has_service(IConfigLoader)
        assert container.has_service(IWorkflowManager)
        assert container.has_service(ISessionManager)
    
    def test_create_container_function(self, config_dir):
        """测试创建容器函数"""
        container = create_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        assert container is not None
        assert container.get_environment() == "test"
        
        # 验证核心服务已注册
        assert container.has_service(IConfigLoader)
        assert container.has_service(IWorkflowManager)
        assert container.has_service(ISessionManager)
    
    def test_global_container_management(self, config_dir):
        """测试全局容器管理"""
        # 重置全局容器
        reset_global_container()
        
        # 获取全局容器
        container1 = get_global_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 再次获取应该返回同一个实例
        container2 = get_global_container()
        
        assert container1 is container2
        
        # 重置后应该创建新实例
        reset_global_container()
        container3 = get_global_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        assert container1 is not container3
    
    def test_service_resolution(self, config_dir):
        """测试服务解析"""
        container = create_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 解析配置加载器
        config_loader = container.get(IConfigLoader)
        assert config_loader is not None
        
        # 解析工作流管理器
        workflow_manager = container.get(IWorkflowManager)
        assert workflow_manager is not None
        
        # 解析会话管理器
        session_manager = container.get(ISessionManager)
        assert session_manager is not None
    
    def test_service_lifetime_singleton(self, config_dir):
        """测试单例服务生命周期"""
        container = create_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 获取两次配置加载器
        config_loader1 = container.get(IConfigLoader)
        config_loader2 = container.get(IConfigLoader)
        
        # 应该是同一个实例
        assert config_loader1 is config_loader2
    
    def test_service_lifetime_transient(self, config_dir):
        """测试瞬态服务生命周期"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册瞬态服务
        class TestService:
            pass
        
        container.register(
            TestService,
            TestService,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        # 获取两次应该返回不同实例
        service1 = container.get(TestService)
        service2 = container.get(TestService)
        
        assert service1 is not service2
    
    def test_additional_services_registration(self, config_dir):
        """测试额外服务注册"""
        additional_services = {
            "test_service": {
                "type": "tests.integration.test_di_integration.TestService",
                "implementation": "tests.integration.test_di_integration.TestService",
                "lifetime": ServiceLifetime.SINGLETON
            }
        }
        
        container = create_container(
            config_path=str(config_dir),
            environment="test",
            additional_services=additional_services
        )
        
        # 验证额外服务已注册
        from tests.integration.test_di_integration import TestService
        assert container.has_service(TestService)
    
    def test_configuration_validation(self, config_dir):
        """测试配置验证"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        validation_result = di_config.validate_configuration()
        
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
        assert len(validation_result["registered_services"]) >= 3  # 至少有3个核心服务
    
    def test_configuration_validation_missing_service(self, config_dir):
        """测试配置验证（缺少服务）"""
        di_config = DIConfig()
        # 只注册部分服务
        di_config._register_config_loader(str(config_dir))
        
        validation_result = di_config.validate_configuration()
        
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) > 0
        assert len(validation_result["warnings"]) > 0
    
    def test_lifecycle_manager_integration(self, config_dir):
        """测试生命周期管理器集成"""
        # 重置全局生命周期管理器
        reset_global_lifecycle_manager()
        
        # 创建容器
        container = create_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 获取生命周期管理器
        lifecycle_manager = get_global_lifecycle_manager()
        
        # 注册服务到生命周期管理器
        config_loader = container.get(IConfigLoader)
        if hasattr(config_loader, 'initialize') and hasattr(config_loader, 'dispose'):
            lifecycle_manager.register_service("config_loader", config_loader)
        
        # 初始化服务
        results = lifecycle_manager.initialize_all_services()
        
        # 验证初始化结果
        assert "config_loader" in results
        
        # 获取服务状态
        status = lifecycle_manager.get_service_status("config_loader")
        assert status is not None
    
    def test_environment_specific_services(self, config_dir):
        """测试环境特定服务"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册环境特定服务
        class TestService:
            pass
        
        container.register(
            TestService,
            TestService,
            environment="test",
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 在test环境下应该能获取服务
        container.set_environment("test")
        assert container.has_service(TestService)
        
        # 在其他环境下应该不能获取服务
        container.set_environment("production")
        assert not container.has_service(TestService)
    
    def test_container_clear(self, config_dir):
        """测试容器清理"""
        container = create_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 验证服务已注册
        assert container.has_service(IConfigLoader)
        
        # 清理容器
        container.clear()
        
        # 验证服务已清理
        assert not container.has_service(IConfigLoader)
    
    def test_error_handling_missing_dependency(self, config_dir):
        """测试错误处理（缺少依赖）"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册有依赖的服务
        class ServiceWithDependency:
            def __init__(self, dependency: IMissingService):
                self.dependency = dependency
        
        class IMissingService:
            pass
        
        container.register(IMissingService, ServiceWithDependency)
        
        # 尝试获取服务应该失败
        with pytest.raises(Exception):
            container.get(IMissingService)
    
    def test_circular_dependency_detection(self, config_dir):
        """测试循环依赖检测"""
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册循环依赖的服务
        class ServiceA:
            def __init__(self, service_b: 'ServiceB'):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        container.register(ServiceA, ServiceA)
        container.register(ServiceB, ServiceB)
        
        # 尝试获取服务应该检测到循环依赖
        with pytest.raises(Exception):
            container.get(ServiceA)


class TestService:
    """测试服务类"""
    pass


class IMissingService:
    """缺失服务接口"""
    pass


if __name__ == "__main__":
    pytest.main([__file__])