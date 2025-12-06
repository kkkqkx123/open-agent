"""LangGraph集成适配器

提供LangGraph到Thread checkpoint的适配，实现LangGraph的BaseCheckpointSaver接口。
"""

from typing import Dict, Any, Optional, List, AsyncIterator, Tuple
from datetime import datetime
import uuid

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointTuple
from langgraph.checkpoint.memory import MemorySaver

from src.services.logger.injection import get_logger
from src.interfaces.threads.checkpoint import IThreadCheckpointRepository
from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointStatus, CheckpointType


logger = get_logger(__name__)


class LangGraphCheckpointAdapter(BaseCheckpointSaver):
    """LangGraph到Thread checkpoint的适配器
    
    实现LangGraph的BaseCheckpointSaver接口，将LangGraph的检查点操作
    转换为Thread checkpoint的操作。
    """
    
    def __init__(self, repository: IThreadCheckpointRepository):
        """初始化适配器
        
        Args:
            repository: Thread检查点仓储
        """
        self._repository = repository
        logger.info("LangGraphCheckpointAdapter initialized")
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """获取检查点元组
        
        Args:
            config: 配置信息
            
        Returns:
            检查点元组，不存在返回None
        """
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            
            if not thread_id or not checkpoint_id:
                return None
            
            # 查找检查点
            checkpoint = await self._repository.find_by_id(checkpoint_id)
            if not checkpoint or checkpoint.thread_id != thread_id:
                return None
            
            # 转换为LangGraph检查点元组
            return self._to_checkpoint_tuple(checkpoint, config)
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint tuple: {e}")
            return None
    
    async def alist(
        self, 
        config: Dict[str, Any], 
        *, 
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> AsyncIterator[CheckpointTuple]:
        """列出检查点元组
        
        Args:
            config: 配置信息
            filter: 过滤条件
            before: 限制条件
            limit: 数量限制
            
        Yields:
            检查点元组
        """
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return
            
            # 获取线程的所有检查点
            checkpoints = await self._repository.find_by_thread(thread_id)
            
            # 应用过滤条件
            if filter:
                checkpoints = self._apply_filter(checkpoints, filter)
            
            # 应用时间限制
            if before:
                checkpoints = self._apply_before_filter(checkpoints, before)
            
            # 应用数量限制
            if limit:
                checkpoints = checkpoints[:limit]
            
            # 转换并返回
            for checkpoint in checkpoints:
                yield self._to_checkpoint_tuple(checkpoint, config)
                
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
    
    async def aput(
        self, 
        config: Dict[str, Any], 
        checkpoint: Checkpoint, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """保存检查点
        
        Args:
            config: 配置信息
            checkpoint: LangGraph检查点
            metadata: 元数据
            
        Returns:
            保存的配置信息
        """
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                raise ValueError("Thread ID is required in config")
            
            # 转换LangGraph检查点为Thread检查点
            thread_checkpoint = self._from_langgraph_checkpoint(
                checkpoint, 
                thread_id, 
                metadata
            )
            
            # 保存检查点
            success = await self._repository.save(thread_checkpoint)
            if not success:
                raise ValueError("Failed to save checkpoint")
            
            # 返回更新后的配置
            result_config = config.copy()
            result_config["configurable"] = result_config.get("configurable", {}).copy()
            result_config["configurable"]["checkpoint_id"] = thread_checkpoint.id
            
            logger.debug(f"Saved LangGraph checkpoint {thread_checkpoint.id} for thread {thread_id}")
            return result_config
            
        except Exception as e:
            logger.error(f"Failed to put checkpoint: {e}")
            raise
    
    async def adelete(self, config: Dict[str, Any]) -> None:
        """删除检查点
        
        Args:
            config: 配置信息
        """
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            
            if not thread_id or not checkpoint_id:
                return
            
            # 验证检查点属于指定线程
            checkpoint = await self._repository.find_by_id(checkpoint_id)
            if checkpoint and checkpoint.thread_id == thread_id:
                await self._repository.delete(checkpoint_id)
                logger.debug(f"Deleted checkpoint {checkpoint_id} for thread {thread_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
    
    def _to_checkpoint_tuple(self, checkpoint: ThreadCheckpoint, config: Dict[str, Any]) -> CheckpointTuple:
        """将Thread检查点转换为LangGraph检查点元组
        
        Args:
            checkpoint: Thread检查点
            config: 配置信息
            
        Returns:
            LangGraph检查点元组
        """
        # 创建LangGraph检查点
        langgraph_checkpoint = Checkpoint(
            id=checkpoint.id,
            channel_values=checkpoint.state_data,
            channel_versions={},
            versions_seen={},
            ts=checkpoint.created_at
        )
        
        # 创建检查点元组
        return CheckpointTuple(
            config=config,
            checkpoint=langgraph_checkpoint,
            parent_config=None,
            pending_writes=None
        )
    
    def _from_langgraph_checkpoint(
        self, 
        checkpoint: Checkpoint, 
        thread_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThreadCheckpoint:
        """将LangGraph检查点转换为Thread检查点
        
        Args:
            checkpoint: LangGraph检查点
            thread_id: 线程ID
            metadata: 元数据
            
        Returns:
            Thread检查点
        """
        # 构建Thread检查点元数据
        checkpoint_metadata = {}
        if metadata:
            checkpoint_metadata.update(metadata)
        
        # 添加LangGraph特定信息
        checkpoint_metadata.update({
            "langgraph_checkpoint_id": checkpoint.id,
            "langgraph_created_at": checkpoint.ts.isoformat() if checkpoint.ts else None,
            "source": "langgraph"
        })
        
        # 创建Thread检查点
        return ThreadCheckpoint(
            id=checkpoint.id,
            thread_id=thread_id,
            state_data=checkpoint.channel_values,
            metadata=checkpoint_metadata,
            checkpoint_type=CheckpointType.AUTO,
            created_at=checkpoint.ts or datetime.now()
        )
    
    def _apply_filter(self, checkpoints: List[ThreadCheckpoint], filter: Dict[str, Any]) -> List[ThreadCheckpoint]:
        """应用过滤条件
        
        Args:
            checkpoints: 检查点列表
            filter: 过滤条件
            
        Returns:
            过滤后的检查点列表
        """
        filtered = checkpoints
        
        # 按状态过滤
        if "status" in filter:
            status_filter = filter["status"]
            if isinstance(status_filter, str):
                status_filter = [status_filter]
            filtered = [cp for cp in filtered if cp.status.value in status_filter]
        
        # 按类型过滤
        if "checkpoint_type" in filter:
            type_filter = filter["checkpoint_type"]
            if isinstance(type_filter, str):
                type_filter = [type_filter]
            filtered = [cp for cp in filtered if cp.checkpoint_type.value in type_filter]
        
        # 按时间范围过滤
        if "created_after" in filter:
            created_after = filter["created_after"]
            if isinstance(created_after, str):
                created_after = datetime.fromisoformat(created_after)
            filtered = [cp for cp in filtered if cp.created_at >= created_after]
        
        if "created_before" in filter:
            created_before = filter["created_before"]
            if isinstance(created_before, str):
                created_before = datetime.fromisoformat(created_before)
            filtered = [cp for cp in filtered if cp.created_at <= created_before]
        
        return filtered
    
    def _apply_before_filter(self, checkpoints: List[ThreadCheckpoint], before: Dict[str, Any]) -> List[ThreadCheckpoint]:
        """应用时间限制过滤
        
        Args:
            checkpoints: 检查点列表
            before: 时间限制
            
        Returns:
            过滤后的检查点列表
        """
        if "step" in before:
            # 按步骤数量限制
            step_limit = before["step"]
            return checkpoints[:step_limit]
        
        if "ts" in before:
            # 按时间限制
            ts_limit = before["ts"]
            if isinstance(ts_limit, str):
                ts_limit = datetime.fromisoformat(ts_limit)
            return [cp for cp in checkpoints if cp.created_at <= ts_limit]
        
        return checkpoints


class ThreadCheckpointLangGraphManager:
    """Thread检查点LangGraph管理器
    
    提供Thread checkpoint与LangGraph的高级集成功能。
    """
    
    def __init__(self, repository: IThreadCheckpointRepository):
        """初始化管理器
        
        Args:
            repository: Thread检查点仓储
        """
        self._repository = repository
        self._adapter = LangGraphCheckpointAdapter(repository)
        logger.info("ThreadCheckpointLangGraphManager initialized")
    
    def get_langgraph_saver(self) -> LangGraphCheckpointAdapter:
        """获取LangGraph检查点保存器
        
        Returns:
            LangGraph检查点保存器
        """
        return self._adapter
    
    async def migrate_langgraph_checkpoints(
        self, 
        langgraph_saver: MemorySaver,
        thread_id: str
    ) -> Dict[str, Any]:
        """迁移LangGraph检查点到Thread checkpoint
        
        Args:
            langgraph_saver: LangGraph内存保存器
            thread_id: 线程ID
            
        Returns:
            迁移结果
        """
        try:
            migrated_count = 0
            failed_count = 0
            
            # 获取LangGraph检查点
            config = {"configurable": {"thread_id": thread_id}}
            
            async for checkpoint_tuple in langgraph_saver.alist(config):
                try:
                    # 转换并保存
                    thread_checkpoint = self._adapter._from_langgraph_checkpoint(
                        checkpoint_tuple.checkpoint,
                        thread_id,
                        {"migrated_from": "langgraph_memory"}
                    )
                    
                    success = await self._repository.save(thread_checkpoint)
                    if success:
                        migrated_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to migrate checkpoint {checkpoint_tuple.checkpoint.id}: {e}")
                    failed_count += 1
            
            return {
                "thread_id": thread_id,
                "migrated_count": migrated_count,
                "failed_count": failed_count,
                "total_processed": migrated_count + failed_count
            }
            
        except Exception as e:
            logger.error(f"Failed to migrate LangGraph checkpoints for thread {thread_id}: {e}")
            raise
    
    async def create_langgraph_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        step: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建LangGraph兼容的检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            step: 步骤号
            
        Returns:
            创建结果
        """
        try:
            # 构建元数据
            metadata = {"source": "langgraph"}
            if step is not None:
                metadata["step"] = step
            
            # 创建Thread检查点
            checkpoint = ThreadCheckpoint(
                thread_id=thread_id,
                state_data=state_data,
                metadata=metadata,
                checkpoint_type=CheckpointType.AUTO
            )
            
            # 保存检查点
            success = await self._repository.save(checkpoint)
            if not success:
                raise ValueError("Failed to save checkpoint")
            
            # 创建LangGraph配置
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint.id,
                    "checkpoint_ns": ""
                }
            }
            
            return {
                "success": True,
                "checkpoint_id": checkpoint.id,
                "config": config,
                "created_at": checkpoint.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create LangGraph checkpoint for thread {thread_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restore_langgraph_checkpoint(
        self, 
        thread_id: str, 
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """恢复LangGraph检查点
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
            
        Returns:
            恢复结果
        """
        try:
            # 查找检查点
            checkpoint = await self._repository.find_by_id(checkpoint_id)
            if not checkpoint or checkpoint.thread_id != thread_id:
                return {
                    "success": False,
                    "error": "Checkpoint not found or does not belong to thread"
                }
            
            # 验证检查点
            if not checkpoint.can_restore():
                return {
                    "success": False,
                    "error": f"Checkpoint cannot be restored: {checkpoint.status}"
                }
            
            # 标记为已恢复
            checkpoint.mark_restored()
            await self._repository.update(checkpoint)
            
            # 创建LangGraph配置
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint.id,
                    "checkpoint_ns": ""
                }
            }
            
            return {
                "success": True,
                "state_data": checkpoint.state_data,
                "config": config,
                "restored_at": checkpoint.last_restored_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restore LangGraph checkpoint {checkpoint_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }