"""Session-Thread关联仓储实现"""

from src.services.logger import get_logger
import json
from typing import Dict, Any, Optional, List, Union, cast, Sequence
from datetime import datetime

from src.interfaces.sessions.association import ISessionThreadAssociationRepository, ISessionThreadAssociation
from .backends.base import ISessionStorageBackend
from .backends.thread_base import IThreadStorageBackend
from src.core.sessions.association import SessionThreadAssociation
from src.core.common.exceptions import StorageError

logger = get_logger(__name__)


class SessionThreadAssociationRepository(ISessionThreadAssociationRepository):
    """Session-Thread关联仓储实现"""
    
    def __init__(
        self,
        session_backend: ISessionStorageBackend,
        thread_backend: IThreadStorageBackend
    ):
        """初始化关联仓储
        
        Args:
            session_backend: 会话存储后端
            thread_backend: 线程存储后端
        """
        self._session_backend = session_backend
        self._thread_backend = thread_backend
        logger.info("SessionThreadAssociationRepository initialized")
    
    async def create(self, association: Union[ISessionThreadAssociation, SessionThreadAssociation]) -> bool:
        """创建关联
        
        Args:
            association: 关联实体
            
        Returns:
            是否创建成功
        """
        try:
            # 将关联数据保存到会话后端
            association_key = f"association:{association.association_id}"
            association_data = association.to_dict()
            
            success = await self._session_backend.save(association_key, association_data)
            if not success:
                raise StorageError("Failed to save association to session backend")
            
            # 同时在线程后端保存引用
            thread_ref_key = f"thread_associations:{association.thread_id}"
            thread_ref_data = {
                "association_id": association.association_id,
                "session_id": association.session_id,
                "thread_name": association.thread_name,
                "created_at": association.created_at.isoformat()
            }
            
            await self._thread_backend.save(thread_ref_key, thread_ref_data)
            
            logger.debug(f"Created association {association.association_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create association: {e}")
            raise StorageError(f"Failed to create association: {e}")
    
    async def get(self, association_id: str) -> Optional[SessionThreadAssociation]:
        """获取关联
        
        Args:
            association_id: 关联ID
            
        Returns:
            关联实体，不存在返回None
        """
        try:
            association_key = f"association:{association_id}"
            data = await self._session_backend.load(association_key)
            
            if data:
                return SessionThreadAssociation.from_dict(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get association {association_id}: {e}")
            return None
    
    async def get_by_session_and_thread(
        self, 
        session_id: str, 
        thread_id: str
    ) -> Optional[SessionThreadAssociation]:
        """根据Session和Thread ID获取关联
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            关联实体，不存在返回None
        """
        try:
            # 查询会话中的所有关联
            associations = await self.list_by_session(session_id)
            
            for association in associations:
                if association.thread_id == thread_id:
                    return association
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get association by session {session_id} and thread {thread_id}: {e}")
            return None
    
    async def list_by_session(self, session_id: str) -> List[SessionThreadAssociation]:
        """列出Session的所有关联
        
        Args:
            session_id: 会话ID
            
        Returns:
            关联列表
        """
        try:
            # 获取会话的所有键
            session_keys = await self._session_backend.list_keys()
            
            associations = []
            association_prefix = "association:"
            
            for key in session_keys:
                if key.startswith(association_prefix):
                    data = await self._session_backend.load(key)
                    if data and data.get("session_id") == session_id:
                        association = SessionThreadAssociation.from_dict(data)
                        if association.is_active:
                            associations.append(association)
            
            # 按创建时间排序
            associations.sort(key=lambda x: x.created_at, reverse=True)
            logger.debug(f"Found {len(associations)} active associations for session {session_id}")
            return associations
            
        except Exception as e:
            logger.error(f"Failed to list associations by session {session_id}: {e}")
            raise StorageError(f"Failed to list associations by session: {e}")
    
    async def list_by_thread(self, thread_id: str) -> List[SessionThreadAssociation]:
        """列出Thread的所有关联
        
        Args:
            thread_id: 线程ID
            
        Returns:
            关联列表
        """
        try:
            # 获取线程的所有关联引用
            thread_keys = await self._thread_backend.list_keys()
            
            associations = []
            ref_prefix = "thread_associations:"
            
            for key in thread_keys:
                if key.startswith(ref_prefix) and key.endswith(thread_id):
                    ref_data = await self._thread_backend.load(key)
                    if ref_data:
                        association_id = ref_data.get("association_id")
                        if association_id:
                            association = await self.get(association_id)
                            if association and association.is_active:
                                associations.append(association)
            
            # 按创建时间排序
            associations.sort(key=lambda x: x.created_at, reverse=True)
            logger.debug(f"Found {len(associations)} active associations for thread {thread_id}")
            return associations
            
        except Exception as e:
            logger.error(f"Failed to list associations by thread {thread_id}: {e}")
            raise StorageError(f"Failed to list associations by thread: {e}")
    
    async def update(self, association: Union[ISessionThreadAssociation, SessionThreadAssociation]) -> bool:
        """更新关联
        
        Args:
            association: 关联实体
            
        Returns:
            是否更新成功
        """
        try:
            association_key = f"association:{association.association_id}"
            association_data = association.to_dict()
            
            success = await self._session_backend.save(association_key, association_data)
            if not success:
                raise StorageError("Failed to update association in session backend")
            
            logger.debug(f"Updated association {association.association_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update association {association.association_id}: {e}")
            raise StorageError(f"Failed to update association: {e}")
    
    async def delete(self, association_id: str) -> bool:
        """删除关联
        
        Args:
            association_id: 关联ID
            
        Returns:
            是否删除成功
        """
        try:
            # 先获取关联信息
            association = await self.get(association_id)
            if not association:
                return False
            
            # 从会话后端删除
            association_key = f"association:{association_id}"
            session_deleted = await self._session_backend.delete(association_key)
            
            # 从线程后端删除引用
            thread_ref_key = f"thread_associations:{association.thread_id}"
            thread_deleted = await self._thread_backend.delete(thread_ref_key)
            
            success = session_deleted and thread_deleted
            if success:
                logger.debug(f"Deleted association {association_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete association {association_id}: {e}")
            raise StorageError(f"Failed to delete association: {e}")
    
    async def delete_by_session_and_thread(self, session_id: str, thread_id: str) -> bool:
        """根据Session和Thread ID删除关联
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        try:
            association = await self.get_by_session_and_thread(session_id, thread_id)
            if association:
                return await self.delete(association.association_id)
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete association by session {session_id} and thread {thread_id}: {e}")
            raise StorageError(f"Failed to delete association: {e}")
    
    async def exists(self, session_id: str, thread_id: str) -> bool:
        """检查关联是否存在
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        try:
            association = await self.get_by_session_and_thread(session_id, thread_id)
            return association is not None and association.is_active
            
        except Exception as e:
            logger.error(f"Failed to check association existence for session {session_id} and thread {thread_id}: {e}")
            return False
    
    async def get_active_associations_by_session(self, session_id: str) -> List[SessionThreadAssociation]:
        """获取Session的活跃关联
        
        Args:
            session_id: 会话ID
            
        Returns:
            活跃关联列表
        """
        return await self.list_by_session(session_id)
    
    async def cleanup_inactive_associations(self, max_age_days: int = 30) -> int:
        """清理非活跃关联
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的关联数量
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            # 获取所有关联
            session_keys = await self._session_backend.list_keys()
            association_prefix = "association:"
            
            for key in session_keys:
                if key.startswith(association_prefix):
                    data = await self._session_backend.load(key)
                    if data:
                        association = SessionThreadAssociation.from_dict(data)
                        
                        # 清理条件：非活跃或超过保留期限
                        should_delete = (
                            not association.is_active or 
                            association.updated_at < cutoff_date
                        )
                        
                        if should_delete:
                            if await self.delete(association.association_id):
                                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} inactive associations")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup inactive associations: {e}")
            raise StorageError(f"Failed to cleanup inactive associations: {e}")