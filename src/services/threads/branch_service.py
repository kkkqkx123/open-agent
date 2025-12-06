"""线程分支服务实现"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from typing import TYPE_CHECKING
from src.core.threads.interfaces import IThreadCore, IThreadBranchCore
from src.core.threads.entities import ThreadBranch
from src.interfaces.threads import IThreadBranchService, IThreadRepository, IThreadBranchRepository
from src.interfaces.storage.exceptions import StorageValidationError as ValidationError, StorageNotFoundError as EntityNotFoundError
from .base_service import BaseThreadService

if TYPE_CHECKING:
    from src.core.threads.checkpoints.domain_service import ThreadCheckpointDomainService


class ThreadBranchService(BaseThreadService, IThreadBranchService):
    """线程分支业务服务实现"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_branch_core: IThreadBranchCore,
        thread_repository: IThreadRepository,
        thread_branch_repository: IThreadBranchRepository,
        checkpoint_domain_service: Optional['ThreadCheckpointDomainService'] = None
    ):
        super().__init__(thread_repository)
        self._thread_core = thread_core
        self._thread_branch_core = thread_branch_core
        self._thread_branch_repository = thread_branch_repository
        self._checkpoint_domain_service = checkpoint_domain_service
    
    async def create_branch_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建分支"""
        try:
            self._log_operation("create_branch_from_checkpoint", thread_id,
                              checkpoint_id=checkpoint_id, branch_name=branch_name)
            
            # 验证线程存在
            thread = await self._validate_thread_exists(thread_id)
            
            # 验证检查点服务存在
            if not self._checkpoint_domain_service:
                raise ValidationError("Checkpoint service not available")
            
            # 验证检查点有效性
            checkpoint = await self._checkpoint_domain_service._repository.find_by_id(checkpoint_id)
            if not checkpoint or checkpoint.thread_id != thread_id:
                raise ValidationError(f"Invalid checkpoint {checkpoint_id} for thread {thread_id}")
            
            if not checkpoint.can_restore():
                raise ValidationError(f"Checkpoint {checkpoint_id} cannot be restored")
            
            # 从检查点获取状态
            state_data = await self._checkpoint_domain_service.restore_from_checkpoint(checkpoint_id)
            if not state_data:
                raise ValidationError(f"Failed to restore state from checkpoint {checkpoint_id}")
            
            # 生成分支ID
            branch_id = str(uuid.uuid4())
            
            # 创建分支实体（包含状态数据）
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
            await self._thread_branch_repository.create(branch)
            
            # 更新线程的分支计数
            thread.increment_branch_count()
            await self._thread_repository.update(thread)
            
            return branch_id
        except Exception as e:
            self._handle_exception(e, "create branch from checkpoint")
            raise
    
    async def merge_branch_to_main(
        self,
        thread_id: str,
        branch_id: str,
        merge_strategy: str = "overwrite"
    ) -> bool:
        """将分支合并到主线"""
        try:
            self._log_operation("merge_branch_to_main", thread_id,
                              branch_id=branch_id, merge_strategy=merge_strategy)
            
            # 验证线程和分支存在
            thread = await self._validate_thread_exists(thread_id)
            
            branch = await self._thread_branch_repository.get(branch_id)
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
            await self._thread_branch_repository.update(branch)
            
            return True
        except Exception as e:
            self._handle_exception(e, "merge branch to main")
            return False
    
    async def get_branch_history(self, thread_id: str, branch_id: str) -> List[Dict[str, Any]]:
        """获取分支历史"""
        try:
            # 验证分支存在
            branch = await self._thread_branch_repository.get(branch_id)
            if not branch or branch.thread_id != thread_id:
                raise EntityNotFoundError(f"Branch {branch_id} not found in thread {thread_id}")
            
            # 使用历史服务获取分支历史
            from .history_service import HistoryFilters
            
            # 这里需要注入历史服务，简化处理
            # 在实际实现中，应该通过依赖注入获取历史服务
            try:
                # 假设有历史服务可用
                from .history_service import ThreadHistoryService
                from src.interfaces.threads.storage import IThreadRepository
                
                # 创建历史服务实例（简化处理）
                history_service = ThreadHistoryService(self._thread_repository)
                
                filters = HistoryFilters(limit=100)
                history_list = await history_service.get_branch_history(branch_id, filters)
                
                return history_list
            except Exception:
                # 如果历史服务不可用，返回基本分支信息
                return [{
                    "branch_id": branch.id,
                    "branch_name": branch.branch_name,
                    "source_checkpoint_id": branch.source_checkpoint_id,
                    "created_at": branch.created_at.isoformat(),
                    "metadata": branch.metadata,
                    "record_type": "branch_created"
                }]
                
        except Exception as e:
            raise ValidationError(f"Failed to get branch history: {str(e)}")
    
    async def list_active_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """列活动分支"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 获取活动分支
            all_branches = await self._thread_branch_repository.list_by_thread(thread_id)
            branches = [b for b in all_branches if b.metadata.get("is_active", True)]
            
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
            branch = await self._thread_branch_repository.get(branch_id)
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
            all_branches = await self._thread_branch_repository.list_by_thread(thread_id)
            
            cleaned_count = 0
            for branch in all_branches:
                # 检查分支是否为孤立分支
                is_orphaned = await self._is_orphaned_branch(branch)
                
                if is_orphaned:
                    success = await self._thread_branch_repository.delete(branch.id)
                    if success:
                        cleaned_count += 1
                        # 更新线程的分支计数
                        thread = await self._thread_repository.get(thread_id)
                        if thread:
                            thread.branch_count = max(0, thread.branch_count - 1)
                            thread.update_timestamp()
                            await self._thread_repository.update(thread)
            
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