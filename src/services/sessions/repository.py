"""会话仓储实现"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from interfaces.repository.session import ISessionRepository
from src.adapters.storage.backends.base import ISessionStorageBackend
from src.interfaces.logger import ILogger
from src.interfaces.storage.exceptions import StorageError
from src.core.sessions import Session


class SessionRepository(ISessionRepository):
    """会话仓储实现 - 协调多个存储后端"""
    
    def __init__(
        self,
        primary_backend: ISessionStorageBackend,
        secondary_backends: Optional[List[ISessionStorageBackend]] = None,
        logger: Optional[ILogger] = None
    ):
        """初始化会话仓储
        
        Args:
            primary_backend: 主存储后端（必须）
            secondary_backends: 辅助存储后端列表，用于冗余和查询扩展
            logger: 日志记录器
        """
        self.primary_backend = primary_backend
        self.secondary_backends = secondary_backends or []
        self._logger = logger
        if self._logger:
            self._logger.info(
                f"SessionRepository initialized with {1 + len(self.secondary_backends)} backend(s)"
            )
    
    async def create(self, session: Session) -> bool:
        """创建会话 - 保存到所有后端
        
        Args:
            session: 会话实体
            
        Returns:
            是否创建成功
        """
        try:
            # 将 Session 实体转换为存储格式
            data = self._session_to_dict(session)
            
            # 保存到主后端
            if not await self.primary_backend.save(session.session_id, data):
                raise StorageError("Failed to save to primary backend")
            
            # 保存到辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.save(session.session_id, data)
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"Failed to save to secondary backend: {e}")
            
            if self._logger:
                self._logger.info(f"Session created: {session.session_id}")
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to create session: {e}")
            raise StorageError(f"Failed to create session: {e}")
    
    async def get(self, session_id: str) -> Optional[Session]:
        """获取会话 - 优先从主后端读取
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话实体，不存在返回None
        """
        try:
            # 从主后端读取
            data = await self.primary_backend.load(session_id)
            if data is None:
                # 尝试从辅助后端读取
                for backend in self.secondary_backends:
                    try:
                        data = await backend.load(session_id)
                        if data:
                            break
                    except Exception:
                        continue
            
            if data:
                return self._dict_to_session(data)
            return None
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update(self, session: Session) -> bool:
        """更新会话 - 更新所有后端
        
        Args:
            session: 会话实体
            
        Returns:
            是否更新成功
        """
        try:
            data = self._session_to_dict(session)
            
            # 更新主后端
            if not await self.primary_backend.save(session.session_id, data):
                raise StorageError("Failed to update primary backend")
            
            # 更新辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.save(session.session_id, data)
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"Failed to update secondary backend: {e}")
            
            if self._logger:
                self._logger.debug(f"Session updated: {session.session_id}")
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to update session: {e}")
            raise StorageError(f"Failed to update session: {e}")
    
    async def delete(self, session_id: str) -> bool:
        """删除会话 - 删除所有后端
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除主后端
            primary_deleted = await self.primary_backend.delete(session_id)
            
            # 删除辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.delete(session_id)
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"Failed to delete from secondary backend: {e}")
            
            if self._logger:
                self._logger.info(f"Session deleted: {session_id}")
            return primary_deleted
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to delete session: {e}")
            raise StorageError(f"Failed to delete session: {e}")
    
    async def list_by_status(self, status: str) -> List[Session]:
        """按状态列会话 - 从主后端读取并过滤
        
        Args:
            status: 会话状态
            
        Returns:
            会话列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            sessions: List['Session'] = []
            
            for session_id in keys:
                session = await self.get(session_id)
                if session and session.status == status:
                    sessions.append(session)
            
            # 按更新时间倒序
            sessions.sort(key=lambda s: s.updated_at, reverse=True)
            if self._logger:
                self._logger.debug(f"Listed {len(sessions)} sessions with status {status}")
            return sessions
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to list sessions by status: {e}")
            raise StorageError(f"Failed to list sessions by status: {e}")
    
    async def list_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Session]:
        """按日期范围列会话
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            会话列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            sessions: List['Session'] = []
            
            for session_id in keys:
                session = await self.get(session_id)
                if session and start_date <= session.created_at <= end_date:
                    sessions.append(session)
            
            # 按创建时间倒序
            sessions.sort(key=lambda s: s.created_at, reverse=True)
            if self._logger:
                self._logger.debug(f"Listed {len(sessions)} sessions in date range")
            return sessions
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to list sessions by date range: {e}")
            raise StorageError(f"Failed to list sessions by date range: {e}")
    
    async def search(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Session]:
        """搜索会话
        
        Args:
            query: 查询字符串
            limit: 返回数量限制
            
        Returns:
            会话列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            sessions: List['Session'] = []
            
            query_lower = query.lower()
            for session_id in keys:
                if len(sessions) >= limit:
                    break
                
                # 检查会话ID是否匹配
                if query_lower in session_id.lower():
                    session = await self.get(session_id)
                    if session:
                        sessions.append(session)
                    continue
                
                # 检查元数据是否匹配
                session = await self.get(session_id)
                if session:
                    metadata_str = str(session.metadata).lower()
                    if query_lower in metadata_str:
                        sessions.append(session)
            
            # 按更新时间倒序
            sessions.sort(key=lambda s: s.updated_at, reverse=True)
            if self._logger:
                self._logger.debug(f"Searched and found {len(sessions)} sessions matching '{query}'")
            return sessions
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to search sessions: {e}")
            raise StorageError(f"Failed to search sessions: {e}")
    
    async def get_count_by_status(self) -> Dict[str, int]:
        """获取各状态会话数量
        
        Returns:
            状态到数量的映射字典
        """
        try:
            keys = await self.primary_backend.list_keys()
            count_map: Dict[str, int] = {}
            
            for session_id in keys:
                session = await self.get(session_id)
                if session:
                    status_key = session.status.value
                    count_map[status_key] = count_map.get(status_key, 0) + 1
            
            if self._logger:
                self._logger.debug(f"Session count by status: {count_map}")
            return count_map
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to get session count by status: {e}")
            raise StorageError(f"Failed to get session count by status: {e}")
    
    async def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧会话
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的会话数量
        """
        try:
            from datetime import timedelta
            
            keys = await self.primary_backend.list_keys()
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            for session_id in keys:
                session = await self.get(session_id)
                if session:
                    # 只清理已完成或失败的旧会话
                    is_terminal = session.status.value in ['completed', 'failed']
                    is_old = session.updated_at < cutoff_date
                    
                    if is_terminal and is_old:
                        if await self.delete(session_id):
                            deleted_count += 1
            
            if self._logger:
                self._logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to cleanup old sessions: {e}")
            raise StorageError(f"Failed to cleanup old sessions: {e}")
    
    async def add_interaction(self, session_id: str, interaction: Dict[str, Any]) -> bool:
        """添加用户交互
        
        Args:
            session_id: 会话ID
            interaction: 交互数据字典
            
        Returns:
            是否添加成功
        """
        try:
            session = await self.get(session_id)
            if not session:
                raise StorageError(f"Session not found: {session_id}")
            
            # 交互保存在会话元数据中
            if "interactions" not in session.metadata:
                session.metadata["interactions"] = []
            
            session.metadata["interactions"].append(interaction)
            session._updated_at = datetime.now()
            
            return await self.update(session)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to add interaction: {e}")
            raise StorageError(f"Failed to add interaction: {e}")
    
    async def get_interactions(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取交互历史
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            
        Returns:
            交互列表
        """
        try:
            session = await self.get(session_id)
            if not session:
                return []
            
            interactions = session.metadata.get("interactions", [])
            if limit:
                interactions = interactions[-limit:]
            
            # 确保返回类型正确
            result: List[Dict[str, Any]] = []
            for interaction in interactions:
                if isinstance(interaction, dict):
                    result.append(interaction)
                else:
                    # 如果不是字典，尝试转换
                    result.append({"data": str(interaction)})
            
            if self._logger:
                self._logger.debug(f"Retrieved {len(result)} interactions for session {session_id}")
            return result
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to get interactions: {e}")
            raise StorageError(f"Failed to get interactions: {e}")
    
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        try:
            return await self.primary_backend.exists(session_id)
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to check session existence: {e}")
            raise StorageError(f"Failed to check session existence: {e}")
    
    # === 私有方法 ===
    
    def _session_to_dict(self, session: Session) -> Dict[str, Any]:
        """会话实体转为字典
        
        Args:
            session: 会话实体
            
        Returns:
            会话数据字典
        """
        return {
            "session_id": session.session_id,
            "status": session.status.value if hasattr(session.status, 'value') else session.status,
            "message_count": session.message_count,
            "checkpoint_count": session.checkpoint_count,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "metadata": session.metadata,
            "tags": session.tags,
            "thread_ids": session.thread_ids
        }
    
    def _dict_to_session(self, data: Dict[str, Any]) -> Session:
        """字典转为会话实体
        
        Args:
            data: 会话数据字典
            
        Returns:
            会话实体
        """
        return Session(
            session_id=data["session_id"],
            _status=data["status"],
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            _created_at=datetime.fromisoformat(data["created_at"]),
            _updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            thread_ids=data.get("thread_ids", [])
        )