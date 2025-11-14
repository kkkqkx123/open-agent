"""Thread协作管理器"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.threads.interfaces import IThreadManager
from ...application.checkpoint.manager import ICheckpointManager
from ...domain.threads.collaboration import ThreadCollaboration, SharedThreadState


class CollaborationManager:
    """Thread协作管理器"""
    
    def __init__(
        self,
        thread_manager: IThreadManager,
        checkpoint_manager: ICheckpointManager
    ):
        """初始化协作管理器
        
        Args:
            thread_manager: Thread管理器
            checkpoint_manager: Checkpoint管理器
        """
        self.thread_manager = thread_manager
        self.checkpoint_manager = checkpoint_manager
    
    async def share_thread_state(
        self,
        source_thread_id: str,
        target_thread_id: str,
        checkpoint_id: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """共享thread状态到其他thread
        
        Args:
            source_thread_id: 源thread ID
            target_thread_id: 目标thread ID
            checkpoint_id: checkpoint ID
            permissions: 权限配置
            
        Returns:
            共享是否成功
        """
        # 验证源thread存在
        if not await self.thread_manager.thread_exists(source_thread_id):
            return False
        
        # 验证目标thread存在
        if not await self.thread_manager.thread_exists(target_thread_id):
            return False
        
        # 验证checkpoint存在
        checkpoint = await self.checkpoint_manager.get_checkpoint(source_thread_id, checkpoint_id)
        if not checkpoint:
            return False
        
        # 获取checkpoint状态
        state_data = checkpoint.get("state_data", {})
        
        # 根据权限决定如何共享
        if permissions is None:
            permissions = {"read": True, "write": False}
        
        if permissions.get("write", False):
            # 允许写入，直接更新目标thread状态
            success = await self.thread_manager.update_thread_state(target_thread_id, state_data)
        else:
            # 只读，可能需要创建只读视图或其他机制
            # 这里简化处理，只记录共享关系
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
            target_metadata = await self.thread_manager.get_thread_info(target_thread_id)
            if target_metadata:
                shared_states = target_metadata.get("shared_states", [])
                shared_states.append({
                    "shared_id": shared_state.shared_id,
                    "source_thread_id": shared_state.source_thread_id,
                    "checkpoint_id": shared_state.checkpoint_id,
                    "permissions": shared_state.permissions,
                    "created_at": shared_state.created_at.isoformat(),
                    "metadata": shared_state.metadata
                })
                await self.thread_manager.update_thread_metadata(target_thread_id, {
                    "shared_states": shared_states
                })
            
            success = True
        
        return success
    
    async def create_shared_session(
        self,
        thread_ids: List[str],
        session_config: Dict[str, Any]
    ) -> str:
        """创建共享会话
        
        Args:
            thread_ids: Thread ID列表
            session_config: 会话配置
            
        Returns:
            共享会话ID
        """
        # 验证所有threads存在
        for thread_id in thread_ids:
            if not await self.thread_manager.thread_exists(thread_id):
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
            thread_metadata = await self.thread_manager.get_thread_info(thread_id)
            if thread_metadata:
                collaborations = thread_metadata.get("collaborations", [])
                collaborations.append({
                    "collaboration_id": collaboration.collaboration_id,
                    "thread_ids": collaboration.thread_ids,
                    "permissions": collaboration.permissions,
                    "created_at": collaboration.created_at.isoformat(),
                    "metadata": collaboration.metadata,
                    "status": collaboration.status
                })
                await self.thread_manager.update_thread_metadata(thread_id, {
                    "collaborations": collaborations
                })
        
        return collaboration_id
    
    async def sync_thread_states(
        self,
        thread_ids: List[str],
        sync_strategy: str = "bidirectional"
    ) -> bool:
        """同步多个thread状态
        
        Args:
            thread_ids: Thread ID列表
            sync_strategy: 同步策略
            
        Returns:
            同步是否成功
        """
        if len(thread_ids) < 2:
            return False
        
        # 验证所有threads存在
        for thread_id in thread_ids:
            if not await self.thread_manager.thread_exists(thread_id):
                return False
        
        # 获取所有threads的最新状态
        thread_states = {}
        for thread_id in thread_ids:
            state = await self.thread_manager.get_thread_state(thread_id)
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
                if await self.thread_manager.update_thread_state(thread_id, merged_state):
                    success_count += 1
            
            return success_count == len(thread_ids)
        
        elif sync_strategy == "master_slave":
            # 主从同步：使用第一个thread作为主
            master_state = thread_states[thread_ids[0]]
            success_count = 0
            for thread_id in thread_ids[1:]:
                if await self.thread_manager.update_thread_state(thread_id, master_state):
                    success_count += 1
            
            return success_count == len(thread_ids) - 1
        
        else:
            # 默认使用双向同步
            merged_state = {}
            for state in thread_states.values():
                merged_state.update(state)
            
            success_count = 0
            for thread_id in thread_ids:
                if await self.thread_manager.update_thread_state(thread_id, merged_state):
                    success_count += 1
            
            return success_count == len(thread_ids)