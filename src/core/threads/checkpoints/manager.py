"""Thread检查点管理器

提供Thread检查点的高级管理功能，协调多个领域服务。
"""

from src.interfaces.dependency_injection import get_logger
from typing import List, Optional, Dict, Any
from datetime import datetime

from .storage.service import ThreadCheckpointDomainService, CheckpointManager
from .storage.models import ThreadCheckpoint, CheckpointStatistics, CheckpointType
from .storage.repository import IThreadCheckpointRepository


logger = get_logger(__name__)


class ThreadCheckpointManager:
    """Thread检查点管理器
    
    提供Thread检查点的统一管理接口，协调领域服务和外部系统。
    """
    
    def __init__(
        self,
        domain_service: ThreadCheckpointDomainService,
        checkpoint_manager: CheckpointManager
    ):
        """初始化管理器
        
        Args:
            domain_service: 检查点领域服务
            checkpoint_manager: 检查点管理器
        """
        self._domain_service = domain_service
        self._checkpoint_manager = checkpoint_manager
        logger.info("ThreadCheckpointManager initialized")
    
    async def create_and_backup_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        create_backup: bool = True
    ) -> Dict[str, str]:
        """创建并备份检查点 - 业务编排
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            create_backup: 是否创建备份
            
        Returns:
            包含检查点ID和备份ID的字典
        """
        try:
            # 1. 创建检查点（调用领域服务）
            checkpoint = await self._domain_service.create_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                checkpoint_type=checkpoint_type,
                metadata=metadata
            )
            
            result = {"checkpoint_id": checkpoint.id}
            
            # 2. 创建备份（调用管理器）
            if create_backup:
                backup_id = await self._checkpoint_manager.create_backup(checkpoint.id)
                result["backup_id"] = backup_id
            
            # 3. 发送事件（业务编排）
            await self._publish_checkpoint_created_event(
                thread_id, checkpoint.id, result.get("backup_id")
            )
            
            logger.info(f"Created and backed up checkpoint {checkpoint.id} for thread {thread_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create and backup checkpoint for thread {thread_id}: {e}")
            raise
    
    async def restore_with_validation(
        self, 
        thread_id: str, 
        checkpoint_id: str,
        validate_thread: bool = True
    ) -> Dict[str, Any]:
        """恢复并验证 - 业务编排
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
            validate_thread: 是否验证线程状态
            
        Returns:
            恢复的状态数据
        """
        try:
            # 1. 验证Thread状态（业务规则）
            if validate_thread:
                await self._validate_thread_state(thread_id)
            
            # 2. 恢复检查点（调用领域服务）
            state_data = await self._domain_service.restore_from_checkpoint(checkpoint_id)
            
            if state_data is None:
                raise ValueError(f"Failed to restore from checkpoint {checkpoint_id}")
            
            # 3. 验证恢复状态（业务规则）
            await self._validate_restored_state(state_data)
            
            # 4. 更新Thread状态（业务编排）
            await self._update_thread_state(thread_id, state_data)
            
            # 5. 发送事件（业务编排）
            await self._publish_checkpoint_restored_event(thread_id, checkpoint_id)
            
            logger.info(f"Restored and validated checkpoint {checkpoint_id} for thread {thread_id}")
            return state_data
            
        except Exception as e:
            logger.error(f"Failed to restore and validate checkpoint {checkpoint_id}: {e}")
            raise
    
    async def create_checkpoint_chain(
        self,
        thread_id: str,
        state_data_list: List[Dict[str, Any]],
        chain_metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """创建检查点链
        
        Args:
            thread_id: 线程ID
            state_data_list: 状态数据列表
            chain_metadata: 链元数据
            
        Returns:
            检查点ID列表
        """
        try:
            checkpoint_ids = []
            
            for i, state_data in enumerate(state_data_list):
                # 为链中的每个检查点添加元数据
                metadata = {
                    "chain_index": i,
                    "chain_length": len(state_data_list),
                    "chain_metadata": chain_metadata or {}
                }
                
                # 创建检查点
                checkpoint = await self._domain_service.create_checkpoint(
                    thread_id=thread_id,
                    state_data=state_data,
                    metadata=metadata
                )
                
                checkpoint_ids.append(checkpoint.id)
            
            logger.info(f"Created checkpoint chain with {len(checkpoint_ids)} checkpoints for thread {thread_id}")
            return checkpoint_ids
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint chain for thread {thread_id}: {e}")
            raise
    
    async def get_thread_checkpoint_timeline(
        self,
        thread_id: str,
        include_backups: bool = True
    ) -> List[Dict[str, Any]]:
        """获取线程检查点时间线
        
        Args:
            thread_id: 线程ID
            include_backups: 是否包含备份
            
        Returns:
            时间线数据
        """
        try:
            # 获取检查点历史
            checkpoints = await self._domain_service.get_thread_checkpoint_history(thread_id)
            
            timeline = []
            for checkpoint in checkpoints:
                timeline_item = {
                    "id": checkpoint.id,
                    "type": checkpoint.checkpoint_type.value,
                    "status": checkpoint.status.value,
                    "created_at": checkpoint.created_at.isoformat(),
                    "size_bytes": checkpoint.size_bytes,
                    "restore_count": checkpoint.restore_count,
                    "metadata": checkpoint.metadata
                }
                
                # 添加备份信息
                if include_backups:
                    backups = await self._checkpoint_manager.get_backup_chain(checkpoint.id)
                    timeline_item["backups"] = [
                        {
                            "id": backup.id,
                            "created_at": backup.created_at.isoformat(),
                            "backup_timestamp": backup.metadata.get("backup_timestamp")
                        }
                        for backup in backups
                    ]
                
                timeline.append(timeline_item)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint timeline for thread {thread_id}: {e}")
            raise
    
    async def optimize_checkpoint_storage(
        self,
        thread_id: str,
        max_checkpoints: int = 50,
        archive_days: int = 30
    ) -> Dict[str, int]:
        """优化检查点存储
        
        Args:
            thread_id: 线程ID
            max_checkpoints: 最大检查点数量
            archive_days: 归档天数
            
        Returns:
            优化结果统计
        """
        try:
            results = {
                "archived": 0,
                "deleted": 0,
                "backups_created": 0
            }
            
            # 1. 归档旧检查点
            archived_count = await self._domain_service.archive_old_checkpoints(thread_id, archive_days)
            results["archived"] = archived_count
            
            # 2. 清理过期检查点
            deleted_count = await self._domain_service.cleanup_expired_checkpoints(thread_id)
            results["deleted"] = deleted_count
            
            # 3. 检查是否需要创建备份
            checkpoints = await self._domain_service.get_thread_checkpoint_history(thread_id)
            important_checkpoints = [
                cp for cp in checkpoints 
                if cp.checkpoint_type in [CheckpointType.MANUAL, CheckpointType.MILESTONE]
                and cp.restore_count == 0  # 没有备份的重要检查点
            ]
            
            for checkpoint in important_checkpoints[:5]:  # 最多创建5个备份
                try:
                    await self._checkpoint_manager.create_backup(checkpoint.id)
                    results["backups_created"] += 1
                except Exception as e:
                    logger.warning(f"Failed to create backup for checkpoint {checkpoint.id}: {e}")
            
            logger.info(f"Optimized checkpoint storage for thread {thread_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to optimize checkpoint storage for thread {thread_id}: {e}")
            raise
    
    async def get_comprehensive_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取综合统计信息
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            综合统计信息
        """
        try:
            # 获取基础统计
            stats = await self._domain_service.get_checkpoint_statistics(thread_id)
            
            # 获取额外统计信息
            if thread_id:
                checkpoints = await self._domain_service.get_thread_checkpoint_history(thread_id)
            else:
                # 获取所有检查点
                repository = self._domain_service._repository
                # 获取所有活跃的检查点
                from .storage.models import CheckpointStatus
                checkpoints = []
                for status in CheckpointStatus:
                    checkpoints.extend(await repository.find_by_status(status))
            
            # 计算额外统计
            type_distribution = {}
            restore_frequency = {}
            
            for checkpoint in checkpoints:
                # 类型分布
                cp_type = checkpoint.checkpoint_type.value
                type_distribution[cp_type] = type_distribution.get(cp_type, 0) + 1
                
                # 恢复频率
                if checkpoint.restore_count > 0:
                    restore_frequency[checkpoint.restore_count] = restore_frequency.get(checkpoint.restore_count, 0) + 1
            
            # 构建综合统计
            comprehensive_stats = {
                **stats.to_dict(),
                "type_distribution": type_distribution,
                "restore_frequency": restore_frequency,
                "average_restores_per_checkpoint": (
                    sum(cp.restore_count for cp in checkpoints) / len(checkpoints)
                    if checkpoints else 0
                )
            }
            
            return comprehensive_stats
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive statistics: {e}")
            raise
    
    # 私有方法 - 业务编排逻辑
    async def _validate_thread_state(self, thread_id: str) -> None:
        """验证线程状态
        
        Args:
            thread_id: 线程ID
        """
        # 这里可以添加线程状态验证逻辑
        # 例如：检查线程是否存在、是否处于可恢复状态等
        logger.debug(f"Validating thread state for {thread_id}")
    
    async def _validate_restored_state(self, state_data: Dict[str, Any]) -> None:
        """验证恢复状态
        
        Args:
            state_data: 恢复的状态数据
        """
        # 这里可以添加状态数据验证逻辑
        # 例如：检查数据完整性、格式正确性等
        if not state_data:
            raise ValueError("Restored state data is empty")
        
        logger.debug("Validating restored state data")
    
    async def _update_thread_state(self, thread_id: str, state_data: Dict[str, Any]) -> None:
        """更新线程状态
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
        """
        # 这里可以添加线程状态更新逻辑
        # 例如：更新线程的当前状态、记录恢复时间等
        logger.debug(f"Updating thread state for {thread_id}")
    
    async def _publish_checkpoint_created_event(
        self, 
        thread_id: str, 
        checkpoint_id: str, 
        backup_id: Optional[str]
    ) -> None:
        """发布检查点创建事件
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
            backup_id: 备份ID
        """
        # 这里可以添加事件发布逻辑
        # 例如：发送到消息队列、记录审计日志等
        event_data = {
            "event_type": "checkpoint_created",
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "backup_id": backup_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Publishing checkpoint created event: {event_data}")
    
    async def _publish_checkpoint_restored_event(
        self, 
        thread_id: str, 
        checkpoint_id: str
    ) -> None:
        """发布检查点恢复事件
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
        """
        # 这里可以添加事件发布逻辑
        event_data = {
            "event_type": "checkpoint_restored",
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Publishing checkpoint restored event: {event_data}")


class CheckpointOrchestrator:
    """检查点编排器
    
    提供跨多个线程的检查点编排功能。
    """
    
    def __init__(self, checkpoint_manager: ThreadCheckpointManager):
        """初始化编排器
        
        Args:
            checkpoint_manager: 检查点管理器
        """
        self._checkpoint_manager = checkpoint_manager
        logger.info("CheckpointOrchestrator initialized")
    
    async def create_cross_thread_snapshot(
        self,
        thread_ids: List[str],
        snapshot_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """创建跨线程快照
        
        Args:
            thread_ids: 线程ID列表
            snapshot_metadata: 快照元数据
            
        Returns:
            每个线程的检查点ID列表
        """
        try:
            snapshot_results = {}
            
            for thread_id in thread_ids:
                # 为每个线程创建里程碑检查点
                checkpoint_ids = await self._checkpoint_manager.create_checkpoint_chain(
                    thread_id=thread_id,
                    state_data_list=[{"snapshot": True}],  # 简化的状态数据
                    chain_metadata={
                        "cross_thread_snapshot": True,
                        "snapshot_metadata": snapshot_metadata or {}
                    }
                )
                
                snapshot_results[thread_id] = checkpoint_ids
            
            logger.info(f"Created cross-thread snapshot for {len(thread_ids)} threads")
            return snapshot_results
            
        except Exception as e:
            logger.error(f"Failed to create cross-thread snapshot: {e}")
            raise
    
    async def restore_cross_thread_snapshot(
        self,
        snapshot_results: Dict[str, List[str]]
    ) -> Dict[str, bool]:
        """恢复跨线程快照
        
        Args:
            snapshot_results: 快照结果
            
        Returns:
            每个线程的恢复结果
        """
        try:
            restore_results = {}
            
            for thread_id, checkpoint_ids in snapshot_results.items():
                try:
                    # 恢复每个线程的最新检查点
                    if checkpoint_ids:
                        await self._checkpoint_manager.restore_with_validation(
                            thread_id=thread_id,
                            checkpoint_id=checkpoint_ids[0]
                        )
                        restore_results[thread_id] = True
                    else:
                        restore_results[thread_id] = False
                        
                except Exception as e:
                    logger.error(f"Failed to restore thread {thread_id}: {e}")
                    restore_results[thread_id] = False
            
            logger.info(f"Restored cross-thread snapshot for {len(snapshot_results)} threads")
            return restore_results
            
        except Exception as e:
            logger.error(f"Failed to restore cross-thread snapshot: {e}")
            raise