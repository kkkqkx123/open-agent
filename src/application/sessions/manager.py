"""会话管理器 - 重构版本

专注于用户交互追踪，负责：
1. 会话生命周期管理
2. 用户交互历史追踪
3. 多Thread协调（通过ThreadService委托）
4. 会话级状态管理
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Tuple, Dict, AsyncGenerator, Coroutine
from pathlib import Path
import uuid
import json
import hashlib
import logging
from datetime import datetime
from dataclasses import dataclass

from ..threads.interfaces import IThreadService
from ..workflow.manager import IWorkflowManager
from ...infrastructure.graph.config import GraphConfig as WorkflowConfig
from ...infrastructure.graph.states import WorkflowState
from ...domain.sessions.store import ISessionStore
from ...domain.tools.interfaces import ToolResult
from .git_manager import IGitManager
from ...domain.state.interfaces import IStateManager

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class UserRequest:
    """用户请求数据模型"""
    request_id: str
    user_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class UserInteraction:
    """用户交互数据模型"""
    interaction_id: str
    session_id: str
    thread_id: Optional[str]
    interaction_type: str  # "user_input", "system_response", "error", etc.
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: Optional[str]
    thread_ids: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class ISessionManager(ABC):
    """重构后的会话管理器接口"""

    @abstractmethod
    async def create_session(self, user_request: UserRequest) -> str:
        """创建用户会话"""
        pass

    @abstractmethod
    async def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """获取会话上下文"""
        pass

    @abstractmethod
    async def track_user_interaction(self, session_id: str, interaction: UserInteraction) -> None:
        """追踪用户交互"""
        pass

    @abstractmethod
    async def get_interaction_history(self, session_id: str, limit: Optional[int] = None) -> List[UserInteraction]:
        """获取交互历史"""
        pass

    @abstractmethod
    async def coordinate_threads(self, session_id: str, thread_configs: List[Dict[str, Any]]) -> Dict[str, str]:
        """协调多个Thread执行"""
        pass

    @abstractmethod
    async def execute_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """在会话中执行工作流"""
        pass

    @abstractmethod
    async def stream_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], Any]:
        """在会话中流式执行工作流"""
        pass

    # === 兼容性方法 ===

    @abstractmethod
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass

    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        pass

    @abstractmethod
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        pass

    @abstractmethod
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        pass


class SessionManager(ISessionManager):
    """会话管理器实现 - 重构版本
    
    专注于用户交互追踪，通过ThreadService委托Thread管理
    """

    def __init__(
        self,
        thread_service: IThreadService,  # 改为依赖ThreadService
        session_store: ISessionStore,
        git_manager: Optional[IGitManager] = None,
        storage_path: Optional[Path] = None,
        state_manager: Optional[IStateManager] = None
    ) -> None:
        """初始化会话管理器

        Args:
            thread_service: Thread服务（核心依赖）
            session_store: 会话存储
            git_manager: Git管理器（可选）
            storage_path: 存储路径（可选）
            state_manager: 状态管理器（可选）
        """
        self.thread_service = thread_service  # 使用ThreadService而不是ThreadManager
        self.session_store = session_store
        self.git_manager = git_manager
        self.storage_path = storage_path or Path("./sessions")
        self.state_manager = state_manager

        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("SessionManager初始化完成（重构版本）")

    async def create_session(self, user_request: UserRequest) -> str:
        """创建用户会话"""
        # 生成会话ID
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        # 创建会话目录
        session_dir = self.storage_path / session_id
        session_dir.mkdir(exist_ok=True)

        # 初始化Git仓库（如果提供了Git管理器）
        if self.git_manager:
            self.git_manager.init_repo(session_dir)

        # 创建会话上下文
        session_context = SessionContext(
            session_id=session_id,
            user_id=user_request.user_id,
            thread_ids=[],
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                "request_id": user_request.request_id,
                "initial_content": user_request.content,
                **user_request.metadata
            }
        )

        # 保存会话数据
        session_data = {
            "context": self._serialize_session_context(session_context),
            "interactions": [],
            "thread_configs": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.session_store.save_session(session_id, session_data)

        # 追踪初始用户交互
        initial_interaction = UserInteraction(
            interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            thread_id=None,
            interaction_type="user_request",
            content=user_request.content,
            metadata=user_request.metadata,
            timestamp=datetime.now()
        )
        await self.track_user_interaction(session_id, initial_interaction)

        # 提交初始状态到Git（如果提供了Git管理器）
        if self.git_manager:
            self.git_manager.commit_changes(
                session_dir,
                "初始化用户会话",
                {"session_id": session_id, "request_id": user_request.request_id}
            )

        logger.info(f"创建用户会话成功: {session_id}, user_id: {user_request.user_id}")
        return session_id

    async def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """获取会话上下文"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return None

        return self._deserialize_session_context(session_data["context"])

    async def track_user_interaction(self, session_id: str, interaction: UserInteraction) -> None:
        """追踪用户交互"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            logger.warning(f"会话不存在: {session_id}")
            return

        # 添加交互记录
        interactions = session_data.get("interactions", [])
        interactions.append(self._serialize_user_interaction(interaction))
        session_data["interactions"] = interactions
        session_data["updated_at"] = datetime.now().isoformat()

        # 保存会话数据
        self.session_store.save_session(session_id, session_data)

        # 提交到Git（如果提供了Git管理器）
        if self.git_manager:
            session_dir = self.storage_path / session_id
            self.git_manager.commit_changes(
                session_dir,
                f"追踪用户交互: {interaction.interaction_type}",
                {"session_id": session_id, "interaction_id": interaction.interaction_id}
            )

        logger.debug(f"追踪用户交互成功: {session_id}, {interaction.interaction_type}")

    async def get_interaction_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[UserInteraction]:
        """获取交互历史"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return []

        interactions_data = session_data.get("interactions", [])
        
        # 应用限制
        if limit and len(interactions_data) > limit:
            interactions_data = interactions_data[-limit:]  # 获取最新的交互

        # 反序列化交互记录
        interactions = []
        for interaction_data in interactions_data:
            interaction = self._deserialize_user_interaction(interaction_data)
            if interaction:
                interactions.append(interaction)

        return interactions

    async def coordinate_threads(self, session_id: str, thread_configs: List[Dict[str, Any]]) -> Dict[str, str]:
        """协调多个Thread执行"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            raise ValueError(f"会话不存在: {session_id}")

        thread_ids = {}
        session_context = self._deserialize_session_context(session_data["context"])

        # 创建Thread
        for thread_config in thread_configs:
            thread_name = thread_config["name"]
            config_path = thread_config.get("config_path")
            initial_state = thread_config.get("initial_state")

            # 委托ThreadService创建Thread
            if config_path:
                thread_id = await self.thread_service.create_thread_from_config(
                    config_path, 
                    metadata={"session_id": session_id, "thread_name": thread_name}
                )
            else:
                # 使用graph_id创建
                graph_id = thread_config.get("graph_id", "default")
                thread_id = await self.thread_service.create_thread(
                    graph_id,
                    metadata={"session_id": session_id, "thread_name": thread_name}
                )

            # 如果有初始状态，设置到Thread
            if initial_state:
                await self.thread_service.update_thread_state(thread_id, initial_state)

            thread_ids[thread_name] = thread_id
            session_context.thread_ids.append(thread_id)

            # 追踪Thread创建交互
            interaction = UserInteraction(
                interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                thread_id=thread_id,
                interaction_type="thread_created",
                content=f"创建Thread: {thread_name}",
                metadata={"thread_name": thread_name, "config_path": config_path},
                timestamp=datetime.now()
            )
            await self.track_user_interaction(session_id, interaction)

        # 更新会话上下文
        session_context.updated_at = datetime.now()
        session_data["context"] = self._serialize_session_context(session_context)
        session_data["thread_configs"] = {config["name"]: config for config in thread_configs}
        session_data["updated_at"] = datetime.now().isoformat()
        self.session_store.save_session(session_id, session_data)

        logger.info(f"协调Thread执行成功: {session_id}, 创建了{len(thread_ids)}个Thread")
        return thread_ids

    async def execute_workflow_in_session(
        self, 
        session_id: str, 
        thread_name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """在会话中执行工作流"""
        # 获取会话上下文
        session_context = await self.get_session_context(session_id)
        if not session_context:
            raise ValueError(f"会话不存在: {session_id}")

        # 查找Thread ID
        thread_id = None
        session_data = self.session_store.get_session(session_id)
        if session_data is None:
            raise ValueError(f"会话 {session_id} 不存在")
        thread_configs = session_data.get("thread_configs", {})
        
        if thread_name in thread_configs:
            # 从thread_configs中查找
            thread_config = thread_configs[thread_name]
            config_path = thread_config.get("config_path")
            
            # 查找对应的thread_id
            for tid in session_context.thread_ids:
                thread_info = await self.thread_service.get_thread_info(tid)
                if thread_info and thread_info.get("metadata", {}).get("thread_name") == thread_name:
                    thread_id = tid
                    break
        else:
            raise ValueError(f"Thread不存在: {thread_name}")

        if not thread_id:
            raise ValueError(f"找不到Thread: {thread_name}")

        # 追踪执行开始交互
        interaction = UserInteraction(
            interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            thread_id=thread_id,
            interaction_type="workflow_execution_start",
            content=f"开始执行工作流: {thread_name}",
            metadata={"thread_name": thread_name, "config": config},
            timestamp=datetime.now()
        )
        await self.track_user_interaction(session_id, interaction)

        try:
            # 委托ThreadService执行工作流
            result = await self.thread_service.execute_workflow(thread_id, config)

            # 追踪执行成功交互
            success_interaction = UserInteraction(
                interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                thread_id=thread_id,
                interaction_type="workflow_execution_success",
                content=f"工作流执行成功: {thread_name}",
                metadata={"thread_name": thread_name, "result_keys": list(result.keys()) if isinstance(result, dict) else []},
                timestamp=datetime.now()
            )
            await self.track_user_interaction(session_id, success_interaction)

            return result  # type: ignore

        except Exception as e:
            # 追踪执行错误交互
            error_interaction = UserInteraction(
                interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                thread_id=thread_id,
                interaction_type="workflow_execution_error",
                content=f"工作流执行失败: {thread_name}",
                metadata={"thread_name": thread_name, "error": str(e)},
                timestamp=datetime.now()
            )
            await self.track_user_interaction(session_id, error_interaction)
            raise

    async def stream_workflow_in_session(  # type: ignore
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], Any]:
        """在会话中流式执行工作流"""
        # 获取会话上下文
        session_context = await self.get_session_context(session_id)
        if not session_context:
            raise ValueError(f"会话不存在: {session_id}")

        # 查找Thread ID（类似execute_workflow_in_session）
        thread_id = None
        session_data = self.session_store.get_session(session_id)
        if session_data is None:
            raise ValueError(f"会话 {session_id} 不存在")
        thread_configs = session_data.get("thread_configs", {})
        
        if thread_name in thread_configs:
            thread_config = thread_configs[thread_name]
            
            # 查找对应的thread_id
            for tid in session_context.thread_ids:
                thread_info = await self.thread_service.get_thread_info(tid)
                if thread_info and thread_info.get("metadata", {}).get("thread_name") == thread_name:
                    thread_id = tid
                    break
        else:
            raise ValueError(f"Thread不存在: {thread_name}")

        if not thread_id:
            raise ValueError(f"找不到Thread: {thread_name}")

        # 追踪流式执行开始交互
        interaction = UserInteraction(
            interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            thread_id=thread_id,
            interaction_type="workflow_stream_start",
            content=f"开始流式执行工作流: {thread_name}",
            metadata={"thread_name": thread_name, "config": config},
            timestamp=datetime.now()
        )
        await self.track_user_interaction(session_id, interaction)

        try:
            # 委托ThreadService流式执行工作流
            async for state in await self.thread_service.stream_workflow(thread_id, config):
                yield state

            # 追踪流式执行完成交互
            completion_interaction = UserInteraction(
                interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                thread_id=thread_id,
                interaction_type="workflow_stream_complete",
                content=f"流式工作流执行完成: {thread_name}",
                metadata={"thread_name": thread_name},
                timestamp=datetime.now()
            )
            await self.track_user_interaction(session_id, completion_interaction)

        except Exception as e:
            # 追踪流式执行错误交互
            error_interaction = UserInteraction(
                interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                thread_id=thread_id,
                interaction_type="workflow_stream_error",
                content=f"流式工作流执行失败: {thread_name}",
                metadata={"thread_name": thread_name, "error": str(e)},
                timestamp=datetime.now()
            )
            await self.track_user_interaction(session_id, error_interaction)
            raise

    # === 向后兼容方法 ===

    async def create_session_with_threads(
        self,
        workflow_configs: Dict[str, str],  # 线程名 -> 工作流配置路径
        dependencies: Optional[Dict[str, List[str]]] = None,  # 线程依赖关系
        agent_config: Optional[dict[str, Any]] = None,
        initial_states: Optional[Dict[str, WorkflowState]] = None # 每个线程的初始状态
    ) -> str:
        """原子性创建Session和多个Thread（向后兼容）"""
        # 创建用户请求
        user_request = UserRequest(
            request_id=f"request_{uuid.uuid4().hex[:8]}",
            user_id=None,
            content=f"创建多线程会话: {list(workflow_configs.keys())}",
            metadata={
                "workflow_configs": workflow_configs,
                "dependencies": dependencies,
                "agent_config": agent_config
            },
            timestamp=datetime.now()
        )

        # 创建会话
        session_id = await self.create_session(user_request)

        # 准备Thread配置
        thread_configs_list = []
        for thread_name, config_path in workflow_configs.items():
            thread_config = {
                "name": thread_name,
                "config_path": config_path,
                "initial_state": initial_states.get(thread_name) if initial_states else None
            }
            thread_configs_list.append(thread_config)

        # 协调Thread创建
        await self.coordinate_threads(session_id, thread_configs_list)

        return session_id

    def create_session_legacy(
        self,
        workflow_config_path: str,
        agent_config: Optional[dict[str, Any]] = None,
        initial_state: Optional[WorkflowState] = None
    ) -> str:
        """创建新会话（向后兼容）"""
        import asyncio
        
        # 创建用户请求
        user_request = UserRequest(
            request_id=f"request_{uuid.uuid4().hex[:8]}",
            user_id=None,
            content=f"创建会话: {workflow_config_path}",
            metadata={
                "workflow_config_path": workflow_config_path,
                "agent_config": agent_config
            },
            timestamp=datetime.now()
        )

        # 异步创建会话
        loop = asyncio.get_event_loop()
        session_id = loop.run_until_complete(self.create_session(user_request))
        
        # 创建单个线程
        thread_config = {
            "name": "default_thread",
            "config_path": workflow_config_path,
            "initial_state": initial_state
        }
        
        # 协调Thread创建
        loop.run_until_complete(self.coordinate_threads(session_id, [thread_config]))
        
        return session_id

    # === 私有辅助方法 ===

    def _serialize_session_context(self, context: SessionContext) -> Dict[str, Any]:
        """序列化会话上下文"""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "thread_ids": context.thread_ids,
            "status": context.status,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "metadata": context.metadata
        }

    def _deserialize_session_context(self, data: Dict[str, Any]) -> SessionContext:
        """反序列化会话上下文"""
        return SessionContext(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            thread_ids=data.get("thread_ids", []),
            status=data.get("status", "active"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )

    def _serialize_user_interaction(self, interaction: UserInteraction) -> Dict[str, Any]:
        """序列化用户交互"""
        return {
            "interaction_id": interaction.interaction_id,
            "session_id": interaction.session_id,
            "thread_id": interaction.thread_id,
            "interaction_type": interaction.interaction_type,
            "content": interaction.content,
            "metadata": interaction.metadata,
            "timestamp": interaction.timestamp.isoformat()
        }

    def _deserialize_user_interaction(self, data: Dict[str, Any]) -> Optional[UserInteraction]:
        """反序列化用户交互"""
        try:
            return UserInteraction(
                interaction_id=data["interaction_id"],
                session_id=data["session_id"],
                thread_id=data.get("thread_id"),
                interaction_type=data["interaction_type"],
                content=data["content"],
                metadata=data.get("metadata", {}),
                timestamp=datetime.fromisoformat(data["timestamp"])
            )
        except Exception as e:
            logger.error(f"反序列化用户交互失败: {e}")
            return None

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        session_context = await self.get_session_context(session_id)
        if not session_context:
            return {}

        interactions = await self.get_interaction_history(session_id)

        # 统计交互类型
        interaction_stats = {}
        for interaction in interactions:
            interaction_type = interaction.interaction_type
            interaction_stats[interaction_type] = interaction_stats.get(interaction_type, 0) + 1

        # 获取Thread状态
        thread_states = {}
        for thread_id in session_context.thread_ids:
            thread_info = await self.thread_service.get_thread_info(thread_id)
            if thread_info:
                thread_states[thread_id] = {
                    "status": thread_info.get("status"),
                    "checkpoint_count": thread_info.get("checkpoint_count", 0),
                    "updated_at": thread_info.get("updated_at")
                }

        return {
            "session_id": session_id,
            "user_id": session_context.user_id,
            "status": session_context.status,
            "created_at": session_context.created_at.isoformat(),
            "updated_at": session_context.updated_at.isoformat(),
            "thread_count": len(session_context.thread_ids),
            "interaction_count": len(interactions),
            "interaction_stats": interaction_stats,
            "thread_states": thread_states
        }

    # === 兼容性方法实现 ===

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话
        
        Returns:
            List[Dict[str, Any]]: 会话列表，只包含会话级别信息
        """
        # 获取所有会话数据
        raw_sessions = self.session_store.list_sessions()
        
        # 转换为符合新架构的会话信息
        sessions = []
        for raw_session in raw_sessions:
            session_id = raw_session.get("session_id")
            if session_id:
                # 获取会话上下文
                session_context = await self.get_session_context(session_id)
                if session_context:
                    # 构建纯会话信息
                    session_info = {
                        "session_id": session_context.session_id,
                        "user_id": session_context.user_id,
                        "status": session_context.status,
                        "created_at": session_context.created_at.isoformat(),
                        "updated_at": session_context.updated_at.isoformat(),
                        "thread_count": len(session_context.thread_ids),  # 只提供线程数量
                        "interaction_count": len(await self.get_interaction_history(session_id))
                    }
                    sessions.append(session_info)
        
        # 按创建时间倒序排列
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话信息，如果不存在则返回None
        """
        session_context = await self.get_session_context(session_id)
        if not session_context:
            return None
            
        # 获取交互历史
        interactions = await self.get_interaction_history(session_id)
        
        # 获取线程状态摘要
        thread_states = {}
        for thread_id in session_context.thread_ids:
            thread_info = await self.thread_service.get_thread_info(thread_id)
            if thread_info:
                thread_states[thread_id] = {
                    "status": thread_info.get("status"),
                    "updated_at": thread_info.get("updated_at")
                }
        
        return {
            "session_id": session_context.session_id,
            "user_id": session_context.user_id,
            "status": session_context.status,
            "created_at": session_context.created_at.isoformat(),
            "updated_at": session_context.updated_at.isoformat(),
            "thread_ids": session_context.thread_ids,
            "thread_count": len(session_context.thread_ids),
            "metadata": session_context.metadata,
            "interaction_count": len(interactions),
            "thread_states": thread_states
        }

    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 删除存储的会话数据
            self.session_store.delete_session(session_id)

            # 删除会话目录
            session_dir = self.storage_path / session_id
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)

            logger.info(f"删除会话成功: {session_id}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {session_id}, error: {e}")
            return False

    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 会话是否存在
        """
        return await self.get_session_context(session_id) is not None

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话信息，如果不存在则返回None
        """
        return await self.get_session(session_id)

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 会话历史记录
        """
        if self.git_manager:
            session_dir = self.storage_path / session_id
            return self.git_manager.get_commit_history(session_dir)
        else:
            # 如果没有Git管理器，返回基于交互历史的基本历史
            interactions = await self.get_interaction_history(session_id)
            history = []
            for interaction in interactions:
                history.append({
                    "timestamp": interaction.timestamp.isoformat(),
                    "message": f"{interaction.interaction_type}: {interaction.content}",
                    "author": "system",
                    "interaction_id": interaction.interaction_id,
                    "thread_id": interaction.thread_id
                })
            return history