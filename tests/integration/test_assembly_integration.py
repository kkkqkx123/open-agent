"""组装集成测试

测试组件组装器和应用启动器的集成功能。
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import cast

from src.bootstrap import ApplicationBootstrap
from src.infrastructure.assembler import ComponentAssembler
from src.infrastructure.container import DependencyContainer, ILifecycleAware
from infrastructure.config.loader.file_config_loader import FileConfigLoader


class TestAssemblyIntegration:
    """组装集成测试类"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "configs"
            config_dir.mkdir()
            
            # 创建应用配置文件
            app_config = config_dir / "application.yaml"
            app_config.write_text("""
version: "1.0"

application:
  name: "TestApp"
  version: "1.0.0"
  environment: "testing"

components:
  llm:
    factory: "infrastructure.llm.factory.LLMFactory"
    config_path: "configs/llms"
  
  tools:
    manager: "infrastructure.tools.manager.ToolManager"
    config_path: "configs/tools"
  
  agents: {}
  workflows: {}
  sessions: {}

services:
  IConfigLoader:
    implementation: "infrastructure.config_loader.YamlConfigLoader"
    lifetime: "singleton"
    parameters:
      base_path: "configs"
  
  ICheckpointManager:
    implementation: "application.checkpoint.manager.CheckpointManager"
    lifetime: "singleton"

dependencies:
  singletons:
    - "IConfigLoader"
    - "ILLMFactory"
    - "IToolManager"
    - "ICheckpointManager"
  
  scoped:
    - "IWorkflowBuilder"

environments:
  testing:
    log_level: "DEBUG"
    hot_reload: false
    debug: true

startup:
  health_check:
    enabled: false
""")
            
            # 创建LLM配置目录
            llm_dir = config_dir / "llms"
            llm_dir.mkdir()
            
            # 创建LLM配置文件
            llm_config = llm_dir / "_group.yaml"
            llm_config.write_text("""
default_llm:
  provider: "mock"
  model: "test-model"
  timeout: 30
""")
            
            # 创建工具配置目录
            tools_dir = config_dir / "tools"
            tools_dir.mkdir()
            
            # 创建工具配置文件
            tools_config = tools_dir / "_group.yaml"
            tools_config.write_text("""
default_tools:
  - "calculator"
  - "weather"
""")
            
            yield str(config_dir)
    
    def test_component_assembler_basic_functionality(self, temp_config_dir):
        """测试组件组装器基本功能"""
        # 创建配置加载器
        config_loader = FileConfigLoader(temp_config_dir)
        
        # 加载应用配置
        config_path = "application.yaml"
        app_config = config_loader.load(config_path)
        
        # 创建组装器
        container = DependencyContainer()
        assembler = ComponentAssembler(container, config_loader)
        
        # 组装组件
        assembled_container = assembler.assemble(app_config)
        
        # 验证容器
        assert assembled_container is not None
        assert assembled_container.get_environment() == "testing"
        
        # 验证服务注册
        from infrastructure.config.loader.file_config_loader import IConfigLoader
        assert assembled_container.has_service(IConfigLoader)
        
        # 获取服务
        config_loader_instance = assembled_container.get(IConfigLoader)
        assert config_loader_instance is not None
    
    def test_application_bootstrap_basic_functionality(self, temp_config_dir):
        """测试应用启动器基本功能"""
        # 创建启动器
        config_path = os.path.join(temp_config_dir, "application.yaml")
        bootstrap = ApplicationBootstrap(config_path)
        
        # 启动应用
        container = bootstrap.bootstrap()
        
        # 验证启动状态
        assert bootstrap.is_running()
        startup_time = bootstrap.get_startup_time()
        assert startup_time is not None
        assert startup_time > 0
        
        # 验证容器
        assert container is not None
        assert container.get_environment() == "testing"
        
        # 关闭应用
        bootstrap.shutdown()
        assert not bootstrap.is_running()
    
    def test_enhanced_container_lifecycle(self, temp_config_dir):
        """测试增强容器的生命周期管理"""
        from src.infrastructure.container import ILifecycleAware
        
        # 创建生命周期感知的服务
        class LifecycleTestService(ILifecycleAware):
            def __init__(self):
                self.initialized = False
                self.disposed = False
            
            def initialize(self):
                self.initialized = True
            
            def dispose(self):
                self.disposed = True
        
        # 创建容器
        container = DependencyContainer()
        
        # 注册服务
        container.register_instance(ITestService, LifecycleTestService())
        
        # 获取服务
        service = container.get(ITestService)
        # 类型断言，因为我们知道它是LifecycleTestService实例
        test_service = cast(LifecycleTestService, service)
        # 对于实例注册的服务，initialize()方法应该在注册时就被调用
        assert test_service.initialized
        assert not test_service.disposed
        
        # 释放容器
        container.dispose()
        assert test_service.disposed
    
    def test_enhanced_container_scoped_services(self, temp_config_dir):
        """测试增强容器的作用域服务"""
        from src.infrastructure.container import ServiceLifetime
        
        # 创建容器
        container = DependencyContainer()
        
        # 注册作用域服务
        container.register(ITestService, TestServiceImplementation, lifetime=ServiceLifetime.SCOPED)
        
        # 在不同作用域中获取服务
        with container.scope() as scope_id:
            service1 = container.get(ITestService)
            service2 = container.get(ITestService)
            assert service1 is service2  # 同一作用域内是同一实例
        
        # 在新作用域中获取服务
        with container.scope() as scope_id2:
            service3 = container.get(ITestService)
            assert service1 is not service3  # 不同作用域内是不同实例
    
    def test_circular_dependency_detection(self, temp_config_dir):
        """测试循环依赖检测"""
        from src.infrastructure.exceptions import CircularDependencyError
        
        # 创建容器
        container = DependencyContainer()
        
        # 注册有循环依赖的服务
        container.register(IServiceA, ServiceA)
        container.register(IServiceB, ServiceB)
        
        # 尝试获取服务应该抛出循环依赖错误
        with pytest.raises(CircularDependencyError):
            container.get(IServiceA)
    
    def test_dependency_analysis(self, temp_config_dir):
        """测试依赖关系分析"""
        # 创建容器
        container = DependencyContainer()
        
        # 注册服务
        container.register(IServiceA, ServiceA)
        container.register(IServiceB, ServiceB)
        container.register(IServiceC, ServiceC)
        
        # 分析依赖关系
        analysis = container.analyze_dependencies()
        
        # 验证分析结果
        assert "circular_dependencies" in analysis
        assert "dependency_depths" in analysis
        assert "root_services" in analysis
        assert "total_services" in analysis
        assert analysis["total_services"] == 3


# 测试接口定义
class ITestService:
    """测试服务接口"""
    pass


class IServiceA:
    """服务A接口"""
    pass


class IServiceB:
    """服务B接口"""
    pass


class IServiceC:
    """服务C接口"""
    pass


# 测试实现
class TestServiceImplementation(ITestService, ILifecycleAware):
    """测试服务实现"""
    def __init__(self):
        self.initialized = False
        self.disposed = False
    
    def initialize(self):
        self.initialized = True
    
    def dispose(self):
        self.disposed = True


class ServiceA(IServiceA):
    """服务A实现"""
    def __init__(self, service_b: IServiceB):
        self.service_b = service_b


class ServiceB(IServiceB):
    """服务B实现"""
    def __init__(self, service_a: IServiceA):
        self.service_a = service_a


class ServiceC(IServiceC):
    """服务C实现"""
    pass