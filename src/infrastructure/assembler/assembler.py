"""组件组装器实现

提供配置驱动的组件组装功能，支持自动依赖解析和生命周期管理。
"""

import logging
from typing import Dict, Any, Optional, Type
from pathlib import Path

from infrastructure.graph.builder import GraphBuilder

from .interfaces import IComponentAssembler
from .exceptions import (
    AssemblyError,
    ConfigurationError
)
from ..container import IDependencyContainer, ServiceLifetime, DependencyContainer
from ..config.config_loader import IConfigLoader

logger = logging.getLogger(__name__)


class ComponentAssembler(IComponentAssembler):
    """简化的组件组装器实现
    
    根据架构文档建议，实现配置驱动的组装流程：
    1. 读取配置 → 验证Schema
    2. LLMFactory 根据 llm 配置创建/缓存模型实例
    3. ToolFactory 根据 tools 配置创建工具
    4. AgentFactory 组合 LLM + Tools + Prompt
    5. WorkflowBuilder 把 Agents 装配成 StateGraph
    6. SessionFactory 创建 Checkpointer
    """
    
    def __init__(
        self,
        container: Optional[IDependencyContainer] = None,
        config_loader: Optional[IConfigLoader] = None
    ):
        """初始化组件组装器
        
        Args:
            container: 依赖注入容器
            config_loader: 配置加载器
        """
        self.container = container or DependencyContainer()
        self.config_loader = config_loader
        self._factories: Dict[str, Any] = {}
        
        logger.info("ComponentAssembler初始化完成")
    
    def assemble(self, config: Dict[str, Any]) -> IDependencyContainer:
        """组装组件
        
        Args:
            config: 组装配置
            
        Returns:
            IDependencyContainer: 组装后的依赖注入容器
            
        Raises:
            AssemblyError: 组装失败时抛出
        """
        try:
            logger.info("开始组件组装过程")
            
            # 1. 验证配置
            errors = self.validate_configuration(config)
            if errors:
                raise ConfigurationError(f"配置验证失败: {'; '.join(errors)}")
            
            # 2. 设置环境
            app_config = config.get("application", {})
            env = app_config.get("environment", "default")
            self.container.set_environment(env)
            logger.info(f"设置环境为: {env}")
            
            # 3. 创建基础工厂
            self._create_base_factories(config)
            
            # 4. 创建业务工厂
            self._create_business_factories(config)
            
            # 5. 注册服务到容器
            self._register_services(config)
            
            logger.info("组件组装完成")
            return self.container
            
        except Exception as e:
            logger.error(f"组件组装失败: {e}")
            raise AssemblyError(f"组件组装失败: {e}")
    
    def register_services(self, services_config: Dict[str, Any]) -> None:
        """注册服务
        
        Args:
            services_config: 服务配置
        """
        # 此方法保留用于向后兼容，但实际组装逻辑在assemble方法中完成
        logger.info("register_services调用，但实际组装在assemble方法中完成")
    
    def register_dependencies(self, dependencies_config: Dict[str, Any]) -> None:
        """注册依赖关系
        
        Args:
            dependencies_config: 依赖配置
        """
        # 此方法保留用于向后兼容，但实际组装逻辑在assemble方法中完成
        logger.info("register_dependencies调用，但实际组装在assemble方法中完成")
    
    def resolve_dependencies(self, service_type: Type) -> Any:
        """解析依赖
        
        Args:
            service_type: 服务类型
            
        Returns:
            Any: 服务实例
        """
        try:
            return self.container.get(service_type)
        except Exception as e:
            raise AssemblyError(f"解析依赖 {service_type} 失败: {e}")
    
    def _resolve_type(self, service_name: str) -> Optional[Type]:
        """根据服务名称解析类型

        Args:
            service_name: 服务名称

        Returns:
            Optional[Type]: 服务类型，如果不存在则返回None
        """
        type_mapping = {
            "ILLMFactory": self._get_type_from_module("..llm.interfaces", "ILLMClientFactory"),
            "IToolFactory": self._get_type_from_module("...domain.tools.interfaces", "IToolFactory"),
            "IAgentFactory": self._get_type_from_module("...domain.agent.interfaces", "IAgentFactory"),
            "IToolExecutor": self._get_type_from_module("...infrastructure.tools.executor", "IToolExecutor"),
        }
        return type_mapping.get(service_name)
    
    def _get_type_from_module(self, module_path: str, type_name: str) -> Optional[Type]:
        """从模块中获取类型

        Args:
            module_path: 模块路径
            type_name: 类型名称

        Returns:
            Optional[Type]: 类型对象
        """
        try:
            module = __import__(module_path, fromlist=[type_name])
            return getattr(module, type_name, None)
        except (ImportError, AttributeError):
            return None
    
    def validate_configuration(self, config: Dict[str, Any]) -> list[str]:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if "version" not in config:
            errors.append("缺少版本信息")
        
        if "application" not in config:
            errors.append("缺少应用程序配置")
        
        if "components" not in config:
            errors.append("缺少组件配置")
        
        # 验证组件配置
        components_config = config.get("components", {})
        required_components = ["llm", "tools", "agents", "workflows", "sessions"]
        for component in required_components:
            if component not in components_config:
                errors.append(f"缺少组件配置: {component}")
        
        return errors
    
    def get_assembly_plan(self) -> Dict[str, Any]:
        """获取组装计划
        
        Returns:
            Dict[str, Any]: 组装计划
        """
        return {
            "factories": list(self._factories.keys()),
            "description": "简化的配置驱动组装流程"
        }
    
    def _create_base_factories(self, config: Dict[str, Any]) -> None:
        """创建基础工厂
        
        Args:
            config: 配置字典
        """
        logger.info("创建基础工厂")
        
        components_config = config.get("components", {})
        
        # 1. 创建LLM工厂
        llm_config = components_config.get("llm", {})
        from ..llm.factory import LLMFactory
        self._factories["llm_factory"] = LLMFactory(llm_config)
        
        # 2. 创建工具工厂
        tools_config = components_config.get("tools", {})
        from ...domain.tools.factory import ToolFactory
        
        # 创建工具工厂
        self._factories["tool_factory"] = ToolFactory(tools_config)
        
        logger.info("基础工厂创建完成")
    
    def _create_business_factories(self, config: Dict[str, Any]) -> None:
        """创建业务工厂
        
        Args:
            config: 配置字典
        """
        logger.info("创建业务工厂")
        
        components_config = config.get("components", {})
        
        # 3. 创建工具执行器
        from ...infrastructure.tools.executor import AsyncToolExecutor
        from ..logger.logger import Logger

        # 创建工具执行器
        tool_executor_logger = Logger("ToolExecutor")
        tool_executor = AsyncToolExecutor(
            tool_manager=self._factories["tool_factory"],  # 直接使用ToolFactory
            logger=tool_executor_logger
        )

        self._factories["tool_executor"] = tool_executor
        
        # 4. 创建图构建器
        workflows_config = components_config.get("workflows", {})
        from src.infrastructure.graph.builder import GraphBuilder
        from src.infrastructure.graph.registry import get_global_registry
        
        self._factories["graph_builder"] = GraphBuilder(
            node_registry=get_global_registry()
        )
        
        # 5. 创建状态管理器
        from ...domain.state.manager import StateManager
        self._factories["state_manager"] = StateManager()
        
        # 6. 创建会话工厂
        sessions_config = components_config.get("sessions", {})
        self._factories["session_factory"] = SessionFactory(sessions_config)
        
        logger.info("业务工厂创建完成")
    
    def _register_services(self, config: Dict[str, Any]) -> None:
        """注册服务到容器

        Args:
            config: 应用配置
        """
        logger.info("注册服务到容器")

        # 注册配置中定义的服务
        self._register_configured_services(config)
        
        # 注册基础服务
        from ..llm.interfaces import ILLMClientFactory
        self.container.register_instance(
            interface=ILLMClientFactory,
            instance=self._factories["llm_factory"]
        )
        
        from ...domain.tools.interfaces import IToolFactory
        self.container.register_instance(
            interface=IToolFactory,
            instance=self._factories["tool_factory"]
        )
        
        # 注册业务服务
        
        from src.infrastructure.graph.builder import GraphBuilder
        self.container.register_instance(
            interface=GraphBuilder,
            instance=self._factories["graph_builder"]
        )
        
        # 注册状态管理器
        from ...domain.state.interfaces import IStateManager
        self.container.register_instance(
            interface=IStateManager,
            instance=self._factories["state_manager"]
        )
        
        # 注册会话管理器
        # 注册会话相关服务
        from ...application.sessions.manager import SessionManager, ISessionManager
        from ...domain.sessions.store import ISessionStore
        from ...domain.sessions.store import FileSessionStore
        
        # 创建会话存储
        storage_path = Path(self._factories["session_factory"].storage_path)
        session_store = FileSessionStore(storage_path)
        
        # 创建工作流管理器
        from ...application.workflow.manager import WorkflowManager, IWorkflowManager
        from ...domain.workflow.config_manager import WorkflowConfigManager
        from ...domain.workflow.registry import WorkflowRegistry
        from ...domain.workflow.visualizer import WorkflowVisualizer
        
        # 创建工作流组件
        config_manager = WorkflowConfigManager(config_loader=self.config_loader)
        visualizer = WorkflowVisualizer()
        registry = WorkflowRegistry()
        
        workflow_manager = WorkflowManager(
            config_manager=config_manager,
            visualizer=visualizer,
            registry=registry
        )
        
        self.container.register_instance(
            interface=IWorkflowManager,
            instance=workflow_manager
        )
        
        self.container.register_instance(
            interface=ISessionStore,
            instance=session_store
        )
        
        # 注册Checkpoint相关服务
        from ...domain.checkpoint.interfaces import ICheckpointManager
        from ...application.checkpoint.manager import CheckpointManager, DefaultCheckpointPolicy
        from ...domain.checkpoint.config import CheckpointConfig
        from ...domain.checkpoint.interfaces import ICheckpointStore
        from ...infrastructure.checkpoint.memory_store import MemoryCheckpointStore
        # 创建Checkpoint存储
        checkpoint_store = MemoryCheckpointStore()
        
        # 创建Checkpoint配置
        checkpoint_config = CheckpointConfig(
            enabled=True,
            storage_type="memory",
            auto_save=True,
            save_interval=5,
            max_checkpoints=100
        )
        
        # 创建Checkpoint管理器
        checkpoint_manager = CheckpointManager(
            checkpoint_store=checkpoint_store,
            config=checkpoint_config
        )
        
        # 注册Checkpoint管理器
        self.container.register_instance(
            interface=ICheckpointManager,
            instance=checkpoint_manager
        )
        
        # 注册Thread相关服务
        from ...domain.threads.interfaces import IThreadManager
        from ...domain.threads.manager import ThreadManager
        from ...infrastructure.langgraph.adapter import LangGraphAdapter
        from ...infrastructure.threads.metadata_store import MemoryThreadMetadataStore, IThreadMetadataStore
        from ...application.threads.branch_manager import BranchManager
        from ...application.threads.snapshot_manager import SnapshotManager
        from ...application.threads.collaboration_manager import CollaborationManager
        from ...infrastructure.threads.branch_store import ThreadBranchStore, IThreadBranchStore
        from ...infrastructure.threads.snapshot_store import ThreadSnapshotStore, IThreadSnapshotStore
        
        # 创建Thread元数据存储
        thread_metadata_store = MemoryThreadMetadataStore()
        
        # 创建LangGraph适配器
        langgraph_adapter = LangGraphAdapter(use_memory_checkpoint=True)
        
        # 创建ThreadManager
        thread_manager = ThreadManager(thread_metadata_store, checkpoint_manager, langgraph_adapter)
        
        # 注册Thread服务
        self.container.register_instance(
            interface=IThreadManager,
            instance=thread_manager
        )
        
        self.container.register_instance(
            interface=IThreadMetadataStore,
            instance=thread_metadata_store
        )
        
        # 创建并注册分支存储
        branch_store = ThreadBranchStore()
        self.container.register_instance(
            interface=IThreadBranchStore,
            instance=branch_store
        )
        
        # 创建并注册快照存储
        snapshot_store = ThreadSnapshotStore()
        self.container.register_instance(
            interface=IThreadSnapshotStore,
            instance=snapshot_store
        )
        
        # 创建并注册分支管理器
        branch_manager = BranchManager(thread_manager, checkpoint_manager)
        self.container.register_instance(
            interface=BranchManager,
            instance=branch_manager
        )
        
        # 创建并注册快照管理器
        snapshot_manager = SnapshotManager(thread_manager, checkpoint_manager)
        self.container.register_instance(
            interface=SnapshotManager,
            instance=snapshot_manager
        )
        
        # 创建并注册协作管理器
        collaboration_manager = CollaborationManager(thread_manager, checkpoint_manager)
        self.container.register_instance(
            interface=CollaborationManager,
            instance=collaboration_manager
        )
        
        # 现在可以创建SessionManager，因为它需要thread_manager实例
        session_manager = SessionManager(
            thread_manager=thread_manager,  # 现在thread_manager已创建
            session_store=session_store,
            state_manager=self._factories["state_manager"]
        )
        
        self.container.register_instance(
            interface=ISessionManager,
            instance=session_manager
        )
        
        # Session-Thread映射器已删除，Session将直接管理多个Thread
        
        logger.info("服务注册完成")
    
    def _register_configured_services(self, config: Dict[str, Any]) -> None:
        """注册配置中定义的服务
        
        Args:
            config: 应用配置
        """
        services_config = config.get('services', {})
        if not services_config:
            return
        
        logger.info(f"注册配置中定义的服务: {list(services_config.keys())}")
        
        for service_name, service_config in services_config.items():
            try:
                # 解析服务接口和实现
                implementation_path = service_config.get('implementation')
                lifetime_str = service_config.get('lifetime', 'singleton')
                parameters = service_config.get('parameters', {})
                
                if not implementation_path:
                    logger.warning(f"服务 {service_name} 缺少 implementation 配置，跳过注册")
                    continue
                
                # 解析生命周期
                lifetime = ServiceLifetime.SINGLETON
                if lifetime_str.lower() == 'transient':
                    lifetime = ServiceLifetime.TRANSIENT
                elif lifetime_str.lower() == 'scoped':
                    lifetime = ServiceLifetime.SCOPED
                
                # 动态导入实现类
                module_path, class_name = implementation_path.rsplit('.', 1)
                import importlib
                module = importlib.import_module(module_path)
                implementation_class = getattr(module, class_name)
                
                # 动态导入接口类
                if '.' in service_name:
                    interface_module_path, interface_class_name = service_name.rsplit('.', 1)
                    interface_module = importlib.import_module(interface_module_path)
                    interface_class = getattr(interface_module, interface_class_name)
                else:
                    # 如果没有模块路径，尝试从已知的模块导入
                    if service_name == "IConfigLoader":
                        from ..config.config_loader import IConfigLoader
                        interface_class = IConfigLoader
                    elif service_name == "ICheckpointManager":
                        from ...domain.checkpoint.interfaces import ICheckpointManager
                        interface_class = ICheckpointManager
                    else:
                        raise ImportError(f"无法解析接口类: {service_name}")
                
                # 注册服务
                if parameters:
                    # 如果有参数，使用工厂方法
                    def create_service_func() -> Any:
                        return implementation_class(**parameters)
                    
                    self.container.register_factory(
                        interface=interface_class,
                        factory=create_service_func,
                        lifetime=lifetime
                    )
                else:
                    # 直接注册实现类
                    self.container.register(
                        interface=interface_class,
                        implementation=implementation_class,
                        lifetime=lifetime
                    )
                
                logger.debug(f"成功注册服务: {service_name} -> {implementation_path}")
                
            except Exception as e:
                logger.error(f"注册服务 {service_name} 失败: {e}")
                # 继续注册其他服务，不要因为一个服务失败而中断
                continue


class SessionFactory:
    """会话工厂实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化会话工厂
        
        Args:
            config: 会话配置
        """
        self.config = config
        self.storage_type = config.get("storage_type", "file")
        self.storage_path = config.get("storage_path", "sessions")
        self.auto_save = config.get("auto_save", True)
        
        logger.info(f"SessionFactory初始化完成，存储类型: {self.storage_type}")
    
    def create_session_store(self) -> Any:
        """创建会话存储实例
        
        Returns:
            会话存储实例
        """
        if self.storage_type == "file":
            from ...domain.sessions.store import FileSessionStore
            return FileSessionStore(Path(self.storage_path))
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    def create_checkpointer(self) -> Any:
        """创建检查点实例
        
        Returns:
            检查点实例
        """
        # 这里可以根据配置创建不同类型的检查点
        # 目前返回一个简单的检查点实现
        return SimpleCheckpointer(self.auto_save)
    

class SimpleCheckpointer:
    """简单的检查点实现"""
    
    def __init__(self, auto_save: bool = True):
        """初始化检查点
        
        Args:
            auto_save: 是否自动保存
        """
        self.auto_save = auto_save
        self.checkpoints: Dict[str, Any] = {}
    
    def save_checkpoint(self, checkpoint_id: str, data: Any) -> None:
        """保存检查点
        
        Args:
            checkpoint_id: 检查点ID
            data: 检查点数据
        """
        self.checkpoints[checkpoint_id] = data
    
    def load_checkpoint(self, checkpoint_id: str) -> Any:
        """加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点数据
        """
        return self.checkpoints.get(checkpoint_id)
    
    def list_checkpoints(self) -> list[str]:
        """列出所有检查点ID
        
        Returns:
            检查点ID列表
        """
        return list(self.checkpoints.keys())