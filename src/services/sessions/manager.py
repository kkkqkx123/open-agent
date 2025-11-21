"""Session管理器服务"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.interfaces.sessions import ISessionManager, ISessionStore
from src.core.sessions import Session, SessionStatus, SessionMetadata
from src.core.sessions.interfaces import ISessionCore


class SessionManager(ISessionManager):
    """Session管理器实现"""
    
    def __init__(
        self, 
        session_store: ISessionStore,
        session_core: ISessionCore
    ):
        """初始化Session管理器
        
        Args:
            session_store: Session存储接口
            session_core: Session核心接口
        """
        self._session_store = session_store
        self._session_core = session_core
    
    async def create_session(
        self, 
        graph_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建新会话
        
        Args:
            graph_id: 关联的图ID
            thread_id: 关联的线程ID
            metadata: 会话元数据
            config: 会话配置
            
        Returns:
            新创建的会话ID
        """
        session_id = str(uuid.uuid4())
        
        # 使用核心接口创建会话数据
        session_data = self._session_core.create_session(
            session_id=session_id,
            graph_id=graph_id,
            thread_id=thread_id,
            metadata=metadata,
            config=config
        )
        
        # 保存到存储
        await self._session_store.save_session(session_data)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            会话详细信息字典，不存在时返回None
        """
        return await self._session_store.get_session(session_id)
    
    async def update_session(
        self, 
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """更新会话信息
        
        Args:
            session_id: 会话唯一标识
            updates: 更新内容
            
        Returns:
            更新成功返回True，失败返回False
        """
        # 获取现有会话
        session_data = await self._session_store.get_session(session_id)
        if not session_data:
            return False
        
        # 应用更新
        session_data.update(updates)
        session_data["updated_at"] = datetime.utcnow().isoformat()
        
        # 保存更新
        return await self._session_store.save_session(session_data)
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            删除成功返回True，失败返回False
        """
        return await self._session_store.delete_session(session_id)
    
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出会话
        
        Args:
            filters: 可选的过滤条件
            
        Returns:
            会话列表
        """
        return await self._session_store.list_sessions(filters)
    
    async def update_session_status(
        self, 
        session_id: str,
        new_status: str
    ) -> bool:
        """更新会话状态
        
        Args:
            session_id: 会话唯一标识
            new_status: 新状态
            
        Returns:
            更新成功返回True，失败返回False
        """
        # 获取现有会话
        session_data = await self._session_store.get_session(session_id)
        if not session_data:
            return False
        
        # 使用核心接口更新状态
        success = self._session_core.update_session_status(session_data, new_status)
        if success:
            # 保存更新
            return await self._session_store.save_session(session_data)
        
        return False
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            会话摘要信息，不存在时返回None
        """
        session_data = await self._session_store.get_session(session_id)
        if not session_data:
            return None
        
        # 使用核心接口获取摘要
        return self._session_core.get_session_summary(session_data)
    
    async def archive_session(self, session_id: str) -> bool:
        """归档会话
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            归档成功返回True，失败返回False
        """
        return await self.update_session_status(session_id, SessionStatus.ARCHIVED.value)
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """获取活动会话列表
        
        Returns:
            活动会话列表
        """
        return await self.list_sessions({"status": SessionStatus.ACTIVE.value})
    
    async def get_session_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """获取会话数量
        
        Args:
            filters: 可选的过滤条件
            
        Returns:
            会话数量
        """
        sessions = await self.list_sessions(filters)
        return len(sessions)
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            存在返回True，不存在返回False
        """
        return await self._session_store.session_exists(session_id)