"""Threads实体工厂 - 负责创建和验证Thread实体"""

from typing import Dict, Any, Optional
from datetime import datetime

from .interfaces import IThreadCore, IThreadBranchCore, IThreadSnapshotCore
from .entities import Thread, ThreadBranch, ThreadSnapshot, ThreadStatus, ThreadType, ThreadMetadata


class ThreadFactory(IThreadCore):
    """Thread实体工厂 - 负责Thread实体的创建和基础操作"""
    
    def create_thread(
        self,
        thread_id: str,
        graph_id: Optional[str] = None,
        thread_type: str = "main",
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        parent_thread_id: Optional[str] = None,
        source_checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建新的Thread实体"""
        try:
            # 创建Thread实体
            thread = Thread(
                id=thread_id,
                graph_id=graph_id,
                type=ThreadType(thread_type),
                parent_thread_id=parent_thread_id,
                source_checkpoint_id=source_checkpoint_id,
                metadata=ThreadMetadata(**(metadata or {})),
                config=config or {}
            )
            
            return thread.to_dict()
        except Exception as e:
            raise ValueError(f"Failed to create thread: {str(e)}")
    
    def get_thread_status(self, thread_data: Dict[str, Any]) -> str:
        """获取线程状态"""
        return thread_data.get("status", "active")
    
    def update_thread_status(self, thread_data: Dict[str, Any], new_status: str) -> bool:
        """更新线程状态"""
        try:
            thread = Thread.from_dict(thread_data)
            success = thread.transition_to(ThreadStatus(new_status))
            if success:
                thread_data.update(thread.to_dict())
            return success
        except Exception:
            return False
    
    def can_transition_status(self, thread_data: Dict[str, Any], target_status: str) -> bool:
        """检查状态是否可以转换"""
        try:
            thread = Thread.from_dict(thread_data)
            return thread.can_transition_to(ThreadStatus(target_status))
        except Exception:
            return False
    
    def validate_thread_data(self, thread_data: Dict[str, Any]) -> bool:
        """验证线程数据的有效性"""
        try:
            # 检查必要字段
            required_fields = ["id", "status", "type", "created_at", "updated_at", "metadata", "config", "state"]
            for field in required_fields:
                if field not in thread_data:
                    return False
            
            # 尝试创建Thread实例
            Thread.from_dict(thread_data)
            return True
        except Exception:
            return False


class ThreadBranchFactory(IThreadBranchCore):
    """Thread分支实体工厂 - 负责ThreadBranch实体的创建和验证"""
    
    def create_branch(
        self,
        branch_id: str,
        thread_id: str,
        parent_thread_id: str,
        source_checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建分支实体"""
        try:
            branch = ThreadBranch(
                id=branch_id,
                thread_id=thread_id,
                parent_thread_id=parent_thread_id,
                source_checkpoint_id=source_checkpoint_id,
                branch_name=branch_name,
                metadata=metadata or {}
            )
            
            return branch.to_dict()
        except Exception as e:
            raise ValueError(f"Failed to create branch: {str(e)}")
    
    def validate_branch_data(self, branch_data: Dict[str, Any]) -> bool:
        """验证分支数据的有效性"""
        try:
            # 检查必要字段
            required_fields = ["id", "thread_id", "parent_thread_id", "source_checkpoint_id", "branch_name", "created_at", "metadata"]
            for field in required_fields:
                if field not in branch_data:
                    return False
            
            # 尝试创建ThreadBranch实例
            ThreadBranch.from_dict(branch_data)
            return True
        except Exception:
            return False


class ThreadSnapshotFactory(IThreadSnapshotCore):
    """Thread快照实体工厂 - 负责ThreadSnapshot实体的创建和验证"""
    
    def create_snapshot(
        self,
        snapshot_id: str,
        thread_id: str,
        checkpoint_id: str,
        snapshot_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建快照实体"""
        try:
            snapshot = ThreadSnapshot(
                id=snapshot_id,
                thread_id=thread_id,
                snapshot_name=f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=description,
                state_snapshot=snapshot_data,
                metadata=metadata or {}
            )
            
            return snapshot.to_dict()
        except Exception as e:
            raise ValueError(f"Failed to create snapshot: {str(e)}")
    
    def validate_snapshot_data(self, snapshot_data: Dict[str, Any]) -> bool:
        """验证快照数据的有效性"""
        try:
            # 检查必要字段
            required_fields = ["id", "thread_id", "snapshot_name", "created_at", "state_snapshot", "metadata"]
            for field in required_fields:
                if field not in snapshot_data:
                    return False
            
            # 尝试创建ThreadSnapshot实例
            ThreadSnapshot.from_dict(snapshot_data)
            return True
        except Exception:
            return False