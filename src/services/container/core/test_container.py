"""测试容器实现"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, TypeVar, ContextManager, Callable
from contextlib import contextmanager
from types import TracebackType

from src.interfaces.container import IDependencyContainer
from src.interfaces.logger import ILogger
from src.interfaces.common_infra import ServiceLifetime

# 导入日志绑定
from ..bindings.logger_bindings import register_test_logger_services

# 泛型类型变量
_ServiceT = TypeVar("_ServiceT")


class TestContainer(ContextManager["TestContainer"]):
    """测试容器，用于集成测试"""

    __test__ = False  # 告诉pytest这不是一个测试类

    def __enter__(self) -> "TestContainer":
        """进入上下文管理器"""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """退出上下文管理器，自动清理"""
        self.cleanup()

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        # 注意：这里需要使用实际的容器实现，暂时使用占位符
        # 在实际使用时需要替换为正确的容器实现
        self.container = self._create_container()
        
        # 创建配置加载器代理类
        class IConfigLoaderProxy:
            pass
        
        # 创建工具管理器代理类
        class IToolManagerProxy:
            pass
        
        # 保存代理类供 getter 方法使用
        self.IConfigLoaderProxy = IConfigLoaderProxy
        self.IToolManagerProxy = IToolManagerProxy
        
        self._setup_services()

    def _create_container(self) -> IDependencyContainer:
        """创建依赖注入容器
        
        注意：这里需要根据实际的容器实现进行调整
        """
        # 临时解决方案：创建一个简单的容器模拟
        # 在实际使用时需要替换为真正的容器实现
        class MockContainer(IDependencyContainer):
            def __init__(self) -> None:
                self._services: Dict[Type[Any], Any] = {}
                self._environment = "default"
            
            def register_factory(
                self,
                interface: Type[Any],
                factory: Callable[[], Any],
                environment: str = "default",
                lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                metadata: Optional[Dict[str, Any]] = None
            ) -> None:
                self._services[interface] = factory
            
            def register(
                self,
                interface: Type[Any],
                implementation: Type[Any],
                environment: str = "default",
                lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                metadata: Optional[Dict[str, Any]] = None
            ) -> None:
                self._services[interface] = implementation
            
            def register_instance(
                self, 
                interface: Type[Any], 
                instance: Any, 
                environment: str = "default",
                metadata: Optional[Dict[str, Any]] = None
            ) -> None:
                self._services[interface] = instance
            
            def register_factory_with_delayed_resolution(
                self,
                interface: Type[Any],
                factory_factory: Callable[[], Callable[..., Any]],
                environment: str = "default",
                lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                metadata: Optional[Dict[str, Any]] = None
            ) -> None:
                factory = factory_factory()
                self._services[interface] = factory
            
            def resolve_dependencies(self, service_types: List[Type[Any]]) -> Dict[Type[Any], Any]:
                result: Dict[Type[Any], Any] = {}
                for service_type in service_types:
                    result[service_type] = self.get(service_type)
                return result
            
            def get(self, service_type: Type[_ServiceT]) -> _ServiceT:
                if service_type in self._services:
                    service = self._services[service_type]
                    if callable(service) and not isinstance(service, type):
                        return service()  # type: ignore
                    elif isinstance(service, type):
                        return service()  # type: ignore
                    return service  # type: ignore
                raise ValueError(f"Service {service_type} not registered")
            
            def try_get(self, service_type: Type[_ServiceT]) -> Optional[_ServiceT]:
                try:
                    return self.get(service_type)
                except ValueError:
                    return None
            
            def has_service(self, service_type: Type[Any]) -> bool:
                return service_type in self._services
            
            def get_environment(self) -> str:
                return self._environment
            
            def set_environment(self, env: str) -> None:
                self._environment = env
            
            def clear(self) -> None:
                self._services.clear()
            
            def validate_configuration(self) -> Any:
                # 返回简单的验证结果
                return type('ValidationResult', (), {'is_valid': True, 'errors': []})()
            
            def get_registration_count(self) -> int:
                return len(self._services)
            
            def get_registered_services(self) -> List[Type]:
                return list(self._services.keys())
            
            def create_test_isolation(self, isolation_id: Optional[str] = None) -> IDependencyContainer:
                # 为测试隔离创建新容器
                isolated_container = MockContainer()
                isolated_container.set_environment(f"test_{isolation_id or 'default'}")
                return isolated_container
            
            def reset_test_state(self, isolation_id: Optional[str] = None) -> None:
                # 重置测试状态
                test_env = f"test_{isolation_id or 'default'}"
                if self.get_environment() == test_env:
                    self.clear()
        
        return MockContainer()

    def _setup_services(self) -> None:
        """设置测试服务"""
        # 注册配置加载器
        self.container.register_factory(
            self.IConfigLoaderProxy,
            lambda: self._create_config_loader(),
            lifetime=ServiceLifetime.SINGLETON,
        )

        # 注册日志记录器 - 使用自定义Logger实现
        test_config = {
            "log_level": "DEBUG",
            "log_outputs": [
                {
                    "type": "console",
                    "level": "DEBUG",
                    "format": "text"
                }
            ],
            "secret_patterns": [
                "sk-[a-zA-Z0-9]{20,}",
                "\\w+@\\w+\\.\\w+"
            ]
        }
        register_test_logger_services(self.container, test_config)

        # 注册工具管理器
        def create_tool_manager() -> Any:
            # 简化的工具管理器创建
            class MockToolManager:
                def __init__(self, config_loader: Any, logger: ILogger) -> None:
                    self.config_loader = config_loader
                    self.logger = logger
                
                def get_tool(self, tool_name: str) -> None:
                    return None
            
            config_loader = self.container.get(self.IConfigLoaderProxy)
            logger = self.container.get(ILogger)
            return MockToolManager(config_loader, logger)
        
        self.container.register_factory(
            self.IToolManagerProxy,
            create_tool_manager,
            lifetime=ServiceLifetime.SINGLETON,
        )

    def _create_config_loader(self):
        """创建配置加载器"""
        class MockConfigLoader:
            def __init__(self, config_path):
                self.config_path = config_path
                self._configs = {}
            
            def load_config(self, config_name):
                return self._configs.get(config_name, {})
            
            def save_config(self, config_name, config_data):
                self._configs[config_name] = config_data
        
        return MockConfigLoader(str(self.temp_path / "configs"))

    def get_container(self) -> IDependencyContainer:
        """获取依赖注入容器"""
        return self.container

    def create_test_config(self, config_path: str, content: Dict[str, Any]) -> None:
        """创建测试配置文件"""
        import yaml  # type: ignore

        config_file = self.temp_path / config_path
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True)

    def create_test_file(self, file_path: str, content: str) -> None:
        """创建测试文件"""
        test_file = self.temp_path / file_path
        test_file.parent.mkdir(parents=True, exist_ok=True)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

    def create_test_module(self, module_path: str, content: str) -> None:
        """创建测试模块"""
        module_file = self.temp_path / module_path
        module_file.parent.mkdir(parents=True, exist_ok=True)

        # 确保有__init__.py文件
        init_file = module_file.parent / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        with open(module_file, "w", encoding="utf-8") as f:
            f.write(content)

    def get_config_loader(self) -> Any:
        """获取配置加载器"""
        return self.container.get(self.IConfigLoaderProxy)
    
    def get_tool_manager(self) -> Any:
        """获取工具管理器"""
        return self.container.get(self.IToolManagerProxy)
    
    def get_logger(self) -> ILogger:
        """获取日志记录器"""
        return self.container.get(ILogger)

    def setup_basic_configs(self) -> None:
        """设置基础配置文件"""
        # 全局配置
        self.create_test_config(
            "configs/global.yaml",
            {
                "log_level": "INFO",
                "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
                "secret_patterns": ["sk-[a-zA-Z0-9]{20,}", "\\w+@\\w+\\.\\w+"],
                "env": "test",
                "debug": True,
            },
        )

        # LLM组配置
        self.create_test_config(
            "configs/llms/_group.yaml",
            {
                "openai_group": {
                    "base_url": "https://api.openai.com/v1",
                    "headers": {"User-Agent": "ModularAgent/1.0"},
                    "parameters": {"temperature": 0.7, "max_tokens": 2000},
                }
            },
        )

        # Agent组配置
        self.create_test_config(
            "configs/agents/_group.yaml",
            {
                "default_group": {
                    "tool_sets": ["basic"],
                    "system_prompt": "You are a helpful assistant.",
                }
            },
        )

        # 工具集组配置
        self.create_test_config(
            "configs/tool-sets/_group.yaml",
            {"basic_tools": {"tools": ["search", "calculator"], "timeout": 30}},
        )

    def setup_basic_modules(self) -> None:
        """设置基础模块结构"""
        # 创建领域层模块
        self.create_test_module("src/domain/__init__.py", "")
        self.create_test_module(
            "src/domain/entities.py",
            """
from dataclasses import dataclass

@dataclass
class Entity:
    id: str
    name: str
""",
        )

        # 创建基础设施层模块
        self.create_test_module("src/infrastructure/__init__.py", "")
        self.create_test_module(
            "src/infrastructure/repository.py",
            """
from src.domain.entities import Entity

class Repository:
    def get(self, id: str) -> Entity:
        pass
""",
        )

        # 创建应用层模块
        self.create_test_module("src/application/__init__.py", "")
        self.create_test_module(
            "src/application/service.py",
            """
from src.domain.entities import Entity
from src.infrastructure.repository import Repository

class ApplicationService:
    def __init__(self, repository: Repository):
        self.repository = repository
    
    def get_entity(self, id: str) -> Entity:
        return self.repository.get(id)
""",
        )

        # 创建表现层模块
        self.create_test_module("src/presentation/__init__.py", "")
        self.create_test_module(
            "src/presentation/cli.py",
            """
from src.application.service import ApplicationService

class CLI:
    def __init__(self, service: ApplicationService):
        self.service = service
""",
        )

    def cleanup(self) -> None:
        """清理测试环境"""
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

    @contextmanager
    def context(self) -> Any:
        """上下文管理器，自动清理（保留向后兼容性）"""
        try:
            yield self
        finally:
            self.cleanup()

    def set_environment_variable(self, name: str, value: str) -> None:
        """设置环境变量"""
        os.environ[name] = value

    def clear_environment_variable(self, name: str) -> None:
        """清除环境变量"""
        if name in os.environ:
            del os.environ[name]

    def create_test_files_with_violations(self) -> None:
        """创建有架构违规的测试文件"""
        # 领域层违规：依赖基础设施层
        self.create_test_module(
            "src/domain/violation.py",
            """
from src.infrastructure.repository import Repository  # 违规：领域层不应依赖基础设施层

class DomainViolation:
    def __init__(self):
        self.repo = Repository()
""",
        )

        # 基础设施层违规：依赖应用层
        self.create_test_module(
            "src/infrastructure/violation.py",
            """
from src.application.service import ApplicationService  # 违规：基础设施层不应依赖应用层

class InfrastructureViolation:
    def __init__(self):
        self.service = ApplicationService(None)
""",
        )

        # 创建循环依赖
        self.create_test_module(
            "src/module_a.py",
            """
from src.module_b import ModuleB

class ModuleA:
    def __init__(self):
        self.module_b = ModuleB()
""",
        )

        self.create_test_module(
            "src/module_b.py",
            """
from src.module_a import ModuleA

class ModuleB:
    def __init__(self):
        self.module_a = ModuleA()
""",
        )