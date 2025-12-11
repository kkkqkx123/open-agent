"""Thread检查点仓储模式

定义Thread检查点的仓储接口和实现，遵循DDD仓储模式原则。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.interfaces.dependency_injection import get_logger

from .models import ThreadCheckpoint, CheckpointStatistics, CheckpointStatus, CheckpointType


# 延迟初始化logger以避免循环导入
logger = None

def _get_logger():
    global logger
    if logger is None:
        from src.interfaces.dependency_injection import get_logger
        logger = get_logger(__name__)
    return logger


class IThreadCheckpointRepository(ABC):
    """Thread检查点仓储接口
    
    定义Thread检查点的数据访问抽象，遵循仓储模式原则。
    """
    
    @abstractmethod
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存检查点
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            是否保存成功
            
        Raises:
            RepositoryError: 保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """根据ID查找检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点实体，不存在返回None
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点列表
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_active_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有活跃检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            活跃检查点列表
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: CheckpointStatus) -> List[ThreadCheckpoint]:
        """根据状态查找检查点
        
        Args:
            status: 检查点状态
            
        Returns:
            检查点列表
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_by_type(self, checkpoint_type: CheckpointType) -> List[ThreadCheckpoint]:
        """根据类型查找检查点
        
        Args:
            checkpoint_type: 检查点类型
            
        Returns:
            检查点列表
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_expired(self, before_time: Optional[datetime] = None) -> List[ThreadCheckpoint]:
        """查找过期的检查点
        
        Args:
            before_time: 过期时间点，None表示当前时间
            
        Returns:
            过期检查点列表
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def update(self, checkpoint: ThreadCheckpoint) -> bool:
        """更新检查点
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            是否更新成功
            
        Raises:
            RepositoryError: 更新失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
            
        Raises:
            RepositoryError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_by_thread(self, thread_id: str) -> int:
        """删除Thread的所有检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            删除的检查点数量
            
        Raises:
            RepositoryError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_expired(self, before_time: Optional[datetime] = None) -> int:
        """删除过期的检查点
        
        Args:
            before_time: 过期时间点，None表示当前时间
            
        Returns:
            删除的检查点数量
            
        Raises:
            RepositoryError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点数量
            
        Raises:
            RepositoryError: 统计失败时抛出
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: CheckpointStatus) -> int:
        """根据状态统计检查点数量
        
        Args:
            status: 检查点状态
            
        Returns:
            检查点数量
            
        Raises:
            RepositoryError: 统计失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_statistics(self, thread_id: Optional[str] = None) -> CheckpointStatistics:
        """获取检查点统计信息
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            统计信息
            
        Raises:
            RepositoryError: 统计失败时抛出
        """
        pass
    
    @abstractmethod
    async def exists(self, checkpoint_id: str) -> bool:
        """检查检查点是否存在
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否存在
            
        Raises:
            RepositoryError: 检查失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_latest_by_thread(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """查找Thread的最新检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最新检查点，不存在返回None
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass
    
    @abstractmethod
    async def find_oldest_by_thread(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """查找Thread的最旧检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最旧检查点，不存在返回None
            
        Raises:
            RepositoryError: 查找失败时抛出
        """
        pass


class ThreadCheckpointRepository(IThreadCheckpointRepository):
    """Thread检查点仓储实现
    
    基于存储后端的Thread检查点仓储实现。
    """
    
    def __init__(self, storage_backend):
        """初始化仓储
        
        Args:
            storage_backend: 存储后端
        """
        self._backend = storage_backend
        _get_logger().info("ThreadCheckpointRepository initialized")
    
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存检查点"""
        try:
            # 验证检查点
            if not checkpoint.is_valid():
                raise ValueError("Invalid checkpoint")
            
            # 转换为存储格式
            data = checkpoint.to_dict()
            data["type"] = "thread_checkpoint"
            
            # 保存到后端
            result = await self._backend.save_impl(data)
            
            _get_logger().info(f"Saved checkpoint {checkpoint.id} for thread {checkpoint.thread_id}")
            return bool(result)
            
        except Exception as e:
            _get_logger().error(f"Failed to save checkpoint {checkpoint.id}: {e}")
            raise RepositoryError(f"Failed to save checkpoint: {e}") from e
    
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """根据ID查找检查点"""
        try:
            # 从后端加载
            data = await self._backend.load_impl(checkpoint_id)
            
            if data is None:
                return None
            
            # 验证数据类型
            if data.get("type") != "thread_checkpoint":
                _get_logger().warning(f"Data {checkpoint_id} is not a thread checkpoint")
                return None
            
            # 转换为领域对象
            return ThreadCheckpoint.from_dict(data)
            
        except Exception as e:
            _get_logger().error(f"Failed to find checkpoint {checkpoint_id}: {e}")
            raise RepositoryError(f"Failed to find checkpoint: {e}") from e
    
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有检查点"""
        try:
            # 查询Thread的所有检查点
            filters = {"type": "thread_checkpoint", "thread_id": thread_id}
            results = await self._backend.list_impl(filters)
            
            # 转换为领域对象
            checkpoints = []
            for data in results:
                try:
                    checkpoint = ThreadCheckpoint.from_dict(data)
                    checkpoints.append(checkpoint)
                except Exception as e:
                    _get_logger().warning(f"Failed to convert checkpoint data: {e}")
                    continue
            
            # 按创建时间排序（最新的在前）
            checkpoints.sort(key=lambda x: x.created_at, reverse=True)
            
            _get_logger().info(f"Found {len(checkpoints)} checkpoints for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            _get_logger().error(f"Failed to find checkpoints for thread {thread_id}: {e}")
            raise RepositoryError(f"Failed to find checkpoints: {e}") from e
    
    async def find_active_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有活跃检查点"""
        try:
            # 查询Thread的所有检查点
            all_checkpoints = await self.find_by_thread(thread_id)
            
            # 过滤活跃检查点
            active_checkpoints = [
                cp for cp in all_checkpoints 
                if cp.status == CheckpointStatus.ACTIVE and not cp.is_expired()
            ]
            
            _get_logger().info(f"Found {len(active_checkpoints)} active checkpoints for thread {thread_id}")
            return active_checkpoints
            
        except Exception as e:
            _get_logger().error(f"Failed to find active checkpoints for thread {thread_id}: {e}")
            raise RepositoryError(f"Failed to find active checkpoints: {e}") from e
    
    async def find_by_status(self, status: CheckpointStatus) -> List[ThreadCheckpoint]:
        """根据状态查找检查点"""
        try:
            # 查询指定状态的检查点
            filters = {"type": "thread_checkpoint", "status": status.value}
            results = await self._backend.list_impl(filters)
            
            # 转换为领域对象
            checkpoints = []
            for data in results:
                try:
                    checkpoint = ThreadCheckpoint.from_dict(data)
                    checkpoints.append(checkpoint)
                except Exception as e:
                    _get_logger().warning(f"Failed to convert checkpoint data: {e}")
                    continue
            
            _get_logger().info(f"Found {len(checkpoints)} checkpoints with status {status}")
            return checkpoints
            
        except Exception as e:
            _get_logger().error(f"Failed to find checkpoints with status {status}: {e}")
            raise RepositoryError(f"Failed to find checkpoints: {e}") from e
    
    async def find_by_type(self, checkpoint_type: CheckpointType) -> List[ThreadCheckpoint]:
        """根据类型查找检查点"""
        try:
            # 查询指定类型的检查点
            filters = {"type": "thread_checkpoint", "checkpoint_type": checkpoint_type.value}
            results = await self._backend.list_impl(filters)
            
            # 转换为领域对象
            checkpoints = []
            for data in results:
                try:
                    checkpoint = ThreadCheckpoint.from_dict(data)
                    checkpoints.append(checkpoint)
                except Exception as e:
                    _get_logger().warning(f"Failed to convert checkpoint data: {e}")
                    continue
            
            _get_logger().info(f"Found {len(checkpoints)} checkpoints with type {checkpoint_type}")
            return checkpoints
            
        except Exception as e:
            _get_logger().error(f"Failed to find checkpoints with type {checkpoint_type}: {e}")
            raise RepositoryError(f"Failed to find checkpoints: {e}") from e
    
    async def find_expired(self, before_time: Optional[datetime] = None) -> List[ThreadCheckpoint]:
        """查找过期的检查点"""
        try:
            # 确定过期时间点
            if before_time is None:
                before_time = datetime.now()
            
            # 查询所有检查点
            filters = {"type": "thread_checkpoint"}
            results = await self._backend.list_impl(filters)
            
            # 过滤过期检查点
            expired_checkpoints = []
            for data in results:
                try:
                    checkpoint = ThreadCheckpoint.from_dict(data)
                    if checkpoint.is_expired() or checkpoint.expires_at and checkpoint.expires_at < before_time:
                        expired_checkpoints.append(checkpoint)
                except Exception as e:
                    _get_logger().warning(f"Failed to convert checkpoint data: {e}")
                    continue
            
            _get_logger().info(f"Found {len(expired_checkpoints)} expired checkpoints")
            return expired_checkpoints
            
        except Exception as e:
            _get_logger().error(f"Failed to find expired checkpoints: {e}")
            raise RepositoryError(f"Failed to find expired checkpoints: {e}") from e
    
    async def update(self, checkpoint: ThreadCheckpoint) -> bool:
        """更新检查点"""
        try:
            # 验证检查点
            if not checkpoint.id:
                raise ValueError("Checkpoint ID is required")
            
            # 检查检查点是否存在
            existing = await self.find_by_id(checkpoint.id)
            if existing is None:
                raise ValueError(f"Checkpoint {checkpoint.id} not found")
            
            # 转换为存储格式
            data = checkpoint.to_dict()
            data["type"] = "thread_checkpoint"
            
            # 更新到后端
            result = await self._backend.save_impl(data)
            
            _get_logger().info(f"Updated checkpoint {checkpoint.id}")
            return bool(result)
            
        except Exception as e:
            _get_logger().error(f"Failed to update checkpoint {checkpoint.id}: {e}")
            raise RepositoryError(f"Failed to update checkpoint: {e}") from e
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        try:
            # 从后端删除
            result = await self._backend.delete_impl(checkpoint_id)
            
            if result:
                _get_logger().info(f"Deleted checkpoint {checkpoint_id}")
            else:
                _get_logger().warning(f"Checkpoint {checkpoint_id} not found for deletion")
            
            return result
            
        except Exception as e:
            _get_logger().error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            raise RepositoryError(f"Failed to delete checkpoint: {e}") from e
    
    async def delete_by_thread(self, thread_id: str) -> int:
        """删除Thread的所有检查点"""
        try:
            # 查找Thread的所有检查点
            checkpoints = await self.find_by_thread(thread_id)
            
            # 删除所有检查点
            deleted_count = 0
            for checkpoint in checkpoints:
                if await self.delete(checkpoint.id):
                    deleted_count += 1
            
            _get_logger().info(f"Deleted {deleted_count} checkpoints for thread {thread_id}")
            return deleted_count
            
        except Exception as e:
            _get_logger().error(f"Failed to delete checkpoints for thread {thread_id}: {e}")
            raise RepositoryError(f"Failed to delete checkpoints: {e}") from e
    
    async def delete_expired(self, before_time: Optional[datetime] = None) -> int:
        """删除过期的检查点"""
        try:
            # 查找过期检查点
            expired_checkpoints = await self.find_expired(before_time)
            
            # 删除过期检查点
            deleted_count = 0
            for checkpoint in expired_checkpoints:
                if await self.delete(checkpoint.id):
                    deleted_count += 1
            
            _get_logger().info(f"Deleted {deleted_count} expired checkpoints")
            return deleted_count
            
        except Exception as e:
            _get_logger().error(f"Failed to delete expired checkpoints: {e}")
            raise RepositoryError(f"Failed to delete expired checkpoints: {e}") from e
    
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量"""
        try:
            checkpoints = await self.find_by_thread(thread_id)
            return len(checkpoints)
            
        except Exception as e:
            _get_logger().error(f"Failed to count checkpoints for thread {thread_id}: {e}")
            raise RepositoryError(f"Failed to count checkpoints: {e}") from e
    
    async def count_by_status(self, status: CheckpointStatus) -> int:
        """根据状态统计检查点数量"""
        try:
            checkpoints = await self.find_by_status(status)
            return len(checkpoints)
            
        except Exception as e:
            _get_logger().error(f"Failed to count checkpoints with status {status}: {e}")
            raise RepositoryError(f"Failed to count checkpoints: {e}") from e
    
    async def get_statistics(self, thread_id: Optional[str] = None) -> CheckpointStatistics:
        """获取检查点统计信息"""
        try:
            # 获取检查点列表
            if thread_id:
                checkpoints = await self.find_by_thread(thread_id)
            else:
                # 获取所有检查点
                filters = {"type": "thread_checkpoint"}
                results = await self._backend.list_impl(filters)
                checkpoints = []
                for data in results:
                    try:
                        checkpoint = ThreadCheckpoint.from_dict(data)
                        checkpoints.append(checkpoint)
                    except Exception as e:
                        _get_logger().warning(f"Failed to convert checkpoint data: {e}")
                        continue
            
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
            
            _get_logger().info(f"Generated statistics for {len(checkpoints)} checkpoints")
            return stats
            
        except Exception as e:
            _get_logger().error(f"Failed to generate statistics: {e}")
            raise RepositoryError(f"Failed to generate statistics: {e}") from e
    
    async def exists(self, checkpoint_id: str) -> bool:
        """检查检查点是否存在"""
        try:
            checkpoint = await self.find_by_id(checkpoint_id)
            return checkpoint is not None
            
        except Exception as e:
            _get_logger().error(f"Failed to check existence of checkpoint {checkpoint_id}: {e}")
            raise RepositoryError(f"Failed to check existence: {e}") from e
    
    async def find_latest_by_thread(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """查找Thread的最新检查点"""
        try:
            checkpoints = await self.find_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            _get_logger().error(f"Failed to find latest checkpoint for thread {thread_id}: {e}")
            raise RepositoryError(f"Failed to find latest checkpoint: {e}") from e
    
    async def find_oldest_by_thread(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """查找Thread的最旧检查点"""
        try:
            checkpoints = await self.find_by_thread(thread_id)
            return checkpoints[-1] if checkpoints else None
            
        except Exception as e:
            _get_logger().error(f"Failed to find oldest checkpoint for thread {thread_id}: {e}")
            raise RepositoryError(f"Failed to find oldest checkpoint: {e}") from e


class RepositoryError(Exception):
    """仓储错误"""
    pass