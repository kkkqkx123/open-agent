"""内存检查点Repository实现"""

import time
import uuid
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ICheckpointRepository
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class MemoryCheckpointRepository(ICheckpointRepository):
    """内存检查点Repository实现 - 直接使用内存存储"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存检查点Repository"""
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._thread_index: Dict[str, List[str]] = {}
        self._workflow_index: Dict[str, List[str]] = {}
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存checkpoint数据"""
        try:
            checkpoint_id = checkpoint_data.get("checkpoint_id")
            if not checkpoint_id:
                checkpoint_id = str(uuid.uuid4())
            
            # 添加时间戳
            current_time = time.time()
            full_checkpoint = {
                "checkpoint_id": checkpoint_id,
                "created_at": current_time,
                "updated_at": current_time,
                **checkpoint_data
            }
            
            # 保存到存储
            self._storage[checkpoint_id] = full_checkpoint
            
            # 更新索引
            thread_id = checkpoint_data["thread_id"]
            if thread_id not in self._thread_index:
                self._thread_index[thread_id] = []
            if checkpoint_id not in self._thread_index[thread_id]:
                self._thread_index[thread_id].append(checkpoint_id)
            
            if "workflow_id" in checkpoint_data:
                workflow_id = checkpoint_data["workflow_id"]
                if workflow_id not in self._workflow_index:
                    self._workflow_index[workflow_id] = []
                if checkpoint_id not in self._workflow_index[workflow_id]:
                    self._workflow_index[workflow_id].append(checkpoint_id)
            
            logger.debug(f"Memory checkpoint saved: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save memory checkpoint: {e}")
            raise
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            checkpoint = self._storage.get(checkpoint_id)
            if checkpoint:
                logger.debug(f"Memory checkpoint loaded: {checkpoint_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to load memory checkpoint {checkpoint_id}: {e}")
            raise
    
    async def list_checkpoints(
        self, 
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出指定thread的所有checkpoint"""
        try:
            checkpoint_ids = self._thread_index.get(thread_id, [])
            checkpoints = [self._storage[cid] for cid in checkpoint_ids if cid in self._storage]
            
            # 按创建时间倒序排序
            checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
            
            # 应用limit限制
            if limit is not None:
                checkpoints = checkpoints[:limit]
            
            logger.debug(f"Listed memory checkpoints for {thread_id}: {len(checkpoints)} items")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list memory checkpoints for {thread_id}: {e}")
            raise
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        try:
            checkpoint = self._storage.get(checkpoint_id)
            if not checkpoint:
                return False
            
            # 从索引中移除
            thread_id = checkpoint["thread_id"]
            if thread_id in self._thread_index and checkpoint_id in self._thread_index[thread_id]:
                self._thread_index[thread_id].remove(checkpoint_id)
            
            if "workflow_id" in checkpoint:
                workflow_id = checkpoint["workflow_id"]
                if workflow_id in self._workflow_index and checkpoint_id in self._workflow_index[workflow_id]:
                    self._workflow_index[workflow_id].remove(checkpoint_id)
            
            # 从存储中删除
            del self._storage[checkpoint_id]
            logger.debug(f"Memory checkpoint deleted: {checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory checkpoint {checkpoint_id}: {e}")
            raise
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            logger.error(f"Failed to get latest memory checkpoint for {thread_id}: {e}")
            raise
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            checkpoint_ids = self._workflow_index.get(workflow_id, [])
            checkpoints = [self._storage[cid] for cid in checkpoint_ids if cid in self._storage]
            
            # 过滤指定thread的检查点
            checkpoints = [cp for cp in checkpoints if cp.get("thread_id") == thread_id]
            
            # 按创建时间倒序排序
            checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
            
            logger.debug(f"Got workflow memory checkpoints for {thread_id}/{workflow_id}: {len(checkpoints)} items")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to get workflow memory checkpoints for {thread_id}/{workflow_id}: {e}")
            raise
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            
            if len(checkpoints) <= max_count:
                return 0
            
            # 需要删除的checkpoint
            to_delete = checkpoints[max_count:]
            
            # 删除旧checkpoint
            deleted_count = 0
            for checkpoint in to_delete:
                checkpoint_id = checkpoint["checkpoint_id"]
                if await self.delete_checkpoint(checkpoint_id):
                    deleted_count += 1
            
            logger.debug(f"Cleaned up old memory checkpoints for {thread_id}: deleted {deleted_count} items")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old memory checkpoints for {thread_id}: {e}")
            raise