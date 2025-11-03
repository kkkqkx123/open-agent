"""Thread管理器实现 - 重构版本

专注于执行与LangGraph交互，负责：
1. LangGraph工作流的执行和流式处理
2. Thread生命周期管理
3. 通过LangGraphAdapter统一状态管理
4. Thread分支和快照管理
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator, cast
import logging

from .interfaces import IThreadManager
from ...infrastructure.threads.metadata_store import IThreadMetadataStore
from ...domain.checkpoint.interfaces import ICheckpointManager
from ...infrastructure.langgraph.adapter import ILangGraphAdapter
from ...infrastructure.graph.config import GraphConfig
from ...infrastructure.graph.states import WorkflowState
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class ThreadManager(IThreadManager):
    """Thread管理器实现 - 重构版本
    
    专注于执行与LangGraph交互，通过LangGraphAdapter统一管理状态
    """
    
    def __init__(
        self,
        metadata_store: IThreadMetadataStore,
        checkpoint_manager: ICheckpointManager,
        langgraph_adapter: ILangGraphAdapter
    ):
        """初始化Thread管理器
        
        Args:
            metadata_store: Thread元数据存储
            checkpoint_manager: Checkpoint管理器（保持向后兼容）
            langgraph_adapter: LangGraph适配器（新增）
        """
        self.metadata_store = metadata_store
        self.checkpoint_manager = checkpoint_manager
        self.langgraph_adapter = langgraph_adapter
        
        # 图缓存
        self._graph_cache: Dict[str, Any] = {}
        
        logger.info("ThreadManager初始化完成（重构版本）")
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread"""
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        # 创建Thread元数据
        thread_metadata = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "checkpoint_count": 0,
            "total_steps": 0,
            **(metadata or {})
        }
        
        # 保存元数据
        success = await self.metadata_store.save_metadata(thread_id, thread_metadata)
        if not success:
            logger.error(f"保存Thread元数据失败: {thread_id}")
            raise RuntimeError(f"创建Thread失败: {thread_id}")
        
        logger.info(f"创建Thread成功: {thread_id}, graph_id: {graph_id}")
        return thread_id
    
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread（新增方法）
        
        Args:
            config_path: 工作流配置文件路径
            metadata: 额外元数据
            
        Returns:
            str: Thread ID
        """
        # 加载图配置
        graph_config = await self._load_graph_config(config_path)
        graph_id = graph_config.name
        
        # 创建Thread
        thread_metadata = metadata or {}
        thread_metadata.update({
            "config_path": config_path,
            "config_version": graph_config.version or "latest"
        })
        
        return await self.create_thread(graph_id, thread_metadata)
    
    async def execute_workflow( # type: ignore
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """执行工作流（新增核心方法）
        
        Args:
            thread_id: Thread ID
            config: 运行配置
            initial_state: 初始状态
            
        Returns:
            WorkflowState: 执行结果
        """
        try:
            # 验证Thread存在
            if not await self.thread_exists(thread_id):
                raise ValueError(f"Thread不存在: {thread_id}")
            
            # 获取Thread信息
            thread_info = await self.get_thread_info(thread_id)
            if not thread_info:
                raise RuntimeError(f"无法获取Thread信息: {thread_id}")
            
            # 加载或获取图
            graph = await self._get_or_create_graph(thread_info)
            
            # 如果有初始状态，保存为checkpoint
            if initial_state:
                await self.langgraph_adapter.save_checkpoint(
                    thread_id,
                    cast(WorkflowState, initial_state),
                    {"trigger_reason": "initial_state"}
                )
            
            # 执行工作流
            result = await self.langgraph_adapter.execute_graph(graph, thread_id, cast(RunnableConfig, config))
            
            # 更新Thread元数据
            await self._update_thread_execution_stats(thread_id)
            
            logger.info(f"工作流执行成功: thread_id={thread_id}")
            return result
            
        except Exception as e:
            logger.error(f"执行工作流失败: thread_id={thread_id}, error={e}")
            await self._handle_execution_error(thread_id, e)
            raise
    
    async def stream_workflow( # type: ignore
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[WorkflowState, None]:
        """流式执行工作流（新增核心方法）
        
        Args:
            thread_id: Thread ID
            config: 运行配置
            initial_state: 初始状态
            
        Yields:
            WorkflowState: 中间状态
        """
        try:
            # 验证Thread存在
            if not await self.thread_exists(thread_id):
                raise ValueError(f"Thread不存在: {thread_id}")
            
            # 获取Thread信息
            thread_info = await self.get_thread_info(thread_id)
            if not thread_info:
                raise RuntimeError(f"无法获取Thread信息: {thread_id}")
            
            # 加载或获取图
            graph = await self._get_or_create_graph(thread_info)
            
            # 如果有初始状态，保存为checkpoint
            if initial_state:
                await self.langgraph_adapter.save_checkpoint(
                thread_id,
                cast(WorkflowState, initial_state),
                {"trigger_reason": "initial_state"}
                )
            
            # 流式执行工作流
            async for state in await self.langgraph_adapter.stream_graph(graph, thread_id, cast(RunnableConfig, config)):
                yield state
            
            # 更新Thread元数据
            await self._update_thread_execution_stats(thread_id)
            
            logger.info(f"流式工作流执行成功: thread_id={thread_id}")
            
        except Exception as e:
            logger.error(f"流式执行工作流失败: thread_id={thread_id}, error={e}")
            await self._handle_execution_error(thread_id, e)
            raise
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        if not metadata:
            return None
        
        # 获取checkpoint数量（使用LangGraphAdapter）
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        metadata["checkpoint_count"] = len(checkpoints)
        
        # 获取最新checkpoint状态
        if checkpoints:
            latest_checkpoint = checkpoints[0]  # 假设列表按时间倒序
            metadata["latest_checkpoint_id"] = latest_checkpoint.get("id")
            metadata["latest_checkpoint_created_at"] = latest_checkpoint.get("timestamp")
        
        return metadata
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        if not metadata:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        metadata["status"] = status
        metadata["updated_at"] = datetime.now().isoformat()
        
        success = await self.metadata_store.save_metadata(thread_id, metadata)
        if success:
            logger.info(f"Thread状态更新成功: {thread_id} -> {status}")
        
        return success
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        current_metadata = await self.metadata_store.get_metadata(thread_id)
        if not current_metadata:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 合并元数据，保留系统字段
        system_fields = {"thread_id", "graph_id", "created_at", "checkpoint_count"}
        updated_metadata = {
            k: v for k, v in current_metadata.items() 
            if k in system_fields
        }
        updated_metadata.update(metadata)
        updated_metadata["updated_at"] = datetime.now().isoformat()
        
        success = await self.metadata_store.save_metadata(thread_id, updated_metadata)
        if success:
            logger.info(f"Thread元数据更新成功: {thread_id}")
        
        return success
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        # 检查Thread是否存在
        metadata = await self.metadata_store.get_metadata(thread_id)
        if not metadata:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 删除所有checkpoints（使用LangGraphAdapter）
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        for checkpoint in checkpoints:
            checkpoint_id = checkpoint.get("id")
            if checkpoint_id:
                await self.langgraph_adapter.delete_checkpoint(thread_id, checkpoint_id)
        
        # 删除元数据
        success = await self.metadata_store.delete_metadata(thread_id)
        if success:
            logger.info(f"Thread删除成功: {thread_id}")
        
        return success
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads"""
        threads = await self.metadata_store.list_threads()
        
        # 应用过滤条件
        if filters:
            filtered_threads = []
            for thread in threads:
                match = True
                for key, value in filters.items():
                    if thread.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_threads.append(thread)
            threads = filtered_threads
        
        # 按创建时间排序
        threads.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 应用数量限制
        if limit:
            threads = threads[:limit]
        
        return threads
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        return metadata is not None
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态（使用LangGraphAdapter）"""
        if not await self.thread_exists(thread_id):
            return None

        # 获取最新checkpoint
        checkpoint = await self.langgraph_adapter.load_checkpoint(thread_id)
        if not checkpoint:
            return {}

        state_data = checkpoint.get("state", {})
        if not isinstance(state_data, dict):
            return {}
        return state_data
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态（使用LangGraphAdapter）"""
        if not await self.thread_exists(thread_id):
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 创建新的checkpoint
        checkpoint_id = await self.langgraph_adapter.save_checkpoint(
        thread_id,
        cast(WorkflowState, state),
        metadata={"trigger_reason": "thread_state_update"}
        )
        
        if checkpoint_id:
            # 更新Thread元数据
            metadata = await self.metadata_store.get_metadata(thread_id)
            if metadata:
                metadata["updated_at"] = datetime.now().isoformat()
                metadata["total_steps"] = metadata.get("total_steps", 0) + 1
                await self.metadata_store.save_metadata(thread_id, metadata)
            
            logger.info(f"Thread状态更新成功: {thread_id}, checkpoint: {checkpoint_id}")
            return True
        
        return False
    
    async def fork_thread(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支"""
        # 验证源thread存在
        if not await self.thread_exists(source_thread_id):
            raise ValueError(f"源thread不存在: {source_thread_id}")
        
        # 验证checkpoint存在
        checkpoint = await self.langgraph_adapter.load_checkpoint(source_thread_id, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"checkpoint不存在: {checkpoint_id}")
        
        # 获取源thread信息
        source_info = await self.get_thread_info(source_thread_id)
        if not source_info:
            raise RuntimeError(f"无法获取源thread信息: {source_thread_id}")
        
        # 创建新thread
        new_thread_id = await self.create_thread(
            graph_id=source_info.get("graph_id", "default_graph"),
            metadata={
                "branch_name": branch_name,
                "source_thread_id": source_thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_type": "fork",
                **(metadata or {})
            }
        )
        
        # 复制checkpoint状态到新thread
        state_data = checkpoint.get("state", {})
        success = await self.update_thread_state(new_thread_id, state_data)
        if not success:
            logger.warning(f"复制checkpoint状态到新thread失败: {new_thread_id}")
        
        return new_thread_id
    
    async def create_thread_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建thread状态快照"""
        # 验证thread存在
        if not await self.thread_exists(thread_id):
            raise ValueError(f"Thread不存在: {thread_id}")
        
        # 获取所有checkpoints
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        checkpoint_ids = [cp.get("id") for cp in checkpoints if cp.get("id")]
        
        # 创建快照ID
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
        
        # 保存快照信息到thread元数据
        thread_metadata = await self.metadata_store.get_metadata(thread_id)
        if thread_metadata:
            snapshots = thread_metadata.get("snapshots", [])
            snapshots.append({
                "snapshot_id": snapshot_id,
                "thread_id": thread_id,
                "snapshot_name": snapshot_name,
                "description": description,
                "checkpoint_ids": checkpoint_ids,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "total_checkpoints": len(checkpoint_ids)
                }
            })
            thread_metadata["snapshots"] = snapshots
            thread_metadata["updated_at"] = datetime.now().isoformat()
            await self.metadata_store.save_metadata(thread_id, thread_metadata)
        
        return snapshot_id
    
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚thread到指定checkpoint"""
        # 1. 验证checkpoint存在
        checkpoint = await self.langgraph_adapter.load_checkpoint(thread_id, checkpoint_id)
        if not checkpoint:
            return False
        
        # 2. 创建回滚checkpoint（用于undo）
        rollback_metadata = {
            "rollback_from": checkpoint_id,
            "rollback_reason": "user_requested",
            "original_state": await self.get_thread_state(thread_id)
        }
        
        # 3. 恢复状态
        state_data = checkpoint.get("state", {})
        await self.langgraph_adapter.save_checkpoint(
            thread_id,
            state_data,
            {
                "rollback_to": checkpoint_id,
                **rollback_metadata
            }
        )
        
        # 4. 记录回滚操作
        await self.metadata_store.update_metadata(thread_id, {
            "last_rollback": datetime.now().isoformat(),
            "rollback_checkpoint": checkpoint_id
        })
        
        return True
    
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取thread历史记录（使用LangGraphAdapter）"""
        if not await self.thread_exists(thread_id):
            return []
        
        # 获取所有checkpoints
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        
        # 应用限制
        if limit and len(checkpoints) > limit:
            checkpoints = checkpoints[:limit]
        
        return checkpoints
    
    # === 私有辅助方法 ===
    
    async def _load_graph_config(self, config_path: str) -> GraphConfig:
        """加载图配置"""
        # 这里应该使用配置加载器，暂时简化实现
        # TODO: 集成CentralizedConfigManager
        from ...infrastructure.config_loader import IConfigLoader
        # 临时实现，实际应该依赖注入
        config_loader = None  # 应该通过依赖注入获取
        if config_loader:
            return config_loader.load_graph_config(config_path)
        else:
            # 简化实现
            return GraphConfig(name="default", version="1.0", description="Default graph config")
    
    async def _get_or_create_graph(self, thread_info: Dict[str, Any]) -> Any:
        """获取或创建图"""
        graph_id = thread_info.get("graph_id")
        config_path = thread_info.get("config_path")
        
        # 检查缓存
        cache_key = f"{graph_id}_{config_path}"
        if cache_key in self._graph_cache:
            return self._graph_cache[cache_key]
        
        # 创建图配置
        if config_path:
            graph_config = await self._load_graph_config(config_path)
        else:
            # 简化实现
            graph_config = GraphConfig(name=cast(str, graph_id), version="1.0", description="Graph config from graph_id")
        
        # 创建图
        graph = await self.langgraph_adapter.create_graph(graph_config)
        
        # 缓存图
        self._graph_cache[cache_key] = graph
        
        return graph
    
    async def _update_thread_execution_stats(self, thread_id: str) -> None:
        """更新Thread执行统计"""
        metadata = await self.metadata_store.get_metadata(thread_id)
        if metadata:
            metadata["updated_at"] = datetime.now().isoformat()
            metadata["total_steps"] = metadata.get("total_steps", 0) + 1
            await self.metadata_store.save_metadata(thread_id, metadata)
    
    async def _handle_execution_error(self, thread_id: str, error: Exception) -> None:
        """处理执行错误"""
        # 更新Thread状态为错误
        await self.update_thread_status(thread_id, "error")
        
        # 记录错误信息
        await self.metadata_store.update_metadata(thread_id, {
            "last_error": str(error),
            "error_at": datetime.now().isoformat()
        })
    
    async def clear_graph_cache(self) -> None:
        """清空图缓存"""
        self._graph_cache.clear()
        logger.info("ThreadManager图缓存已清空")
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "graph_cache_size": len(self._graph_cache),
            "cached_graphs": list(self._graph_cache.keys())
        }