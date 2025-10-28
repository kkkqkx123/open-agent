"""组件组装器实现

提供配置驱动的组件组装功能，支持自动依赖解析和生命周期管理。
"""

import logging
from typing import Dict, Any, Optional, Type
from pathlib import Path

from .interfaces import IComponentAssembler
from .exceptions import (
    AssemblyError,
    ConfigurationError
)
from ..container import IDependencyContainer, ServiceLifetime, DependencyContainer
from ..config_loader import IConfigLoader

logger = logging.getLogger(__name__)


class ComponentAssembler(IComponentAssembler):
    """简化的组件组装器实现
    
    根据架构文档建议，实现配置驱动的组装流程：
    1) 读取配置 → 验证Schema
    2) LLMFactory 根据 llm 配置创建/缓存模型实例
    3) ToolFactory 根据 tools 配置创建工具
    4) AgentFactory 组合 LLM + Tools + Prompt
    5) WorkflowBuilder 把 Agents 装配成 StateGraph
    6) SessionFactory 创建 Checkpointer
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
            
            # 2. 创建基础工厂
            self._create_base_factories(config)
            
            # 3. 创建业务工厂
            self._create_business_factories(config)
            
            # 4. 注册服务到容器
            self._register_services()
            
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
        # 此方法保留用于向后兼容，但实际组装逻辑在assemble方法中
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
            "IToolExecutor": self._get_type_from_module("..tools.interfaces", "IToolExecutor"),
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
        
        # 3. 创建Agent工厂
        agents_config = components_config.get("agents", {})
        from ...domain.agent.factory import AgentFactory
        from ...infrastructure.tools.executor import ToolExecutor
        from ..logger.logger import Logger
        
        # 创建工具执行器
        tool_executor_logger = Logger("ToolExecutor")
        tool_executor = ToolExecutor(
            tool_manager=self._factories["tool_factory"],  # 直接使用ToolFactory
            logger=tool_executor_logger
        )
        
        self._factories["agent_factory"] = AgentFactory(
            llm_factory=self._factories["llm_factory"],
            tool_executor=tool_executor
        )
        
        # 4. 创建工作流构建器
        workflows_config = components_config.get("workflows", {})
        from ...application.workflow.builder_adapter import WorkflowBuilderAdapter
        from src.infrastructure.graph.registry import get_global_registry
        
        self._factories["workflow_builder"] = WorkflowBuilderAdapter(
            node_registry=get_global_registry()
        )
        
        # 5. 创建状态管理器
        from ...domain.state.manager import StateManager
        self._factories["state_manager"] = StateManager()
        
        # 6. 创建会话工厂
        sessions_config = components_config.get("sessions", {})
        self._factories["session_factory"] = SessionFactory(sessions_config)
        
        logger.info("业务工厂创建完成")
    
    def _register_services(self) -> None:
        """注册服务到容器"""
        logger.info("注册服务到容器")
        
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
        from ...domain.agent.interfaces import IAgentFactory
        self.container.register_instance(
            interface=IAgentFactory,
            instance=self._factories["agent_factory"]
        )
        
        from ...application.workflow.interfaces import IWorkflowBuilder
        self.container.register_instance(
            interface=IWorkflowBuilder,
            instance=self._factories["workflow_builder"]
        )
        
        # 注册状态管理器
        from ...domain.state.interfaces import IStateManager
        self.container.register_instance(
            interface=IStateManager,
            instance=self._factories["state_manager"]
        )
        
        # 注册会话管理器
        from ...application.sessions.manager import SessionManager, ISessionManager
        from ...domain.sessions.store import ISessionStore
        from ...domain.sessions.store import FileSessionStore
        
        # 创建会话存储
        storage_path = Path(self._factories["session_factory"].storage_path)
        session_store = FileSessionStore(storage_path)
        
        # 创建工作流管理器
        from ...application.workflow.manager import WorkflowManager, IWorkflowManager
        workflow_manager = WorkflowManager(self._factories["workflow_builder"])
        
        session_manager = SessionManager(
            workflow_manager=workflow_manager,
            session_store=session_store
        )
        
        self.container.register_instance(
            interface=ISessionManager,
            instance=session_manager
        )
        
        self.container.register_instance(
            interface=IWorkflowManager,
            instance=workflow_manager
        )
        
        self.container.register_instance(
            interface=ISessionStore,
            instance=session_store
        )
        
        # 注册Thread相关服务
        from ...domain.threads.interfaces import IThreadManager
        from ...domain.threads.manager import ThreadManager
        from ...infrastructure.threads.metadata_store import MemoryThreadMetadataStore, IThreadMetadataStore
        from ...application.checkpoint.interfaces import ICheckpointManager
        from ...application.threads.session_thread_mapper import SessionThreadMapper, ISessionThreadMapper
        from ...application.threads.branch_manager import BranchManager
        from ...application.threads.snapshot_manager import SnapshotManager
        from ...application.threads.collaboration_manager import CollaborationManager
        from ...infrastructure.threads.branch_store import ThreadBranchStore, IThreadBranchStore
        from ...infrastructure.threads.snapshot_store import ThreadSnapshotStore, IThreadSnapshotStore
        
        # 创建Thread元数据存储
        thread_metadata_store = MemoryThreadMetadataStore()
        
        # 获取CheckpointManager（假设已经注册）
        checkpoint_manager = self.container.get(ICheckpointManager)
        
        # 创建ThreadManager
        thread_manager = ThreadManager(thread_metadata_store, checkpoint_manager)
        
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
        
        # 创建并注册Session-Thread映射器
        session_thread_mapper = SessionThreadMapper(session_manager, thread_manager)
        self.container.register_instance(
            interface=ISessionThreadMapper,
            instance=session_thread_mapper
        )
        
        logger.info("服务注册完成")


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