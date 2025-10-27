"""Thread管理器实现"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from .interfaces import IThreadManager
from ...infrastructure.threads.metadata_store import IThreadMetadataStore
from ...application.checkpoint.interfaces import ICheckpointManager

logger = logging.getLogger(__name__)


class ThreadManager(IThreadManager):
    """Thread管理器实现"""
    
    def __init__(
        self,
        metadata_store: IThreadMetadataStore,
        checkpoint_manager: ICheckpointManager
    ):
        """初始化Thread管理器
        
        Args:
            metadata_store: Thread元数据存储
            checkpoint_manager: Checkpoint管理器
        """
        self.metadata_store = metadata_store
        self.checkpoint_manager = checkpoint_manager
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread"""
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        # 创建Thread元数据
        thread_metadata = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "checkpoint_count": 0,
            "total_steps": 0,
            **(metadata or {})
        }
        
        # 保存元数据
        success = await self.metadata_store.save_metadata(thread_id, thread_metadata)
        if not success:
            logger.error(f"保存Thread元数据失败: {thread_id}")
            raise RuntimeError(f"创建Thread失败: {thread_id}")
        
        logger.info(f"创建Thread成功: {thread_id}, graph_id: {graph_id}")
        return thread_id
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        if not metadata:
            return None
        
        # 获取checkpoint数量
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        metadata["checkpoint_count"] = len(checkpoints)
        
        # 获取最新checkpoint状态
        latest_checkpoint = await self.checkpoint_manager.get_latest_checkpoint(thread_id)
        if latest_checkpoint:
            metadata["latest_checkpoint_id"] = latest_checkpoint.get("id")
            metadata["latest_checkpoint_created_at"] = latest_checkpoint.get("created_at")
        
        return metadata
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        if not metadata:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        metadata["status"] = status
        metadata["updated_at"] = datetime.now().isoformat()
        
        success = await self.metadata_store.save_metadata(thread_id, metadata)
        if success:
            logger.info(f"Thread状态更新成功: {thread_id} -> {status}")
        
        return success
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        current_metadata = await self.metadata_store.get_metadata(thread_id)
        if not current_metadata:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 合并元数据，保留系统字段
        system_fields = {"thread_id", "graph_id", "created_at", "checkpoint_count"}
        updated_metadata = {
            k: v for k, v in current_metadata.items() 
            if k in system_fields
        }
        updated_metadata.update(metadata)
        updated_metadata["updated_at"] = datetime.now().isoformat()
        
        success = await self.metadata_store.save_metadata(thread_id, updated_metadata)
        if success:
            logger.info(f"Thread元数据更新成功: {thread_id}")
        
        return success
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        # 检查Thread是否存在
        metadata = await self.metadata_store.get_metadata(thread_id)
        if not metadata:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 删除所有checkpoints
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        for checkpoint in checkpoints:
            await self.checkpoint_manager.delete_checkpoint(thread_id, checkpoint["id"])
        
        # 删除元数据
        success = await self.metadata_store.delete_metadata(thread_id)
        if success:
            logger.info(f"Thread删除成功: {thread_id}")
        
        return success
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads"""
        threads = await self.metadata_store.list_threads()
        
        # 应用过滤条件
        if filters:
            filtered_threads = []
            for thread in threads:
                match = True
                for key, value in filters.items():
                    if thread.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_threads.append(thread)
            threads = filtered_threads
        
        # 按创建时间排序
        threads.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 应用数量限制
        if limit:
            threads = threads[:limit]
        
        return threads
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        return metadata is not None
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
        if not await self.thread_exists(thread_id):
            return None
        
        # 获取最新checkpoint
        latest_checkpoint = await self.checkpoint_manager.get_latest_checkpoint(thread_id)
        if not latest_checkpoint:
            return {}
        
        return latest_checkpoint.get("state_data", {})
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        if not await self.thread_exists(thread_id):
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 创建新的checkpoint
        checkpoint_id = await self.checkpoint_manager.create_checkpoint(
            thread_id, 
            "default_workflow",  # 默认工作流ID
            state,
            metadata={"trigger_reason": "thread_state_update"}
        )
        
        if checkpoint_id:
            # 更新Thread元数据
            metadata = await self.metadata_store.get_metadata(thread_id)
            if metadata:
                metadata["updated_at"] = datetime.now().isoformat()
                metadata["total_steps"] = metadata.get("total_steps", 0) + 1
                await self.metadata_store.save_metadata(thread_id, metadata)
            
            logger.info(f"Thread状态更新成功: {thread_id}, checkpoint: {checkpoint_id}")
            return True
        
        return False