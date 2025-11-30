"""LangGraph集成适配器

将LangGraph的checkpoint接口适配到项目的接口，实现ICheckpointStore和IThreadCheckpointStorage接口。
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from langgraph.checkpoint.base import Checkpoint, CheckpointTuple
from langchain_core.runnables.config import RunnableConfig

from src.interfaces.checkpoint import ICheckpointStore
from src.interfaces.threads.checkpoint import IThreadCheckpointStorage
from src.core.common.exceptions import (
    CheckpointNotFoundError,
    CheckpointStorageError
)
from src.core.common.serialization import Serializer
from src.core.threads.checkpoints.storage.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointStatistics
)


logger = logging.getLogger(__name__)


class ILangGraphAdapter(ABC):
    """LangGraph适配器接口"""
    
    @abstractmethod
    def create_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> RunnableConfig:
        """创建LangGraph标准配置
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            RunnableConfig: LangGraph配置
        """
        pass
    
    @abstractmethod
    def create_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Checkpoint:
        """创建LangGraph标准checkpoint
        
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
            
        Returns:
            Checkpoint: LangGraph checkpoint
        """
        pass
    
    @abstractmethod
    def extract_state(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            metadata: 可选的元数据
            
        Returns:
            Any: 提取的状态
        """
        pass


class LangGraphCheckpointAdapter(ICheckpointStore, IThreadCheckpointStorage, ILangGraphAdapter):
    """LangGraph checkpoint适配器实现
    
    将LangGraph的checkpoint机制适配到ICheckpointStore和IThreadCheckpointStorage接口。
    """
    
    def __init__(self, checkpointer: Any = None):
        """初始化适配器
        
        Args:
            checkpointer: LangGraph checkpointer实例
        """
        self.checkpointer = checkpointer
        self.serializer = Serializer()
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存checkpoint数据
        
        Args:
            data: checkpoint数据字典
            
        Returns:
            str: 保存的数据ID
        """
        try:
            if not self.checkpointer:
                raise CheckpointStorageError("Checkpointer未初始化")
            
            thread_id = data.get("thread_id")
            if not thread_id:
                raise CheckpointStorageError("checkpoint_data必须包含'thread_id'")
            
            # 生成checkpoint ID
            import uuid
            from typing import cast
            checkpoint_id: str = cast(str, data.get("id", str(uuid.uuid4())))
            data["id"] = checkpoint_id
            
            # 创建LangGraph配置
            config = self.create_config(thread_id)
            
            # 提取状态数据
            state_data = data.get("state_data", {})
            workflow_id = data.get("workflow_id", "")
            metadata = data.get("metadata", {})
            
            # 创建LangGraph checkpoint
            langgraph_checkpoint = self.create_checkpoint(state_data, workflow_id, metadata)
            
            # 保存到LangGraph checkpointer
            # LangGraph的put方法需要config, checkpoint, metadata, new_versions参数
            new_versions: dict[str, Any] = {}
            self.checkpointer.put(config, langgraph_checkpoint, metadata, new_versions)
            
            logger.debug(f"Saved checkpoint for thread {thread_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise CheckpointStorageError(f"保存checkpoint失败: {e}") from e
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            if not self.checkpointer:
                raise CheckpointStorageError("Checkpointer未初始化")
            
            # 创建LangGraph配置
            config = self.create_config(thread_id)
            
            # 从LangGraph checkpointer获取checkpoint列表
            checkpoint_tuples = list(self.checkpointer.list(config))
            
            # 转换为内部格式
            checkpoints = []
            for checkpoint_tuple in checkpoint_tuples:
                checkpoint_data = self._convert_checkpoint_tuple(checkpoint_tuple, thread_id)
                if checkpoint_data:
                    checkpoints.append(checkpoint_data)
            
            # 按创建时间倒序排列
            checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
            
            logger.debug(f"Listed {len(checkpoints)} checkpoints for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}") from e
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        try:
            if not self.checkpointer:
                raise CheckpointStorageError("Checkpointer未初始化")
            
            # 创建LangGraph配置
            config = self.create_config(thread_id, checkpoint_id)
            
            # 从LangGraph checkpointer获取checkpoint
            result = self.checkpointer.get(config)
            
            if result is None:
                return None
            
            # 转换为内部格式
            if isinstance(result, CheckpointTuple):
                return self._convert_checkpoint_tuple(result, thread_id)
            elif isinstance(result, dict):
                # 如果直接返回字典，尝试构建checkpoint数据
                state = self.extract_state(result)
                return {
                    "id": str(uuid.uuid4()),  # 生成一个ID
                    "thread_id": thread_id,
                    "session_id": "",
                    "workflow_id": result.get("workflow_id", ""),
                    "state_data": state,
                    "metadata": result.get("metadata", {}),
                    "created_at": result.get("created_at", 0),
                    "updated_at": result.get("updated_at", 0)
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to load checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"加载checkpoint失败: {e}") from e
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID，如果为None则删除所有
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if not self.checkpointer:
                raise CheckpointStorageError("Checkpointer未初始化")
            
            # LangGraph通常没有直接的删除方法，我们可以通过不保存来间接"删除"
            # 但这里我们尝试使用checkpointer的删除功能（如果存在）
            if hasattr(self.checkpointer, 'delete_thread'):
                self.checkpointer.delete_thread(thread_id)
                return True
            else:
                # 如果没有删除功能，返回False
                logger.warning("Checkpointer does not support deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"删除checkpoint失败: {e}") from e
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        try:
            # 获取所有checkpoint并返回最新的
            checkpoints = await self.list_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"获取最新checkpoint失败: {e}") from e
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个
        
        Args:
            thread_id: thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        try:
            # 获取所有checkpoint
            all_checkpoints = await self.list_by_thread(thread_id)
            
            if len(all_checkpoints) <= max_count:
                # 不需要清理
                return 0
            
            # 需要删除的checkpoint（保留最新的max_count个）
            checkpoints_to_delete = all_checkpoints[max_count:]
            
            # 删除旧的checkpoint
            deleted_count = 0
            for checkpoint_data in checkpoints_to_delete:
                checkpoint_id = checkpoint_data.get("id")
                if checkpoint_id:
                    success = await self.delete_by_thread(thread_id, checkpoint_id)
                    if success:
                        deleted_count += 1
            
            logger.debug(f"Cleaned up {deleted_count} old checkpoints for thread {thread_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"清理旧checkpoint失败: {e}") from e
    
    def create_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> RunnableConfig:
        """创建LangGraph标准配置"""
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": ""  # 空的命名空间，表示根命名空间
            }
        }
        if checkpoint_id:
            # 如果提供了checkpoint_id，将其添加到配置中
            config["configurable"]["checkpoint_id"] = checkpoint_id
        return config
    
    def create_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Checkpoint:
        """创建LangGraph标准checkpoint"""
        try:
            # 序列化整个状态
            serialized_state = self.serializer.serialize(state, format=self.serializer.FORMAT_COMPACT_JSON)
        except Exception as e:
            logger.error(f"状态序列化失败: {e}")
            raise CheckpointStorageError(f"状态序列化失败: {e}")
        
        # 创建一个LangGraph兼容的checkpoint结构
        timestamp_iso = self._get_current_timestamp()
        
        checkpoint: Checkpoint = {
            "v": 4,  # LangGraph版本
            "ts": timestamp_iso,
            "id": str(uuid.uuid4()),
            "channel_values": {
                "__root__": serialized_state,  # 使用特殊通道名存储序列化状态
                "workflow_id": workflow_id
            },
            "channel_versions": {
                "__root__": 1,
                "workflow_id": 1
            },
            "versions_seen": {
                "__root__": {"__start__": 1},
                "workflow_id": {"__start__": 1}
            },
            "updated_channels": ["__root__", "workflow_id"]
        }
        
        return checkpoint
    
    def extract_state(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态"""
        if not checkpoint:
            return {}
        
        try:
            # 从checkpoint获取channel_values
            if isinstance(checkpoint, dict):
                channel_values = checkpoint.get("channel_values", {})
            elif hasattr(checkpoint, 'checkpoint'):
                # 如果checkpoint是一个对象，尝试获取其checkpoint属性
                channel_values = checkpoint.checkpoint.get("channel_values", {}) if checkpoint.checkpoint else {}
            else:
                channel_values = {}
            
            # 尝试从特殊通道获取序列化状态
            serialized_state = channel_values.get("__root__")
            if serialized_state is not None:
                # 反序列化完整状态
                return self.serializer.deserialize(serialized_state, format=self.serializer.FORMAT_COMPACT_JSON)
            
            # 尝试从其他可能的通道获取
            for key, value in channel_values.items():
                if key != "workflow_id" and isinstance(value, str):
                    try:
                        # 尝试反序列化这个值
                        return self.serializer.deserialize(value, format=self.serializer.FORMAT_COMPACT_JSON)
                    except:
                        continue
            
            # 如果没有找到，返回空字典
            return {}
        except Exception as e:
            logger.error(f"提取状态失败: {e}")
            return {}
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳（ISO格式）"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _convert_checkpoint_tuple(self, checkpoint_tuple: CheckpointTuple, thread_id: str) -> Optional[Dict[str, Any]]:
        """将LangGraph的CheckpointTuple转换为内部格式"""
        try:
            # 提取checkpoint数据
            checkpoint = checkpoint_tuple.checkpoint
            config = checkpoint_tuple.config
            metadata = checkpoint_tuple.metadata or {}
            
            # 提取状态
            state = self.extract_state(checkpoint, metadata)
            
            # 生成或使用ID
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id", str(uuid.uuid4()))
            
            return {
                "id": checkpoint_id,
                "thread_id": thread_id,
                "session_id": "",  # 从configurable中获取session_id（如果存在）
                "workflow_id": metadata.get("workflow_id", ""),
                "state_data": state,
                "metadata": metadata,
                "created_at": checkpoint.get("ts", self._get_current_timestamp()),
                "updated_at": checkpoint.get("ts", self._get_current_timestamp())
            }
        except Exception as e:
            logger.error(f"转换CheckpointTuple失败: {e}")
            return None
    
    # === IThreadCheckpointStorage 接口实现 ===
    
    async def save_checkpoint(self, thread_id: str, checkpoint: ThreadCheckpoint) -> str:
        """保存Thread检查点"""
        try:
            # 确保thread_id匹配
            checkpoint.thread_id = thread_id
            
            # 转换为字典格式保存
            checkpoint_data = checkpoint.to_dict()
            return await self.save(checkpoint_data)
            
        except Exception as e:
            logger.error(f"Failed to save thread checkpoint: {e}")
            raise CheckpointStorageError(f"保存Thread检查点失败: {e}") from e
    
    async def load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载Thread检查点"""
        try:
            checkpoint_data = await self.load_by_thread(thread_id, checkpoint_id)
            if checkpoint_data:
                return ThreadCheckpoint.from_dict(checkpoint_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to load thread checkpoint: {e}")
            raise CheckpointStorageError(f"加载Thread检查点失败: {e}") from e
    
    async def list_checkpoints(self, thread_id: str, status: Optional[CheckpointStatus] = None) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点"""
        try:
            checkpoint_list = await self.list_by_thread(thread_id)
            
            # 转换为ThreadCheckpoint对象并过滤状态
            checkpoints = []
            for checkpoint_data in checkpoint_list:
                checkpoint = ThreadCheckpoint.from_dict(checkpoint_data)
                if status is None or checkpoint.status == status:
                    checkpoints.append(checkpoint)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list thread checkpoints: {e}")
            raise CheckpointStorageError(f"列出Thread检查点失败: {e}") from e
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点"""
        try:
            return await self.delete_by_thread(thread_id, checkpoint_id)
            
        except Exception as e:
            logger.error(f"Failed to delete thread checkpoint: {e}")
            raise CheckpointStorageError(f"删除Thread检查点失败: {e}") from e
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点"""
        try:
            checkpoint_data = await self.get_latest(thread_id)
            if checkpoint_data:
                return ThreadCheckpoint.from_dict(checkpoint_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest thread checkpoint: {e}")
            raise CheckpointStorageError(f"获取最新Thread检查点失败: {e}") from e
    
    async def cleanup_old_thread_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的Thread检查点"""
        try:
            return await self.cleanup_old_checkpoints(thread_id, max_count)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old thread checkpoints: {e}")
            raise CheckpointStorageError(f"清理旧Thread检查点失败: {e}") from e
    
    async def get_checkpoint_statistics(self, thread_id: str) -> CheckpointStatistics:
        """获取Thread检查点统计信息"""
        try:
            # 获取所有检查点
            checkpoints = await self.list_checkpoints(thread_id)
            
            # 计算统计信息
            stats = CheckpointStatistics()
            stats.total_checkpoints = len(checkpoints)
            
            for checkpoint in checkpoints:
                # 状态统计
                if checkpoint.status == CheckpointStatus.ACTIVE:
                    stats.active_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.EXPIRED:
                    stats.expired_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.CORRUPTED:
                    stats.corrupted_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.ARCHIVED:
                    stats.archived_checkpoints += 1
                
                # 大小统计
                stats.total_size_bytes += checkpoint.size_bytes
                if checkpoint.size_bytes > stats.largest_checkpoint_bytes:
                    stats.largest_checkpoint_bytes = checkpoint.size_bytes
                if stats.smallest_checkpoint_bytes == 0 or checkpoint.size_bytes < stats.smallest_checkpoint_bytes:
                    stats.smallest_checkpoint_bytes = checkpoint.size_bytes
                
                # 恢复统计
                stats.total_restores += checkpoint.restore_count
                
                # 年龄统计
                age_hours = checkpoint.get_age_hours()
                if stats.oldest_checkpoint_age_hours == 0 or age_hours > stats.oldest_checkpoint_age_hours:
                    stats.oldest_checkpoint_age_hours = age_hours
                if stats.newest_checkpoint_age_hours == 0 or age_hours < stats.newest_checkpoint_age_hours:
                    stats.newest_checkpoint_age_hours = age_hours
            
            # 计算平均值
            if stats.total_checkpoints > 0:
                stats.average_size_bytes = stats.total_size_bytes / stats.total_checkpoints
                stats.average_restores = stats.total_restores / stats.total_checkpoints
                stats.average_age_hours = (stats.oldest_checkpoint_age_hours + stats.newest_checkpoint_age_hours) / 2
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get thread checkpoint statistics: {e}")
            raise CheckpointStorageError(f"获取Thread检查点统计失败: {e}") from e