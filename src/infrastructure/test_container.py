"""测试容器实现"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, TypeVar, ContextManager
from contextlib import contextmanager
from types import TracebackType

from .container import IDependencyContainer, DependencyContainer
from .config.loader.file_config_loader import IConfigLoader, FileConfigLoader
from .environment import IEnvironmentChecker, EnvironmentChecker
from .architecture_check import ArchitectureChecker
from .exceptions import InfrastructureError


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
        self.container = DependencyContainer()
        self._setup_services()

    def _setup_services(self) -> None:
        """设置测试服务"""
        # 注册配置加载器
        self.container.register_factory(
            IConfigLoader,  # type: ignore
            lambda: FileConfigLoader(str(self.temp_path / "configs")),
            lifetime="singleton",
        )

        # 同时注册YamlConfigLoader具体类型，以便在测试中可以直接获取
        self.container.register_factory(
            FileConfigLoader,
            lambda: FileConfigLoader(str(self.temp_path / "configs")),
            lifetime="singleton",
        )

        # 注册环境检查器
        self.container.register(
            IEnvironmentChecker,  # type: ignore
            EnvironmentChecker,
            lifetime="singleton",
        )

        # 注册架构检查器
        self.container.register_factory(
            ArchitectureChecker,  # type: ignore
            lambda: ArchitectureChecker(str(self.temp_path / "src")),
            lifetime="singleton",
        )

        # 注册日志记录器（使用延迟导入以避免循环导入）
        def create_logger() -> Any:  # type: ignore
            from .logger import get_logger
            return get_logger("test")  # type: ignore
        
        # 从logger模块导入ILogger接口
        from .logger import ILogger
        self.container.register_factory(
            ILogger,  # type: ignore
            create_logger,
            lifetime="singleton",
        )

        # 注册工具管理器（使用延迟导入以避免循环导入）
        def create_tool_manager() -> Any:  # type: ignore
            from .tools import ToolManager
            from .logger import ILogger
            return ToolManager(
                self.container.get(IConfigLoader),  # type: ignore
                self.container.get(ILogger) # type: ignore
            )
        
        # 从tools模块导入IToolManager接口
        from src.interfaces.tools import IToolManager
        from src.services.tools.manager import ToolManager
        
        self.container.register_factory(
            IToolManager,
            create_tool_manager,
            lifetime="singleton",
        )
        
        # 同时注册ToolManager具体类型
        self.container.register_factory(
            ToolManager,
            create_tool_manager,
            lifetime="singleton",
        )

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

    def get_config_loader(self) -> IConfigLoader:
        """获取配置加载器"""
        return self.container.get(IConfigLoader)  # type: ignore

    def get_environment_checker(self) -> IEnvironmentChecker:
        """获取环境检查器"""
        return self.container.get(IEnvironmentChecker)  # type: ignore

    def get_architecture_checker(self) -> ArchitectureChecker:
        """获取架构检查器"""
        return self.container.get(ArchitectureChecker)

    def get_tool_manager(self) -> Any:  # type: ignore
        """获取工具管理器"""
        from .tools import ToolManager
        from .logger import ILogger, get_logger
        # 由于循环导入问题，我们直接创建一个新的工具管理器实例
        config_loader = self.container.get(IConfigLoader)  # type: ignore
        logger = get_logger("test")
        return ToolManager(config_loader, logger)

    def get_logger(self) -> Any:  # type: ignore
        """获取日志记录器"""
        from .logger import ILogger, get_logger
        # 由于循环导入问题，直接返回一个logger实例
        return get_logger("test")

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
