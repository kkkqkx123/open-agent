"""会话存储混入类

提供会话特定的业务逻辑实现。
"""

import time
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from .base_mixin import BaseStorageMixin
from ..exceptions import ValidationError


logger = get_logger(__name__)


class SessionStorageMixin(BaseStorageMixin):
    """会话存储混入类
    
    封装会话特定的业务逻辑，与存储技术解耦。
    """
    
    def __init__(self, provider):
        """初始化会话存储混入
        
        Args:
            provider: 存储提供者实例
        """
        super().__init__(provider, "sessions")
    
    async def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据
            
        Returns:
            是否保存成功
        """
        return await self.save(session_id, data)
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，不存在返回None
        """
        return await self.load(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        return await self.delete(session_id)
    
    async def list_sessions(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            会话列表
        """
        return await self.list(filters, limit)
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        return await self.exists(session_id)
    
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
            raise
    
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
            
            result = await self.update(session_id, updates)
            
            if result:
                logger.debug(f"Session status updated: {session_id} -> {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            raise
    
    def _prepare_data(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备会话数据用于存储
        
        Args:
            id: 会话ID
            data: 原始会话数据
            
        Returns:
            存储格式的会话数据
        """
        current_time = time.time()
        
        session_data = {
            "id": id,
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
    
    def _extract_data(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
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