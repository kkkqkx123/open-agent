"""Thread应用服务实现

整合所有Thread相关功能，提供统一的服务接口。
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator, cast
import logging

from .interfaces import IThreadService
from ...domain.threads.interfaces import IThreadRepository, IThreadDomainService, IThreadBranchRepository, IThreadSnapshotRepository
from ...domain.threads.models import Thread, ThreadBranch, ThreadSnapshot
from ...infrastructure.threads.metadata_store import IThreadMetadataStore
from ...infrastructure.threads.branch_store import IThreadBranchStore
from ...infrastructure.threads.snapshot_store import IThreadSnapshotStore
from ...domain.checkpoint.interfaces import ICheckpointManager
from ...infrastructure.langgraph.adapter import ILangGraphAdapter
from ...infrastructure.graph.config import GraphConfig
from ...infrastructure.graph.states import WorkflowState
from ...domain.threads.collaboration import ThreadCollaboration, SharedThreadState
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class ThreadService(IThreadService):
    """Thread应用服务实现
    
    整合了Thread管理、分支管理、快照管理、查询管理、协作管理等功能。
    """
    
    def __init__(
        self,
        thread_repository: IThreadRepository,
        thread_domain_service: IThreadDomainService,
        branch_repository: IThreadBranchRepository,
        snapshot_repository: IThreadSnapshotRepository,
        checkpoint_manager: ICheckpointManager,
        langgraph_adapter: ILangGraphAdapter,
        metadata_store: IThreadMetadataStore,
        branch_store: IThreadBranchStore,
        snapshot_store: IThreadSnapshotStore
    ):
        """初始化Thread服务
        
        Args:
            thread_repository: Thread仓储
            thread_domain_service: Thread领域服务
            branch_repository: 分支仓储
            snapshot_repository: 快照仓储
            checkpoint_manager: 检查点管理器
            langgraph_adapter: LangGraph适配器
            metadata_store: 元数据存储
            branch_store: 分支存储
            snapshot_store: 快照存储
        """
        self.thread_repository = thread_repository
        self.thread_domain_service = thread_domain_service
        self.branch_repository = branch_repository
        self.snapshot_repository = snapshot_repository
        self.checkpoint_manager = checkpoint_manager
        self.langgraph_adapter = langgraph_adapter
        self.metadata_store = metadata_store
        self.branch_store = branch_store
        self.snapshot_store = snapshot_store
        
        # 图缓存
        self._graph_cache: Dict[str, Any] = {}
        
        logger.info("ThreadService初始化完成")
    
    # === Thread生命周期管理 ===
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread"""
        thread = await self.thread_domain_service.create_thread(graph_id, metadata)
        
        # 保存到仓储
        success = await self.thread_repository.save(thread)
        if not success:
            logger.error(f"保存Thread失败: {thread.thread_id}")
            raise RuntimeError(f"创建Thread失败: {thread.thread_id}")
        
        # 保存元数据到存储
        thread_metadata = {
            "thread_id": thread.thread_id,
            "graph_id": thread.graph_id,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "status": thread.status,
            "checkpoint_count": 0,
            "total_steps": 0,
            **thread.metadata
        }
        await self.metadata_store.save_metadata(thread.thread_id, thread_metadata)
        
        logger.info(f"创建Thread成功: {thread.thread_id}, graph_id: {graph_id}")
        return thread.thread_id
    
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread"""
        thread = await self.thread_domain_service.create_thread_from_config(config_path, metadata)
        
        # 保存到仓储
        success = await self.thread_repository.save(thread)
        if not success:
            logger.error(f"保存Thread失败: {thread.thread_id}")
            raise RuntimeError(f"创建Thread失败: {thread.thread_id}")
        
        # 保存元数据到存储
        thread_metadata = {
            "thread_id": thread.thread_id,
            "graph_id": thread.graph_id,
            "config_path": config_path,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "status": thread.status,
            "checkpoint_count": 0,
            "total_steps": 0,
            **thread.metadata
        }
        await self.metadata_store.save_metadata(thread.thread_id, thread_metadata)
        
        logger.info(f"从配置创建Thread成功: {thread.thread_id}, config_path: {config_path}")
        return thread.thread_id
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        # 从仓储获取Thread实体
        thread = await self.thread_repository.find_by_id(thread_id)
        if not thread:
            return None
        
        # 获取checkpoint数量
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        
        # 获取分支和快照信息
        branches = await self.branch_repository.find_by_thread(thread_id)
        snapshots = await self.snapshot_repository.find_by_thread(thread_id)
        
        # 构建返回信息
        return {
            "thread_id": thread.thread_id,
            "graph_id": thread.graph_id,
            "status": thread.status,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "metadata": thread.metadata,
            "checkpoint_count": len(checkpoints),
            "branch_count": len(branches),
            "snapshot_count": len(snapshots),
            "branches": [
                {
                    "branch_id": branch.branch_id,
                    "branch_name": branch.branch_name,
                    "created_at": branch.created_at.isoformat(),
                    "status": branch.status
                }
                for branch in branches
            ],
            "snapshots": [
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "snapshot_name": snapshot.snapshot_name,
                    "created_at": snapshot.created_at.isoformat()
                }
                for snapshot in snapshots
            ]
        }
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态"""
        thread = await self.thread_repository.find_by_id(thread_id)
        if not thread:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 更新实体状态
        thread.update_status(status)
        
        # 保存到仓储
        success = await self.thread_repository.save(thread)
        if success:
            # 更新元数据存储
            await self.metadata_store.update_metadata(thread_id, {
                "status": status,
                "updated_at": thread.updated_at.isoformat()
            })
            logger.info(f"Thread状态更新成功: {thread_id} -> {status}")
        
        return success
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        thread = await self.thread_repository.find_by_id(thread_id)
        if not thread:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 更新实体元数据
        thread.update_metadata(metadata)
        
        # 保存到仓储
        success = await self.thread_repository.save(thread)
        if success:
            # 更新元数据存储
            await self.metadata_store.update_metadata(thread_id, {
                "metadata": thread.metadata,
                "updated_at": thread.updated_at.isoformat()
            })
            logger.info(f"Thread元数据更新成功: {thread_id}")
        
        return success
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        thread = await self.thread_repository.find_by_id(thread_id)
        if not thread:
            logger.warning(f"Thread不存在: {thread_id}")
            return False
        
        # 删除所有checkpoints
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        for checkpoint in checkpoints:
            checkpoint_id = checkpoint.get("id")
            if checkpoint_id:
                await self.langgraph_adapter.delete_checkpoint(thread_id, checkpoint_id)
        
        # 删除分支
        branches = await self.branch_repository.find_by_thread(thread_id)
        for branch in branches:
            await self.branch_repository.delete(branch.branch_id)
        
        # 删除快照
        snapshots = await self.snapshot_repository.find_by_thread(thread_id)
        for snapshot in snapshots:
            await self.snapshot_repository.delete(snapshot.snapshot_id)
        
        # 删除元数据
        await self.metadata_store.delete_metadata(thread_id)
        
        # 删除Thread实体
        success = await self.thread_repository.delete(thread_id)
        if success:
            logger.info(f"Thread删除成功: {thread_id}")
        
        return success
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads"""
        threads = await self.thread_repository.find_all(filters)
        
        # 转换为字典格式
        result = []
        for thread in threads:
            thread_info = {
                "thread_id": thread.thread_id,
                "graph_id": thread.graph_id,
                "status": thread.status,
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "metadata": thread.metadata
            }
            result.append(thread_info)
        
        # 应用数量限制
        if limit:
            result = result[:limit]
        
        return result
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        return await self.thread_repository.exists(thread_id)
    
    # === 工作流执行 ===
    
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """执行工作流"""
        try:
            # 验证Thread存在
            if not await self.thread_exists(thread_id):
                raise ValueError(f"Thread不存在: {thread_id}")
            
            # 获取Thread信息
            thread = await self.thread_repository.find_by_id(thread_id)
            if not thread:
                raise RuntimeError(f"无法获取Thread信息: {thread_id}")
            
            # 加载或获取图
            graph = await self._get_or_create_graph(thread)
            
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
    
    async def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        try:
            # 验证Thread存在
            if not await self.thread_exists(thread_id):
                raise ValueError(f"Thread不存在: {thread_id}")
            
            # 获取Thread信息
            thread = await self.thread_repository.find_by_id(thread_id)
            if not thread:
                raise RuntimeError(f"无法获取Thread信息: {thread_id}")
            
            # 加载或获取图
            graph = await self._get_or_create_graph(thread)
            
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
    
    # === 状态管理 ===
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
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
        """更新Thread状态"""
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
            thread = await self.thread_repository.find_by_id(thread_id)
            if thread:
                thread.update_metadata({"total_steps": thread.metadata.get("total_steps", 0) + 1})
                await self.thread_repository.save(thread)
                
                await self.metadata_store.update_metadata(thread_id, {
                    "updated_at": thread.updated_at.isoformat(),
                    "total_steps": thread.metadata.get("total_steps", 0)
                })
            
            logger.info(f"Thread状态更新成功: {thread_id}, checkpoint: {checkpoint_id}")
            return True
        
        return False
    
    # === 分支管理 ===
    
    async def create_branch(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建Thread分支"""
        # 验证源thread存在
        source_thread = await self.thread_repository.find_by_id(thread_id)
        if not source_thread:
            raise ValueError(f"源thread不存在: {thread_id}")
        
        # 验证checkpoint存在
        checkpoint = await self.langgraph_adapter.load_checkpoint(thread_id, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"checkpoint不存在: {checkpoint_id}")
        
        # 创建新thread
        new_thread = await self.thread_domain_service.fork_thread(
            source_thread, checkpoint_id, branch_name, metadata
        )
        
        # 保存新thread
        success = await self.thread_repository.save(new_thread)
        if not success:
            raise RuntimeError(f"创建分支Thread失败: {new_thread.thread_id}")
        
        # 复制checkpoint状态到新thread
        state_data = checkpoint.get("state", {})
        await self.update_thread_state(new_thread.thread_id, state_data)
        
        # 创建分支记录
        branch = ThreadBranch(
            branch_id=f"branch_{uuid.uuid4().hex[:8]}",
            source_thread_id=thread_id,
            source_checkpoint_id=checkpoint_id,
            branch_name=branch_name,
            created_at=datetime.now(),
            metadata=metadata or {},
            status="active"
        )
        
        # 保存分支信息
        await self.branch_repository.save(branch)
        await self.branch_store.save_branch(branch)
        
        # 更新新thread的元数据，包含分支信息
        await self.metadata_store.update_metadata(new_thread.thread_id, {
            "branch_info": {
                "branch_id": branch.branch_id,
                "source_thread_id": thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_name": branch_name
            }
        })
        
        return new_thread.thread_id
    
    async def get_thread_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取Thread的所有分支"""
        branches = await self.branch_repository.find_by_thread(thread_id)
        
        result = []
        for branch in branches:
            result.append({
                "branch_id": branch.branch_id,
                "source_thread_id": branch.source_thread_id,
                "source_checkpoint_id": branch.source_checkpoint_id,
                "branch_name": branch.branch_name,
                "created_at": branch.created_at.isoformat(),
                "status": branch.status,
                "metadata": branch.metadata
            })
        
        return result
    
    async def merge_branch(
        self,
        target_thread_id: str,
        source_thread_id: str,
        merge_strategy: str = "latest"
    ) -> bool:
        """合并分支到目标Thread"""
        # 验证目标thread存在
        if not await self.thread_exists(target_thread_id):
            return False
        
        # 验证源thread存在
        if not await self.thread_exists(source_thread_id):
            return False
        
        # 获取源thread的最新状态
        source_state = await self.get_thread_state(source_thread_id)
        if source_state is None:
            return False
        
        # 根据策略合并状态
        if merge_strategy == "latest":
            # 直接使用源thread的最新状态
            success = await self.update_thread_state(target_thread_id, source_state)
        elif merge_strategy == "preserve_target":
            # 保留目标thread状态，只合并特定字段
            target_state = await self.get_thread_state(target_thread_id)
            if target_state is None:
                target_state = {}
            
            # 合并逻辑（简化实现）
            merged_state = {**target_state, **source_state}
            success = await self.update_thread_state(target_thread_id, merged_state)
        else:
            # 默认使用latest策略
            success = await self.update_thread_state(target_thread_id, source_state)
        
        if success:
            # 更新元数据记录合并操作
            await self.metadata_store.update_metadata(target_thread_id, {
                "last_merge": datetime.now().isoformat(),
                "merged_from": source_thread_id,
                "merge_strategy": merge_strategy
            })
        
        return success
    
    # === 快照管理 ===
    
    async def create_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建Thread快照"""
        # 验证thread存在
        if not await self.thread_exists(thread_id):
            raise ValueError(f"Thread不存在: {thread_id}")
        
        # 获取thread所有checkpoints
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        checkpoint_ids = [cp.get("id") for cp in checkpoints if cp.get("id")]
        
        # 创建快照记录
        snapshot = ThreadSnapshot(
            snapshot_id=f"snapshot_{uuid.uuid4().hex[:8]}",
            thread_id=thread_id,
            snapshot_name=snapshot_name,
            description=description,
            checkpoint_ids=checkpoint_ids,
            created_at=datetime.now(),
            metadata={
                "total_checkpoints": len(checkpoint_ids),
                "thread_info": await self.get_thread_info(thread_id)
            }
        )
        
        # 保存快照
        await self.snapshot_repository.save(snapshot)
        await self.snapshot_store.save_snapshot(snapshot)
        
        # 更新thread元数据
        await self.metadata_store.update_metadata(thread_id, {
            "last_snapshot": snapshot.snapshot_id,
            "last_snapshot_at": snapshot.created_at.isoformat()
        })
        
        return snapshot.snapshot_id
    
    async def restore_snapshot(
        self,
        thread_id: str,
        snapshot_id: str
    ) -> bool:
        """从快照恢复Thread状态"""
        # 获取快照信息
        snapshot = await self.snapshot_repository.find_by_id(snapshot_id)
        if not snapshot:
            return False
        
        # 获取快照中的最新checkpoint
        checkpoint_ids = snapshot.checkpoint_ids
        if not checkpoint_ids:
            # 空快照，创建空状态
            success = await self.update_thread_state(thread_id, {})
        else:
            # 使用最新的checkpoint（假设列表按时间排序，取最后一个）
            latest_checkpoint_id = checkpoint_ids[-1]
            checkpoint = await self.langgraph_adapter.load_checkpoint(thread_id, latest_checkpoint_id)
            if checkpoint:
                state_data = checkpoint.get("state", {})
                success = await self.update_thread_state(thread_id, state_data)
            else:
                success = False
        
        if success:
            # 记录恢复操作
            await self.metadata_store.update_metadata(thread_id, {
                "last_restored_snapshot": snapshot_id,
                "restored_at": datetime.now().isoformat()
            })
        
        return success
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        snapshot = await self.snapshot_repository.find_by_id(snapshot_id)
        if not snapshot:
            return False
        
        # 从仓储删除
        success = await self.snapshot_repository.delete(snapshot_id)
        if success:
            # 从存储删除
            await self.snapshot_store.delete_snapshot(snapshot_id)
        
        return success
    
    # === 回滚管理 ===
    
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚Thread到指定检查点"""
        # 验证checkpoint存在
        checkpoint = await self.langgraph_adapter.load_checkpoint(thread_id, checkpoint_id)
        if not checkpoint:
            return False
        
        # 创建回滚checkpoint（用于undo）
        rollback_metadata = {
            "rollback_from": checkpoint_id,
            "rollback_reason": "user_requested",
            "original_state": await self.get_thread_state(thread_id)
        }
        
        # 恢复状态
        state_data = checkpoint.get("state", {})
        await self.langgraph_adapter.save_checkpoint(
            thread_id,
            state_data,
            {
                "rollback_to": checkpoint_id,
                **rollback_metadata
            }
        )
        
        # 记录回滚操作
        await self.metadata_store.update_metadata(thread_id, {
            "last_rollback": datetime.now().isoformat(),
            "rollback_checkpoint": checkpoint_id
        })
        
        return True
    
    # === 查询和搜索 ===
    
    async def search_threads(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """搜索Threads"""
        filters = filters or {}
        
        # 获取所有threads
        all_threads = await self.thread_repository.find_all()
        
        # 应用过滤器
        filtered_threads = []
        for thread in all_threads:
            if await self._matches_filters(thread, filters):
                filtered_threads.append(thread)
        
        # 应用分页
        if offset:
            filtered_threads = filtered_threads[offset:]
        if limit:
            filtered_threads = filtered_threads[:limit]
        
        # 转换为字典格式
        result = []
        for thread in filtered_threads:
            thread_info = {
                "thread_id": thread.thread_id,
                "graph_id": thread.graph_id,
                "status": thread.status,
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "metadata": thread.metadata
            }
            result.append(thread_info)
        
        logger.info(f"搜索Threads完成，共{len(result)}个匹配结果")
        return result
    
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息"""
        all_threads = await self.thread_repository.find_all()
        
        total_count = len(all_threads)
        
        # 按状态统计
        status_counts = {}
        graph_counts = {}
        
        for thread in all_threads:
            status = thread.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            graph_id = thread.graph_id
            graph_counts[graph_id] = graph_counts.get(graph_id, 0) + 1
        
        # 计算活跃度
        active_threads = 0
        inactive_threads = 0
        current_time = datetime.now()
        
        for thread in all_threads:
            # 假设30天内有更新为活跃
            if (current_time - thread.updated_at).days <= 30:
                active_threads += 1
            else:
                inactive_threads += 1
        
        stats = {
            "total_threads": total_count,
            "active_threads": active_threads,
            "inactive_threads": inactive_threads,
            "status_distribution": status_counts,
            "graph_distribution": graph_counts,
            "calculated_at": datetime.now().isoformat()
        }
        
        return stats
    
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取Thread历史记录"""
        if not await self.thread_exists(thread_id):
            return []
        
        # 获取所有checkpoints
        checkpoints = await self.langgraph_adapter.list_checkpoints(thread_id)
        
        # 应用限制
        if limit and len(checkpoints) > limit:
            checkpoints = checkpoints[:limit]
        
        return checkpoints
    
    # === 协作管理 ===
    
    async def share_thread_state(
        self,
        source_thread_id: str,
        target_thread_id: str,
        checkpoint_id: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """共享Thread状态到其他Thread"""
        # 验证源thread存在
        if not await self.thread_exists(source_thread_id):
            return False
        
        # 验证目标thread存在
        if not await self.thread_exists(target_thread_id):
            return False
        
        # 验证checkpoint存在
        checkpoint = await self.langgraph_adapter.load_checkpoint(source_thread_id, checkpoint_id)
        if not checkpoint:
            return False
        
        # 获取checkpoint状态
        state_data = checkpoint.get("state_data", {})
        
        # 根据权限决定如何共享
        if permissions is None:
            permissions = {"read": True, "write": False}
        
        if permissions.get("write", False):
            # 允许写入，直接更新目标thread状态
            success = await self.update_thread_state(target_thread_id, state_data)
        else:
            # 只读，记录共享关系
            shared_state = SharedThreadState(
                shared_id=f"shared_{uuid.uuid4().hex[:8]}",
                source_thread_id=source_thread_id,
                target_thread_id=target_thread_id,
                checkpoint_id=checkpoint_id,
                permissions=permissions or {},
                created_at=datetime.now(),
                metadata={"shared_state": state_data}
            )
            
            # 保存共享信息到目标thread元数据
            shared_states = await self.metadata_store.get_metadata(target_thread_id)
            if shared_states is None:
                shared_states = {}
            
            shared_states_list = shared_states.get("shared_states", [])
            shared_states_list.append({
                "shared_id": shared_state.shared_id,
                "source_thread_id": shared_state.source_thread_id,
                "checkpoint_id": shared_state.checkpoint_id,
                "permissions": shared_state.permissions,
                "created_at": shared_state.created_at.isoformat(),
                "metadata": shared_state.metadata
            })
            
            await self.metadata_store.update_metadata(target_thread_id, {
                "shared_states": shared_states_list
            })
            
            success = True
        
        return success
    
    async def create_shared_session(
        self,
        thread_ids: List[str],
        session_config: Dict[str, Any]
    ) -> str:
        """创建共享会话"""
        # 验证所有threads存在
        for thread_id in thread_ids:
            if not await self.thread_exists(thread_id):
                raise ValueError(f"Thread不存在: {thread_id}")
        
        # 创建协作ID
        collaboration_id = f"collab_{uuid.uuid4().hex[:8]}"
        
        # 创建协作记录
        collaboration = ThreadCollaboration(
            collaboration_id=collaboration_id,
            thread_ids=thread_ids,
            permissions=session_config.get("permissions", {}),
            created_at=datetime.now(),
            metadata=session_config.get("metadata", {})
        )
        
        # 保存协作信息到所有相关threads
        for thread_id in thread_ids:
            thread_metadata = await self.metadata_store.get_metadata(thread_id)
            if thread_metadata is None:
                thread_metadata = {}
            
            collaborations = thread_metadata.get("collaborations", [])
            collaborations.append({
                "collaboration_id": collaboration.collaboration_id,
                "thread_ids": collaboration.thread_ids,
                "permissions": collaboration.permissions,
                "created_at": collaboration.created_at.isoformat(),
                "metadata": collaboration.metadata,
                "status": collaboration.status
            })
            
            await self.metadata_store.update_metadata(thread_id, {
                "collaborations": collaborations
            })
        
        return collaboration_id
    
    async def sync_thread_states(
        self,
        thread_ids: List[str],
        sync_strategy: str = "bidirectional"
    ) -> bool:
        """同步多个Thread状态"""
        if len(thread_ids) < 2:
            return False
        
        # 验证所有threads存在
        for thread_id in thread_ids:
            if not await self.thread_exists(thread_id):
                return False
        
        # 获取所有threads的最新状态
        thread_states = {}
        for thread_id in thread_ids:
            state = await self.get_thread_state(thread_id)
            thread_states[thread_id] = state or {}
        
        # 根据策略同步状态
        if sync_strategy == "bidirectional":
            # 双向同步：合并所有状态
            merged_state = {}
            for state in thread_states.values():
                merged_state.update(state)
            
            # 更新所有threads
            success_count = 0
            for thread_id in thread_ids:
                if await self.update_thread_state(thread_id, merged_state):
                    success_count += 1
            
            return success_count == len(thread_ids)
        
        elif sync_strategy == "master_slave":
            # 主从同步：使用第一个thread作为主
            master_state = thread_states[thread_ids[0]]
            success_count = 0
            for thread_id in thread_ids[1:]:
                if await self.update_thread_state(thread_id, master_state):
                    success_count += 1
            
            return success_count == len(thread_ids) - 1
        
        else:
            # 默认使用双向同步
            merged_state = {}
            for state in thread_states.values():
                merged_state.update(state)
            
            success_count = 0
            for thread_id in thread_ids:
                if await self.update_thread_state(thread_id, merged_state):
                    success_count += 1
            
            return success_count == len(thread_ids)
    
    # === 私有辅助方法 ===
    
    async def _get_or_create_graph(self, thread: Thread) -> Any:
        """获取或创建图"""
        graph_id = thread.graph_id
        config_path = thread.metadata.get("config_path")
        
        # 检查缓存
        cache_key = f"{graph_id}_{config_path}"
        if cache_key in self._graph_cache:
            return self._graph_cache[cache_key]
        
        # 创建图配置
        if config_path:
            graph_config = await self._load_graph_config(config_path)
        else:
            # 简化实现
            graph_config = GraphConfig(name=graph_id, version="1.0", description="Graph config from graph_id")
        
        # 创建图
        graph = await self.langgraph_adapter.create_graph(graph_config)
        
        # 缓存图
        self._graph_cache[cache_key] = graph
        
        return graph
    
    async def _load_graph_config(self, config_path: str) -> GraphConfig:
        """加载图配置"""
        # 这里应该使用配置加载器，暂时简化实现
        # TODO: 集成CentralizedConfigManager
        return GraphConfig(name="default", version="1.0", description="Default graph config")
    
    async def _update_thread_execution_stats(self, thread_id: str) -> None:
        """更新Thread执行统计"""
        thread = await self.thread_repository.find_by_id(thread_id)
        if thread:
            thread.update_metadata({"total_steps": thread.metadata.get("total_steps", 0) + 1})
            await self.thread_repository.save(thread)
            
            await self.metadata_store.update_metadata(thread_id, {
                "updated_at": thread.updated_at.isoformat(),
                "total_steps": thread.metadata.get("total_steps", 0)
            })
    
    async def _handle_execution_error(self, thread_id: str, error: Exception) -> None:
        """处理执行错误"""
        # 更新Thread状态为错误
        await self.update_thread_status(thread_id, "error")
        
        # 记录错误信息
        await self.metadata_store.update_metadata(thread_id, {
            "last_error": str(error),
            "error_at": datetime.now().isoformat()
        })
    
    async def _matches_filters(self, thread: Thread, filters: Dict[str, Any]) -> bool:
        """检查Thread是否匹配过滤条件"""
        for key, value in filters.items():
            if key == "status":
                if thread.status != value:
                    return False
            elif key == "graph_id":
                if thread.graph_id != value:
                    return False
            elif key == "metadata":
                for metadata_key, expected_value in value.items():
                    if thread.metadata.get(metadata_key) != expected_value:
                        return False
            elif key == "created_after":
                if isinstance(value, datetime) and thread.created_at < value:
                    return False
            elif key == "created_before":
                if isinstance(value, datetime) and thread.created_at > value:
                    return False
        return True
    
    async def clear_graph_cache(self) -> None:
        """清空图缓存"""
        self._graph_cache.clear()
        logger.info("ThreadService图缓存已清空")
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "graph_cache_size": len(self._graph_cache),
            "cached_graphs": list(self._graph_cache.keys())
        }