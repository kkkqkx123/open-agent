"""完整的LangGraph SDK适配器实现"""

from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
from datetime import datetime
import logging

from ...application.threads.session_thread_mapper import ISessionThreadMapper
from ...application.threads.query_manager import ThreadQueryManager
from ...infrastructure.checkpoint.factory import CheckpointManager
from ...application.sessions.manager import ISessionManager
from ...domain.threads.interfaces import IThreadManager

logger = logging.getLogger(__name__)


class CompleteLangGraphSDKAdapter:
    """完整的LangGraph SDK适配器"""
    
    def __init__(
        self, 
        session_thread_mapper: ISessionThreadMapper,
        checkpoint_manager: CheckpointManager,
        thread_manager: IThreadManager,
        session_manager: ISessionManager,
        query_manager: Optional[ThreadQueryManager] = None
    ):
        """初始化完整的LangGraph SDK适配器
        
        Args:
            session_thread_mapper: Session-Thread映射管理器
            checkpoint_manager: Checkpoint管理器
            thread_manager: Thread管理器
            session_manager: Session管理器
            query_manager: Thread查询管理器（可选）
        """
        self.mapper = session_thread_mapper
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
        
        # 这里需要将graph_id映射到workflow_config_path
        # 暂时使用一个通用的配置路径，实际实现中需要根据graph_id映射
        workflow_config_path = f"configs/workflows/{graph_id}.yaml"
        
        # 创建Session和Thread的映射
        session_id, thread_id = await self.mapper.create_session_with_thread(
            workflow_config_path, 
            thread_metadata,
            initial_state=initial_state
        )
        
        # 如果有初始状态，保存为checkpoint
        if initial_state:
            checkpoint_id = await self.checkpoint_manager.save_checkpoint(
                thread_id, 
                initial_state,
                metadata={"created_at": datetime.now().isoformat()}
            )
            logger.info(f"创建初始checkpoint: {checkpoint_id}")
        
        result = {
            "thread_id": thread_id,
            "session_id": session_id,
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
        """
        if checkpoint_id:
            # 获取特定checkpoint的状态
            checkpoint = await self.checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
            if not checkpoint:
                raise ValueError(f"Checkpoint不存在: {checkpoint_id}")
            return checkpoint["state"]
        else:
            # 获取最新状态
            # 从checkpoint manager获取最新checkpoint
            checkpoints = await self.checkpoint_manager.list_checkpoints(thread_id)
            if checkpoints:
                latest_checkpoint = checkpoints[0]  # 假设列表是按时间倒序排列
                return latest_checkpoint["state"]
            else:
                # 如果没有checkpoint，尝试从thread manager获取状态
                state = await self.thread_manager.get_thread_state(thread_id)
                return state or {}
    
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
        """
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
        
        new_checkpoint_id = await self.checkpoint_manager.save_checkpoint(
            thread_id,
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
        checkpoints = await self.checkpoint_manager.list_checkpoints(
            thread_id, 
            limit=limit, 
            before=before, 
            after=after
        )
        
        # 转换为状态历史格式
        history = []
        for checkpoint in checkpoints:
            history.append({
                "values": checkpoint["state"],
                "checkpoint_id": checkpoint["checkpoint_id"],
                "metadata": checkpoint.get("metadata", {}),
                "created_at": checkpoint.get("created_at", datetime.now().isoformat())
            })
        
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
            checkpoints = await self.checkpoint_manager.list_checkpoints(thread["thread_id"], limit=1)
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
        # 删除checkpoint
        await self.checkpoint_manager.delete_all_checkpoints(thread_id)
        
        # 删除thread
        success = await self.thread_manager.delete_thread(thread_id)
        
        if success:
            # 删除session-thread映射
            session_id = await self.mapper.get_session_for_thread(thread_id)
            if session_id:
                await self.mapper.delete_mapping(session_id)
            
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
        """
        # 获取原thread信息
        original_thread_info = await self.thread_manager.get_thread_info(thread_id)
        if not original_thread_info:
            raise ValueError(f"原Thread不存在: {thread_id}")
        
        # 获取最新的状态
        original_state = await self.threads_get_state(thread_id)
        
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
            initial_state=original_state
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
            checkpoints = await self.checkpoint_manager.list_checkpoints(result["thread_id"], limit=1)
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
        
        # 按时间顺序返回事件
        for checkpoint in reversed(checkpoints):  # 最新的在前
            event = {
                "event": "checkpoint",
                "thread_id": thread_id,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "state": checkpoint["state"],
                "metadata": checkpoint.get("metadata", {}),
                "timestamp": checkpoint.get("created_at", datetime.now().isoformat())
            }
            
            if include_base_state:
                event["base_state"] = checkpoint["state"]
            
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