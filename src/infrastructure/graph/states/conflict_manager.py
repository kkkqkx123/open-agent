"""冲突检测与解决状态管理器

提供状态冲突检测和解决功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
import logging
import copy

from .base_manager import BaseStateManager
from .interface import ConflictType, ConflictResolutionStrategy


logger = logging.getLogger(__name__)


class Conflict:
    """冲突信息类"""
    
    def __init__(self, 
                 conflict_type: ConflictType,
                 field_path: str,
                 current_value: Any,
                 new_value: Any,
                 timestamp: datetime):
        self.conflict_type = conflict_type
        self.field_path = field_path
        self.current_value = current_value
        self.new_value = new_value
        self.timestamp = timestamp
        self.resolution_strategy: Optional[str] = None
        self.resolved: bool = False


class IConflictResolver(ABC):
    """冲突解决器接口"""
    
    @abstractmethod
    def resolve_conflict(self, conflict: Conflict, current_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """解决冲突"""
        pass


class StateConflictResolver(IConflictResolver):
    """状态冲突解决器"""
    
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        self.strategy = strategy
    
    def resolve_conflict(self, conflict: Conflict, current_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """根据策略解决冲突
        
        Args:
            conflict: 冲突信息
            current_state: 当前状态
            new_state: 新状态
            
        Returns:
            解决冲突后的状态
        """
        if self.strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            return self._last_write_wins(current_state, new_state)
        elif self.strategy == ConflictResolutionStrategy.FIRST_WRITE_WINS:
            return self._first_write_wins(current_state, new_state)
        elif self.strategy == ConflictResolutionStrategy.MERGE_CHANGES:
            return self._merge_changes(current_state, new_state)
        else:
            raise ValueError(f"不支持的冲突解决策略: {self.strategy}")
    
    def _last_write_wins(self, current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """最后写入获胜策略"""
        # 保留新状态的所有修改
        return new
    
    def _first_write_wins(self, current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """首次写入获胜策略"""
        # 保留当前状态，拒绝新状态的冲突修改
        result = copy.deepcopy(current)
        # 只合并不冲突的字段
        for key, value in new.items():
            if key not in current:
                # 新字段直接添加
                result[key] = value
            elif current[key] == value:
                # 值相同，直接使用
                result[key] = value
            # 如果字段存在但值不同，则保留当前状态的值（不修改）
        return result
    
    def _merge_changes(self, current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """合并变更策略"""
        result = copy.deepcopy(current)
        
        # 智能合并逻辑
        for key, new_value in new.items():
            if key not in current:
                result[key] = new_value
            elif isinstance(new_value, dict) and isinstance(current[key], dict):
                # 递归合并字典
                result[key] = self._merge_dicts(current[key], new_value)
            elif isinstance(new_value, list) and isinstance(current[key], list):
                # 合并列表（去重）
                result[key] = list(set(current[key] + new_value))
            else:
                # 简单字段，使用新值
                result[key] = new_value
        
        return result
    
    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并字典"""
        result = copy.deepcopy(dict1)
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result


class ConflictStateManager(BaseStateManager):
    """冲突检测与解决状态管理器
    
    提供状态冲突检测和解决功能。
    """
    
    def __init__(
        self,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
    ):
        """初始化冲突管理器
        
        Args:
            conflict_strategy: 冲突解决策略
        """
        super().__init__()
        self.conflict_resolver = StateConflictResolver(conflict_strategy)
        self._state_versions: Dict[str, Dict[str, Any]] = {}
        self._conflict_history: List[Conflict] = []
    
    def create_state_version(self, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建状态版本
        
        Args:
            state: Agent状态
            metadata: 版本元数据
            
        Returns:
            版本ID
        """
        version_id = f"v{len(self._state_versions) + 1}"
        self._state_versions[version_id] = {
            "state": copy.deepcopy(state),
            "metadata": metadata or {},
            "timestamp": datetime.now()
        }
        return version_id
    
    def get_state_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的状态
        
        Args:
            version_id: 版本ID
            
        Returns:
            指定版本的状态，如果不存在则返回None
        """
        if version_id in self._state_versions:
            return copy.deepcopy(self._state_versions[version_id]["state"])
        return None
    
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异
        
        Args:
            state1: 第一个状态
            state2: 第二个状态
            
        Returns:
            差异字典
        """
        differences = {}
        all_keys = set(state1.keys()) | set(state2.keys())
        
        for key in all_keys:
            value1 = state1.get(key)
            value2 = state2.get(key)
            
            if value1 != value2:
                differences[key] = {
                    "old_value": value1,
                    "new_value": value2,
                    "type_changed": type(value1) != type(value2)
                }
        
        return differences
    
    def detect_conflicts(self, current_state: Dict[str, Any], new_state: Dict[str, Any]) -> List[Conflict]:
        """检测状态冲突
        
        Args:
            current_state: 当前状态
            new_state: 新状态
            
        Returns:
            冲突列表
        """
        conflicts = []
        differences = self.compare_states(current_state, new_state)
        
        for field_path, diff_info in differences.items():
            conflict_type = self._determine_conflict_type(field_path, diff_info)
            
            conflict = Conflict(
                conflict_type=conflict_type,
                field_path=field_path,
                current_value=diff_info["old_value"],
                new_value=diff_info["new_value"],
                timestamp=datetime.now()
            )
            conflicts.append(conflict)
        
        return conflicts
    
    def update_state_with_conflict_resolution(self,
                                            current_state: Dict[str, Any],
                                            new_state: Dict[str, Any],
                                            context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[Conflict]]:
        """带冲突解决的状态更新
        
        Args:
            current_state: 当前状态
            new_state: 新状态
            context: 上下文信息
            
        Returns:
            解决冲突后的状态和未解决的冲突列表
        """
        # 检测冲突
        conflicts = self.detect_conflicts(current_state, new_state)
        
        if not conflicts:
            # 无冲突，直接更新
            return new_state, []
        
        # 记录冲突
        self._conflict_history.extend(conflicts)
        
        # 应用冲突解决策略
        resolved_state = copy.deepcopy(current_state)
        unresolved_conflicts = []
        
        for conflict in conflicts:
            try:
                # 尝试自动解决冲突
                if self._can_auto_resolve(conflict):
                    resolved_state = self.conflict_resolver.resolve_conflict(conflict, resolved_state, new_state)
                    conflict.resolved = True
                    conflict.resolution_strategy = self.conflict_resolver.strategy.value
                else:
                    unresolved_conflicts.append(conflict)
            except Exception as e:
                logger.error(f"自动解决冲突失败: {e}")
                unresolved_conflicts.append(conflict)
        
        return resolved_state, unresolved_conflicts
    
    def _determine_conflict_type(self, field_path: str, diff_info: Dict[str, Any]) -> ConflictType:
        """确定冲突类型
        
        Args:
            field_path: 字段路径
            diff_info: 差异信息
            
        Returns:
            冲突类型
        """
        if diff_info["type_changed"]:
            return ConflictType.STRUCTURE_CHANGE
        
        old_value = diff_info["old_value"]
        new_value = diff_info["new_value"]
        
        if isinstance(old_value, list) and isinstance(new_value, list):
            return ConflictType.LIST_OPERATION
        
        return ConflictType.FIELD_MODIFICATION
    
    def _can_auto_resolve(self, conflict: Conflict) -> bool:
        """判断是否可以自动解决冲突
        
        Args:
            conflict: 冲突信息
            
        Returns:
            是否可以自动解决
        """
        # 根据冲突类型和业务规则判断
        if conflict.conflict_type == ConflictType.VERSION_MISMATCH:
            return False  # 版本冲突需要手动解决
        return True
    
    def get_conflict_history(self, limit: int = 50) -> List[Conflict]:
        """获取冲突历史
        
        Args:
            limit: 返回的最大冲突数
            
        Returns:
            冲突历史列表
        """
        return self._conflict_history[-limit:] if self._conflict_history else []
    
    def clear_conflict_history(self) -> None:
        """清空冲突历史"""
        self._conflict_history.clear()


# 便捷的创建函数
def create_enhanced_state_manager(
    enable_pooling: bool = True,
    max_pool_size: int = 10,
    enable_diff_tracking: bool = True,
    conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
) -> 'ConflictStateManager':
    """创建冲突状态管理器（增强功能）
    
    Args:
        enable_pooling: 是否启用对象池
        max_pool_size: 对象池最大大小
        enable_diff_tracking: 是否启用差异跟踪
        conflict_strategy: 冲突解决策略
        
    Returns:
        冲突状态管理器实例
    """
    # 注意：这个函数是为了保持向后兼容性
    # 实际使用时应该使用CompositeStateManager来获得完整功能
    return ConflictStateManager(conflict_strategy=conflict_strategy)