"""Thread分支管理器"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.threads.models import ThreadBranch
from ...domain.threads.interfaces import IThreadManager
from ...application.checkpoint.manager import ICheckpointManager


class BranchManager:
    """Thread分支管理器"""
    
    def __init__(
        self,
        thread_manager: IThreadManager,
        checkpoint_manager: ICheckpointManager
    ):
        """初始化分支管理器
        
        Args:
            thread_manager: Thread管理器
            checkpoint_manager: Checkpoint管理器
        """
        self.thread_manager = thread_manager
        self.checkpoint_manager = checkpoint_manager
    
    async def fork_thread(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建thread分支
        
        Args:
            source_thread_id: 源thread ID
            checkpoint_id: 源checkpoint ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新thread ID
        """
        # 1. 验证源thread和checkpoint存在
        source_info = await self.thread_manager.get_thread_info(source_thread_id)
        if not source_info:
            raise ValueError(f"源thread不存在: {source_thread_id}")
        
        checkpoint = await self.checkpoint_manager.get_checkpoint(source_thread_id, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"checkpoint不存在: {checkpoint_id}")
        
        # 2. 创建新thread
        new_thread_id = await self.thread_manager.create_thread(
            graph_id=source_info.get("graph_id", "default_graph"),
            metadata={
                "branch_name": branch_name,
                "source_thread_id": source_thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_type": "fork",
                **(metadata or {})
            }
        )
        
        # 3. 复制checkpoint状态到新thread
        state_data = checkpoint.get("state_data", {})
        await self.thread_manager.update_thread_state(new_thread_id, state_data)
        
        # 4. 记录分支关系（这里简化处理，实际可能需要专门的分支存储）
        branch_metadata = {
            "branch_id": f"branch_{uuid.uuid4().hex[:8]}",
            "source_thread_id": source_thread_id,
            "source_checkpoint_id": checkpoint_id,
            "branch_name": branch_name,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "status": "active"
        }
        
        # 更新新thread的元数据，包含分支信息
        await self.thread_manager.update_thread_metadata(new_thread_id, {
            "branch_info": branch_metadata
        })
        
        return new_thread_id
    
    async def get_thread_branches(
        self,
        thread_id: str
    ) -> List[ThreadBranch]:
        """获取thread的所有分支
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread分支列表
        """
        # 获取thread信息
        thread_info = await self.thread_manager.get_thread_info(thread_id)
        if not thread_info:
            return []
        
        branches = []
        
        # 检查是否有分支信息
        if "branch_info" in thread_info:
            branch_info = thread_info["branch_info"]
            branch = ThreadBranch(
                branch_id=branch_info["branch_id"],
                source_thread_id=branch_info["source_thread_id"],
                source_checkpoint_id=branch_info["source_checkpoint_id"],
                branch_name=branch_info["branch_name"],
                created_at=datetime.fromisoformat(branch_info["created_at"]),
                metadata=branch_info["metadata"],
                status=branch_info.get("status", "active")
            )
            branches.append(branch)
        
        # TODO: 在实际实现中，可能需要查询专门的分支存储来获取所有分支
        
        return branches
    
    async def merge_branch(
        self,
        target_thread_id: str,
        source_thread_id: str,
        merge_strategy: str = "latest"
    ) -> bool:
        """合并分支到目标thread
        
        Args:
            target_thread_id: 目标thread ID
            source_thread_id: 源thread ID（分支）
            merge_strategy: 合并策略
            
        Returns:
            合并是否成功
        """
        # 验证目标thread存在
        if not await self.thread_manager.thread_exists(target_thread_id):
            return False
        
        # 验证源thread存在
        if not await self.thread_manager.thread_exists(source_thread_id):
            return False
        
        # 获取源thread的最新状态
        source_state = await self.thread_manager.get_thread_state(source_thread_id)
        if source_state is None:
            return False
        
        # 根据策略合并状态
        if merge_strategy == "latest":
            # 直接使用源thread的最新状态
            success = await self.thread_manager.update_thread_state(target_thread_id, source_state)
        elif merge_strategy == "preserve_target":
            # 保留目标thread状态，只合并特定字段
            target_state = await self.thread_manager.get_thread_state(target_thread_id)
            if target_state is None:
                target_state = {}
            
            # 合并逻辑（简化实现）
            merged_state = {**target_state, **source_state}
            success = await self.thread_manager.update_thread_state(target_thread_id, merged_state)
        else:
            # 默认使用latest策略
            success = await self.thread_manager.update_thread_state(target_thread_id, source_state)
        
        if success:
            # 更新元数据记录合并操作
            await self.thread_manager.update_thread_metadata(target_thread_id, {
                "last_merge": datetime.now().isoformat(),
                "merged_from": source_thread_id,
                "merge_strategy": merge_strategy
            })
        
        return success