"""依赖注入配置"""
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from ...application.sessions.manager import ISessionManager
from ...application.workflow.manager import IWorkflowManager
from .data_access.session_dao import SessionDAO
from .data_access.history_dao import HistoryDAO
from .data_access.workflow_dao import WorkflowDAO
from .cache.memory_cache import MemoryCache
from .services.session_service import SessionService
from .services.workflow_service import WorkflowService
from .services.analytics_service import AnalyticsService
from .services.history_service import HistoryService
from .services.websocket_service import websocket_service

# 全局缓存实例
_cache = MemoryCache()

# 全局数据访问对象实例
_session_dao = None
_history_dao = None
_workflow_dao = None

# 全局服务实例
_session_service = None
_workflow_service = None
_analytics_service = None
_history_service = None


def get_cache() -> MemoryCache:
    """获取缓存实例"""
    return _cache


def get_session_dao() -> SessionDAO:
    """获取会话数据访问对象"""
    global _session_dao
    if _session_dao is None:
        # 数据库文件路径
        data_path = Path("data")
        db_path = data_path / "sessions" / "metadata.db"
        _session_dao = SessionDAO(db_path)
    return _session_dao


def get_history_dao() -> HistoryDAO:
    """获取历史数据访问对象"""
    global _history_dao
    if _history_dao is None:
        # 数据路径
        data_path = Path("data")
        _history_dao = HistoryDAO(data_path)
    return _history_dao


def get_workflow_dao() -> WorkflowDAO:
    """获取工作流数据访问对象"""
    global _workflow_dao
    if _workflow_dao is None:
        # 数据库文件路径
        data_path = Path("data")
        db_path = data_path / "workflows" / "metadata.db"
        _workflow_dao = WorkflowDAO(db_path)
    return _workflow_dao


async def get_session_manager() -> ISessionManager:
    """获取会话管理器"""
    # 这里应该从依赖注入容器中获取
    # 暂时返回一个模拟实例
    from ...application.sessions.manager import SessionManager
    return SessionManager()


async def get_workflow_manager() -> IWorkflowManager:
    """获取工作流管理器"""
    # 这里应该从依赖注入容器中获取
    # 暂时返回一个模拟实例
    from ...application.workflow.manager import WorkflowManager
    return WorkflowManager()


async def get_session_service(
    session_manager: Annotated[ISessionManager, Depends(get_session_manager)],
    session_dao: Annotated[SessionDAO, Depends(get_session_dao)],
    history_dao: Annotated[HistoryDAO, Depends(get_history_dao)],
    cache: Annotated[MemoryCache, Depends(get_cache)]
) -> SessionService:
    """获取会话服务"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService(
            session_manager=session_manager,
            session_dao=session_dao,
            history_dao=history_dao,
            cache=cache
        )
    return _session_service


async def get_workflow_service(
    workflow_manager: Annotated[IWorkflowManager, Depends(get_workflow_manager)],
    workflow_dao: Annotated[WorkflowDAO, Depends(get_workflow_dao)],
    cache: Annotated[MemoryCache, Depends(get_cache)]
) -> WorkflowService:
    """获取工作流服务"""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService(
            workflow_manager=workflow_manager,
            workflow_dao=workflow_dao,
            cache=cache
        )
    return _workflow_service


async def get_analytics_service(
    session_dao: Annotated[SessionDAO, Depends(get_session_dao)],
    history_dao: Annotated[HistoryDAO, Depends(get_history_dao)],
    cache: Annotated[MemoryCache, Depends(get_cache)]
) -> AnalyticsService:
    """获取分析服务"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(
            session_dao=session_dao,
            history_dao=history_dao,
            cache=cache
        )
    return _analytics_service


async def get_history_service(
    history_dao: Annotated[HistoryDAO, Depends(get_history_dao)],
    cache: Annotated[MemoryCache, Depends(get_cache)]
) -> HistoryService:
    """获取历史服务"""
    global _history_service
    if _history_service is None:
        _history_service = HistoryService(
            history_dao=history_dao,
            cache=cache
        )
    return _history_service


def get_websocket_service():
    """获取WebSocket服务"""
    return websocket_service


async def initialize_dependencies():
    """初始化依赖项"""
    # 初始化数据库
    session_dao = get_session_dao()
    await session_dao.initialize()
    
    workflow_dao = get_workflow_dao()
    await workflow_dao.initialize()
    
    # 初始化缓存清理任务
    async def cleanup_cache():
        while True:
            await asyncio.sleep(300)  # 每5分钟清理一次
            await _cache.cleanup_expired()
    
    # 启动后台任务
    asyncio.create_task(cleanup_cache())