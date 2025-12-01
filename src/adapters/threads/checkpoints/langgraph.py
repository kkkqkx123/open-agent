"""LangGraph检查点适配器

实现Thread检查点的LangGraph适配器，作为反防腐层。
"""

from src.services.logger import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, ChannelVersions
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.config import RunnableConfig

from src.core.threads.checkpoints.storage.repository import IThreadCheckpointRepository
from src.core.threads.checkpoints.storage.models import ThreadCheckpoint, CheckpointStatus
from src.core.threads.checkpoints.storage.exceptions import CheckpointStorageError


logger = get_logger(__name__)


class LangGraphCheckpointAdapter(IThreadCheckpointRepository):
    """LangGraph检查点适配器 - 纯技术实现
    
    作为反防腐层，将领域模型转换为LangGraph格式。
    """
    
    def __init__(self, langgraph_checkpointer: BaseCheckpointSaver):
        """初始化适配器
        
        Args:
            langgraph_checkpointer: LangGraph检查点保存器
        """
        self._checkpointer = langgraph_checkpointer
        logger.info("LangGraphCheckpointAdapter initialized")
    
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存检查点 - 技术实现
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            是否保存成功
        """
        try:
            # 创建配置
            lg_config = RunnableConfig(configurable={"thread_id": checkpoint.thread_id})
            
            # 转换为LangGraph格式
            lg_checkpoint = self._convert_to_langgraph_checkpoint(checkpoint)
            
            # 创建检查点元数据
            lg_metadata: CheckpointMetadata = {
                "source": "update",
                "step": 0,
                "parents": {}
            }
            
            # 创建空的新版本
            lg_new_versions: ChannelVersions = {}
            
            # 调用LangGraph API（同步调用）
            self._checkpointer.put(lg_config, lg_checkpoint, lg_metadata, lg_new_versions)
            
            logger.debug(f"Saved checkpoint {checkpoint.id} to LangGraph")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint.id} to LangGraph: {e}")
            raise CheckpointStorageError(f"LangGraph save failed: {e}", operation="save")
    
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """根据ID查找检查点 - 技术实现
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点实体，不存在返回None
        """
        try:
            # 创建配置用于查询
            lg_config = RunnableConfig(configurable={"checkpoint_id": checkpoint_id})
            
            # 从LangGraph加载
            lg_checkpoint = self._checkpointer.get(lg_config)
            if not lg_checkpoint:
                return None
            
            # 转换为领域模型
            return self._convert_from_langgraph_checkpoint(lg_checkpoint)
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id} from LangGraph: {e}")
            raise CheckpointStorageError(f"LangGraph load failed: {e}", operation="load")
    
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有检查点 - 技术实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点列表
        """
        try:
            # 创建LangGraph配置
            lg_config = RunnableConfig(configurable={"thread_id": thread_id})
            
            # 获取检查点列表
            lg_checkpoint_tuples = self._checkpointer.list(lg_config)
            
            # 转换为领域模型
            checkpoints = []
            for checkpoint_tuple in lg_checkpoint_tuples:
                try:
                    checkpoint = self._convert_from_langgraph_checkpoint(checkpoint_tuple.checkpoint)
                    if checkpoint:
                        checkpoints.append(checkpoint)
                except Exception as e:
                    logger.warning(f"Failed to convert LangGraph checkpoint: {e}")
                    continue
            
            # 按创建时间排序（最新的在前）
            checkpoints.sort(key=lambda x: x.created_at, reverse=True)
            
            logger.debug(f"Found {len(checkpoints)} checkpoints for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"LangGraph list failed: {e}", operation="list")
    
    async def find_active_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有活跃检查点 - 技术实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            活跃检查点列表
        """
        try:
            # 获取所有检查点
            all_checkpoints = await self.find_by_thread(thread_id)
            
            # 过滤活跃检查点
            active_checkpoints = [
                cp for cp in all_checkpoints 
                if cp.status == CheckpointStatus.ACTIVE and not cp.is_expired()
            ]
            
            logger.debug(f"Found {len(active_checkpoints)} active checkpoints for thread {thread_id}")
            return active_checkpoints
            
        except Exception as e:
            logger.error(f"Failed to find active checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"LangGraph filter failed: {e}", operation="filter")
    
    async def find_by_status(self, status: CheckpointStatus) -> List[ThreadCheckpoint]:
        """根据状态查找检查点 - 技术实现
        
        Args:
            status: 检查点状态
            
        Returns:
            检查点列表
        """
        try:
            # LangGraph不直接支持状态过滤，需要获取所有检查点后过滤
            # 这里简化实现，实际可能需要根据具体LangGraph实现调整
            logger.warning("LangGraph adapter does not support efficient status filtering")
            
            # 返回空列表，表示不支持此操作
            return []
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints with status {status}: {e}")
            raise CheckpointStorageError(f"LangGraph filter failed: {e}", operation="filter")
    
    async def find_by_type(self, checkpoint_type) -> List[ThreadCheckpoint]:
        """根据类型查找检查点 - 技术实现
        
        Args:
            checkpoint_type: 检查点类型
            
        Returns:
            检查点列表
        """
        try:
            # LangGraph不直接支持类型过滤，需要获取所有检查点后过滤
            logger.warning("LangGraph adapter does not support efficient type filtering")
            
            # 返回空列表，表示不支持此操作
            return []
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints with type {checkpoint_type}: {e}")
            raise CheckpointStorageError(f"LangGraph filter failed: {e}", operation="filter")
    
    async def find_expired(self, before_time: Optional[datetime] = None) -> List[ThreadCheckpoint]:
        """查找过期的检查点 - 技术实现
        
        Args:
            before_time: 过期时间点，None表示当前时间
            
        Returns:
            过期检查点列表
        """
        try:
            # LangGraph不直接支持过期时间过滤，需要获取所有检查点后过滤
            logger.warning("LangGraph adapter does not support efficient expiration filtering")
            
            # 返回空列表，表示不支持此操作
            return []
            
        except Exception as e:
            logger.error(f"Failed to find expired checkpoints: {e}")
            raise CheckpointStorageError(f"LangGraph filter failed: {e}", operation="filter")
    
    async def update(self, checkpoint: ThreadCheckpoint) -> bool:
        """更新检查点 - 技术实现
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            是否更新成功
        """
        try:
            # LangGraph的put操作会覆盖现有检查点
            return await self.save(checkpoint)
            
        except Exception as e:
            logger.error(f"Failed to update checkpoint {checkpoint.id}: {e}")
            raise CheckpointStorageError(f"LangGraph update failed: {e}", operation="update")
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点 - 技术实现
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        try:
            # LangGraph可能不直接支持删除操作
            # 这里简化实现，实际可能需要根据具体LangGraph实现调整
            logger.warning("LangGraph adapter may not support checkpoint deletion")
            
            # 返回False，表示不支持此操作
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            raise CheckpointStorageError(f"LangGraph delete failed: {e}", operation="delete")
    
    async def delete_by_thread(self, thread_id: str) -> int:
        """删除Thread的所有检查点 - 技术实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            删除的检查点数量
        """
        try:
            # LangGraph可能不直接支持批量删除操作
            logger.warning("LangGraph adapter does not support batch deletion")
            
            # 返回0，表示不支持此操作
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"LangGraph batch delete failed: {e}", operation="batch_delete")
    
    async def delete_expired(self, before_time: Optional[datetime] = None) -> int:
        """删除过期的检查点 - 技术实现
        
        Args:
            before_time: 过期时间点，None表示当前时间
            
        Returns:
            删除的检查点数量
        """
        try:
            # LangGraph可能不直接支持批量删除操作
            logger.warning("LangGraph adapter does not support batch deletion")
            
            # 返回0，表示不支持此操作
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete expired checkpoints: {e}")
            raise CheckpointStorageError(f"LangGraph batch delete failed: {e}", operation="batch_delete")
    
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量 - 技术实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点数量
        """
        try:
            checkpoints = await self.find_by_thread(thread_id)
            return len(checkpoints)
            
        except Exception as e:
            logger.error(f"Failed to count checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"LangGraph count failed: {e}", operation="count")
    
    async def count_by_status(self, status: CheckpointStatus) -> int:
        """根据状态统计检查点数量 - 技术实现
        
        Args:
            status: 检查点状态
            
        Returns:
            检查点数量
        """
        try:
            # LangGraph不直接支持状态过滤
            logger.warning("LangGraph adapter does not support efficient status counting")
            
            # 返回0，表示不支持此操作
            return 0
            
        except Exception as e:
            logger.error(f"Failed to count checkpoints with status {status}: {e}")
            raise CheckpointStorageError(f"LangGraph count failed: {e}", operation="count")
    
    async def get_statistics(self, thread_id: Optional[str] = None) -> Any:
        """获取检查点统计信息 - 技术实现
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            统计信息
        """
        try:
            # LangGraph不直接支持统计功能
            logger.warning("LangGraph adapter does not support statistics")
            
            # 返回None，表示不支持此操作
            return None
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise CheckpointStorageError(f"LangGraph statistics failed: {e}", operation="statistics")
    
    async def exists(self, checkpoint_id: str) -> bool:
        """检查检查点是否存在 - 技术实现
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否存在
        """
        try:
            checkpoint = await self.find_by_id(checkpoint_id)
            return checkpoint is not None
            
        except Exception as e:
            logger.error(f"Failed to check existence of checkpoint {checkpoint_id}: {e}")
            raise CheckpointStorageError(f"LangGraph exists check failed: {e}", operation="exists")
    
    async def find_latest_by_thread(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """查找Thread的最新检查点 - 技术实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最新检查点，不存在返回None
        """
        try:
            checkpoints = await self.find_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            logger.error(f"Failed to find latest checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"LangGraph find latest failed: {e}", operation="find_latest")
    
    async def find_oldest_by_thread(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """查找Thread的最旧检查点 - 技术实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最旧检查点，不存在返回None
        """
        try:
            checkpoints = await self.find_by_thread(thread_id)
            return checkpoints[-1] if checkpoints else None
            
        except Exception as e:
            logger.error(f"Failed to find oldest checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"LangGraph find oldest failed: {e}", operation="find_oldest")
    
    # 私有方法 - 格式转换
    def _convert_to_langgraph_checkpoint(self, checkpoint: ThreadCheckpoint) -> Checkpoint:
        """将领域检查点转换为LangGraph格式
        
        Args:
            checkpoint: 领域检查点
            
        Returns:
            LangGraph检查点
        """
        return Checkpoint(
            v=1,
            id=checkpoint.id,
            ts=checkpoint.created_at.isoformat(),
            channel_values=checkpoint.state_data,
            channel_versions={},
            versions_seen={},
            updated_channels=list(checkpoint.state_data.keys()) if checkpoint.state_data else None
        )
    
    def _convert_from_langgraph_checkpoint(self, lg_checkpoint: Checkpoint) -> Optional[ThreadCheckpoint]:
        """将LangGraph检查点转换为领域模型
        
        Args:
            lg_checkpoint: LangGraph检查点
            
        Returns:
            领域检查点，转换失败返回None
        """
        try:
            # 从时间戳解析为 datetime
            created_at = datetime.fromisoformat(lg_checkpoint["ts"])
            updated_at = created_at
            
            # 构建领域模型
            checkpoint_data = {
                "id": lg_checkpoint["id"],
                "thread_id": "",  # LangGraph checkpoint不包含thread_id
                "state_data": lg_checkpoint["channel_values"],
                "metadata": {},
                "status": "active",  # 默认状态
                "checkpoint_type": "auto",  # 默认类型
                "created_at": created_at,
                "updated_at": updated_at,
                "expires_at": None,
                "size_bytes": 0,
                "restore_count": 0,
                "last_restored_at": None,
            }
            
            return ThreadCheckpoint.from_dict(checkpoint_data)
            
        except Exception as e:
            logger.error(f"Failed to convert LangGraph checkpoint to domain model: {e}")
            return None


class MemoryLangGraphCheckpointAdapter(LangGraphCheckpointAdapter):
    """内存LangGraph检查点适配器
    
    使用内存存储的LangGraph适配器实现。
    """
    
    def __init__(self):
        """初始化内存LangGraph适配器"""
        super().__init__(MemorySaver())
        logger.info("MemoryLangGraphCheckpointAdapter initialized")