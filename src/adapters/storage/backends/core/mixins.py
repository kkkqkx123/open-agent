"""存储业务逻辑混入类

提供会话和线程特定的业务逻辑实现。
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from src.interfaces.storage import ISessionStorage, IThreadStorage, IStorageProvider
from .exceptions import StorageBackendError, ValidationError


logger = get_logger(__name__)


class SessionStorageMixin:
    """会话存储混入类
    
    封装会话特定的业务逻辑，与存储技术解耦。
    """
    
    def __init__(self, provider: IStorageProvider):
        """初始化会话存储混入
        
        Args:
            provider: 存储提供者实例
        """
        self._provider = provider
        self._table_name = "sessions"
    
    async def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据
            
        Returns:
            是否保存成功
        """
        try:
            # 验证数据
            self._validate_session_data(data)
            
            # 添加会话特定字段
            session_data = self._prepare_session_data(session_id, data)
            
            # 保存到存储
            result_id = await self._provider.save(self._table_name, session_data)
            
            logger.debug(f"Session saved: {session_id}")
            return result_id == session_id
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise StorageBackendError(f"Failed to save session: {e}")
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，不存在返回None
        """
        try:
            # 从存储加载
            storage_data = await self._provider.load(self._table_name, session_id)
            
            if storage_data is None:
                return None
            
            # 转换为业务数据
            session_data = self._extract_session_data(storage_data)
            
            logger.debug(f"Session loaded: {session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise StorageBackendError(f"Failed to load session: {e}")
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            result = await self._provider.delete(self._table_name, session_id)
            
            if result:
                logger.debug(f"Session deleted: {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise StorageBackendError(f"Failed to delete session: {e}")
    
    async def list_sessions(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            会话列表
        """
        try:
            # 从存储查询
            storage_results = await self._provider.list(self._table_name, filters, limit)
            
            # 转换为业务数据
            sessions = []
            for storage_data in storage_results:
                try:
                    session_data = self._extract_session_data(storage_data)
                    sessions.append(session_data)
                except Exception as e:
                    logger.warning(f"Failed to extract session data: {e}")
                    continue
            
            logger.debug(f"Listed {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise StorageBackendError(f"Failed to list sessions: {e}")
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        try:
            return await self._provider.exists(self._table_name, session_id)
        except Exception as e:
            logger.error(f"Failed to check session existence: {e}")
            raise StorageBackendError(f"Failed to check session existence: {e}")
    
    async def get_session_threads(self, session_id: str) -> List[str]:
        """获取会话关联的线程ID列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程ID列表
        """
        try:
            session_data = await self.load_session(session_id)
            if session_data is None:
                return []
            
            return session_data.get("thread_ids", [])
            
        except Exception as e:
            logger.error(f"Failed to get session threads: {e}")
            raise StorageBackendError(f"Failed to get session threads: {e}")
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态
        
        Args:
            session_id: 会话ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        try:
            updates = {
                "status": status,
                "updated_at": time.time()
            }
            
            result = await self._provider.update(self._table_name, session_id, updates)
            
            if result:
                logger.debug(f"Session status updated: {session_id} -> {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            raise StorageBackendError(f"Failed to update session status: {e}")
    
    def _validate_session_data(self, data: Dict[str, Any]) -> None:
        """验证会话数据
        
        Args:
            data: 会话数据
            
        Raises:
            ValidationError: 数据无效时抛出
        """
        required_fields = ["status"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}", field_name=field)
        
        # 验证状态值
        valid_statuses = ["active", "inactive", "completed", "failed"]
        if data["status"] not in valid_statuses:
            raise ValidationError(
                f"Invalid status: {data['status']}, must be one of {valid_statuses}",
                field_name="status"
            )
    
    def _prepare_session_data(self, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备会话数据用于存储
        
        Args:
            session_id: 会话ID
            data: 原始会话数据
            
        Returns:
            存储格式的会话数据
        """
        current_time = time.time()
        
        session_data = {
            "id": session_id,
            "status": data["status"],
            "message_count": data.get("message_count", 0),
            "checkpoint_count": data.get("checkpoint_count", 0),
            "created_at": data.get("created_at", current_time),
            "updated_at": current_time,
            "metadata": data.get("metadata", {}),
            "tags": data.get("tags", []),
            "thread_ids": data.get("thread_ids", [])
        }
        
        return session_data
    
    def _extract_session_data(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """从存储数据提取会话数据
        
        Args:
            storage_data: 存储格式的数据
            
        Returns:
            业务格式的会话数据
        """
        return {
            "session_id": storage_data["id"],
            "status": storage_data["status"],
            "message_count": storage_data["message_count"],
            "checkpoint_count": storage_data["checkpoint_count"],
            "created_at": storage_data["created_at"],
            "updated_at": storage_data["updated_at"],
            "metadata": storage_data["metadata"],
            "tags": storage_data["tags"],
            "thread_ids": storage_data["thread_ids"]
        }


class ThreadStorageMixin:
    """线程存储混入类
    
    封装线程特定的业务逻辑，与存储技术解耦。
    """
    
    def __init__(self, provider: IStorageProvider):
        """初始化线程存储混入
        
        Args:
            provider: 存储提供者实例
        """
        self._provider = provider
        self._table_name = "threads"
    
    async def save_thread(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据
        
        Args:
            thread_id: 线程ID
            data: 线程数据
            
        Returns:
            是否保存成功
        """
        try:
            # 验证数据
            self._validate_thread_data(data)
            
            # 添加线程特定字段
            thread_data = self._prepare_thread_data(thread_id, data)
            
            # 保存到存储
            result_id = await self._provider.save(self._table_name, thread_data)
            
            logger.debug(f"Thread saved: {thread_id}")
            return result_id == thread_id
            
        except Exception as e:
            logger.error(f"Failed to save thread {thread_id}: {e}")
            raise StorageBackendError(f"Failed to save thread: {e}")
    
    async def load_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程数据，不存在返回None
        """
        try:
            # 从存储加载
            storage_data = await self._provider.load(self._table_name, thread_id)
            
            if storage_data is None:
                return None
            
            # 转换为业务数据
            thread_data = self._extract_thread_data(storage_data)
            
            logger.debug(f"Thread loaded: {thread_id}")
            return thread_data
            
        except Exception as e:
            logger.error(f"Failed to load thread {thread_id}: {e}")
            raise StorageBackendError(f"Failed to load thread: {e}")
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        try:
            result = await self._provider.delete(self._table_name, thread_id)
            
            if result:
                logger.debug(f"Thread deleted: {thread_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise StorageBackendError(f"Failed to delete thread: {e}")
    
    async def list_threads(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出线程
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            线程列表
        """
        try:
            # 从存储查询
            storage_results = await self._provider.list(self._table_name, filters, limit)
            
            # 转换为业务数据
            threads = []
            for storage_data in storage_results:
                try:
                    thread_data = self._extract_thread_data(storage_data)
                    threads.append(thread_data)
                except Exception as e:
                    logger.warning(f"Failed to extract thread data: {e}")
                    continue
            
            logger.debug(f"Listed {len(threads)} threads")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to list threads: {e}")
            raise StorageBackendError(f"Failed to list threads: {e}")
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        try:
            return await self._provider.exists(self._table_name, thread_id)
        except Exception as e:
            logger.error(f"Failed to check thread existence: {e}")
            raise StorageBackendError(f"Failed to check thread existence: {e}")
    
    async def get_threads_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取线程列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程列表
        """
        try:
            filters = {"session_id": session_id}
            return await self.list_threads(filters)
            
        except Exception as e:
            logger.error(f"Failed to get threads by session: {e}")
            raise StorageBackendError(f"Failed to get threads by session: {e}")
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新线程状态
        
        Args:
            thread_id: 线程ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        try:
            updates = {
                "status": status,
                "updated_at": time.time()
            }
            
            result = await self._provider.update(self._table_name, thread_id, updates)
            
            if result:
                logger.debug(f"Thread status updated: {thread_id} -> {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update thread status: {e}")
            raise StorageBackendError(f"Failed to update thread status: {e}")
    
    async def get_thread_branches(self, thread_id: str) -> List[str]:
        """获取线程关联的分支ID列表
        
        Args:
            thread_id: 线程ID
            
        Returns:
            分支ID列表
        """
        try:
            thread_data = await self.load_thread(thread_id)
            if thread_data is None:
                return []
            
            return thread_data.get("branch_ids", [])
            
        except Exception as e:
            logger.error(f"Failed to get thread branches: {e}")
            raise StorageBackendError(f"Failed to get thread branches: {e}")
    
    def _validate_thread_data(self, data: Dict[str, Any]) -> None:
        """验证线程数据
        
        Args:
            data: 线程数据
            
        Raises:
            ValidationError: 数据无效时抛出
        """
        required_fields = ["session_id", "status"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}", field_name=field)
        
        # 验证状态值
        valid_statuses = ["active", "inactive", "completed", "failed", "paused"]
        if data["status"] not in valid_statuses:
            raise ValidationError(
                f"Invalid status: {data['status']}, must be one of {valid_statuses}",
                field_name="status"
            )
    
    def _prepare_thread_data(self, thread_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备线程数据用于存储
        
        Args:
            thread_id: 线程ID
            data: 原始线程数据
            
        Returns:
            存储格式的线程数据
        """
        current_time = time.time()
        
        thread_data = {
            "id": thread_id,
            "session_id": data["session_id"],
            "status": data["status"],
            "created_at": data.get("created_at", current_time),
            "updated_at": current_time,
            "metadata": data.get("metadata", {}),
            "tags": data.get("tags", []),
            "branch_ids": data.get("branch_ids", [])
        }
        
        return thread_data
    
    def _extract_thread_data(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """从存储数据提取线程数据
        
        Args:
            storage_data: 存储格式的数据
            
        Returns:
            业务格式的线程数据
        """
        return {
            "thread_id": storage_data["id"],
            "session_id": storage_data["session_id"],
            "status": storage_data["status"],
            "created_at": storage_data["created_at"],
            "updated_at": storage_data["updated_at"],
            "metadata": storage_data["metadata"],
            "tags": storage_data["tags"],
            "branch_ids": storage_data["branch_ids"]
        }