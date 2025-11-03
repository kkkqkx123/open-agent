"""Thread管理器实现"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from .interfaces import IThreadManager
from ...infrastructure.threads.metadata_store import IThreadMetadataStore
from ...domain.checkpoint.interfaces import ICheckpointManager

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

        state_data = latest_checkpoint.get("state_data")
        if not isinstance(state_data, dict):
            return {}
        return state_data
    
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
    
    async def fork_thread(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支"""
        # 验证源thread存在
        if not await self.thread_exists(source_thread_id):
            raise ValueError(f"源thread不存在: {source_thread_id}")
        
        # 验证checkpoint存在
        checkpoint = await self.checkpoint_manager.get_checkpoint(source_thread_id, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"checkpoint不存在: {checkpoint_id}")
        
        # 获取源thread信息
        source_info = await self.get_thread_info(source_thread_id)
        if not source_info:
            raise RuntimeError(f"无法获取源thread信息: {source_thread_id}")
        
        # 创建新thread
        new_thread_id = await self.create_thread(
            graph_id=source_info.get("graph_id", "default_graph"),
            metadata={
                "branch_name": branch_name,
                "source_thread_id": source_thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_type": "fork",
                **(metadata or {})
            }
        )
        
        # 复制checkpoint状态到新thread
        state_data = checkpoint.get("state_data", {})
        success = await self.update_thread_state(new_thread_id, state_data)
        if not success:
            logger.warning(f"复制checkpoint状态到新thread失败: {new_thread_id}")
        
        return new_thread_id
    
    async def create_thread_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建thread状态快照"""
        # 验证thread存在
        if not await self.thread_exists(thread_id):
            raise ValueError(f"Thread不存在: {thread_id}")
        
        # 获取所有checkpoints
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        checkpoint_ids = [cp.get("id") for cp in checkpoints if cp.get("id")]
        
        # 创建快照ID
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
        
        # 保存快照信息到thread元数据
        thread_metadata = await self.metadata_store.get_metadata(thread_id)
        if thread_metadata:
            snapshots = thread_metadata.get("snapshots", [])
            snapshots.append({
                "snapshot_id": snapshot_id,
                "thread_id": thread_id,
                "snapshot_name": snapshot_name,
                "description": description,
                "checkpoint_ids": checkpoint_ids,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "total_checkpoints": len(checkpoint_ids)
                }
            })
            thread_metadata["snapshots"] = snapshots
            thread_metadata["updated_at"] = datetime.now().isoformat()
            await self.metadata_store.save_metadata(thread_id, thread_metadata)
        
        return snapshot_id
    
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚thread到指定checkpoint"""
        # 1. 验证checkpoint存在
        checkpoint = await self.checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
        if not checkpoint:
            return False
        
        # 2. 创建回滚checkpoint（用于undo）
        rollback_metadata = {
            "rollback_from": checkpoint_id,
            "rollback_reason": "user_requested",
            "original_state": await self.get_thread_state(thread_id)
        }
        
        # 3. 恢复状态
        await self.checkpoint_manager.restore_from_checkpoint(thread_id, checkpoint_id)
        
        # 4. 记录回滚操作
        await self.metadata_store.update_metadata(thread_id, {
            "last_rollback": datetime.now().isoformat(),
            "rollback_checkpoint": checkpoint_id
        })
        
        return True
    
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取thread历史记录"""
        if not await self.thread_exists(thread_id):
            return []
        
        # 获取所有checkpoints
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        
        # 应用限制
        if limit and len(checkpoints) > limit:
            checkpoints = checkpoints[:limit]
        
        return checkpoints
