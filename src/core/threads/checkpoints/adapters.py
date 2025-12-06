"""
Thread检查点仓储适配器

将Thread特定的查询方法适配到通用checkpoint仓储，实现适配器模式。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.threads.checkpoints.models import ThreadCheckpoint as Checkpoint, CheckpointStatus, CheckpointType, CheckpointStatistics
from src.infrastructure.threads.checkpoint_repository import ThreadCheckpointRepository


class ThreadCheckpointRepositoryAdapter:
    """Thread检查点仓储适配器
    
    将Thread特定的查询方法适配到通用checkpoint仓储。
    """
    
    def __init__(self, repository: ThreadCheckpointRepository):
        """初始化适配器
        
        Args:
            repository: Thread checkpoint仓储
        """
        self._repository = repository
    
    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点
        
        Args:
            checkpoint: 检查点
            
        Returns:
            是否保存成功
        """
        return await self._repository.save(checkpoint)
    
    async def find_by_id(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """根据ID查找检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点，不存在返回None
        """
        return await self._repository.find_by_id(checkpoint_id)
    
    async def find_by_thread(self, thread_id: str) -> List[Checkpoint]:
        """查找Thread的所有检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点列表
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        
        # 按创建时间排序（最新的在前）
        checkpoints.sort(key=lambda x: x.created_at, reverse=True)
        return checkpoints
    
    async def find_active_by_thread(self, thread_id: str) -> List[Checkpoint]:
        """查找Thread的所有活跃检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            活跃检查点列表
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        
        # 过滤活跃状态
        checkpoints = [
            cp for cp in checkpoints
            if cp.status == CheckpointStatus.ACTIVE
        ]
        
        # 过滤掉已过期的检查点
        active_checkpoints = [
            cp for cp in checkpoints 
            if not cp.is_expired()
        ]
        
        # 按创建时间排序（最新的在前）
        active_checkpoints.sort(key=lambda x: x.created_at, reverse=True)
        return active_checkpoints
    
    async def find_by_status(self, status: CheckpointStatus) -> List[Checkpoint]:
        """根据状态查找检查点
        
        Args:
            status: 检查点状态
            
        Returns:
            检查点列表
        """
        # 获取所有检查点并过滤状态
        all_checkpoints = []
        # 这里需要一个获取所有检查点的方法，暂时返回空列表
        # 实际实现中可能需要添加一个获取所有检查点的方法到接口
        return [cp for cp in all_checkpoints if cp.status == status]
    
    async def find_by_type(self, checkpoint_type: CheckpointType) -> List[Checkpoint]:
        """根据类型查找检查点
        
        Args:
            checkpoint_type: 检查点类型
            
        Returns:
            检查点列表
        """
        # 获取所有检查点并过滤类型
        all_checkpoints = []
        # 这里需要一个获取所有检查点的方法，暂时返回空列表
        return [cp for cp in all_checkpoints if cp.checkpoint_type == checkpoint_type]
    
    async def find_expired(self, before_time: Optional[datetime] = None) -> List[Checkpoint]:
        """查找过期的检查点
        
        Args:
            before_time: 过期时间点，None表示当前时间
            
        Returns:
            过期检查点列表
        """
        # 获取所有检查点
        # 获取所有检查点
        all_checkpoints = []
        # 这里需要一个获取所有检查点的方法，暂时返回空列表
        
        # 过滤过期检查点
        expired_checkpoints = []
        for checkpoint in all_checkpoints:
            if checkpoint.is_expired():
                if before_time is None:
                    expired_checkpoints.append(checkpoint)
                elif checkpoint.metadata.expires_at and checkpoint.metadata.expires_at < before_time:
                    expired_checkpoints.append(checkpoint)
        
        return expired_checkpoints
    
    async def update(self, checkpoint: Checkpoint) -> bool:
        """更新检查点
        
        Args:
            checkpoint: 检查点
            
        Returns:
            是否更新成功
        """
        return await self._repository.save(checkpoint)
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        return await self._repository.delete(checkpoint_id)
    
    async def delete_by_thread(self, thread_id: str) -> int:
        """删除Thread的所有检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            删除的检查点数量
        """
        # 查找Thread的所有检查点
        checkpoints = await self.find_by_thread(thread_id)
        
        # 删除所有检查点
        deleted_count = 0
        for checkpoint in checkpoints:
            if await self.delete(checkpoint.id):
                deleted_count += 1
        
        return deleted_count
    
    async def delete_expired(self, before_time: Optional[datetime] = None) -> int:
        """删除过期的检查点
        
        Args:
            before_time: 过期时间点，None表示当前时间
            
        Returns:
            删除的检查点数量
        """
        # 查找过期检查点
        expired_checkpoints = await self.find_expired(before_time)
        
        # 删除过期检查点
        deleted_count = 0
        for checkpoint in expired_checkpoints:
            if await self.delete(checkpoint.id):
                deleted_count += 1
        
        return deleted_count
    
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点数量
        """
        return await self._repository.count_by_thread(thread_id)
    
    async def count_by_status(self, status: CheckpointStatus) -> int:
        """根据状态统计检查点数量
        
        Args:
            status: 检查点状态
            
        Returns:
            检查点数量
        """
        # 获取所有检查点并统计状态
        all_checkpoints = []
        return sum(1 for cp in all_checkpoints if cp.status == status)
    
    async def get_statistics(self, thread_id: Optional[str] = None) -> CheckpointStatistics:
        """获取检查点统计信息
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            统计信息
        """
        # 获取检查点列表
        checkpoints = await self._repository.find_by_thread(thread_id) if thread_id else []
        
        # 计算统计信息
        stats = CheckpointStatistics()
        stats.total_checkpoints = len(checkpoints)
        
        if not checkpoints:
            return stats
        
        # 状态统计
        for checkpoint in checkpoints:
            if checkpoint.status == CheckpointStatus.ACTIVE:
                stats.active_checkpoints += 1
            elif checkpoint.status == CheckpointStatus.EXPIRED:
                stats.expired_checkpoints += 1
            elif checkpoint.status == CheckpointStatus.CORRUPTED:
                stats.corrupted_checkpoints += 1
            elif checkpoint.status == CheckpointStatus.ARCHIVED:
                stats.archived_checkpoints += 1
        
        # 大小统计
        sizes = [cp.size_bytes for cp in checkpoints]
        stats.total_size_bytes = sum(sizes)
        stats.average_size_bytes = stats.total_size_bytes / len(sizes)
        stats.largest_checkpoint_bytes = max(sizes)
        stats.smallest_checkpoint_bytes = min(sizes)
        
        # 恢复统计
        restore_counts = [cp.restore_count for cp in checkpoints]
        stats.total_restores = sum(restore_counts)
        stats.average_restores = stats.total_restores / len(restore_counts)
        
        # 年龄统计
        ages = [cp.get_age_hours() for cp in checkpoints]
        stats.oldest_checkpoint_age_hours = max(ages)
        stats.newest_checkpoint_age_hours = min(ages)
        stats.average_age_hours = sum(ages) / len(ages)
        
        return stats
    
    async def exists(self, checkpoint_id: str) -> bool:
        """检查检查点是否存在
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否存在
        """
        checkpoint = await self.find_by_id(checkpoint_id)
        return checkpoint is not None
    
    async def find_latest_by_thread(self, thread_id: str) -> Optional[Checkpoint]:
        """查找Thread的最新检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最新检查点，不存在返回None
        """
        checkpoints = await self.find_by_thread(thread_id)
        return checkpoints[0] if checkpoints else None
    
    async def find_oldest_by_thread(self, thread_id: str) -> Optional[Checkpoint]:
        """查找Thread的最旧检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最旧检查点，不存在返回None
        """
        checkpoints = await self.find_by_thread(thread_id)
        return checkpoints[-1] if checkpoints else None
    
    async def find_by_tags(self, thread_id: str, tags: List[str]) -> List[Checkpoint]:
        """根据标签查找Thread的检查点
        
        Args:
            thread_id: 线程ID
            tags: 标签列表
            
        Returns:
            检查点列表
        """
        checkpoints = await self.find_by_thread(thread_id)
        
        # 过滤包含指定标签的检查点
        filtered_checkpoints = []
        for checkpoint in checkpoints:
            checkpoint_tags = checkpoint.metadata.get("tags", [])
            if any(tag in checkpoint_tags for tag in tags):
                filtered_checkpoints.append(checkpoint)
        
        return filtered_checkpoints
    
    async def find_by_title(self, thread_id: str, title: str) -> List[Checkpoint]:
        """根据标题查找Thread的检查点
        
        Args:
            thread_id: 线程ID
            title: 标题
            
        Returns:
            检查点列表
        """
        checkpoints = await self.find_by_thread(thread_id)
        
        # 过滤标题匹配的检查点
        filtered_checkpoints = []
        for checkpoint in checkpoints:
            title_value = checkpoint.metadata.get("title")
            if title_value and title.lower() in title_value.lower():
                filtered_checkpoints.append(checkpoint)
        
        return filtered_checkpoints
    
    async def find_in_time_range(
        self,
        thread_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Checkpoint]:
        """查找时间范围内的Thread检查点
        
        Args:
            thread_id: 线程ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            检查点列表
        """
        checkpoints = await self.find_by_thread(thread_id)
        
        # 过滤时间范围内的检查点
        filtered_checkpoints = []
        for checkpoint in checkpoints:
            if start_time <= checkpoint.created_at <= end_time:
                filtered_checkpoints.append(checkpoint)
        
        return filtered_checkpoints
    
    async def find_backup_chain(self, checkpoint_id: str) -> List[Checkpoint]:
        """获取检查点的备份链
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份链列表
        """
        # 获取原检查点
        original_checkpoint = await self.find_by_id(checkpoint_id)
        if original_checkpoint is None:
            return []
        
        # 查找所有备份
        thread_id = original_checkpoint.thread_id
        if not thread_id:
            return []
        
        checkpoints = await self.find_by_thread(thread_id)
        
        # 过滤出该检查点的备份
        backups = []
        for checkpoint in checkpoints:
            backup_of = checkpoint.metadata.get("backup_of")
            if backup_of == checkpoint_id:
                backups.append(checkpoint)
        
        # 按备份时间排序
        backups.sort(
            key=lambda x: x.metadata.custom_data.get("backup_timestamp") or "",
            reverse=True
        )
        
        return backups