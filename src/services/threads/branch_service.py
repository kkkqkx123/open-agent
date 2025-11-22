"""线程分支服务实现"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.interfaces import IThreadCore, IThreadBranchCore
from src.core.threads.entities import Thread, ThreadBranch, ThreadStatus
from src.interfaces.threads import IThreadBranchService, IThreadRepository, IThreadBranchRepository
from src.core.common.exceptions import ValidationError, StorageNotFoundError as EntityNotFoundError
from .repository_adapter import ThreadRepositoryAdapter, ThreadBranchRepositoryAdapter


class ThreadBranchService(IThreadBranchService):
    """线程分支业务服务实现"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_branch_core: IThreadBranchCore,
        thread_repository: IThreadRepository,
        thread_branch_repository: IThreadBranchRepository
    ):
        self._thread_core = thread_core
        self._thread_branch_core = thread_branch_core
        self._thread_repository = ThreadRepositoryAdapter(thread_repository)
        self._thread_branch_repository = ThreadBranchRepositoryAdapter(thread_branch_repository)
    
    async def create_branch_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建分支"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 生成分支ID
            branch_id = str(uuid.uuid4())
            
            # 创建分支实体
            branch_data = self._thread_branch_core.create_branch(
                branch_id=branch_id,
                thread_id=thread_id,
                parent_thread_id=thread_id,
                source_checkpoint_id=checkpoint_id,
                branch_name=branch_name,
                metadata=metadata or {}
            )
            
            # 保存分支
            branch = ThreadBranch.from_dict(branch_data)
            await self._thread_branch_repository.save_branch(branch)
            
            # 更新线程的分支计数
            thread.increment_branch_count()
            await self._thread_repository.update_thread(thread_id, thread)
            
            return branch_id
        except Exception as e:
            raise ValidationError(f"Failed to create branch from checkpoint: {str(e)}")
    
    async def merge_branch_to_main(
        self,
        thread_id: str,
        branch_id: str,
        merge_strategy: str = "overwrite"
    ) -> bool:
        """将分支合并到主线"""
        try:
            # 验证线程和分支存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            branch = await self._thread_branch_repository.get_branch(branch_id)
            if not branch:
                raise EntityNotFoundError(f"Branch {branch_id} not found")
            
            if branch.thread_id != thread_id:
                raise ValidationError(f"Branch {branch_id} does not belong to thread {thread_id}")
            
            # 执行合并逻辑（根据策略）
            if merge_strategy == "overwrite":
                # 覆盖主线状态（简化处理）
                pass
            elif merge_strategy == "merge":
                # 合并状态（这里简化处理）
                pass
            else:
                raise ValidationError(f"Unsupported merge strategy: {merge_strategy}")
            
            # 标记分支为非活动
            branch.metadata["is_active"] = False
            branch.metadata["merged_at"] = datetime.now().isoformat()
            await self._thread_branch_repository.update_branch(branch_id, branch)
            
            return True
        except Exception as e:
            raise ValidationError(f"Failed to merge branch to main: {str(e)}")
    
    async def get_branch_history(self, thread_id: str, branch_id: str) -> List[Dict[str, Any]]:
        """获取分支历史"""
        try:
            # 验证分支存在
            branch = await self._thread_branch_repository.get_branch(branch_id)
            if not branch or branch.thread_id != thread_id:
                raise EntityNotFoundError(f"Branch {branch_id} not found in thread {thread_id}")
            
            # 获取分支历史记录
            history = await self._thread_branch_repository.get_branch_history(branch_id)
            
            return history
        except Exception as e:
            raise ValidationError(f"Failed to get branch history: {str(e)}")
    
    async def list_active_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """列活动分支"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 获取活动分支
            branches = await self._thread_branch_repository.list_active_branches(thread_id)
            
            return [
                {
                    "branch_id": branch.id,
                    "branch_name": branch.branch_name,
                    "source_checkpoint_id": branch.source_checkpoint_id,
                    "created_at": branch.created_at.isoformat(),
                    "metadata": branch.metadata,
                    "is_active": branch.metadata.get("is_active", True)
                }
                for branch in branches
            ]
        except Exception as e:
            raise ValidationError(f"Failed to list active branches: {str(e)}")
    
    async def validate_branch_integrity(self, thread_id: str, branch_id: str) -> bool:
        """验证分支完整性"""
        try:
            # 验证分支存在
            branch = await self._thread_branch_repository.get_branch(branch_id)
            if not branch or branch.thread_id != thread_id:
                return False
            
            # 基本完整性检查
            if not branch.branch_name or not branch.source_checkpoint_id:
                return False
            
            # 检查分支状态一致性
            is_active = branch.metadata.get("is_active", True)
            merged_at = branch.metadata.get("merged_at")
            if is_active and merged_at:
                return False  # 已合并的分支不应标记为活动
            
            return True
        except Exception:
            return False
    
    async def cleanup_orphaned_branches(self, thread_id: str) -> int:
        """清理孤立分支"""
        try:
            # 获取线程的所有分支
            all_branches = await self._thread_branch_repository.list_branches_by_thread(thread_id)
            
            cleaned_count = 0
            for branch in all_branches:
                # 检查分支是否为孤立分支
                is_orphaned = await self._is_orphaned_branch(branch)
                
                if is_orphaned:
                    success = await self._thread_branch_repository.delete_branch(branch.id)
                    if success:
                        cleaned_count += 1
                        # 更新线程的分支计数
                        thread = await self._thread_repository.get_thread(thread_id)
                        if thread:
                            thread.branch_count = max(0, thread.branch_count - 1)
                            thread.updated_at = datetime.now()
                            await self._thread_repository.update_thread(thread_id, thread)
            
            return cleaned_count
        except Exception as e:
            raise ValidationError(f"Failed to cleanup orphaned branches: {str(e)}")
    
    async def _is_orphaned_branch(self, branch: ThreadBranch) -> bool:
        """检查分支是否为孤立分支"""
        try:
            # 检查对应的检查点是否存在
            # 这里简化处理，实际应用中可能需要调用检查点服务
            checkpoint_exists = True  # 假设检查点存在
            
            # 检查分支是否长时间未活动
            time_since_last_activity = datetime.now() - branch.created_at
            is_inactive = time_since_last_activity.total_seconds() > 86400  # 24小时
            
            # 检查分支是否已合并且长时间未访问
            merged_at = branch.metadata.get("merged_at")
            is_merged_and_old = False
            if merged_at:
                try:
                    merged_time = datetime.fromisoformat(merged_at)
                    is_merged_and_old = (datetime.now() - merged_time).total_seconds() > 604800  # 7天
                except (ValueError, TypeError):
                    # 如果时间格式无效，不算作旧分支
                    pass
            
            is_active = branch.metadata.get("is_active", True)
            
            return (not checkpoint_exists) or (is_inactive and not is_active) or is_merged_and_old
        except Exception:
            return False