"""Thread检查点适配器

提供Thread检查点的外部接口适配，处理API和外部系统集成。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.interfaces.dependency_injection import get_logger
from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointStatistics, CheckpointType
from src.core.threads.checkpoints.service import ThreadCheckpointService


logger = get_logger(__name__)


class ThreadCheckpointAdapter:
    """Thread检查点适配器
    
    提供统一的检查点操作接口，适配不同的使用场景。
    """
    
    def __init__(self, checkpoint_service: ThreadCheckpointService):
        """初始化适配器
        
        Args:
            checkpoint_service: 统一的检查点服务
        """
        self._service = checkpoint_service
        logger.info("ThreadCheckpointAdapter initialized")
    
    # 基本检查点操作
    async def create_auto_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        expiration_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建自动检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            expiration_hours: 过期小时数
            
        Returns:
            创建结果
        """
        try:
            checkpoint = await self._service.create_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                checkpoint_type=CheckpointType.AUTO,
                expiration_hours=expiration_hours
            )
            
            return {
                "success": True,
                "checkpoint_id": checkpoint.id,
                "thread_id": checkpoint.thread_id,
                "created_at": checkpoint.created_at.isoformat(),
                "expires_at": checkpoint.expires_at.isoformat() if checkpoint.expires_at else None,
                "size_bytes": checkpoint.size_bytes
            }
            
        except Exception as e:
            logger.error(f"Failed to create auto checkpoint for thread {thread_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_manual_checkpoint_with_metadata(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建带元数据的手动检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            创建结果
        """
        try:
            checkpoint = await self._service.create_manual_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                title=title,
                description=description,
                tags=tags
            )
            
            return {
                "success": True,
                "checkpoint_id": checkpoint.id,
                "thread_id": checkpoint.thread_id,
                "title": checkpoint.metadata.get("title"),
                "description": checkpoint.metadata.get("description"),
                "tags": checkpoint.metadata.get("tags", []),
                "created_at": checkpoint.created_at.isoformat(),
                "size_bytes": checkpoint.size_bytes
            }
            
        except Exception as e:
            logger.error(f"Failed to create manual checkpoint for thread {thread_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restore_checkpoint_safe(self, checkpoint_id: str) -> Dict[str, Any]:
        """安全恢复检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            恢复结果
        """
        try:
            state_data = await self._service.restore_from_checkpoint(checkpoint_id)
            
            if state_data is None:
                return {
                    "success": False,
                    "error": "Checkpoint not found or cannot be restored"
                }
            
            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "state_data": state_data,
                "restored_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restore checkpoint {checkpoint_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 批量操作
    async def batch_create_checkpoints(
        self, 
        checkpoints_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量创建检查点
        
        Args:
            checkpoints_data: 检查点数据列表
            
        Returns:
            批量创建结果
        """
        results = {
            "success_count": 0,
            "failure_count": 0,
            "results": []
        }
        
        for data in checkpoints_data:
            try:
                checkpoint = await self._service.create_checkpoint(**data)
                results["results"].append({
                    "success": True,
                    "checkpoint_id": checkpoint.id,
                    "thread_id": checkpoint.thread_id
                })
                results["success_count"] += 1
                
            except Exception as e:
                results["results"].append({
                    "success": False,
                    "error": str(e),
                    "thread_id": data.get("thread_id")
                })
                results["failure_count"] += 1
        
        return results
    
    async def batch_cleanup_checkpoints(
        self, 
        thread_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """批量清理检查点
        
        Args:
            thread_ids: 线程ID列表，None表示清理所有线程
            
        Returns:
            清理结果
        """
        results = {
            "total_cleaned": 0,
            "thread_results": {}
        }
        
        if thread_ids:
            for thread_id in thread_ids:
                try:
                    cleaned_count = await self._service.cleanup_expired_checkpoints(thread_id)
                    results["thread_results"][thread_id] = cleaned_count
                    results["total_cleaned"] += cleaned_count
                    
                except Exception as e:
                    results["thread_results"][thread_id] = {"error": str(e)}
        else:
            try:
                cleaned_count = await self._service.cleanup_expired_checkpoints()
                results["total_cleaned"] = cleaned_count
                
            except Exception as e:
                results["error"] = str(e)
        
        return results
    
    # 查询和分析
    async def get_thread_checkpoint_summary(
        self, 
        thread_id: str,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """获取线程检查点摘要
        
        Args:
            thread_id: 线程ID
            include_details: 是否包含详细信息
            
        Returns:
            摘要信息
        """
        try:
            # 获取统计信息
            stats = await self._service.get_checkpoint_statistics(thread_id)
            
            # 获取历史记录
            history = await self._service.get_thread_checkpoint_history(thread_id, limit=10)
            
            # 获取分析结果
            frequency_analysis = await self._service.analyze_checkpoint_frequency(thread_id)
            size_analysis = await self._service.analyze_checkpoint_size_distribution(thread_id)
            type_analysis = await self._service.analyze_checkpoint_type_distribution(thread_id)
            
            result = {
                "thread_id": thread_id,
                "statistics": stats.to_dict(),
                "recent_checkpoints": [
                    {
                        "id": cp.id,
                        "type": cp.checkpoint_type.value,
                        "status": cp.status.value,
                        "created_at": cp.created_at.isoformat(),
                        "size_bytes": cp.size_bytes
                    }
                    for cp in history
                ],
                "analysis": {
                    "frequency": frequency_analysis,
                    "size_distribution": size_analysis,
                    "type_distribution": type_analysis
                }
            }
            
            if include_details:
                result["detailed_checkpoints"] = [cp.to_dict() for cp in history]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint summary for thread {thread_id}: {e}")
            return {
                "thread_id": thread_id,
                "error": str(e)
            }
    
    async def get_checkpoint_health_report(
        self, 
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取检查点健康报告
        
        Args:
            thread_id: 线程ID，None表示全局报告
            
        Returns:
            健康报告
        """
        try:
            # 获取优化建议
            optimization_suggestions = await self._service.suggest_optimization_strategy(thread_id)
            
            # 获取统计信息
            stats = await self._service.get_checkpoint_statistics(thread_id)
            
            # 计算健康分数
            health_score = self._calculate_health_score(stats, optimization_suggestions)
            
            return {
                "thread_id": thread_id,
                "health_score": health_score,
                "statistics": stats.to_dict(),
                "optimization_suggestions": optimization_suggestions,
                "health_status": self._get_health_status(health_score),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return {
                "thread_id": thread_id,
                "error": str(e)
            }
    
    # 备份和恢复
    async def create_checkpoint_backup(self, checkpoint_id: str) -> Dict[str, Any]:
        """创建检查点备份
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份结果
        """
        try:
            backup_id = await self._service.create_backup(checkpoint_id)
            
            return {
                "success": True,
                "original_checkpoint_id": checkpoint_id,
                "backup_id": backup_id,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup for checkpoint {checkpoint_id}: {e}")
            return {
                "success": False,
                "checkpoint_id": checkpoint_id,
                "error": str(e)
            }
    
    async def get_checkpoint_backup_info(self, checkpoint_id: str) -> Dict[str, Any]:
        """获取检查点备份信息
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份信息
        """
        try:
            backup_chain = await self._service.get_backup_chain(checkpoint_id)
            
            return {
                "checkpoint_id": checkpoint_id,
                "backup_count": len(backup_chain),
                "backups": [
                    {
                        "backup_id": backup.id,
                        "created_at": backup.created_at.isoformat(),
                        "size_bytes": backup.size_bytes,
                        "backup_timestamp": backup.metadata.get("backup_timestamp")
                    }
                    for backup in backup_chain
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup info for checkpoint {checkpoint_id}: {e}")
            return {
                "checkpoint_id": checkpoint_id,
                "error": str(e)
            }
    
    # 工具方法
    def _calculate_health_score(
        self, 
        stats: CheckpointStatistics, 
        suggestions: Dict[str, Any]
    ) -> int:
        """计算健康分数
        
        Args:
            stats: 统计信息
            suggestions: 优化建议
            
        Returns:
            健康分数 (0-100)
        """
        base_score = 100
        
        # 根据优化建议扣分
        high_priority_count = suggestions.get("high_priority_count", 0)
        medium_priority_count = suggestions.get("medium_priority_count", 0)
        low_priority_count = suggestions.get("low_priority_count", 0)
        
        score = base_score - (high_priority_count * 20) - (medium_priority_count * 10) - (low_priority_count * 5)
        
        # 根据统计信息调整
        if stats.total_checkpoints == 0:
            score = min(score, 50)  # 没有检查点不是健康状态
        
        expired_ratio = stats.expired_checkpoints / max(stats.total_checkpoints, 1)
        if expired_ratio > 0.3:
            score = min(score, 60)  # 过期检查点太多
        
        return max(0, min(100, score))
    
    def _get_health_status(self, health_score: int) -> str:
        """获取健康状态
        
        Args:
            health_score: 健康分数
            
        Returns:
            健康状态
        """
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "fair"
        elif health_score >= 40:
            return "poor"
        else:
            return "critical"