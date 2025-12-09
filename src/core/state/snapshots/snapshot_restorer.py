"""状态快照恢复器

提供从快照恢复状态的功能。
"""

from typing import Any, Callable, Dict, Optional

from src.interfaces.state.base import IState
from ..factories.state_factory import StateFactory
from src.infrastructure.state.snapshots.snapshot_storage import StateSnapshot


class StateSnapshotRestorer:
    """状态快照恢复器
    
    负责从快照恢复状态。
    """
    
    def __init__(self) -> None:
        """初始化恢复器"""
        pass
    
    def restore_state(self, snapshot: StateSnapshot) -> Optional[IState]:
        """恢复状态
        
        Args:
            snapshot: 状态快照
            
        Returns:
            Optional[IState]: 恢复的状态对象
        """
        try:
            # 从快照数据中提取状态类型
            state_type = self._extract_state_type(snapshot)
            
            if state_type is None:
                return None
            
            # 使用状态工厂创建状态
            state = StateFactory.create_state_from_dict(state_type, snapshot.state_data)
            
            return state
            
        except Exception:
            # 如果恢复失败，返回None
            return None
    
    def restore_with_validation(self,
                               snapshot: StateSnapshot,
                               validator: Optional[Callable[[IState], bool]] = None) -> Optional[IState]:
        """带验证的状态恢复
        
        Args:
            snapshot: 状态快照
            validator: 验证函数
            
        Returns:
            Optional[IState]: 恢复的状态对象
        """
        # 验证快照数据
        if not self._validate_snapshot(snapshot):
            return None
        
        # 恢复状态
        state = self.restore_state(snapshot)
        
        if state is None:
            return None
        
        # 自定义验证
        if validator and not validator(state):
            return None
        
        return state
    
    def restore_partial(self, 
                       snapshot: StateSnapshot,
                       fields: list[str]) -> Optional[Dict[str, Any]]:
        """部分恢复状态数据
        
        Args:
            snapshot: 状态快照
            fields: 要恢复的字段列表
            
        Returns:
            Optional[Dict[str, Any]]: 部分状态数据
        """
        try:
            state_data = snapshot.state_data
            partial_data = {}
            
            for field in fields:
                if field in state_data:
                    partial_data[field] = state_data[field]
                elif "data" in state_data and field in state_data["data"]:
                    partial_data[field] = state_data["data"][field]
            
            return partial_data if partial_data else None
            
        except Exception:
            return None
    
    def restore_metadata(self, snapshot: StateSnapshot) -> Optional[Dict[str, Any]]:
        """恢复元数据
        
        Args:
            snapshot: 状态快照
            
        Returns:
            Optional[Dict[str, Any]]: 元数据
        """
        try:
            state_data = snapshot.state_data
            
            if "metadata" in state_data:
                metadata = state_data["metadata"]
                if isinstance(metadata, dict):
                    return metadata.copy()
                else:
                    return {}
            
            return {}
            
        except Exception:
            return None
    
    def restore_with_migration(self,
                              snapshot: StateSnapshot,
                              migration_map: Dict[str, Any]) -> Optional[IState]:
        """带迁移的状态恢复
        
        Args:
            snapshot: 状态快照
            migration_map: 迁移映射
            
        Returns:
            Optional[IState]: 恢复的状态对象
        """
        try:
            # 应用迁移
            migrated_data = self._apply_migration(snapshot.state_data, migration_map)
            
            # 创建新的快照数据
            migrated_snapshot = StateSnapshot(
                state_id=snapshot.state_id,
                state_data=migrated_data,
                name=snapshot.name,
                description=snapshot.description,
                tags=(snapshot.tags or []) + ["migrated"],
                created_at=snapshot.created_at
            )
            
            # 恢复状态
            return self.restore_state(migrated_snapshot)
            
        except Exception:
            return None
    
    def compare_with_current(self,
                            snapshot: StateSnapshot,
                            current_state: IState) -> Dict[str, Any]:
        """与当前状态比较
        
        Args:
            snapshot: 状态快照
            current_state: 当前状态
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        try:
            # 恢复快照状态
            snapshot_state = self.restore_state(snapshot)
            
            if snapshot_state is None:
                return {"error": "Failed to restore snapshot"}
            
            # 比较状态数据
            snapshot_data = snapshot_state.to_dict()
            current_data = current_state.to_dict()
            
            differences = self._calculate_diff(snapshot_data, current_data)
            
            return {
                "snapshot_id": snapshot.id,
                "snapshot_name": snapshot.name,
                "snapshot_created_at": snapshot.created_at,
                "differences": differences,
                "is_identical": len(differences["added"]) == 0 and 
                               len(differences["removed"]) == 0 and 
                               len(differences["modified"]) == 0
            }
            
        except Exception as e:
            return {"error": f"Comparison failed: {str(e)}"}
    
    def _extract_state_type(self, snapshot: StateSnapshot) -> Optional[str]:
        """从快照中提取状态类型
        
        Args:
            snapshot: 状态快照
            
        Returns:
            Optional[str]: 状态类型
        """
        data = snapshot.state_data
        
        # 尝试从数据中提取状态类型
        if "state_type" in data:
            return str(data["state_type"])
        elif "type" in data:
            return str(data["type"])
        elif "workflow" in str(data).lower():
            return "workflow"
        elif "tool" in str(data).lower():
            return "tool"
        elif "session" in str(data).lower():
            return "session"
        elif "thread" in str(data).lower():
            return "thread"
        elif "checkpoint" in str(data).lower():
            return "checkpoint"
        else:
            # 默认为workflow
            return "workflow"
    
    def _validate_snapshot(self, snapshot: StateSnapshot) -> bool:
        """验证快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            bool: 是否有效
        """
        # 基本验证
        if not snapshot.state_id:
            return False
        
        if not snapshot.state_data:
            return False
        
        if not isinstance(snapshot.state_data, dict):
            return False
        
        return True
    
    def _apply_migration(self, 
                        data: Dict[str, Any], 
                        migration_map: Dict[str, Any]) -> Dict[str, Any]:
        """应用迁移
        
        Args:
            data: 原始数据
            migration_map: 迁移映射
            
        Returns:
            Dict[str, Any]: 迁移后的数据
        """
        migrated_data = data.copy()
        
        # 字段重命名
        if "rename_fields" in migration_map:
            for old_name, new_name in migration_map["rename_fields"].items():
                if old_name in migrated_data:
                    migrated_data[new_name] = migrated_data.pop(old_name)
        
        # 字段删除
        if "remove_fields" in migration_map:
            for field_name in migration_map["remove_fields"]:
                migrated_data.pop(field_name, None)
        
        # 字段添加
        if "add_fields" in migration_map:
            for field_name, field_value in migration_map["add_fields"].items():
                migrated_data[field_name] = field_value
        
        # 值转换
        if "transform_values" in migration_map:
            for field_name, transform_func in migration_map["transform_values"].items():
                if field_name in migrated_data:
                    try:
                        migrated_data[field_name] = transform_func(migrated_data[field_name])
                    except Exception:
                        pass  # 保持原值
        
        return migrated_data
    
    def _calculate_diff(self, 
                       data1: Dict[str, Any], 
                       data2: Dict[str, Any]) -> Dict[str, Any]:
        """计算数据差异
        
        Args:
            data1: 数据1
            data2: 数据2
            
        Returns:
            Dict[str, Any]: 差异信息
        """
        diff: Dict[str, Dict[str, Any]] = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # 找出添加的字段
        for key in data2:
            if key not in data1:
                diff["added"][key] = data2[key]
        
        # 找出删除的字段
        for key in data1:
            if key not in data2:
                diff["removed"][key] = data1[key]
        
        # 找出修改的字段
        for key in data1:
            if key in data2 and data1[key] != data2[key]:
                diff["modified"][key] = {
                    "old": data1[key],
                    "new": data2[key]
                }
        
        return diff