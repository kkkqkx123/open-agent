"""检查点管理器实现

提供统一的检查点管理，支持多种存储后端和资源管理。
"""

from typing import Any, Dict, List, Optional

from ..hooks import HookPoint, HookSystem, HookContext
from ..optimization.resource_manager import ResourceManager
from .base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata

__all__ = ("CheckpointManager",)


class CheckpointManager:
    """检查点管理器，提供统一的检查点管理。
    
    支持多种存储后端和资源管理。
    """
    
    def __init__(
        self,
        saver: BaseCheckpointSaver,
        resource_manager: Optional[ResourceManager] = None
    ):
        """初始化检查点管理器。
        
        Args:
            saver: 检查点保存器
            resource_manager: 资源管理器
        """
        self.saver = saver
        self.resource_manager = resource_manager
        self.hook_system: Optional[HookSystem] = None
        self.checkpoint_cache: Dict[str, Checkpoint] = {}
        self.max_cache_size = 100
    
    def set_hook_system(self, hook_system: HookSystem) -> None:
        """设置Hook系统。
        
        Args:
            hook_system: Hook系统实例
        """
        self.hook_system = hook_system
    
    def set_resource_manager(self, manager: ResourceManager) -> None:
        """设置资源管理器。
        
        Args:
            manager: 资源管理器实例
        """
        self.resource_manager = manager
    
    async def save_checkpoint(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata
    ) -> str:
        """保存检查点。
        
        Args:
            config: 可运行配置
            checkpoint: 检查点
            metadata: 检查点元数据
            
        Returns:
            检查点ID
        """
        # 执行检查点保存前Hook
        if self.hook_system:
            context = HookContext(
                hook_point=HookPoint.BEFORE_CHECKPOINT,
                graph_id=config.get("graph_id", ""),
                config=config
            )
            await self.hook_system.execute_hooks(HookPoint.BEFORE_CHECKPOINT, context)
        
        try:
            # 检查资源限制
            if self.resource_manager:
                await self.resource_manager.check_checkpoint_limits()
            
            # 生成新版本
            new_versions = {}
            if checkpoint.channel_versions:
                for channel, version in checkpoint.channel_versions.items():
                    new_versions[channel] = self.saver.get_next_version(version, None)
            
            # 保存检查点
            updated_config = await self.saver.aput(
                config,
                checkpoint,
                metadata,
                new_versions
            )
            
            # 更新缓存
            checkpoint_id = checkpoint.id or ""
            if checkpoint_id:
                self._add_to_cache(checkpoint_id, checkpoint)
            
            # 执行检查点保存后Hook
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.AFTER_CHECKPOINT,
                    graph_id=config.get("graph_id", ""),
                    config=updated_config
                )
                await self.hook_system.execute_hooks(HookPoint.AFTER_CHECKPOINT, context)
            
            return checkpoint_id
            
        except Exception as e:
            # 错误处理
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.BEFORE_CHECKPOINT,
                    graph_id=config.get("graph_id", ""),
                    config=config,
                    error=e
                )
                await self.hook_system.execute_hooks(HookPoint.BEFORE_CHECKPOINT, context)
            raise
    
    async def load_checkpoint(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """加载检查点。
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点（如果存在）
        """
        # 先检查缓存
        cache_key = self._get_cache_key(config)
        if cache_key in self.checkpoint_cache:
            return self.checkpoint_cache[cache_key]
        
        # 从存储加载
        checkpoint = await self.saver.aget(config)
        
        # 更新缓存
        if checkpoint and checkpoint.id:
            self._add_to_cache(checkpoint.id, checkpoint)
        
        return checkpoint
    
    async def list_checkpoints(self, config: Dict[str, Any]) -> List[Checkpoint]:
        """列出检查点。
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点列表
        """
        checkpoints = []
        
        async for checkpoint_tuple in self.saver.alist(config):
            checkpoints.append(checkpoint_tuple.checkpoint)
        
        return checkpoints
    
    def _add_to_cache(self, checkpoint_id: str, checkpoint: Checkpoint) -> None:
        """添加检查点到缓存。
        
        Args:
            checkpoint_id: 检查点ID
            checkpoint: 检查点
        """
        self.checkpoint_cache[checkpoint_id] = checkpoint
        
        # 检查缓存大小限制
        if len(self.checkpoint_cache) > self.max_cache_size:
            # 移除最旧的检查点
            oldest_key = next(iter(self.checkpoint_cache))
            del self.checkpoint_cache[oldest_key]
    
    def _get_cache_key(self, config: Dict[str, Any]) -> str:
        """获取缓存键。
        
        Args:
            config: 配置
            
        Returns:
            缓存键
        """
        thread_id = config.get("configurable", {}).get("thread_id", "")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id", "")
        
        return f"{thread_id}:{checkpoint_ns}:{checkpoint_id}"
    
    def clear_cache(self) -> None:
        """清除缓存。"""
        self.checkpoint_cache.clear()
    
    def set_max_cache_size(self, max_size: int) -> None:
        """设置最大缓存大小。
        
        Args:
            max_size: 最大缓存大小
        """
        self.max_cache_size = max_size
        
        # 如果当前缓存超过限制，截断
        if len(self.checkpoint_cache) > max_size:
            # 保留最新的检查点
            items = list(self.checkpoint_cache.items())
            self.checkpoint_cache = dict(items[-max_size:])
    
    async def cleanup_old_checkpoints(self, max_age_days: int = 30) -> int:
        """清理旧检查点。
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的检查点数量
        """
        # 简化实现，实际应该根据时间戳清理
        # 这里只是清除缓存
        cache_size = len(self.checkpoint_cache)
        self.clear_cache()
        return cache_size
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息。
        
        Returns:
            统计信息字典
        """
        stats = {
            "cache_size": len(self.checkpoint_cache),
            "max_cache_size": self.max_cache_size,
            "saver_type": type(self.saver).__name__,
            "has_resource_manager": self.resource_manager is not None,
            "has_hook_system": self.hook_system is not None
        }
        
        if self.resource_manager:
            stats["resource_stats"] = self.resource_manager.get_resource_stats()
        
        return stats