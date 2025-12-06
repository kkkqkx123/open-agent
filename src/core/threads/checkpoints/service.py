"""Thread检查点服务

统一的Thread检查点服务实现，整合所有checkpoint功能。
不再依赖接口层，直接提供具体实现。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import ThreadCheckpoint, CheckpointStatistics, CheckpointStatus, CheckpointType
from .domain_service import ThreadCheckpointDomainService
from .extensions import (
    ThreadCheckpointExtension,
    CheckpointAnalysisHelper,
    CheckpointOptimizationHelper
)


class ThreadCheckpointService:
    """Thread检查点服务
    
    统一的checkpoint服务实现，包含所有业务逻辑和数据访问。
    不依赖接口层，直接提供具体实现。
    """
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    DEFAULT_EXPIRATION_HOURS = 24
    MAX_CHECKPOINT_SIZE_MB = 100
    MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP = 1
    
    def __init__(self, repository):
        """初始化服务
        
        Args:
            repository: 检查点仓储实现
        """
        self._repository = repository
        self._domain_service = ThreadCheckpointDomainService(repository)
        self._extension = ThreadCheckpointExtension()
    
    async def create_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> ThreadCheckpoint:
        """创建检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            expiration_hours: 过期小时数
            
        Returns:
            创建的检查点
        """
        # 使用领域服务创建实体
        checkpoint = self._domain_service.create_checkpoint_entity(
            thread_id, state_data, checkpoint_type, metadata, expiration_hours
        )
        
        # 保存到仓储
        await self._repository.save(checkpoint)
        
        return checkpoint
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """从检查点恢复
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态数据，失败返回None
        """
        checkpoint = await self._repository.find_by_id(checkpoint_id)
        if not checkpoint:
            return None
        
        # 验证恢复条件
        self._domain_service.validate_checkpoint_restore(checkpoint)
        
        # 增加恢复计数
        checkpoint.increment_restore_count()
        await self._repository.update(checkpoint)
        
        return checkpoint.state_data
    
    async def create_manual_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ThreadCheckpoint:
        """创建手动检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            创建的检查点
        """
        metadata = self._domain_service.create_manual_checkpoint_metadata(title, description, tags)
        
        return await self.create_checkpoint(
            thread_id, state_data, CheckpointType.MANUAL, metadata
        )
    
    async def create_error_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        error_message: str,
        error_type: Optional[str] = None
    ) -> ThreadCheckpoint:
        """创建错误检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            创建的检查点
        """
        metadata = self._domain_service.create_error_checkpoint_metadata(error_message, error_type)
        
        return await self.create_checkpoint(
            thread_id, state_data, CheckpointType.ERROR, metadata
        )
    
    async def create_milestone_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        milestone_name: str,
        description: Optional[str] = None
    ) -> ThreadCheckpoint:
        """创建里程碑检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            创建的检查点
        """
        metadata = self._domain_service.create_milestone_checkpoint_metadata(
            milestone_name, description
        )
        
        return await self.create_checkpoint(
            thread_id, state_data, CheckpointType.MILESTONE, metadata
        )
    
    async def cleanup_expired_checkpoints(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点
        
        Args:
            thread_id: 线程ID，None表示清理所有线程的过期检查点
            
        Returns:
            清理的检查点数量
        """
        if thread_id:
            checkpoints = await self._repository.find_by_thread(thread_id)
        else:
            # 获取所有检查点（需要仓储支持）
            checkpoints = await self._repository.find_expired()
        
        # 获取需要清理的候选
        cleanup_candidates = self._domain_service.get_checkpoint_cleanup_candidates(checkpoints)
        
        # 执行清理
        cleaned_count = 0
        for checkpoint in cleanup_candidates:
            if await self._repository.delete(checkpoint.id):
                cleaned_count += 1
        
        return cleaned_count
    
    async def get_thread_checkpoint_history(
        self, 
        thread_id: str, 
        limit: int = 50
    ) -> List[ThreadCheckpoint]:
        """获取线程检查点历史
        
        Args:
            thread_id: 线程ID
            limit: 返回数量限制
            
        Returns:
            检查点历史列表
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        
        # 按创建时间倒序排序
        checkpoints.sort(key=lambda x: x.created_at, reverse=True)
        
        return checkpoints[:limit]
    
    async def get_checkpoint_statistics(
        self, 
        thread_id: Optional[str] = None
    ) -> CheckpointStatistics:
        """获取检查点统计信息
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            统计信息
        """
        return await self._repository.get_statistics(thread_id)
    
    async def archive_old_checkpoints(self, thread_id: str, days: int = 30) -> int:
        """归档旧检查点
        
        Args:
            thread_id: 线程ID
            days: 归档天数阈值
            
        Returns:
            归档的检查点数量
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        
        # 获取需要归档的候选
        archive_candidates = self._domain_service.get_archive_candidates(checkpoints, days)
        
        # 执行归档
        archived_count = 0
        for checkpoint in archive_candidates:
            checkpoint.mark_archived()
            if await self._repository.update(checkpoint):
                archived_count += 1
        
        return archived_count
    
    async def extend_checkpoint_expiration(
        self, 
        checkpoint_id: str, 
        hours: int
    ) -> bool:
        """延长检查点过期时间
        
        Args:
            checkpoint_id: 检查点ID
            hours: 延长的小时数
            
        Returns:
            是否成功
        """
        checkpoint = await self._repository.find_by_id(checkpoint_id)
        if not checkpoint:
            return False
        
        checkpoint.extend_expiration(hours)
        return await self._repository.update(checkpoint)
    
    async def create_backup(self, checkpoint_id: str) -> str:
        """创建检查点备份
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份ID
        """
        original_checkpoint = await self._repository.find_by_id(checkpoint_id)
        if not original_checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # 使用扩展功能创建备份
        backup = self._extension.create_backup_checkpoint(original_checkpoint)
        await self._repository.save(backup)
        
        return backup.id
    
    async def restore_from_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """从备份恢复
        
        Args:
            backup_id: 备份ID
            
        Returns:
            恢复的状态数据
        """
        backup = await self._repository.find_by_id(backup_id)
        if not backup:
            return None
        
        # 验证恢复条件
        self._domain_service.validate_checkpoint_restore(backup)
        
        # 增加恢复计数
        backup.increment_restore_count()
        await self._repository.update(backup)
        
        return backup.state_data
    
    async def get_backup_chain(self, checkpoint_id: str) -> List[ThreadCheckpoint]:
        """获取检查点的备份链
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份链列表
        """
        # 获取所有相关检查点
        original_checkpoint = await self._repository.find_by_id(checkpoint_id)
        if not original_checkpoint:
            return []
        
        # 获取同一线程的所有检查点
        checkpoints = await self._repository.find_by_thread(original_checkpoint.thread_id)
        
        # 使用领域服务获取备份链
        return self._domain_service.get_backup_chain(checkpoints, checkpoint_id)
    
    async def analyze_checkpoint_frequency(self, thread_id: str) -> Dict[str, Any]:
        """分析检查点创建频率
        
        Args:
            thread_id: 线程ID
            
        Returns:
            频率分析结果
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        return CheckpointAnalysisHelper.analyze_checkpoint_frequency(checkpoints)
    
    async def analyze_checkpoint_size_distribution(self, thread_id: str) -> Dict[str, Any]:
        """分析检查点大小分布
        
        Args:
            thread_id: 线程ID
            
        Returns:
            大小分布分析结果
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        return CheckpointAnalysisHelper.analyze_checkpoint_size_distribution(checkpoints)
    
    async def analyze_checkpoint_type_distribution(self, thread_id: str) -> Dict[str, Any]:
        """分析检查点类型分布
        
        Args:
            thread_id: 线程ID
            
        Returns:
            类型分布分析结果
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        return CheckpointAnalysisHelper.analyze_checkpoint_type_distribution(checkpoints)
    
    async def suggest_optimization_strategy(self, thread_id: str) -> Dict[str, Any]:
        """建议优化策略
        
        Args:
            thread_id: 线程ID
            
        Returns:
            优化建议
        """
        checkpoints = await self._repository.find_by_thread(thread_id)
        return CheckpointOptimizationHelper.suggest_optimization_strategy(checkpoints)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        try:
            # 获取全局统计
            stats = await self._repository.get_statistics()
            
            # 检查存储状态
            total_checkpoints = stats.total_checkpoints
            expired_count = stats.expired_checkpoints
            corrupted_count = stats.corrupted_checkpoints
            
            # 计算健康指标
            health_score = 100
            if total_checkpoints > 0:
                expired_ratio = expired_count / total_checkpoints
                corrupted_ratio = corrupted_count / total_checkpoints
                
                # 过期和损坏的检查点会影响健康分数
                health_score -= int(expired_ratio * 30)
                health_score -= int(corrupted_ratio * 50)
            
            health_status = "healthy"
            if health_score < 70:
                health_status = "warning"
            if health_score < 50:
                health_status = "critical"
            
            return {
                "status": health_status,
                "score": health_score,
                "total_checkpoints": total_checkpoints,
                "expired_checkpoints": expired_count,
                "corrupted_checkpoints": corrupted_count,
                "total_size_mb": stats.total_size_bytes / (1024 * 1024),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "score": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }