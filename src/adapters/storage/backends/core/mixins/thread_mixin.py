"""线程存储混入类

提供线程特定的业务逻辑实现。
"""

import time
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from .base_mixin import BaseStorageMixin
from ..exceptions import ValidationError


logger = get_logger(__name__)


class ThreadStorageMixin(BaseStorageMixin):
    """线程存储混入类
    
    封装线程特定的业务逻辑，与存储技术解耦。
    """
    
    def __init__(self, provider):
        """初始化线程存储混入
        
        Args:
            provider: 存储提供者实例
        """
        super().__init__(provider, "threads")
    
    async def save_thread(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据
        
        Args:
            thread_id: 线程ID
            data: 线程数据
            
        Returns:
            是否保存成功
        """
        return await self.save(thread_id, data)
    
    async def load_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程数据，不存在返回None
        """
        return await self.load(thread_id)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        return await self.delete(thread_id)
    
    async def list_threads(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出线程
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            线程列表
        """
        return await self.list(filters, limit)
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        return await self.exists(thread_id)
    
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
            raise
    
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
            
            result = await self.update(thread_id, updates)
            
            if result:
                logger.debug(f"Thread status updated: {thread_id} -> {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update thread status: {e}")
            raise
    
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
            raise
    
    def _prepare_data(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备线程数据用于存储
        
        Args:
            id: 线程ID
            data: 原始线程数据
            
        Returns:
            存储格式的线程数据
        """
        current_time = time.time()
        
        thread_data = {
            "id": id,
            "session_id": data["session_id"],
            "status": data["status"],
            "created_at": data.get("created_at", current_time),
            "updated_at": current_time,
            "metadata": data.get("metadata", {}),
            "tags": data.get("tags", []),
            "branch_ids": data.get("branch_ids", [])
        }
        
        return thread_data
    
    def _extract_data(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
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