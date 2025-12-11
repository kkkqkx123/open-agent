"""会话服务"""
from typing import Optional, Any, List, Dict, Union
from datetime import datetime
from src.interfaces.sessions.service import ISessionService
from src.core.state import WorkflowState
from src.core.sessions.entities import UserRequestEntity
from ..data_access.session_dao import SessionDAO
from src.interfaces.dependency_injection import get_logger

from ..data_access.history_dao import HistoryDAO
from ..cache.memory_cache import MemoryCache
from ..cache.cache_manager import CacheManager
from ..models.requests import SessionCreateRequest, SessionUpdateRequest
from ..models.responses import SessionResponse, SessionListResponse, SessionHistoryResponse
from ..utils.pagination import paginate_list, calculate_pagination
from ..utils.serialization import serialize_session_data
from ..utils.validation import (
    validate_session_id, validate_page_params, validate_sort_params,
    sanitize_string, validate_time_range
)


class SessionService:
    """会话服务"""
    
    def __init__(
        self,
        session_service: ISessionService,
        session_dao: SessionDAO,
        history_dao: HistoryDAO,
        cache: Union[MemoryCache, 'CacheManager'],
        cache_manager: Optional['CacheManager'] = None
    ):
        self.session_service = session_service
        self.session_dao = session_dao
        self.history_dao = history_dao
        self.cache = cache
        self.cache_manager = cache_manager
            
        # 初始化日志记录器
        self.logger = get_logger(__name__)
    
    def _dict_to_agent_state(self, state_dict: Optional[dict[str, Any]]) -> Optional[WorkflowState]:
        """将字典转换为WorkflowState对象"""
        if state_dict is None:
            return None

        agent_state = dict()
        
        # 设置基本属性
        agent_state["current_step"] = state_dict.get("current_step", "")
        agent_state["max_iterations"] = state_dict.get("max_iterations", 10)
        agent_state["iteration_count"] = state_dict.get("iteration_count", 0)
        agent_state["workflow_name"] = state_dict.get("workflow_name", "")
        agent_state["errors"] = state_dict.get("errors", [])
        
        # 处理开始时间
        start_time_str = state_dict.get("start_time")
        if start_time_str:
            try:
                agent_state["start_time"] = datetime.fromisoformat(start_time_str).isoformat()
            except (ValueError, TypeError):
                agent_state["start_time"] = None
        
        # 处理消息
        # 使用简化的消息类型定义
        class BaseMessage:
            def __init__(self, content: str):
                self.content = content
        
        class SystemMessage(BaseMessage):
            def __init__(self, content: str):
                super().__init__(content)
        
        class HumanMessage(BaseMessage):
            def __init__(self, content: str):
                super().__init__(content)
        messages = []
        for msg_data in state_dict.get("messages", []):
            try:
                msg_type = msg_data.get("type", "base")
                content = msg_data.get("content", "")
                
                if msg_type == "system":
                    message = BaseMessage(content=content)
                elif msg_type == "human":
                    message = BaseMessage(content=content)
                else:
                    message = BaseMessage(content=content)
                
                messages.append(message)
            except Exception:
                # 如果创建消息失败，跳过
                continue
        
        agent_state["messages"] = messages
        
        # 处理工具结果
        from src.interfaces.tool.base import ToolResult
        tool_results = []
        for result_data in state_dict.get("tool_results", []):
            try:
                tool_result = ToolResult(
                    tool_name=result_data.get("tool_name", ""),
                    success=result_data.get("success", False),
                    output=result_data.get("result", ""),
                    error=result_data.get("error", "")
                )
                tool_results.append(tool_result)
            except Exception:
                # 如果创建工具结果失败，跳过
                continue
        
        # 将ToolResult对象转换为字典
        tool_results_dict = []
        for tr in tool_results:
            tool_results_dict.append({
                "tool_name": tr.tool_name,
                "success": tr.success,
                "output": tr.output,
                "error": tr.error
            })
        
        agent_state["tool_results"] = tool_results_dict
        
        return agent_state  # type: ignore
    
    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> SessionListResponse:
        """获取会话列表"""
        # 验证参数
        is_valid, error_msg = validate_page_params(page, page_size)
        if not is_valid:
            raise ValueError(error_msg or "分页参数无效")
        
        is_valid, error_msg = validate_sort_params(sort_by, sort_order)
        if not is_valid:
            raise ValueError(error_msg or "排序参数无效")
        
        # 检查缓存
        cache_key = f"sessions:list:{page}:{page_size}:{status}:{search}:{sort_by}:{sort_order}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return SessionListResponse(**cached_result)
        
        # 获取会话列表
        sessions = await self.session_dao.list_sessions(
            status=status,
            limit=page_size * 2,  # 获取更多数据用于过滤和排序
            offset=0
        )
        
        # 应用搜索过滤
        if search:
            search = sanitize_string(search, 100).lower()
            sessions = [
                s for s in sessions 
                if search in s.get("session_id", "").lower() or
                   search in s.get("workflow_config_path", "").lower()
            ]
        
        # 排序
        reverse = sort_order == "desc"
        sessions.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        
        # 分页
        total = len(sessions)
        paginated_sessions = paginate_list(sessions, page, page_size)
        pagination_info = calculate_pagination(total, page, page_size)
        
        # 转换为响应模型
        session_responses = [
            SessionResponse(**serialize_session_data(session))
            for session in paginated_sessions
        ]
        
        result = SessionListResponse(
            sessions=session_responses,
            **pagination_info
        )
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=60)
        
        return result
    
    async def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """获取特定会话"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 检查缓存
        cache_key = f"session:{session_id}"
        cached_session = await self.cache.get(cache_key)
        if cached_session:
            return SessionResponse(**cached_session)
        
        # 从数据库获取
        session_data = await self.session_dao.get_session(session_id)
        if not session_data:
            return None
        
        result = SessionResponse(**serialize_session_data(session_data))
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=300)
        
        return result
    
    async def create_session(self, request: SessionCreateRequest) -> SessionResponse:
        """创建新会话"""
        # 验证配置路径
        if not request.workflow_config_path:
            raise ValueError("工作流配置路径不能为空")
        
        # 创建UserRequest对象 - 使用正确的参数格式
        user_request = UserRequestEntity(
            request_id=f"request_{datetime.now().timestamp()}",
            user_id=None,
            content=f"创建会话: {request.workflow_config_path}",
            metadata={
                "workflow_config_path": request.workflow_config_path,
                "agent_config": request.agent_config,
                "initial_state": request.initial_state
            },
            timestamp=datetime.now()
        )
        
        try:
            # 调用session_service的create_session方法
            session_id = await self.session_service.create_session(user_request)
            
            # 获取会话上下文
            session_context = await self.session_service.get_session_context(session_id)
            if session_context:
                # 构建会话数据用于数据库保存
                session_data = {
                    "session_id": session_context.session_id,
                    "workflow_config_path": request.workflow_config_path,
                    "workflow_id": f"workflow_{session_context.session_id}",
                    "status": session_context.status,
                    "created_at": session_context.created_at,
                    "updated_at": session_context.updated_at,
                    "agent_config": request.agent_config,
                    "metadata": session_context.metadata
                }
                await self.session_dao.create_session(session_data)
        except Exception as e:
            self.logger.error(f"创建会话失败: {e}")
            raise RuntimeError(f"创建会话失败: {str(e)}") from e
        
        # 获取创建的会话
        result = await self.get_session(session_id)
        if not result:
            raise RuntimeError("创建会话失败")
        
        # 清除列表缓存
        await self.cache.delete("sessions:list:*")
        
        return result
    
    async def update_session(self, session_id: str, request: SessionUpdateRequest) -> Optional[SessionResponse]:
        """更新会话"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 获取现有会话
        session_data = await self.session_dao.get_session(session_id)
        if not session_data:
            return None
        
        # 更新数据
        if request.status:
            if not await self.session_dao.update_session_status(session_id, request.status):
                return None
        
        # 清除缓存
        await self.cache.delete(f"session:{session_id}")
        await self.cache.delete("sessions:list:*")
        
        # 返回更新后的会话
        return await self.get_session(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            # 调用session_service的delete_session方法
            await self.session_service.delete_session(session_id)
            
            # 删除数据库记录
            success = await self.session_dao.delete_session(session_id)
            
            # 清除缓存
            await self.cache.delete(f"session:{session_id}")
            await self.cache.delete("sessions:list:*")
            
            return bool(success)
        except Exception as e:
            self.logger.error(f"删除会话失败: {session_id}, error: {e}")
            return False
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        record_types: Optional[List[str]] = None
    ) -> SessionHistoryResponse:
        """获取会话历史"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 验证时间范围
        start_str = start_time.isoformat() if start_time else None
        end_str = end_time.isoformat() if end_time else None
        is_valid, error_msg = validate_time_range(start_str, end_str)
        if not is_valid:
            raise ValueError(error_msg)
        
        # 获取历史记录 - 由于接口限制，使用默认逻辑
        try:
            # 获取历史记录 - 检查get_session_records是否是异步方法
            import inspect
            if inspect.iscoroutinefunction(self.history_dao.get_session_records):
                records = await self.history_dao.get_session_records(
                    session_id=session_id,
                    start_time=start_time,
                    end_time=end_time,
                    record_types=record_types,
                    limit=limit
                )
            else:
                records = self.history_dao.get_session_records(
                    session_id=session_id,
                    start_time=start_time,
                    end_time=end_time,
                    record_types=record_types,
                    limit=limit
                )
            
            return SessionHistoryResponse(
                session_id=session_id,
                history=records,
                total=len(records)
            )
        except Exception:
            # 如果获取失败，使用默认数据
            return SessionHistoryResponse(
                session_id=session_id,
                history=[],
                total=0
            )
    
    async def save_session_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """保存会话状态
        
        Args:
            session_id: 会话ID
            state_data: 状态数据
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 会话状态通过session_dao直接保存，不通过session_manager
            success = await self.session_dao.update_session_state(session_id, state_data)
            if success:
                # 清除相关缓存
                await self.cache.delete(f"session:{session_id}")
            return bool(success)
        except Exception as e:
            self.logger.error(f"保存会话状态失败: {session_id}, error: {e}")
            raise RuntimeError(f"保存会话状态失败: {str(e)}")
    
    async def restore_session(self, session_id: str) -> Optional[SessionResponse]:
        """恢复会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[SessionResponse]: 恢复的会话响应
        """
        try:
            # 获取会话上下文 - 使用get_session_context方法
            session_context = await self.session_service.get_session_context(session_id)
            
            if not session_context:
                return None
                
            # 更新数据库中的状态
            await self.session_dao.update_session_status(session_id, "active")
            
            # 清除缓存
            await self.cache.delete(f"session:{session_id}")
            
            # 获取会话的完整信息以构建响应
            session_info = await self.session_service.get_session_info(session_id)
            if not session_info:
                return None
            
            return SessionResponse(
                session_id=session_context.session_id,
                workflow_config_path=session_info.get("workflow_config_path", ""),
                workflow_id=session_info.get("workflow_id", ""),
                status=session_context.status,
                created_at=session_context.created_at,
                updated_at=session_context.updated_at,
                agent_config=session_info.get("agent_config"),
                metadata=session_context.metadata
            )
        except Exception as e:
            self.logger.error(f"恢复会话失败: {session_id}, error: {e}")
            raise RuntimeError(f"恢复会话失败: {str(e)}")
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 获取会话上下文和交互历史来构建统计信息
            session_context = await self.session_service.get_session_context(session_id)
            if not session_context:
                return {}
            
            # 获取交互历史
            interactions = await self.session_service.get_interaction_history(session_id)
            
            # 构建基本统计信息
            stats = {
                "session_id": session_id,
                "status": session_context.status,
                "created_at": session_context.created_at.isoformat(),
                "updated_at": session_context.updated_at.isoformat(),
                "total_interactions": len(interactions),
                "thread_count": len(session_context.thread_ids),
                "interaction_types": {}
            }
            
            # 统计交互类型
            interaction_types: Dict[str, int] = {}
            for interaction in interactions:
                interaction_type = interaction.interaction_type
                interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
            stats["interaction_types"] = interaction_types
            
            return stats
        except Exception as e:
            self.logger.error(f"获取会话统计信息失败: {session_id}, error: {e}")
            raise RuntimeError(f"获取会话统计信息失败: {str(e)}")