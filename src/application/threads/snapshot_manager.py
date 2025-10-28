"""Thread快照管理器"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.threads.models import ThreadSnapshot
from ...domain.threads.interfaces import IThreadManager
from ...application.checkpoint.interfaces import ICheckpointManager


class SnapshotManager:
    """Thread快照管理器"""
    
    def __init__(
        self,
        thread_manager: IThreadManager,
        checkpoint_manager: ICheckpointManager
    ):
        """初始化快照管理器
        
        Args:
            thread_manager: Thread管理器
            checkpoint_manager: Checkpoint管理器
        """
        self.thread_manager = thread_manager
        self.checkpoint_manager = checkpoint_manager
    
    async def create_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建thread快照
        
        Args:
            thread_id: Thread ID
            snapshot_name: 快照名称
            description: 快照描述
            
        Returns:
            快照ID
        """
        # 1. 验证thread存在
        if not await self.thread_manager.thread_exists(thread_id):
            raise ValueError(f"Thread不存在: {thread_id}")
        
        # 2. 获取thread所有checkpoints
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        if not checkpoints:
            # 如果没有checkpoints，创建一个空快照
            checkpoint_ids = []
        else:
            checkpoint_ids = [cp.get("id") for cp in checkpoints if cp.get("id")]
        
        # 3. 创建快照ID
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
        
        # 4. 创建快照记录
        snapshot_metadata = {
            "snapshot_id": snapshot_id,
            "thread_id": thread_id,
            "snapshot_name": snapshot_name,
            "description": description,
            "checkpoint_ids": checkpoint_ids,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "total_checkpoints": len(checkpoint_ids),
                "thread_info": await self.thread_manager.get_thread_info(thread_id)
            }
        }
        
        # 5. 保存快照元数据到thread（简化实现，实际可能需要专门的快照存储）
        thread_metadata = await self.thread_manager.get_thread_info(thread_id)
        if thread_metadata:
            snapshots = thread_metadata.get("snapshots", [])
            snapshots.append(snapshot_metadata)
            await self.thread_manager.update_thread_metadata(thread_id, {
                "snapshots": snapshots
            })
        
        return snapshot_id
    
    async def restore_snapshot(
        self,
        thread_id: str,
        snapshot_id: str
    ) -> bool:
        """从快照恢复thread状态
        
        Args:
            thread_id: Thread ID
            snapshot_id: 快照ID
            
        Returns:
            恢复是否成功
        """
        # 1. 获取thread信息
        thread_info = await self.thread_manager.get_thread_info(thread_id)
        if not thread_info:
            return False
        
        # 2. 查找快照
        snapshots = thread_info.get("snapshots", [])
        target_snapshot = None
        for snapshot in snapshots:
            if snapshot.get("snapshot_id") == snapshot_id:
                target_snapshot = snapshot
                break
        
        if not target_snapshot:
            return False
        
        # 3. 获取快照中的最新checkpoint
        checkpoint_ids = target_snapshot.get("checkpoint_ids", [])
        if not checkpoint_ids:
            # 空快照，创建空状态
            success = await self.thread_manager.update_thread_state(thread_id, {})
        else:
            # 使用最新的checkpoint（假设列表按时间排序，取最后一个）
            latest_checkpoint_id = checkpoint_ids[-1]
            checkpoint = await self.checkpoint_manager.get_checkpoint(thread_id, latest_checkpoint_id)
            if checkpoint:
                state_data = checkpoint.get("state_data", {})
                success = await self.thread_manager.update_thread_state(thread_id, state_data)
            else:
                success = False
        
        if success:
            # 记录恢复操作
            await self.thread_manager.update_thread_metadata(thread_id, {
                "last_restored_snapshot": snapshot_id,
                "restored_at": datetime.now().isoformat()
            })
        
        return success
    
    async def delete_snapshot(
        self,
        snapshot_id: str
    ) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            删除是否成功
        """
        # 这里需要遍历所有threads来找到包含该快照的thread
        # 在实际实现中，应该有专门的快照存储来避免这种低效操作
        
        # 获取所有threads
        threads = await self.thread_manager.list_threads()
        
        for thread in threads:
            thread_id = thread.get("thread_id")
            if not thread_id:
                continue
                
            snapshots = thread.get("snapshots", [])
            updated_snapshots = []
            found = False
            
            for snapshot in snapshots:
                if snapshot.get("snapshot_id") != snapshot_id:
                    updated_snapshots.append(snapshot)
                else:
                    found = True
            
            if found:
                await self.thread_manager.update_thread_metadata(thread_id, {
                    "snapshots": updated_snapshots
                })
                return True
        
        return False