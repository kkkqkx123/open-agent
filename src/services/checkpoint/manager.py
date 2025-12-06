"""
检查点管理器

提供检查点的业务逻辑管理，包括生命周期管理、Hook集成等。
"""

from typing import Any, Dict, List, Optional
import logging

from src.interfaces.checkpoint.service import ICheckpointService
from src.interfaces.repository.checkpoint import ICheckpointRepository
from src.core.checkpoint.models import Checkpoint, CheckpointMetadata, CheckpointTuple
from src.core.checkpoint.factory import CheckpointFactory
from src.core.checkpoint.validators import CheckpointValidator, CheckpointValidationError
from src.services.checkpoint.cache import CheckpointCache


logger = logging.getLogger(__name__)


class CheckpointManager:
    """检查点管理器
    
    提供检查点的业务逻辑管理，包括缓存、Hook集成、资源管理等。
    """
    
    def __init__(
        self,
        repository: ICheckpointRepository,
        cache: Optional[CheckpointCache] = None,
        max_cache_size: int = 100
    ):
        """初始化检查点管理器
        
        Args:
            repository: 检查点仓库
            cache: 检查点缓存
            max_cache_size: 最大缓存大小
        """
        self.repository = repository
        self.cache = cache or CheckpointCache(max_size=max_cache_size)
        self._hook_system = None
        self._resource_manager = None
    
    def set_hook_system(self, hook_system: Any) -> None:
        """设置Hook系统
        
        Args:
            hook_system: Hook系统实例
        """
        self._hook_system = hook_system
    
    def set_resource_manager(self, resource_manager: Any) -> None:
        """设置资源管理器
        
        Args:
            resource_manager: 资源管理器实例
        """
        self._resource_manager = resource_manager
    
    async def save_checkpoint(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata
    ) -> str:
        """保存检查点
        
        Args:
            config: 可运行配置
            checkpoint: 检查点
            metadata: 检查点元数据
            
        Returns:
            检查点ID
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        # 验证数据
        CheckpointValidator.validate_checkpoint(checkpoint)
        CheckpointValidator.validate_metadata(metadata)
        
        # 执行保存前Hook
        await self._execute_hooks("before_save", {
            "config": config,
            "checkpoint": checkpoint,
            "metadata": metadata
        })
        
        try:
            # 检查资源限制
            if self._resource_manager:
                await self._resource_manager.check_checkpoint_limits()
            
            # 保存到仓库
            checkpoint_data = checkpoint.to_dict()
            metadata_data = metadata.to_dict()
            
            checkpoint_id = await self.repository.save_checkpoint({
                **checkpoint_data,
                "metadata": metadata_data,
                "config": config
            })
            
            # 更新缓存
            self.cache.set(checkpoint_id, checkpoint)
            
            # 执行保存后Hook
            await self._execute_hooks("after_save", {
                "config": config,
                "checkpoint_id": checkpoint_id,
                "checkpoint": checkpoint,
                "metadata": metadata
            })
            
            logger.info(f"检查点保存成功: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")
            await self._execute_hooks("save_error", {
                "config": config,
                "checkpoint": checkpoint,
                "metadata": metadata,
                "error": e
            })
            raise
    
    async def load_checkpoint(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """加载检查点
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点实例，如果不存在则返回None
        """
        # 先从缓存加载
        checkpoint_id = CheckpointFactory.extract_checkpoint_id(config)
        if checkpoint_id:
            cached_checkpoint = self.cache.get(checkpoint_id)
            if cached_checkpoint:
                logger.debug(f"从缓存加载检查点: {checkpoint_id}")
                return cached_checkpoint
        
        # 从仓库加载
        if not checkpoint_id:
            return None
        
        checkpoint_data = await self.repository.load_checkpoint(checkpoint_id)
        if not checkpoint_data:
            return None
        
        # 转换为检查点对象
        checkpoint = Checkpoint.from_dict(checkpoint_data)
        
        # 更新缓存
        if checkpoint_id:
            self.cache.set(checkpoint_id, checkpoint)
        
        logger.debug(f"从仓库加载检查点: {checkpoint_id}")
        return checkpoint
    
    async def load_checkpoint_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """加载检查点元组
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点元组，如果不存在则返回None
        """
        checkpoint = await self.load_checkpoint(config)
        if not checkpoint:
            return None
        
        # 创建元数据（简化实现）
        metadata = CheckpointFactory.create_metadata()
        
        # 创建元组
        return CheckpointFactory.create_tuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata
        )
    
    async def list_checkpoints(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[CheckpointTuple]:
        """列出检查点
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Returns:
            检查点元组列表
        """
        # 构建过滤条件
        filters = {}
        if config:
            thread_id = CheckpointFactory.extract_thread_id(config)
            if thread_id:
                filters["thread_id"] = thread_id
        
        if filter:
            filters.update(filter)
        
        # 从仓库获取检查点列表
        checkpoint_list = await self.repository.list_checkpoints(
            thread_id=filters.get("thread_id", ""),
            limit=limit
        )
        
        # 转换为检查点元组
        tuples = []
        for checkpoint_data in checkpoint_list:
            checkpoint = Checkpoint.from_dict(checkpoint_data)
            metadata_data = checkpoint_data.get("metadata", {})
            metadata = CheckpointMetadata(**metadata_data)
            
            # 创建配置
            tuple_config = CheckpointFactory.create_config(
                thread_id=checkpoint_data.get("thread_id", ""),
                checkpoint_ns=checkpoint_data.get("checkpoint_ns", ""),
                checkpoint_id=checkpoint.id
            )
            
            tuple_data = CheckpointFactory.create_tuple(
                config=tuple_config,
                checkpoint=checkpoint,
                metadata=metadata
            )
            tuples.append(tuple_data)
        
        return tuples
    
    async def delete_checkpoint(self, config: Dict[str, Any]) -> bool:
        """删除检查点
        
        Args:
            config: 可运行配置
            
        Returns:
            是否删除成功
        """
        checkpoint_id = CheckpointFactory.extract_checkpoint_id(config)
        if not checkpoint_id:
            return False
        
        # 从仓库删除
        success = await self.repository.delete_checkpoint(checkpoint_id)
        
        # 从缓存删除
        if success:
            self.cache.delete(checkpoint_id)
        
        return success
    
    async def cleanup_old_checkpoints(self, max_age_days: int = 30) -> int:
        """清理旧检查点
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的检查点数量
        """
        # 清理缓存中的过期项
        cache_cleanup_count = self.cache.cleanup_expired()
        
        # 清理仓库中的旧检查点
        thread_id = ""  # 可以根据需要指定线程ID
        repository_cleanup_count = await self.repository.cleanup_old_checkpoints(
            thread_id, max_count=1000  # 可以根据需要调整
        )
        
        total_cleanup = cache_cleanup_count + repository_cleanup_count
        logger.info(f"清理了 {total_cleanup} 个旧检查点")
        
        return total_cleanup
    
    async def get_checkpoint_stats(self) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Returns:
            统计信息字典
        """
        # 获取仓库统计
        repository_stats = await self.repository.get_checkpoint_statistics()
        
        # 获取缓存统计
        cache_stats = self.cache.get_stats()
        
        return {
            "repository": repository_stats,
            "cache": cache_stats,
            "has_hook_system": self._hook_system is not None,
            "has_resource_manager": self._resource_manager is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        # 检查仓库健康状态
        try:
            # 简单的健康检查：尝试加载一个不存在的检查点
            await self.repository.load_checkpoint("health_check_test")
            repository_healthy = True
            repository_error = None
        except Exception as e:
            repository_healthy = False
            repository_error = str(e)
        
        # 检查缓存健康状态
        cache_healthy = True
        cache_error = None
        
        try:
            # 简单的缓存测试
            test_checkpoint = CheckpointFactory.create_checkpoint()
            self.cache.set("health_check_test", test_checkpoint)
            retrieved = self.cache.get("health_check_test")
            if retrieved is None:
                cache_healthy = False
                cache_error = "缓存读写测试失败"
            else:
                self.cache.delete("health_check_test")
        except Exception as e:
            cache_healthy = False
            cache_error = str(e)
        
        return {
            "healthy": repository_healthy and cache_healthy,
            "repository": {
                "healthy": repository_healthy,
                "error": repository_error
            },
            "cache": {
                "healthy": cache_healthy,
                "error": cache_error,
                "stats": self.cache.get_stats()
            }
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("检查点缓存已清空")
    
    def set_cache_max_size(self, max_size: int) -> None:
        """设置缓存最大大小
        
        Args:
            max_size: 最大缓存大小
        """
        self.cache.set_max_size(max_size)
        logger.info(f"检查点缓存最大大小设置为: {max_size}")
    
    async def _execute_hooks(self, hook_point: str, context: Dict[str, Any]) -> None:
        """执行Hook
        
        Args:
            hook_point: Hook点
            context: 上下文数据
        """
        if self._hook_system:
            try:
                await self._hook_system.execute_hooks(hook_point, context)
            except Exception as e:
                logger.warning(f"执行Hook失败: {hook_point}, 错误: {e}")