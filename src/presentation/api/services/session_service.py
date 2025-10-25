"""会话服务"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.application.sessions.manager import ISessionManager
from ..data_access.session_dao import SessionDAO
from ..data_access.history_dao import HistoryDAO
from ..cache.memory_cache import MemoryCache
from ..models.requests import SessionCreateRequest, SessionUpdateRequest
from ..models.responses import SessionResponse, SessionListResponse, SessionHistoryResponse
from ..utils.pagination import paginate_list, calculate_pagination, validate_page_params
from ..utils.serialization import serialize_session_data
from ..utils.validation import (
    validate_session_id, validate_page_params, validate_sort_params,
    sanitize_string, validate_time_range
)


class SessionService:
    """会话服务"""
    
    def __init__(
        self,
        session_manager: ISessionManager,
        session_dao: SessionDAO,
        history_dao: HistoryDAO,
        cache: MemoryCache
    ):
        self.session_manager = session_manager
        self.session_dao = session_dao
        self.history_dao = history_dao
        self.cache = cache
    
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
            raise ValueError(error_msg)
        
        is_valid, error_msg = validate_sort_params(sort_by, sort_order)
        if not is_valid:
            raise ValueError(error_msg)
        
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
        
        # 创建会话
        session_id = self.session_manager.create_session(
            workflow_config_path=request.workflow_config_path,
            agent_config=request.agent_config,
            initial_state=request.initial_state
        )
        
        # 保存到数据库
        session_data = self.session_manager.get_session(session_id)
        if session_data:
            await self.session_dao.create_session(session_data)
        
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
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 从数据库删除
        success = await self.session_dao.delete_session(session_id)
        
        if success:
            # 从内存中删除
            self.session_manager.delete_session(session_id)
            
            # 清除缓存
            await self.cache.delete(f"session:{session_id}")
            await self.cache.delete("sessions:list:*")
        
        return success
    
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
        
        # 获取历史记录
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
    
    async def save_session_state(self, session_id: str) -> bool:
        """保存会话状态"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 获取当前会话
        session_data = self.session_manager.get_session(session_id)
        if not session_data:
            return False
        
        # 保存状态
        success = self.session_manager.save_session(
            session_id,
            session_data.get("workflow"),
            session_data.get("state")
        )
        
        if success:
            # 更新数据库中的更新时间
            await self.session_dao.update_session_status(session_id, session_data.get("metadata", {}).get("status", "active"))
            
            # 清除缓存
            await self.cache.delete(f"session:{session_id}")
        
        return success
    
    async def restore_session(self, session_id: str) -> Optional[SessionResponse]:
        """恢复会话"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        try:
            workflow, state = self.session_manager.restore_session(session_id)
            
            # 更新数据库状态
            await self.session_dao.update_session_status(session_id, "active")
            
            # 清除缓存
            await self.cache.delete(f"session:{session_id}")
            
            # 返回恢复后的会话信息
            return await self.get_session(session_id)
        except Exception:
            return None
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 检查缓存
        cache_key = f"session:stats:{session_id}"
        cached_stats = await self.cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        # 获取统计信息
        stats = self.history_dao.get_session_statistics(session_id)
        
        # 缓存结果
        await self.cache.set(cache_key, stats, ttl=300)
        
        return stats