"""LangGraph分支服务"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime
import uuid

from src.core.langgraph.manager import ILangGraphManager
from src.core.threads.entities import Thread, ThreadBranch, ThreadStatus
from src.interfaces.threads.storage import IThreadRepository, IThreadBranchRepository

logger = logging.getLogger(__name__)


class ILangGraphBranchService:
    """LangGraph分支服务接口"""
    
    async def create_branch_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从checkpoint创建分支"""
        ...
    
    async def merge_branch_to_main(
        self,
        thread_id: str,
        branch_id: str,
        merge_strategy: str = "overwrite"
    ) -> Dict[str, Any]:
        """合并分支到主线"""
        ...
    
    async def get_branch_history(
        self,
        thread_id: str,
        branch_id: str
    ) -> List[Dict[str, Any]]:
        """获取分支历史"""
        ...


class LangGraphBranchService(ILangGraphBranchService):
    """LangGraph分支服务实现"""
    
    def __init__(
        self,
        langgraph_manager: ILangGraphManager,
        thread_repository: IThreadRepository,
        thread_branch_repository: IThreadBranchRepository
    ):
        self._langgraph_manager = langgraph_manager
        self._thread_repository = thread_repository
        self._thread_branch_repository = thread_branch_repository
        
        logger.info("LangGraphBranchService initialized")
    
    async def create_branch_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从checkpoint创建分支"""
        try:
            # 验证主线Thread存在
            main_thread = await self._thread_repository.get(thread_id)
            if not main_thread:
                raise ValueError(f"Main thread '{thread_id}' not found")
            
            # 验证主线Thread状态
            if not main_thread.is_forkable():
                raise ValueError(f"Main thread '{thread_id}' is not in a forkable state: {main_thread.status}")
            
            # 使用LangGraph创建分支
            branch_thread_id = await self._langgraph_manager.create_branch(
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                branch_name=branch_name
            )
            
            # 创建ThreadBranch实体
            branch_id = str(uuid.uuid4())
            thread_branch = ThreadBranch(
                id=branch_id,
                thread_id=thread_id,
                parent_thread_id=thread_id,
                source_checkpoint_id=checkpoint_id,
                branch_name=branch_name,
                langgraph_branch_thread_id=branch_thread_id,
                langgraph_created_from_checkpoint=checkpoint_id,
                langgraph_merge_status=None,
                merged_at=None,
                merge_strategy=None,
                metadata=metadata or {}
            )
            
            # 保存分支实体
            await self._thread_branch_repository.create(thread_branch)
            
            # 更新主线Thread的分支计数
            main_thread.increment_branch_count()
            await self._thread_repository.update(main_thread)
            
            logger.info(f"Created branch '{branch_name}' with ID '{branch_id}' from thread '{thread_id}'")
            return branch_id
            
        except Exception as e:
            logger.error(f"Error creating branch '{branch_name}' from thread '{thread_id}': {str(e)}")
            raise
    
    async def merge_branch_to_main(
        self,
        thread_id: str,
        branch_id: str,
        merge_strategy: str = "overwrite"
    ) -> Dict[str, Any]:
        """合并分支到主线"""
        try:
            # 验证主线Thread存在
            main_thread = await self._thread_repository.get(thread_id)
            if not main_thread:
                raise ValueError(f"Main thread '{thread_id}' not found")
            
            # 验证分支存在
            branch = await self._thread_branch_repository.get(branch_id)
            if not branch:
                raise ValueError(f"Branch '{branch_id}' not found")
            
            # 验证分支归属
            if branch.thread_id != thread_id:
                raise ValueError(f"Branch '{branch_id}' does not belong to thread '{thread_id}'")
            
            # 验证分支状态
            if not branch.is_active:
                raise ValueError(f"Branch '{branch_id}' is not active")
            
            # 获取分支的LangGraph thread ID
            branch_thread_id = branch.langgraph_branch_thread_id
            if not branch_thread_id:
                raise ValueError(f"Branch '{branch_id}' has no LangGraph thread ID")
            
            # 使用LangGraph执行合并
            merge_result = await self._langgraph_manager.merge_branch(
                main_thread_id=thread_id,
                branch_thread_id=branch_thread_id,
                merge_strategy=merge_strategy
            )
            
            # 更新主线Thread状态
            if merge_result["success"]:
                main_thread.sync_with_langgraph_state(merge_result["merged_state"])
                main_thread.update_timestamp()
                
                # 更新合并信息到元数据
                main_thread.metadata.custom_data.update({
                    "last_merge": {
                        "branch_id": branch_id,
                        "branch_name": branch.branch_name,
                        "merge_strategy": merge_strategy,
                        "merge_time": merge_result["merged_at"],
                        "checkpoint_id": branch.source_checkpoint_id
                    }
                })
                
                await self._thread_repository.update(main_thread)
            
            # 更新分支状态
            branch.is_active = False
            branch.langgraph_merge_status = "merged"
            branch.merge_strategy = merge_strategy
            branch.merged_at = datetime.now()
            branch.metadata.update({
                "merge_result": merge_result
            })
            
            await self._thread_branch_repository.update(branch)
            
            logger.info(f"Merged branch '{branch_id}' into thread '{thread_id}' using '{merge_strategy}' strategy")
            
            return {
                "success": True,
                "branch_id": branch_id,
                "thread_id": thread_id,
                "merge_strategy": merge_strategy,
                "merge_time": merge_result["merged_at"],
                "merged_state": merge_result["merged_state"]
            }
            
        except Exception as e:
            logger.error(f"Error merging branch '{branch_id}' into thread '{thread_id}': {str(e)}")
            raise
    
    async def get_branch_history(
        self,
        thread_id: str,
        branch_id: str
    ) -> List[Dict[str, Any]]:
        """获取分支历史"""
        try:
            # 验证分支存在
            branch = await self._thread_branch_repository.get(branch_id)
            if not branch:
                raise ValueError(f"Branch '{branch_id}' not found")
            
            # 获取分支的LangGraph thread ID
            branch_thread_id = branch.langgraph_branch_thread_id
            if not branch_thread_id:
                logger.warning(f"Branch '{branch_id}' has no LangGraph thread ID, returning empty history")
                return []
            
            # 获取LangGraph checkpoint历史
            history = await self._langgraph_manager.get_checkpoint_history(branch_thread_id)
            
            # 添加分支特定信息
            enriched_history = []
            for checkpoint in history:
                enriched_history.append({
                    **checkpoint,
                    "branch_id": branch_id,
                    "branch_name": branch.branch_name,
                    "parent_thread_id": thread_id
                })
            
            return enriched_history
            
        except Exception as e:
            logger.error(f"Error getting branch history for branch '{branch_id}': {str(e)}")
            return []
    
    async def list_active_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出活跃分支"""
        try:
            # 获取所有分支
            branches = await self._thread_branch_repository.list_by_thread(thread_id)
            
            # 过滤活跃分支
            active_branches = []
            for branch in branches:
                if branch.is_active:
                    # 获取分支状态信息
                    branch_thread_id = branch.langgraph_branch_thread_id
                    branch_state = None
                    
                    if branch_thread_id:
                        branch_state = await self._langgraph_manager.get_thread_state(branch_thread_id)
                    
                    active_branches.append({
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                        "branch_type": branch.branch_type,
                        "created_at": branch.created_at,
                        "source_checkpoint_id": branch.source_checkpoint_id,
                        "langgraph_branch_thread_id": branch_thread_id,
                        "current_state": branch_state,
                        "metadata": branch.metadata
                    })
            
            return active_branches
            
        except Exception as e:
            logger.error(f"Error listing active branches for thread '{thread_id}': {str(e)}")
            return []
    
    async def get_branch_info(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """获取分支信息"""
        try:
            branch = await self._thread_branch_repository.get(branch_id)
            if not branch:
                return None
            
            # 获取LangGraph分支信息
            branch_thread_id = branch.langgraph_branch_thread_id
            branch_info = None
            
            if branch_thread_id:
                branch_info = await self._langgraph_manager.get_branch_info(branch_thread_id)
            
            return {
                "branch_id": branch.id,
                "thread_id": branch.thread_id,
                "parent_thread_id": branch.parent_thread_id,
                "branch_name": branch.branch_name,
                "branch_type": branch.branch_type,
                "source_checkpoint_id": branch.source_checkpoint_id,
                "is_active": branch.is_active,
                "merge_strategy": branch.merge_strategy,
                "created_at": branch.created_at,
                "merged_at": branch.merged_at,
                "langgraph_branch_thread_id": branch_thread_id,
                "langgraph_created_from_checkpoint": branch.langgraph_created_from_checkpoint,
                "langgraph_merge_status": branch.langgraph_merge_status,
                "langgraph_branch_info": branch_info,
                "metadata": branch.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting branch info for branch '{branch_id}': {str(e)}")
            return None
    
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        try:
            branch = await self._thread_branch_repository.get(branch_id)
            if not branch:
                raise ValueError(f"Branch '{branch_id}' not found")
            
            # 检查分支是否可以删除
            if branch.is_active:
                logger.warning(f"Branch '{branch_id}' is still active, deactivating before deletion")
                branch.is_active = False
                await self._thread_branch_repository.update(branch)
            
            # 清理LangGraph资源
            branch_thread_id = branch.langgraph_branch_thread_id
            if branch_thread_id:
                await self._langgraph_manager.cleanup_thread(branch_thread_id)
            
            # 删除分支实体
            await self._thread_branch_repository.delete(branch_id)
            
            logger.info(f"Deleted branch '{branch_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting branch '{branch_id}': {str(e)}")
            raise
    
    async def restore_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """从checkpoint恢复Thread"""
        try:
            # 验证Thread存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            # 使用LangGraph恢复
            restored_state = await self._langgraph_manager.restore_from_checkpoint(
                thread_id=thread_id,
                checkpoint_id=checkpoint_id
            )
            
            # 更新Thread状态
            thread.sync_with_langgraph_state(restored_state)
            thread.update_langgraph_checkpoint(checkpoint_id)
            await self._thread_repository.update(thread)
            
            logger.info(f"Restored thread '{thread_id}' from checkpoint '{checkpoint_id}'")
            
            return {
                "success": True,
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "restored_state": restored_state,
                "restored_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error restoring thread '{thread_id}' from checkpoint '{checkpoint_id}': {str(e)}")
            raise
    
    async def compare_branch_states(
        self,
        branch_id1: str,
        branch_id2: str
    ) -> Dict[str, Any]:
        """比较两个分支的状态"""
        try:
            # 获取分支信息
            branch1 = await self._thread_branch_repository.get(branch_id1)
            branch2 = await self._thread_branch_repository.get(branch_id2)
            
            if not branch1 or not branch2:
                raise ValueError("One or both branches not found")
            
            # 获取LangGraph状态
            state1 = None
            state2 = None
            
            if branch1.langgraph_branch_thread_id:
                state1 = await self._langgraph_manager.get_thread_state(branch1.langgraph_branch_thread_id)
            
            if branch2.langgraph_branch_thread_id:
                state2 = await self._langgraph_manager.get_thread_state(branch2.langgraph_branch_thread_id)
            
            # 简单的状态比较
            comparison = {
                "branch1": {
                    "branch_id": branch_id1,
                    "branch_name": branch1.branch_name,
                    "state": state1
                },
                "branch2": {
                    "branch_id": branch_id2,
                    "branch_name": branch2.branch_name,
                    "state": state2
                },
                "differences": []
            }
            
            # 这里可以添加更复杂的状态比较逻辑
            if state1 and state2:
                # 比较状态版本
                if state1.get("version") != state2.get("version"):
                    comparison["differences"].append({
                        "field": "version",
                        "branch1": state1.get("version"),
                        "branch2": state2.get("version")
                    })
                
                # 比较当前步骤
                if state1.get("current_step") != state2.get("current_step"):
                    comparison["differences"].append({
                        "field": "current_step",
                        "branch1": state1.get("current_step"),
                        "branch2": state2.get("current_step")
                    })
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing branches '{branch_id1}' and '{branch_id2}': {str(e)}")
            raise