"""完整的LangGraph SDK适配器实现"""

from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
from datetime import datetime
import logging

from ...application.threads.query_manager import ThreadQueryManager
from ...application.checkpoint.manager import CheckpointManager
from ...interfaces.sessions.base import ISessionManager
from ...domain.threads.interfaces import IThreadManager

logger = logging.getLogger(__name__)


class LangGraphSDKAdapter:
    """完整的LangGraph SDK适配器"""
    
    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        thread_manager: IThreadManager,
        session_manager: ISessionManager,
        query_manager: Optional[ThreadQueryManager] = None
    ):
        """初始化完整的LangGraph SDK适配器
        
        Args:
            checkpoint_manager: Checkpoint管理器
            thread_manager: Thread管理器
            session_manager: Session管理器
            query_manager: Thread查询管理器（可选）
        """
        self.checkpoint_manager = checkpoint_manager
        self.thread_manager = thread_manager
        self.session_manager = session_manager
        self.query_manager = query_manager or ThreadQueryManager(thread_manager)
    
    async def threads_create(
        self,
        graph_id: str,
        supersteps: Optional[List] = None,
        metadata: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """完整的Thread创建接口
        
        Args:
            graph_id: 图ID
            supersteps: 超步数据（可选）
            metadata: Thread元数据（可选）
            initial_state: 初始状态（可选）
            
        Returns:
            包含thread_id等信息的字典
        """
        thread_metadata = metadata or {}
        if supersteps:
            thread_metadata["supersteps"] = supersteps
        if initial_state:
            thread_metadata["initial_state"] = initial_state
        
        # 直接创建Thread，不再需要Session-Thread映射
        thread_id = await self.thread_manager.create_thread(graph_id, thread_metadata)
        
        # 如果有初始状态，保存为checkpoint
        if initial_state:
            logger.info(f"保存初始状态到checkpoint: {initial_state}")
            checkpoint_id = await self.checkpoint_manager.create_checkpoint(
                thread_id,
                thread_id, # workflow_id
                initial_state,
                metadata={"created_at": datetime.now().isoformat()}
            )
            logger.info(f"创建初始checkpoint: {checkpoint_id}")
        else:
            logger.info("没有初始状态需要保存")
        
        result = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"创建Thread成功: {thread_id}")
        return result
    
    async def threads_get_state(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取Thread状态
        
        Args:
            thread_id: Thread ID
            checkpoint_id: Checkpoint ID（可选），如果不提供则获取最新状态
            
        Returns:
            Thread状态
            
        Raises:
            ValueError: 当Thread不存在时
        """
        # 首先检查thread是否存在
        thread_exists = await self.thread_manager.thread_exists(thread_id)
        if not thread_exists:
            raise ValueError(f"Thread不存在: {thread_id}")
            
        if checkpoint_id:
            # 获取特定checkpoint的状态
            checkpoint = await self.checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
            logger.debug(f"获取特定checkpoint: {checkpoint}")
            if not checkpoint:
                raise ValueError(f"Checkpoint不存在: {checkpoint_id}")
            # 从checkpoint中获取状态数据（使用state_data而不是state）
            state_data = checkpoint.get("state_data", {})
            logger.debug(f"从checkpoint获取状态数据: {state_data}")
            return state_data
        else:
            # 优先从thread manager获取状态
            state = await self.thread_manager.get_thread_state(thread_id)
            logger.info(f"从thread manager获取状态: {state}")
            
            # 如果thread manager有状态，直接返回
            if state:
                return state
                
            # 如果thread manager没有状态，尝试从checkpoint manager获取最新checkpoint
            checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
            logger.info(f"获取到 {len(checkpoints)} 个checkpoints for thread_id: {thread_id}")
            if checkpoints:
                latest_checkpoint = checkpoints[0]  # 假设列表是按时间倒序排列
                logger.info(f"最新checkpoint: {latest_checkpoint}")
                # 从checkpoint中获取状态数据（使用state_data而不是state）
                state_data = latest_checkpoint.get("state_data", {})
                logger.info(f"从最新checkpoint获取状态数据: {state_data}")
                return state_data
            else:
                # 如果都没有，返回空字典
                return {}
    
    async def threads_update_state(
        self, 
        thread_id: str, 
        values: Dict[str, Any], 
        checkpoint_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            values: 要更新的值
            checkpoint_id: Checkpoint ID（可选）
            metadata: 元数据（可选）
            
        Returns:
            更新结果
            
        Raises:
            RuntimeError: 当Thread不存在或更新失败时
        """
        # 首先检查thread是否存在
        thread_exists = await self.thread_manager.thread_exists(thread_id)
        if not thread_exists:
            raise RuntimeError(f"Thread不存在: {thread_id}")
            
        # 更新thread状态
        success = await self.thread_manager.update_thread_state(thread_id, values)
        if not success:
            raise RuntimeError(f"更新Thread状态失败: {thread_id}")
        
        # 创建新的checkpoint
        checkpoint_metadata = metadata or {}
        checkpoint_metadata.update({
            "updated_at": datetime.now().isoformat(),
            "updated_by": "sdk_adapter"
        })
        
        new_checkpoint_id = await self.checkpoint_manager.create_checkpoint(
            thread_id,
            thread_id, # workflow_id
            values,
            metadata=checkpoint_metadata
        )
        
        result = {
            "thread_id": thread_id,
            "checkpoint_id": new_checkpoint_id,
            "updated_at": datetime.now().isoformat(),
            "success": True
        }
        
        logger.info(f"更新Thread状态成功: {thread_id}, checkpoint: {new_checkpoint_id}")
        return result
    
    async def threads_get_state_history(
        self, 
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取Thread状态历史
        
        Args:
            thread_id: Thread ID
            limit: 限制返回数量（可选）
            before: 获取此checkpoint之前的历史（可选）
            after: 获取此checkpoint之后的历史（可选）
            
        Returns:
            状态历史列表
        """
        # 获取checkpoints历史
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        
        # 调试信息
        logger.debug(f"获取到 {len(checkpoints)} 个checkpoints for thread_id: {thread_id}")
        for i, cp in enumerate(checkpoints):
            logger.debug(f"Checkpoint {i}: {cp}")
        
        # 转换为状态历史格式
        history = []
        for checkpoint in checkpoints:
            # 从checkpoint获取状态数据
            state_data = checkpoint.get("state_data", {})
            
            history_item = {
                "values": state_data,
                "checkpoint_id": checkpoint.get("id", checkpoint.get("checkpoint_id", "")),
                "metadata": checkpoint.get("metadata", {}),
                "created_at": checkpoint.get("created_at", datetime.now().isoformat())
            }
            
            # 添加额外的checkpoint信息
            if "step_count" in checkpoint:
                history_item["step"] = checkpoint["step_count"]
            if "trigger_reason" in checkpoint:
                history_item["trigger_reason"] = checkpoint["trigger_reason"]
            
            history.append(history_item)
        
        # 按创建时间倒序排列（最新的在前）
        # 如果没有created_at字段，将它们排在最后
        history.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 应用限制
        if limit and limit < len(history):
            history = history[:limit]
        
        logger.info(f"获取Thread历史成功: {thread_id}, 共{len(history)}条记录")
        return history
    
    async def threads_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出Threads
        
        Args:
            filters: 过滤条件（可选）
            
        Returns:
            Thread列表
        """
        # 使用查询管理器列出threads
        threads = await self.query_manager.search_threads(filters)
        
        # 添加额外信息
        result = []
        for thread in threads:
            thread_info = await self.thread_manager.get_thread_info(thread["thread_id"])
            if thread_info:
                thread.update(thread_info)
            
            # 获取最后活动时间
            checkpoints = await self.checkpoint_manager.list_checkpoints(thread["thread_id"])
            if checkpoints:
                thread["last_active"] = checkpoints[0].get("created_at", datetime.now().isoformat())
            else:
                thread["last_active"] = thread.get("created_at", datetime.now().isoformat())
            
            result.append(thread)
        
        logger.info(f"列出Threads成功，共{len(result)}个")
        return result
    
    async def threads_delete(self, thread_id: str) -> bool:
        """删除Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        # 删除所有相关的checkpoints
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        for checkpoint in checkpoints:
            await self.checkpoint_manager.delete_checkpoint(thread_id, checkpoint.get('id', checkpoint.get('checkpoint_id', '')))
        
        # 删除thread
        success = await self.thread_manager.delete_thread(thread_id)
        
        if success:
            logger.info(f"删除Thread成功: {thread_id}")
        
        return success
    
    
    
    async def threads_copy(
        self, 
        thread_id: str, 
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """复制Thread
        
        Args:
            thread_id: 原Thread ID
            new_metadata: 新的元数据（可选）
            
        Returns:
            新Thread信息
            
        Raises:
            ValueError: 当原Thread不存在时
        """
        # 首先检查thread是否存在
        thread_exists = await self.thread_manager.thread_exists(thread_id)
        if not thread_exists:
            raise ValueError(f"原Thread不存在: {thread_id}")
            
        # 获取原thread信息
        original_thread_info = await self.thread_manager.get_thread_info(thread_id)
        if not original_thread_info:
            raise ValueError(f"原Thread信息不存在: {thread_id}")
        
        # 获取最新的状态
        original_state = await self.threads_get_state(thread_id)
        
        # 创建状态的深拷贝，确保独立性
        import copy
        state_copy = copy.deepcopy(original_state) if original_state else {}
        
        # 创建新thread
        new_thread_metadata = new_metadata or {}
        new_thread_metadata.update({
            "copied_from": thread_id,
            "copied_at": datetime.now().isoformat(),
            **original_thread_info.get("metadata", {})
        })
        
        # 生成新graph_id（这里简单地添加后缀）
        original_graph_id = original_thread_info.get("graph_id", "unknown")
        new_graph_id = f"{original_graph_id}_copy_{int(datetime.now().timestamp())}"
        
        # 创建新thread
        result = await self.threads_create(
            graph_id=new_graph_id,
            metadata=new_thread_metadata,
            initial_state=state_copy
        )
        
        logger.info(f"复制Thread成功: {thread_id} -> {result['thread_id']}")
        return result
    
    async def threads_search(
        self, 
        status: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """搜索Threads
        
        Args:
            status: 状态过滤
            metadata: 元数据过滤
            created_after: 创建时间范围（之后）
            created_before: 创建时间范围（之前）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            搜索结果
        """
        filters = {}
        if status:
            filters["status"] = status
        if metadata:
            filters["metadata"] = metadata
        if created_after:
            filters["created_after"] = created_after
        if created_before:
            filters["created_before"] = created_before
        
        # 使用查询管理器进行搜索
        results = await self.query_manager.search_threads(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        # 添加额外信息
        for result in results:
            # 获取最后活动时间
            checkpoints = await self.checkpoint_manager.list_checkpoints(result["thread_id"])
            if checkpoints:
                result["last_active"] = checkpoints[0].get("created_at", datetime.now().isoformat())
            else:
                result["last_active"] = result.get("created_at", datetime.now().isoformat())
        
        logger.info(f"搜索Threads成功，共{len(results)}个结果")
        return results
    
    async def threads_stream_events(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        events: Optional[List[str]] = None,
        include_base_state: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式获取Thread事件
        
        Args:
            thread_id: Thread ID
            config: 配置（可选）
            events: 事件类型过滤（可选）
            include_base_state: 是否包含基础状态
            
        Yields:
            事件数据
        """
        # 获取所有checkpoints
        checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
        
        # 按时间倒序返回事件（最新的在前）
        for checkpoint in checkpoints:  # 最新的在前，最旧的在后
            # 从checkpoint获取状态数据，如果为空则从thread manager获取
            state_data = checkpoint.get("state_data", {})
            if not state_data:
                # 尝试从thread manager获取当前状态
                state_data = await self.thread_manager.get_thread_state(thread_id)
                if not state_data:
                    state_data = {}
            
            event = {
                "event": "checkpoint",
                "thread_id": thread_id,
                "checkpoint_id": checkpoint.get("id", checkpoint.get("checkpoint_id", "")),
                "state": state_data,
                "metadata": checkpoint.get("metadata", {}),
                "timestamp": checkpoint.get("created_at", datetime.now().isoformat())
            }
            
            if include_base_state:
                # 使用state_data而不是可能不存在的state字段
                event["base_state"] = checkpoint.get("state_data", {})
            
            if not events or event["event"] in events:
                yield event
    
    async def threads_update_metadata(
        self,
        thread_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """更新Thread元数据
        
        Args:
            thread_id: Thread ID
            metadata: 要更新的元数据
            
        Returns:
            更新是否成功
        """
        success = await self.thread_manager.update_thread_metadata(thread_id, metadata)
        
        if success:
            logger.info(f"更新Thread元数据成功: {thread_id}")
        
        return success
    
    async def threads_fork(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> Dict[str, Any]:
        """LangGraph兼容的thread分支功能"""
        # 验证thread存在
        if not await self.thread_manager.thread_exists(thread_id):
            raise ValueError(f"Thread不存在: {thread_id}")
        
        # 验证checkpoint存在
        checkpoint = await self.checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint不存在: {checkpoint_id}")
        
        # 创建分支
        new_thread_id = await self.thread_manager.fork_thread(
            thread_id,
            checkpoint_id,
            branch_name,
            metadata={"forked_from": thread_id, "forked_at": datetime.now().isoformat()}
        )
        
        result = {
            "thread_id": new_thread_id,
            "source_thread_id": thread_id,
            "source_checkpoint_id": checkpoint_id,
            "branch_name": branch_name,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"创建Thread分支成功: {thread_id} -> {new_thread_id}")
        return result
    
    async def threads_rollback(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """LangGraph兼容的thread回滚功能"""
        # 验证thread存在
        if not await self.thread_manager.thread_exists(thread_id):
            raise ValueError(f"Thread不存在: {thread_id}")
        
        # 执行回滚
        success = await self.thread_manager.rollback_thread(thread_id, checkpoint_id)
        
        result = {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "success": success,
            "rolled_back_at": datetime.now().isoformat()
        }
        
        if success:
            logger.info(f"Thread回滚成功: {thread_id} -> {checkpoint_id}")
        else:
            logger.warning(f"Thread回滚失败: {thread_id} -> {checkpoint_id}")
        
        return result