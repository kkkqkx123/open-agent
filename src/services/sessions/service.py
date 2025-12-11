"""会话业务服务实现（增强版）"""

import uuid
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator, Callable, TYPE_CHECKING
from datetime import datetime, timedelta

from src.core.sessions.core_interfaces import ISessionCore, ISessionValidator, ISessionStateTransition
from src.core.sessions.entities import SessionStatus, Session, UserRequestEntity, UserInteractionEntity, SessionContext
from src.interfaces.sessions import ISessionService
from src.interfaces.sessions.service import ISessionService as ISessionServiceInterface
from src.interfaces.repository.session import ISessionRepository
from src.interfaces.threads.service import IThreadService
from src.interfaces.common_domain import AbstractSessionStatus
from src.interfaces.logger import ILogger
from src.interfaces.container.exceptions import ValidationError
from src.interfaces.storage.exceptions import StorageNotFoundError as EntityNotFoundError
from src.interfaces.sessions.exceptions import (
    SessionNotFoundError,
    ThreadNotFoundError,
    WorkflowExecutionError
)
if TYPE_CHECKING:
    from src.core.state import WorkflowState
from src.interfaces.state.session import ISessionStateManager

if TYPE_CHECKING:
    from src.core.sessions.entities import Session

from .git_service import IGitService
from .coordinator import SessionThreadCoordinator


class SessionService(ISessionService):
    """会话业务服务实现（增强版）"""
    
    def __init__(
        self,
        session_core: ISessionCore,
        session_repository: Optional[ISessionRepository] = None,
        thread_service: Optional[IThreadService] = None,
        coordinator: Optional[SessionThreadCoordinator] = None,
        session_validator: Optional[ISessionValidator] = None,
        state_transition: Optional[ISessionStateTransition] = None,
        git_service: Optional[IGitService] = None,
        storage_path: Optional[Path] = None,
        logger: Optional[ILogger] = None,
        session_state_manager: Optional[ISessionStateManager] = None
    ):
        """初始化会话服务
        
        Args:
            session_core: 会话核心接口
            session_repository: 会话仓储（完整版方法）
            thread_service: 线程服务
            coordinator: Session-Thread协调器
            session_validator: 会话验证器
            state_transition: 状态转换器
            git_service: Git服务
            storage_path: 存储路径
            logger: 日志记录器
            session_state_manager: 会话状态管理器
        """
        self._session_core = session_core
        self._session_repository = session_repository
        self._thread_service = thread_service
        self._coordinator = coordinator
        self._session_validator = session_validator
        self._state_transition = state_transition
        self._git_service = git_service
        self._session_state_manager = session_state_manager
        self._storage_path = storage_path or Path("./sessions")
        self._logger = logger
        
        # 确保存储目录存在
        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)
        
        if self._logger:
            self._logger.info("SessionService初始化完成")
    
    # === 会话管理方法（基于ISessionRepository） ===
    
    async def create_session_with_thread(
        self,
        session_config: Dict[str, Any],
        thread_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建会话并关联线程"""
        try:
            # 创建会话实体
            session = self._session_core.create_session(
                user_id=session_config.get("user_id"),
                metadata=session_config.get("metadata", {})
            )
            session_id = session.session_id
            
            # 创建对应的会话状态对象
            if self._session_state_manager:
                session_state = self._session_state_manager.create_session_state(
                    session_id=session_id,
                    user_id=session_config.get("user_id"),
                    config=session_config.get("config", {})
                )
                
                # 如果有线程配置，添加线程ID
                if thread_config and hasattr(session_state, 'add_thread'):
                    thread_id = thread_config.get("thread_id", f"thread_{session_id}")
                    session_state.add_thread(thread_id)
                
                # 保存状态
                self._session_state_manager.save_session_state(session_state)
            
            # 如果需要，创建关联线程
            if thread_config and self._thread_service:
                # 调用线程服务创建线程
                thread_id = thread_config.get("thread_id", f"thread_{session_id}")
                await self._thread_service.create_thread(thread_id, thread_config)
            
            return session_id
        except Exception as e:
            raise ValidationError(f"Failed to create session with thread: {str(e)}")
    
    async def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """更新会话元数据"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 验证会话存在
            session = await self._session_repository.get(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            # 更新元数据
            session.metadata.update(metadata)
            session._updated_at = datetime.now()
            
            # 同步更新状态管理器中的状态
            if self._session_state_manager:
                session_state = self._session_state_manager.get_session_state(session_id)
                if session_state:
                    # 更新状态中的元数据
                    if hasattr(session_state, 'set_session_metadata'):
                        current_metadata = session_state.get_session_metadata() if hasattr(session_state, 'get_session_metadata') else {}
                        current_metadata.update(metadata)
                        session_state.set_session_metadata(current_metadata)
                    self._session_state_manager.save_session_state(session_state)
            
            # 保存更新
            success = await self._session_repository.update(session)
            return success
        except Exception as e:
            raise ValidationError(f"Failed to update session metadata: {str(e)}")
    
    async def increment_message_count(self, session_id: str) -> int:
        """增加消息计数"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            session = await self._session_repository.get(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            session.message_count += 1
            session._updated_at = datetime.now()
            
            # 同步更新状态管理器中的计数
            if self._session_state_manager:
                session_state = self._session_state_manager.get_session_state(session_id)
                if session_state:
                    session_state.increment_message_count()
                    self._session_state_manager.save_session_state(session_state)
            
            await self._session_repository.update(session)
            return session.message_count
        except Exception as e:
            raise ValidationError(f"Failed to increment message count: {str(e)}")
    
    async def increment_checkpoint_count(self, session_id: str) -> int:
        """增加检查点计数"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            session = await self._session_repository.get(session_id)
            if not session:
                raise EntityNotFoundError(f"Session {session_id} not found")
            
            session.checkpoint_count += 1
            session._updated_at = datetime.now()
            
            await self._session_repository.update(session)
            return session.checkpoint_count
        except Exception as e:
            raise ValidationError(f"Failed to increment checkpoint count: {str(e)}")
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要信息"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 完整版实现
            session_context = await self.get_session_context(session_id)
            if not session_context:
                return {}
            
            interactions = await self.get_interaction_history(session_id)
            
            # 统计交互类型
            interaction_stats: Dict[str, int] = {}
            for interaction in interactions:
                interaction_type = interaction.interaction_type
                interaction_stats[interaction_type] = interaction_stats.get(interaction_type, 0) + 1
            
            # 获取Thread状态
            thread_states = {}
            if self._thread_service:
                for thread_id in session_context.thread_ids:
                    thread_info = await self._thread_service.get_thread_info(thread_id)
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
        except Exception as e:
            raise ValidationError(f"Failed to get session summary: {str(e)}")
    
    async def list_sessions_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态列会话"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 验证状态有效性
            try:
                session_status = SessionStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid session status: {status}")
            
            sessions = await self._session_repository.list_by_status(session_status)
            
            return [
                {
                    "session_id": session.session_id,
                    "status": session.status.value,
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata
                }
                for session in sessions
            ]
        except Exception as e:
            raise ValidationError(f"Failed to list sessions by status: {str(e)}")
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """清理不活动的会话"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 使用仓储的清理方法
            max_age_days = max_age_hours // 24 or 1  # 转换为天数，至少1天
            return await self._session_repository.cleanup_old(max_age_days)
        except Exception as e:
            raise ValidationError(f"Failed to cleanup inactive sessions: {str(e)}")
    
    # === 会话生命周期管理 ===
    
    async def create_session(self, user_request: UserRequestEntity) -> str:
        """创建用户会话"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 验证用户请求
            if self._session_validator:
                if not self._session_validator.validate_user_request(user_request):
                    raise ValidationError("用户请求验证失败")
            
            # 创建会话实体
            session_entity = self._session_core.create_session(
                user_id=user_request.user_id,
                metadata={
                    "request_id": user_request.request_id,
                    "initial_content": user_request.content,
                    **user_request.metadata
                }
            )
            
            # 转换为业务实体（Session）
            session = self._entity_to_session(session_entity)
            
            # 创建会话目录
            session_dir = self._storage_path / session.session_id
            session_dir.mkdir(exist_ok=True)
            
            # 初始化Git仓库（如果提供了Git服务）
            if self._git_service:
                self._git_service.init_repo(session_dir)
            
            # 保存会话到仓储（自动协调所有后端）
            await self._session_repository.create(session)
            
            # 追踪初始用户交互
            initial_interaction = UserInteractionEntity(
                interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                session_id=session.session_id,
                thread_id=None,
                interaction_type="user_request",
                content=user_request.content,
                metadata=user_request.metadata,
                timestamp=datetime.now()
            )
            await self.track_user_interaction(session.session_id, initial_interaction)
            
            # 提交初始状态到Git（如果提供了Git服务）
            if self._git_service:
                self._git_service.commit_changes(
                    session_dir,
                    "初始化用户会话",
                    {"session_id": session.session_id, "request_id": user_request.request_id}
                )
            
            if self._logger:
                self._logger.info(f"创建用户会话成功: {session.session_id}, user_id: {user_request.user_id}")
            return str(session.session_id)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"创建会话失败: {e}")
            raise ValidationError(f"创建会话失败: {str(e)}")
    
    async def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """获取会话上下文"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            session = await self._session_repository.get(session_id)
            if not session:
                return None
            
            return SessionContext(
                session_id=session.session_id,
                user_id=session.metadata.get("user_id"),
                thread_ids=session.thread_ids,
                status=session.status.value,
                created_at=session.created_at,
                updated_at=session.updated_at,
                metadata=session.metadata
            )
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取会话上下文失败: {session_id}, error: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 删除存储的会话数据
            await self._session_repository.delete(session_id)
            
            # 删除会话目录
            session_dir = self._storage_path / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
            
            if self._logger:
                self._logger.info(f"删除会话成功: {session_id}")
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"删除会话失败: {session_id}, error: {e}")
            return False
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 从仓储获取所有活跃会话
            sessions = []
            for status in [SessionStatus.ACTIVE, SessionStatus.PAUSED, SessionStatus.COMPLETED]:
                try:
                    status_sessions = await self._session_repository.list_by_status(status)
                    for session in status_sessions:
                        interactions = await self._session_repository.get_interactions(session.session_id)
                        session_info = {
                            "session_id": session.session_id,
                            "user_id": session.metadata.get("user_id"),
                            "status": session.status.value,
                            "created_at": session.created_at.isoformat(),
                            "updated_at": session.updated_at.isoformat(),
                            "thread_count": len(session.thread_ids),
                            "interaction_count": len(interactions)
                        }
                        sessions.append(session_info)
                except Exception:
                    continue
            
            # 按更新时间倒序排列
            def sort_key(x: Dict[str, Any]) -> str:
                return str(x.get("updated_at", ""))
            sessions.sort(key=sort_key, reverse=True)
            return sessions
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"列出会话失败: {e}")
            return []
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        try:
            if self._session_repository:
                return await self._session_repository.exists(session_id)
            return False
        except Exception:
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        session_context = await self.get_session_context(session_id)
        if not session_context:
            return None
            
        # 获取交互历史
        interactions = await self.get_interaction_history(session_id)
        
        # 获取线程状态摘要
        thread_states = {}
        if self._thread_service:
            for thread_id in session_context.thread_ids:
                thread_info = await self._thread_service.get_thread_info(thread_id)
                if thread_info:
                    thread_states[thread_id] = {
                        "status": thread_info.get("status"),
                        "updated_at": thread_info.get("updated_at")
                    }
        
        # 获取状态管理器中的会话摘要（如果可用）
        session_summary = None
        if self._session_state_manager:
            session_state = self._session_state_manager.get_session_state(session_context.session_id)
            if session_state:
                session_summary = session_state.get_session_summary()
        
        result = {
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
        
        # 合并状态管理器提供的信息
        if session_summary:
            result.update({
                "message_count": session_summary.get("message_count", 0),
                "checkpoint_count": session_summary.get("checkpoint_count", 0),
                "last_activity": session_summary.get("last_activity"),
                "is_active": session_summary.get("is_active", True),
                "duration_minutes": session_summary.get("duration_minutes", 0),
                "idle_time_minutes": session_summary.get("idle_time_minutes", 0)
            })
        
        return result
    
    # === 用户交互管理 ===
    
    async def track_user_interaction(self, session_id: str, interaction: UserInteractionEntity) -> None:
        """追踪用户交互"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 检查会话是否存在
            if not await self._session_repository.exists(session_id):
                if self._logger:
                    self._logger.warning(f"会话不存在: {session_id}")
                return
            
            # 验证交互
            if self._session_validator:
                if not self._session_validator.validate_user_interaction(interaction):
                    if self._logger:
                        self._logger.warning(f"用户交互验证失败: {interaction.interaction_id}")
                    return
            
            # 构造交互数据
            interaction_dict = {
                "interaction_id": interaction.interaction_id,
                "session_id": interaction.session_id,
                "thread_id": interaction.thread_id,
                "interaction_type": interaction.interaction_type,
                "content": interaction.content,
                "metadata": interaction.metadata,
                "timestamp": interaction.timestamp.isoformat()
            }
            
            # 通过仓储添加交互
            await self._session_repository.add_interaction(session_id, interaction_dict)
            
            # 提交到Git（如果提供了Git服务）
            if self._git_service:
                session_dir = self._storage_path / session_id
                self._git_service.commit_changes(
                    session_dir,
                    f"追踪用户交互: {interaction.interaction_type}",
                    {"session_id": session_id, "interaction_id": interaction.interaction_id}
                )
            
            if self._logger:
                self._logger.debug(f"追踪用户交互成功: {session_id}, {interaction.interaction_type}")

        except Exception as e:
            if self._logger:
                self._logger.error(f"追踪用户交互失败: {session_id}, error: {e}")
    
    async def get_interaction_history(self, session_id: str, limit: Optional[int] = None) -> List[UserInteractionEntity]:
        """获取交互历史"""
        try:
            if not self._session_repository:
                raise ValidationError("session_repository is required for this operation")
            
            # 从仓储获取交互数据
            interactions_data = await self._session_repository.get_interactions(session_id, limit)
            
            # 转换为 UserInteractionEntity 对象
            interactions = []
            for interaction_data in interactions_data:
                try:
                    interaction = UserInteractionEntity(
                        interaction_id=interaction_data["interaction_id"],
                        session_id=interaction_data["session_id"],
                        thread_id=interaction_data.get("thread_id"),
                        interaction_type=interaction_data["interaction_type"],
                        content=interaction_data["content"],
                        metadata=interaction_data.get("metadata", {}),
                        timestamp=datetime.fromisoformat(interaction_data["timestamp"])
                    )
                    interactions.append(interaction)
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"Failed to deserialize interaction: {e}")
                    continue
            
            return interactions
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取交互历史失败: {session_id}, error: {e}")
            return []
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        if self._git_service:
            session_dir = self._storage_path / session_id
            return self._git_service.get_commit_history(session_dir)
        else:
            # 如果没有Git服务，返回基于交互历史的基本历史
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
    
    # === 多线程协调 ===
    
    async def coordinate_threads(self, session_id: str, thread_configs: List[Dict[str, Any]]) -> Dict[str, str]:
        """协调多个Thread执行"""
        try:
            if not self._coordinator:
                raise ValidationError("coordinator is required for this operation")
            return await self._coordinator.coordinate_threads(session_id, thread_configs)
        except Exception as e:
            if self._logger:
                self._logger.error(f"协调Thread执行失败: {session_id}, error: {e}")
            raise ValidationError(f"协调Thread执行失败: {str(e)}")
    
    # === 工作流执行 ===
    
    async def execute_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> "WorkflowState":
        """在会话中执行工作流"""
        try:
            if not self._coordinator:
                raise ValidationError("coordinator is required for this operation")
            
            result = await self._coordinator.execute_workflow_in_session(session_id, thread_name, config)
            # 确保返回类型正确
            if result is None:
                raise WorkflowExecutionError(session_id, thread_name, RuntimeError("Coordinator returned None"))
            # 类型断言：确保返回的是WorkflowState类型
            if result.__class__.__name__ != 'WorkflowState' and not hasattr(result, 'messages'):
                # 如果不是WorkflowState，尝试转换或抛出错误
                raise WorkflowExecutionError(session_id, thread_name, RuntimeError(f"Expected WorkflowState, got {type(result)}"))
            return result
        except Exception as e:
            if self._logger:
                self._logger.error(f"工作流执行失败: {session_id}, {thread_name}, error: {e}")
            raise WorkflowExecutionError(session_id, thread_name, e)
    
    def stream_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Callable[[], AsyncGenerator[Dict[str, Any], None]]:
        """在会话中流式执行工作流"""
        async def _stream_impl() -> AsyncGenerator[Dict[str, Any], None]:
            if not self._coordinator or not self._thread_service or not self._session_repository:
                raise ValidationError("coordinator, thread_service, and session_repository are required for this operation")
            
            # 获取会话上下文
            session_context = await self.get_session_context(session_id)
            if not session_context:
                raise SessionNotFoundError(f"会话不存在: {session_id}")
            
            # 查找Thread ID（类似execute_workflow_in_session）
            thread_id = None
            session = await self._session_repository.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"会话 {session_id} 不存在")
            thread_configs = session.metadata.get("thread_configs", {})
            
            if thread_name in thread_configs:
                thread_config = thread_configs[thread_name]
                
                # 查找对应的thread_id
                for tid in session_context.thread_ids:
                    thread_info = await self._thread_service.get_thread_info(tid)
                    if thread_info and thread_info.get("metadata", {}).get("thread_name") == thread_name:
                        thread_id = tid
                        break
            else:
                raise ThreadNotFoundError(f"Thread不存在: {thread_name}")
            
            if not thread_id:
                raise ThreadNotFoundError(f"找不到Thread: {thread_name}")
            
            # 追踪流式执行开始交互
            interaction = UserInteractionEntity(
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
                async for state in await self._thread_service.stream_workflow(thread_id, config):
                    yield state
                
                # 追踪流式执行完成交互
                completion_interaction = UserInteractionEntity(
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
                error_interaction = UserInteractionEntity(
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
        
        return _stream_impl
    
    # === 会话管理 ===
    
    async def create_session_with_threads(
        self,
        workflow_configs: Dict[str, str],
        dependencies: Optional[Dict[str, List[str]]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_states: Optional[Dict[str, "WorkflowState"]] = None
    ) -> str:
        """创建会话并关联多个Thread（向后兼容）"""
        # 创建用户请求
        user_request = UserRequestEntity(
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
    
    # === 新增协调器方法 ===
    
    async def sync_session_data(self, session_id: str) -> Dict[str, Any]:
        """同步Session数据"""
        if not self._coordinator:
            raise ValidationError("coordinator is required for this operation")
        return await self._coordinator.sync_session_data(session_id)
    
    async def validate_session_consistency(self, session_id: str) -> List[str]:
        """验证Session一致性"""
        if not self._coordinator:
            raise ValidationError("coordinator is required for this operation")
        return await self._coordinator.validate_session_consistency(session_id)
    
    async def repair_session_inconsistencies(self, session_id: str) -> Dict[str, Any]:
        """修复Session不一致问题"""
        if not self._coordinator:
            raise ValidationError("coordinator is required for this operation")
        return await self._coordinator.repair_session_inconsistencies(session_id)
    
    async def remove_thread_from_session(self, session_id: str, thread_name: str) -> bool:
        """从Session中移除Thread"""
        if not self._coordinator:
            raise ValidationError("coordinator is required for this operation")
        return await self._coordinator.remove_thread_from_session(session_id, thread_name)
    
    # === 私有辅助方法 ===
    
    def _serialize_session_context(self, context: SessionContext) -> Dict[str, Any]:
        """将 SessionContext 序列化为字典
        
        Args:
            context: SessionContext 对象
            
        Returns:
            序列化后的字典
        """
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
        """从字典反序列化 SessionContext
        
        Args:
            data: 序列化的字典
            
        Returns:
            SessionContext 对象
        """
        return SessionContext(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            thread_ids=data.get("thread_ids", []),
            status=data.get("status", "active"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )
    
    def _entity_to_session(self, entity: Session) -> 'Session':
        """将 Session 实体转换为业务实体

        Args:
            entity: Session 核心实体
            
        Returns:
            Session 业务实体
        """
        # 将字符串状态转换为 SessionStatus 枚举
        status_str = entity.status.value if hasattr(entity.status, 'value') else entity.status
        
        # 动态导入避免循环依赖
        from src.core.sessions.entities import Session
        
        return Session(
            session_id=entity.session_id,
            status=status_str,
            message_count=getattr(entity, 'message_count', 0),
            checkpoint_count=getattr(entity, 'checkpoint_count', 0),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            metadata=entity.metadata,
            tags=getattr(entity, 'tags', []),
            thread_ids=entity.thread_ids,
            user_id=entity.metadata.get('user_id') if entity.metadata else None
        )
