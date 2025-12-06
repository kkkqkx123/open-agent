"""线程快照服务实现"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.interfaces import IThreadCore, IThreadSnapshotCore
from src.core.threads.entities import Thread, ThreadMetadata, ThreadSnapshot, ThreadStatus
from src.interfaces.threads import IThreadRepository, IThreadSnapshotRepository
from src.interfaces.repository import ISnapshotRepository
from src.interfaces.storage.exceptions import StorageValidationError as ValidationError, StorageNotFoundError as EntityNotFoundError


class ThreadSnapshotService:
    """线程快照业务服务实现"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_snapshot_core: IThreadSnapshotCore,
        thread_repository: IThreadRepository,
        thread_snapshot_repository: IThreadSnapshotRepository
    ):
        self._thread_core = thread_core
        self._thread_snapshot_core = thread_snapshot_core
        self._thread_repository = thread_repository
        self._thread_snapshot_repository = thread_snapshot_repository
    
    async def create_snapshot_from_thread(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """从线程创建快照"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 生成快照ID和检查点ID
            snapshot_id = str(uuid.uuid4())
            checkpoint_id = f"checkpoint_{datetime.now().timestamp()}"
            
            # 准备快照数据
            metadata = thread.metadata
            snapshot_data = {
                "thread_id": thread_id,
                "thread_status": thread.status,
                "message_count": thread.message_count,
                "checkpoint_count": thread.checkpoint_count,
                "branch_count": thread.branch_count,
                "tags": metadata.get("tags", []) if isinstance(metadata, dict) else [],
                "metadata": metadata if include_metadata else {},
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat()
            }
            
            # 创建快照实体
            snapshot_data_dict = self._thread_snapshot_core.create_snapshot(
                snapshot_id=snapshot_id,
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                snapshot_data=snapshot_data,
                metadata={"description": description or f"Snapshot of thread {thread_id}"}
            )
            
            # 保存快照
            snapshot = ThreadSnapshot.from_dict(snapshot_data_dict)
            snapshot._snapshot_name = snapshot_name
            if description:
                snapshot._description = description
            await self._thread_snapshot_repository.create(snapshot)
            
            # 更新线程的检查点计数
            thread.increment_checkpoint_count()
            await self._thread_repository.update(thread)
            
            return snapshot_id
        except Exception as e:
            raise ValidationError(f"Failed to create snapshot from thread: {str(e)}")
    
    async def restore_thread_from_snapshot(
        self,
        thread_id: str,
        snapshot_id: str,
        restore_strategy: str = "full"
    ) -> bool:
        """从快照恢复线程"""
        try:
            # 验证线程和快照存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            snapshot = await self._thread_snapshot_repository.get(snapshot_id)
            if not snapshot or snapshot.thread_id != thread_id:
                raise EntityNotFoundError(f"Snapshot {snapshot_id} not found for thread {thread_id}")
            
            # 根据恢复策略执行恢复
            if restore_strategy == "full":
                # 完全恢复
                snapshot_data = snapshot.state_snapshot
                thread._status = ThreadStatus(snapshot_data.get("thread_status", thread.status))
                thread._message_count = snapshot_data.get("message_count", thread.message_count)
                thread._checkpoint_count = snapshot_data.get("checkpoint_count", thread.checkpoint_count)
                thread._branch_count = snapshot_data.get("branch_count", thread.branch_count)
                # 更新元数据
                metadata_update = snapshot_data.get("metadata", {})
                if metadata_update:
                    current_metadata = thread.metadata
                    if isinstance(current_metadata, dict):
                        current_metadata.update(metadata_update)
                        thread.metadata = ThreadMetadata(**current_metadata)
                thread.update_timestamp()
                
                await self._thread_repository.update(thread)
                
            elif restore_strategy == "metadata_only":
                # 仅恢复元数据
                snapshot_data = snapshot.state_snapshot
                metadata_update = snapshot_data.get("metadata", {})
                if metadata_update:
                    current_metadata = thread.metadata
                    if isinstance(current_metadata, dict):
                        current_metadata.update(metadata_update)
                        thread.metadata = ThreadMetadata(**current_metadata)
                thread.update_timestamp()
                
                await self._thread_repository.update(thread)
                
            else:
                raise ValidationError(f"Unsupported restore strategy: {restore_strategy}")
            
            return True
        except Exception as e:
            raise ValidationError(f"Failed to restore thread from snapshot: {str(e)}")
    
    async def get_snapshot_comparison(
        self,
        thread_id: str,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较两个快照"""
        try:
            # 验证快照存在
            snapshot1 = await self._thread_snapshot_repository.get(snapshot_id1)
            snapshot2 = await self._thread_snapshot_repository.get(snapshot_id2)
            
            if not snapshot1 or snapshot1.thread_id != thread_id:
                raise EntityNotFoundError(f"Snapshot {snapshot_id1} not found for thread {thread_id}")
            
            if not snapshot2 or snapshot2.thread_id != thread_id:
                raise EntityNotFoundError(f"Snapshot {snapshot_id2} not found for thread {thread_id}")
            
            # 获取快照数据
            data1 = snapshot1.state_snapshot
            data2 = snapshot2.state_snapshot
            
            # 比较关键字段
            comparison = {
                "snapshot1_id": snapshot_id1,
                "snapshot2_id": snapshot_id2,
                "created_at_diff": (snapshot2.created_at - snapshot1.created_at).total_seconds(),
                "message_count_diff": data2.get("message_count", 0) - data1.get("message_count", 0),
                "checkpoint_count_diff": data2.get("checkpoint_count", 0) - data1.get("checkpoint_count", 0),
                "branch_count_diff": data2.get("branch_count", 0) - data1.get("branch_count", 0),
                "status_changed": data1.get("thread_status") != data2.get("thread_status"),
                "tags_changed": data1.get("tags") != data2.get("tags"),
                "metadata_changed": data1.get("metadata") != data2.get("metadata"),
                "total_changes": 0
            }
            
            # 计算总变化数
            comparison["total_changes"] = (
                (1 if comparison["status_changed"] else 0) +
                (1 if comparison["tags_changed"] else 0) +
                (1 if comparison["metadata_changed"] else 0) +
                abs(comparison["message_count_diff"]) +
                abs(comparison["checkpoint_count_diff"]) +
                abs(comparison["branch_count_diff"])
            )
            
            return comparison
        except Exception as e:
            raise ValidationError(f"Failed to get snapshot comparison: {str(e)}")
    
    async def list_thread_snapshots(self, thread_id: str) -> List[Dict[str, Any]]:
        """列线程快照"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 获取线程的所有快照
            snapshots = await self._thread_snapshot_repository.list_by_thread(thread_id)
            
            return [
                {
                    "snapshot_id": snapshot.id,
                    "snapshot_name": snapshot.snapshot_name,
                    "description": snapshot.description,
                    "created_at": snapshot.created_at.isoformat(),
                    "checkpoint_id": "",  # ThreadSnapshot没有checkpoint_id字段
                    "snapshot_size": len(str(snapshot.state_snapshot))
                }
                for snapshot in snapshots
            ]
        except Exception as e:
            raise ValidationError(f"Failed to list thread snapshots: {str(e)}")
    
    async def validate_snapshot_integrity(self, thread_id: str, snapshot_id: str) -> bool:
        """验证快照完整性"""
        try:
            # 验证快照存在
            snapshot = await self._thread_snapshot_repository.get(snapshot_id)
            if not snapshot or snapshot.thread_id != thread_id:
                return False
            
            # 基本完整性检查
            if not snapshot.snapshot_name:
                return False
            
            # 检查快照数据完整性
            snapshot_data = snapshot.state_snapshot
            required_fields = ["thread_id", "thread_status", "message_count", "checkpoint_count"]
            
            for field in required_fields:
                if field not in snapshot_data:
                    return False
            
            # 检查数据类型
            if not isinstance(snapshot_data["message_count"], int) or snapshot_data["message_count"] < 0:
                return False
            
            if not isinstance(snapshot_data["checkpoint_count"], int) or snapshot_data["checkpoint_count"] < 0:
                return False
            
            return True
        except Exception:
            return False
    
    async def cleanup_old_snapshots(self, thread_id: str, max_age_days: int = 30) -> int:
        """清理旧快照"""
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 获取线程的所有快照
            snapshots = await self._thread_snapshot_repository.list_by_thread(thread_id)
            
            cleaned_count = 0
            current_time = datetime.now()
            
            for snapshot in snapshots:
                # 检查快照年龄
                age_days = (current_time - snapshot.created_at).days
                
                if age_days > max_age_days:
                    # 删除旧快照
                    success = await self._thread_snapshot_repository.delete(snapshot.id)
                    if success:
                        cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            raise ValidationError(f"Failed to cleanup old snapshots: {str(e)}")