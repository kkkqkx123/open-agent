"""Threads实体工厂 - 负责创建和验证Thread实体"""

from typing import Dict, Any, Optional
from datetime import datetime

from .interfaces import IThreadCore, IThreadBranchCore, IThreadSnapshotCore
from .entities import Thread, ThreadBranch, ThreadSnapshot, ThreadStatus, ThreadType, ThreadMetadata
from src.infrastructure.error_management.impl.threads import ThreadOperationHandler
from src.infrastructure.error_management import create_error_context, handle_error
from src.interfaces.sessions.exceptions import ThreadCreationError


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
        context = create_error_context(
            "threads",
            "create_thread",
            thread_id=thread_id,
            thread_type=thread_type,
            graph_id=graph_id
        )
        
        def _create_thread():
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
        
        try:
            return ThreadOperationHandler.safe_thread_creation(
                lambda: _create_thread(),
                max_retries=2,
                context=context
            )
        except Exception as e:
            handle_error(e, context)
            raise ThreadCreationError(
                session_id="unknown",
                thread_config=context,
                cause=e
            ) from e
    
    def get_thread_status(self, thread_data: Dict[str, Any]) -> str:
        """获取线程状态"""
        return thread_data.get("status", "active")
    
    def update_thread_status(self, thread_data: Dict[str, Any], new_status: str) -> bool:
        """更新线程状态"""
        thread_id = thread_data.get("id", "unknown")
        context = create_error_context(
            "threads",
            "update_thread_status",
            thread_id=thread_id,
            current_status=thread_data.get("status"),
            target_status=new_status
        )
        
        def _update_status():
            thread = Thread.from_dict(thread_data)
            current_status = thread.status
            success = thread.transition_to(ThreadStatus(new_status))
            if success:
                thread_data.update(thread.to_dict())
            return success
        
        try:
            return ThreadOperationHandler.safe_thread_state_transition(
                lambda: _update_status(),
                thread_id,
                thread_data.get("status", "unknown"),
                new_status,
                context=context
            )
        except Exception as e:
            handle_error(e, context)
            return False
    
    def can_transition_status(self, thread_data: Dict[str, Any], target_status: str) -> bool:
        """检查状态是否可以转换"""
        thread_id = thread_data.get("id", "unknown")
        context = create_error_context(
            "threads",
            "can_transition_status",
            thread_id=thread_id,
            current_status=thread_data.get("status"),
            target_status=target_status
        )
        
        def _check_transition():
            thread = Thread.from_dict(thread_data)
            return thread.can_transition_to(ThreadStatus(target_status))
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_check_transition, default_return=False, context=context)
        except Exception as e:
            handle_error(e, context)
            return False
    
    def validate_thread_data(self, thread_data: Dict[str, Any]) -> bool:
        """验证线程数据的有效性"""
        thread_id = thread_data.get("id", "unknown")
        context = create_error_context(
            "threads",
            "validate_thread_data",
            thread_id=thread_id
        )
        
        def _validate():
            # 检查必要字段
            required_fields = ["id", "status", "type", "created_at", "updated_at", "metadata", "config", "state"]
            for field in required_fields:
                if field not in thread_data:
                    return False
            
            # 尝试创建Thread实例
            Thread.from_dict(thread_data)
            return True
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_validate, default_return=False, context=context)
        except Exception as e:
            handle_error(e, context)
            return False

    def update_thread_state(self, thread_data: Dict[str, Any], state_data: Dict[str, Any]) -> None:
        """更新线程状态数据
        
        Args:
            thread_data: 线程数据
            state_data: 新的状态数据
        """
        thread_id = thread_data.get("id", "unknown")
        context = create_error_context(
            "threads",
            "update_thread_state",
            thread_id=thread_id
        )
        
        def _update_state():
             thread = Thread.from_dict(thread_data)
             # 使用内部属性直接更新状态，因为state是只读属性
             thread._state = state_data
             thread.update_timestamp()
             thread_data.update(thread.to_dict())
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_update_state, context=context)
        except Exception as e:
            handle_error(e, context)
            raise


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
        context = create_error_context(
            "threads",
            "create_branch",
            branch_id=branch_id,
            thread_id=thread_id,
            branch_name=branch_name
        )
        
        def _create_branch():
            branch = ThreadBranch(
                id=branch_id,
                thread_id=thread_id,
                parent_thread_id=parent_thread_id,
                source_checkpoint_id=source_checkpoint_id,
                branch_name=branch_name,
                metadata=metadata or {}
            )
            
            return branch.to_dict()
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_create_branch, context=context)
        except Exception as e:
            handle_error(e, context)
            raise ThreadCreationError(
                session_id="unknown",
                thread_config=context,
                cause=e
            ) from e
    
    def validate_branch_data(self, branch_data: Dict[str, Any]) -> bool:
        """验证分支数据的有效性"""
        branch_id = branch_data.get("id", "unknown")
        context = create_error_context(
            "threads",
            "validate_branch_data",
            branch_id=branch_id
        )
        
        def _validate():
            # 检查必要字段
            required_fields = ["id", "thread_id", "parent_thread_id", "source_checkpoint_id", "branch_name", "created_at", "metadata"]
            for field in required_fields:
                if field not in branch_data:
                    return False
            
            # 尝试创建ThreadBranch实例
            ThreadBranch.from_dict(branch_data)
            return True
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_validate, default_return=False, context=context)
        except Exception as e:
            handle_error(e, context)
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
        context = create_error_context(
            "threads",
            "create_snapshot",
            snapshot_id=snapshot_id,
            thread_id=thread_id
        )
        
        def _create_snapshot():
            snapshot = ThreadSnapshot(
                id=snapshot_id,
                thread_id=thread_id,
                snapshot_name=f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=description,
                state_snapshot=snapshot_data,
                metadata=metadata or {}
            )
            
            return snapshot.to_dict()
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_create_snapshot, context=context)
        except Exception as e:
            handle_error(e, context)
            raise ThreadCreationError(
                session_id="unknown",
                thread_config=context,
                cause=e
            ) from e
    
    def validate_snapshot_data(self, snapshot_data: Dict[str, Any]) -> bool:
        """验证快照数据的有效性"""
        snapshot_id = snapshot_data.get("id", "unknown")
        context = create_error_context(
            "threads",
            "validate_snapshot_data",
            snapshot_id=snapshot_id
        )
        
        def _validate():
            # 检查必要字段
            required_fields = ["id", "thread_id", "snapshot_name", "created_at", "state_snapshot", "metadata"]
            for field in required_fields:
                if field not in snapshot_data:
                    return False
            
            # 尝试创建ThreadSnapshot实例
            ThreadSnapshot.from_dict(snapshot_data)
            return True
        
        try:
            from src.infrastructure.error_management import safe_execution
            return safe_execution(_validate, default_return=False, context=context)
        except Exception as e:
            handle_error(e, context)
            return False