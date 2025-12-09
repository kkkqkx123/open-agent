"""状态快照创建器

提供创建状态快照的功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.interfaces.state.base import IState
from src.infrastructure.state.snapshots.snapshot_storage import StateSnapshot


class StateSnapshotCreator:
    """状态快照创建器
    
    负责创建状态快照。
    """
    
    def __init__(self) -> None:
        """初始化创建器"""
        pass
    
    def create_snapshot(self,
                       state: IState,
                       name: Optional[str] = None,
                       description: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> StateSnapshot:
        """创建状态快照
        
        Args:
            state: 状态对象
            name: 快照名称
            description: 快照描述
            tags: 快照标签
            
        Returns:
            StateSnapshot: 状态快照
        """
        state_id = state.get_id() or "unknown"
        state_data = state.to_dict()
        
        # 生成默认名称
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"snapshot_{timestamp}"
        
        return StateSnapshot(
            state_id=state_id,
            state_data=state_data,
            name=name,
            description=description,
            tags=tags
        )
    
    def create_from_dict(self, data: Dict[str, Any]) -> StateSnapshot:
        """从字典创建状态快照
        
        Args:
            data: 字典数据
            
        Returns:
            StateSnapshot: 状态快照
        """
        return StateSnapshot.from_dict(data)
    
    def create_auto_snapshot(self,
                            state: IState,
                            trigger: str = "auto") -> StateSnapshot:
        """创建自动快照
        
        Args:
            state: 状态对象
            trigger: 触发原因
            
        Returns:
            StateSnapshot: 状态快照
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"auto_{trigger}_{timestamp}"
        description = f"Automatic snapshot triggered by {trigger}"
        tags = ["auto", trigger]
        
        return self.create_snapshot(state, name, description, tags)
    
    def create_checkpoint_snapshot(self,
                                  state: IState,
                                  checkpoint_name: str) -> StateSnapshot:
        """创建检查点快照
        
        Args:
            state: 状态对象
            checkpoint_name: 检查点名称
            
        Returns:
            StateSnapshot: 状态快照
        """
        name = f"checkpoint_{checkpoint_name}"
        description = f"Checkpoint snapshot: {checkpoint_name}"
        tags = ["checkpoint", checkpoint_name]
        
        return self.create_snapshot(state, name, description, tags)
    
    def create_backup_snapshot(self,
                              state: IState,
                              backup_reason: str = "backup") -> StateSnapshot:
        """创建备份快照
        
        Args:
            state: 状态对象
            backup_reason: 备份原因
            
        Returns:
            StateSnapshot: 状态快照
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"backup_{backup_reason}_{timestamp}"
        description = f"Backup snapshot: {backup_reason}"
        tags = ["backup", backup_reason]
        
        return self.create_snapshot(state, name, description, tags)
    
    def create_error_snapshot(self,
                             state: IState,
                             error_message: str) -> StateSnapshot:
        """创建错误快照
        
        Args:
            state: 状态对象
            error_message: 错误消息
            
        Returns:
            StateSnapshot: 状态快照
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"error_{timestamp}"
        description = f"Error snapshot: {error_message}"
        tags = ["error"]
        
        return self.create_snapshot(state, name, description, tags)
    
    def create_milestone_snapshot(self,
                                 state: IState,
                                 milestone_name: str) -> StateSnapshot:
        """创建里程碑快照
        
        Args:
            state: 状态对象
            milestone_name: 里程碑名称
            
        Returns:
            StateSnapshot: 状态快照
        """
        name = f"milestone_{milestone_name}"
        description = f"Milestone snapshot: {milestone_name}"
        tags = ["milestone", milestone_name]
        
        return self.create_snapshot(state, name, description, tags)
    
    def create_batch_snapshots(self,
                              states: List[IState],
                              batch_name: str,
                              description: Optional[str] = None) -> List[StateSnapshot]:
        """创建批量快照
        
        Args:
            states: 状态对象列表
            batch_name: 批次名称
            description: 批次描述
            
        Returns:
            List[StateSnapshot]: 快照列表
        """
        snapshots = []
        
        for i, state in enumerate(states):
            state_id = state.get_id() or f"state_{i}"
            name = f"{batch_name}_{state_id}"
            batch_description = description or f"Batch snapshot: {batch_name}"
            tags = ["batch", batch_name]
            
            snapshot = self.create_snapshot(state, name, batch_description, tags)
            snapshots.append(snapshot)
        
        return snapshots
    
    def validate_snapshot_data(self, state_data: Dict[str, Any]) -> bool:
        """验证快照数据
        
        Args:
            state_data: 状态数据
            
        Returns:
            bool: 是否有效
        """
        # 基本验证
        if not isinstance(state_data, dict):
            return False
        
        if not state_data:
            return False
        
        # 检查必要字段
        required_fields = ["data", "metadata"]
        for field in required_fields:
            if field not in state_data:
                return False
        
        return True
    
    def enrich_snapshot_metadata(self,
                                snapshot: StateSnapshot,
                                additional_metadata: Dict[str, Any]) -> StateSnapshot:
        """丰富快照元数据
        
        Args:
            snapshot: 状态快照
            additional_metadata: 额外元数据
            
        Returns:
            StateSnapshot: 丰富后的快照
        """
        # 在状态数据中添加元数据
        enriched_data = snapshot.state_data.copy()
        
        if "metadata" not in enriched_data:
            enriched_data["metadata"] = {}
        
        enriched_data["metadata"].update(additional_metadata)
        
        # 创建新的快照
        return StateSnapshot(
            state_id=snapshot.state_id,
            state_data=enriched_data,
            name=snapshot.name,
            description=snapshot.description,
            tags=snapshot.tags,
            created_at=snapshot.created_at
        )