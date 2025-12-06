"""内存检查点保存器实现

提供内存中的检查点存储，用于调试和测试。
"""

from collections import defaultdict
from collections.abc import Iterator, Sequence
from typing import Any, Dict, Optional

from .base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

__all__ = ("MemoryCheckpointSaver",)


class MemoryCheckpointSaver(BaseCheckpointSaver[str]):
    """内存检查点保存器。
    
    将检查点存储在内存中，使用defaultdict结构。
    
    注意：
        仅将MemoryCheckpointSaver用于调试或测试目的。
        对于生产用例，建议使用更健壮的数据库如PostgreSQL。
    """
    
    def __init__(self) -> None:
        """初始化内存检查点保存器。"""
        # thread_id -> checkpoint_ns -> checkpoint_id -> checkpoint mapping
        self.storage: defaultdict[
            str,
            Dict[str, Dict[str, Checkpoint]]
        ] = defaultdict(lambda: defaultdict(dict))
        
        # (thread_id, checkpoint_ns, checkpoint_id) -> writes mapping
        self.writes: defaultdict[
            tuple[str, str, str],
            Dict[str, Any]
        ] = defaultdict(dict)
    
    def get(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """获取检查点。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        if value := self.get_tuple(config):
            return value.checkpoint
        return None
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """获取检查点元组。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点元组，如果未找到则为None
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        if checkpoint_id:
            if checkpoint_id in self.storage[thread_id][checkpoint_ns]:
                checkpoint = self.storage[thread_id][checkpoint_ns][checkpoint_id]
                writes = self.writes.get((thread_id, checkpoint_ns, checkpoint_id), {})
                
                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=CheckpointMetadata(),  # 简化实现
                    pending_writes=list(writes.items())
                )
        else:
            if self.storage[thread_id][checkpoint_ns]:
                # 获取最新的检查点
                latest_id = max(self.storage[thread_id][checkpoint_ns].keys())
                checkpoint = self.storage[thread_id][checkpoint_ns][latest_id]
                writes = self.writes.get((thread_id, checkpoint_ns, latest_id), {})
                
                return CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": latest_id,
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=CheckpointMetadata(),  # 简化实现
                    pending_writes=list(writes.items())
                )
        
        return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """列出检查点。
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            匹配的检查点元组的迭代器
        """
        count = 0
        
        thread_ids = [config["configurable"]["thread_id"]] if config else self.storage.keys()
        
        for thread_id in thread_ids:
            for checkpoint_ns in self.storage[thread_id].keys():
                for checkpoint_id, checkpoint in self.storage[thread_id][checkpoint_ns].items():
                    # 简化的过滤逻辑
                    if filter and not self._matches_filter(checkpoint, filter):
                        continue
                    
                    writes = self.writes.get((thread_id, checkpoint_ns, checkpoint_id), {})
                    
                    yield CheckpointTuple(
                        config={
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": checkpoint_ns,
                                "checkpoint_id": checkpoint_id,
                            }
                        },
                        checkpoint=checkpoint,
                        metadata=CheckpointMetadata(),  # 简化实现
                        pending_writes=list(writes.items())
                    )
                    
                    count += 1
                    if limit and count >= limit:
                        return
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, str],
    ) -> Dict[str, Any]:
        """存储检查点。
        
        Args:
            config: 检查点的配置
            checkpoint: 要存储的检查点
            metadata: 检查点的额外元数据
            new_versions: 作为此写入的新通道版本
            
        Returns:
            存储检查点后更新的配置
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        
        # 存储检查点
        self.storage[thread_id][checkpoint_ns][checkpoint["id"]] = checkpoint
        
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储中间写入。
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = config["configurable"]["checkpoint_id"]
        
        outer_key = (thread_id, checkpoint_ns, checkpoint_id)
        
        for channel, value in writes:
            self.writes[outer_key][channel] = value
    
    def _matches_filter(self, checkpoint: Checkpoint, filter: Dict[str, Any]) -> bool:
        """检查检查点是否匹配过滤条件。
        
        Args:
            checkpoint: 检查点
            filter: 过滤条件
            
        Returns:
            是否匹配
        """
        # 简化的过滤实现
        for key, value in filter.items():
            if key in checkpoint and checkpoint[key] != value:
                return False
        return True
    
    def delete_thread(self, thread_id: str) -> None:
        """删除与线程ID关联的所有检查点和写入。
        
        Args:
            thread_id: 线程ID
        """
        if thread_id in self.storage:
            del self.storage[thread_id]
        
        # 删除相关的写入
        keys_to_remove = [
            key for key in self.writes.keys()
            if key[0] == thread_id
        ]
        for key in keys_to_remove:
            del self.writes[key]
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息。
        
        Returns:
            统计信息字典
        """
        total_checkpoints = sum(
            len(checkpoint_dict)
            for checkpoint_dict in self.storage.values()
        )
        
        total_writes = len(self.writes)
        
        return {
            "total_threads": len(self.storage),
            "total_checkpoints": total_checkpoints,
            "total_writes": total_writes
        }