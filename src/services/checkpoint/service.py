"""
检查点服务实现

实现检查点服务的核心业务逻辑，提供通用的检查点管理接口。
"""

from typing import Any, Dict, List, Optional
from collections.abc import AsyncIterator
from datetime import datetime
import logging

from src.interfaces.checkpoint.service import ICheckpointService
from src.interfaces.repository.checkpoint import ICheckpointRepository
from src.core.checkpoint.models import Checkpoint, CheckpointMetadata, CheckpointTuple
from src.core.checkpoint.factory import CheckpointFactory
from src.core.checkpoint.validators import CheckpointValidator, CheckpointValidationError
from src.services.checkpoint.manager import CheckpointManager
from src.services.checkpoint.cache import CheckpointCache


logger = logging.getLogger(__name__)


class CheckpointService(ICheckpointService):
    """检查点服务实现
    
    提供通用的检查点管理功能，专注于基础设施层面的checkpoint操作。
    Thread特定的业务逻辑由ThreadCheckpointService处理。
    """
    
    def __init__(
        self,
        repository: ICheckpointRepository,
        cache: Optional[CheckpointCache] = None,
        max_cache_size: int = 100
    ):
        """初始化检查点服务
        
        Args:
            repository: 检查点仓库
            cache: 检查点缓存
            max_cache_size: 最大缓存大小
        """
        self.repository = repository
        self.cache = cache or CheckpointCache(max_size=max_cache_size)
        self.manager = CheckpointManager(repository, cache, max_cache_size)
    
    async def save_checkpoint(
        self, 
        config: Dict[str, Any], 
        checkpoint: Checkpoint,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存检查点
        
        Args:
            config: 可运行配置
            checkpoint: 检查点对象
            metadata: 检查点元数据
            
        Returns:
            检查点ID
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        # 转换元数据
        metadata_obj: CheckpointMetadata
        if metadata is None:
            metadata_obj = checkpoint.metadata
        elif isinstance(metadata, CheckpointMetadata):
            metadata_obj = metadata
        else:
            metadata_obj = CheckpointMetadata(**metadata)
        
        # 使用管理器保存
        return await self.manager.save_checkpoint(config, checkpoint, metadata_obj)
    
    async def load_checkpoint(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """加载检查点
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点对象，如果不存在则返回None
        """
        return await self.manager.load_checkpoint(config)
    
    async def load_checkpoint_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """加载检查点元组
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点元组，如果不存在则返回None
        """
        return await self.manager.load_checkpoint_tuple(config)
    
    def list_checkpoints(
        self, 
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> AsyncIterator[CheckpointTuple]:
        """列出检查点
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            检查点元组的异步迭代器
        """
        return self._async_list_checkpoints(config, filter, before, limit)
    
    async def _async_list_checkpoints(
        self,
        config: Optional[Dict[str, Any]],
        filter: Optional[Dict[str, Any]],
        before: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> AsyncIterator[CheckpointTuple]:
        """异步列表实现"""
        tuples = await self.manager.list_checkpoints(config, filter=filter, before=before, limit=limit)
        
        for tuple_obj in tuples:
            yield tuple_obj
    
    async def put_writes(
        self,
        config: Dict[str, Any],
        writes: List[tuple[str, Any]],
        task_id: str,
        task_path: str = ""
    ) -> None:
        """存储与检查点关联的中间写入
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        # 验证写入数据
        CheckpointValidator.validate_write_data(writes)
        
        # 获取检查点ID
        checkpoint_id = CheckpointFactory.extract_checkpoint_id(config)
        if not checkpoint_id:
            raise CheckpointValidationError("配置中缺少检查点ID")
        
        # 保存写入数据
        await self.repository.save_writes(checkpoint_id, writes, task_id, task_path)
        
        logger.debug(f"保存了 {len(writes)} 个写入到检查点 {checkpoint_id}")
    
    async def delete_checkpoint(self, config: Dict[str, Any]) -> bool:
        """删除检查点
        
        Args:
            config: 可运行配置
            
        Returns:
            是否删除成功
        """
        return await self.manager.delete_checkpoint(config)
    
    async def cleanup_old_checkpoints(self, max_age_days: int = 30) -> int:
        """清理旧检查点
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的检查点数量
        """
        return await self.manager.cleanup_old_checkpoints(max_age_days)
    
    async def get_checkpoint_stats(self) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Returns:
            统计信息字典
        """
        return await self.manager.get_checkpoint_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        return await self.manager.health_check()
    
    def set_hook_system(self, hook_system: Any) -> None:
        """设置Hook系统
        
        Args:
            hook_system: Hook系统实例
        """
        self.manager.set_hook_system(hook_system)
    
    def set_resource_manager(self, resource_manager: Any) -> None:
        """设置资源管理器
        
        Args:
            resource_manager: 资源管理器实例
        """
        self.manager.set_resource_manager(resource_manager)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.manager.clear_cache()
    
    def set_cache_max_size(self, max_size: int) -> None:
        """设置缓存最大大小
        
        Args:
            max_size: 最大缓存大小
        """
        self.manager.set_cache_max_size(max_size)
    
    async def create_checkpoint_from_state(
        self,
        state: Dict[str, Any],
        config: Dict[str, Any],
        source: Optional[str] = None,
        step: Optional[int] = None
    ) -> str:
        """从状态创建检查点
        
        Args:
            state: 状态数据
            config: 可运行配置
            source: 检查点来源
            step: 检查点步数
            
        Returns:
            检查点ID
        """
        # 创建检查点元组
        tuple_obj = CheckpointFactory.create_from_state(state, config, source, step)
        
        # 保存检查点
        metadata = tuple_obj.metadata or tuple_obj.checkpoint.metadata
        return await self.manager.save_checkpoint(
            config, 
            tuple_obj.checkpoint, 
            metadata
        )
    
    async def batch_save_checkpoints(
        self,
        checkpoints: List[Checkpoint],
        configs: List[Dict[str, Any]]
    ) -> List[str]:
        """批量保存检查点
        
        Args:
            checkpoints: 检查点列表
            configs: 配置列表
            
        Returns:
            检查点ID列表
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if len(checkpoints) != len(configs):
            raise CheckpointValidationError("检查点数量与配置数量不匹配")
        
        checkpoint_ids = []
        for checkpoint, config in zip(checkpoints, configs):
            checkpoint_id = await self.save_checkpoint(config, checkpoint)
            checkpoint_ids.append(checkpoint_id)
        
        return checkpoint_ids
    
    async def batch_delete_checkpoints(
        self,
        configs: List[Dict[str, Any]]
    ) -> int:
        """批量删除检查点
        
        Args:
            configs: 配置列表
            
        Returns:
            删除成功的检查点数量
        """
        deleted_count = 0
        for config in configs:
            if await self.delete_checkpoint(config):
                deleted_count += 1
        
        return deleted_count
    
    async def get_checkpoint_by_id(
        self,
        checkpoint_id: str
    ) -> Optional[Checkpoint]:
        """根据ID获取检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点对象，如果不存在则返回None
        """
        checkpoint_data = await self.repository.load_checkpoint(checkpoint_id)
        if checkpoint_data:
            return Checkpoint.from_dict(checkpoint_data)
        return None
    
    async def update_checkpoint_metadata(
        self,
        checkpoint_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """更新检查点元数据
        
        Args:
            checkpoint_id: 检查点ID
            metadata: 新的元数据
            
        Returns:
            是否更新成功
        """
        try:
            # 加载现有检查点
            checkpoint_data = await self.repository.load_checkpoint(checkpoint_id)
            if not checkpoint_data:
                return False
            
            checkpoint = Checkpoint.from_dict(checkpoint_data)
            
            # 更新元数据
            if isinstance(metadata, CheckpointMetadata):
                checkpoint.metadata = metadata
            else:
                checkpoint.metadata = CheckpointMetadata(**metadata)
            
            # 保存更新
            await self.repository.save_checkpoint({
                **checkpoint.to_dict(),
                **checkpoint.metadata.to_dict()
            })
            
            # 更新缓存
            self.cache.set(checkpoint_id, checkpoint)
            
            return True
            
        except Exception as e:
            logger.error(f"更新检查点元数据失败: {checkpoint_id}, 错误: {e}")
            return False