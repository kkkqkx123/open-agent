"""组合状态管理器

整合所有状态管理功能的完整解决方案。
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .interface import ConflictResolutionStrategy
from .base_manager import BaseStateManager
from .pooling_manager import PoolingStateManager
from .conflict_manager import ConflictStateManager, Conflict
from .version_manager import VersionStateManager


class CompositeStateManager(BaseStateManager):
    """组合状态管理器
    
    整合对象池、冲突解决和版本管理等多种功能的完整状态管理解决方案。
    """
    
    def __init__(
        self,
        enable_pooling: bool = True,
        max_pool_size: int = 100,
        enable_diff_tracking: bool = True,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
    ):
        """初始化组合状态管理器
        
        Args:
            enable_pooling: 是否启用对象池
            max_pool_size: 对象池最大大小
            enable_diff_tracking: 是否启用差异跟踪
            conflict_strategy: 冲突解决策略
        """
        super().__init__()
        
        # 初始化各功能模块
        self._pooling_manager = PoolingStateManager(
            enable_pooling=enable_pooling,
            max_pool_size=max_pool_size,
            enable_diff_tracking=enable_diff_tracking
        )
        self._conflict_manager = ConflictStateManager(
            conflict_strategy=conflict_strategy
        )
        self._version_manager = VersionStateManager()
        
        # 保存配置参数
        self._enable_pooling = enable_pooling
        self._max_pool_size = max_pool_size
        self._enable_diff_tracking = enable_diff_tracking
        self._conflict_strategy = conflict_strategy
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态
        
        Args:
            state_id: 状态ID
            initial_state: 初始状态
            
        Returns:
            创建的状态
        """
        return self._pooling_manager.create_state(state_id, initial_state)
    
    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态
        
        Args:
            state_id: 状态ID
            current_state: 当前状态
            updates: 更新内容
            
        Returns:
            更新后的状态
        """
        # 使用冲突管理器进行冲突检测和解决
        if self._conflict_manager:
            resolved_state, _ = self._conflict_manager.update_state_with_conflict_resolution(
                current_state, 
                self._pooling_manager.update_state(state_id, current_state, updates)
            )
            return resolved_state
        else:
            return self._pooling_manager.update_state(state_id, current_state, updates)
    
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态对象，如果不存在则返回None
        """
        return self._pooling_manager.get_state(state_id)
    
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异
        
        Args:
            state1: 第一个状态
            state2: 第二个状态
            
        Returns:
            差异字典
        """
        return self._conflict_manager.compare_states(state1, state2)
    
    def serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态
        
        Args:
            state: 要序列化的状态
            
        Returns:
            序列化后的字符串
        """
        return self._pooling_manager.serialize_state(state)
    
    def deserialize_state(self, serialized_data: str) -> Dict[str, Any]:
        """反序列化状态
        
        Args:
            serialized_data: 序列化的数据
            
        Returns:
            反序列化后的状态
        """
        return self._pooling_manager.deserialize_state(serialized_data)
    
    # 性能优化相关方法
    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """获取内存使用统计
        
        Returns:
            内存使用统计
        """
        return self._pooling_manager.get_memory_usage_stats()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计信息
        """
        return self._pooling_manager.get_performance_stats()
    
    def cleanup(self, state_id: Optional[str] = None) -> None:
        """清理资源
        
        Args:
            state_id: 要清理的状态ID，如果为None则清理所有
        """
        self._pooling_manager.cleanup(state_id)
    
    # 冲突管理相关方法
    def detect_conflicts(self, current_state: Dict[str, Any], new_state: Dict[str, Any]) -> List[Conflict]:
        """检测状态冲突
        
        Args:
            current_state: 当前状态
            new_state: 新状态
            
        Returns:
            冲突列表
        """
        return self._conflict_manager.detect_conflicts(current_state, new_state)
    
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
        return self._conflict_manager.update_state_with_conflict_resolution(
            current_state, new_state, context or {}
        )
    
    def get_conflict_history(self, limit: int = 50) -> List[Conflict]:
        """获取冲突历史
        
        Args:
            limit: 返回的最大冲突数
            
        Returns:
            冲突历史列表
        """
        return self._conflict_manager.get_conflict_history(limit)
    
    def clear_conflict_history(self) -> None:
        """清空冲突历史"""
        self._conflict_manager.clear_conflict_history()
    
    # 为兼容性公开冲突解决器
    @property
    def conflict_resolver(self):
        """获取冲突解决器"""
        return self._conflict_manager.conflict_resolver
    
    def _can_auto_resolve(self, conflict):
        """判断是否可以自动解决冲突"""
        return self._conflict_manager._can_auto_resolve(conflict)
    
    def _determine_conflict_type(self, field_path, diff_info):
        """确定冲突类型"""
        return self._conflict_manager._determine_conflict_type(field_path, diff_info)
    
    # 版本管理相关方法
    def create_state_version(self, state_id: str, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建状态版本
        
        Args:
            state_id: 状态ID
            state: 状态对象
            metadata: 版本元数据
            
        Returns:
            版本ID
        """
        return self._version_manager.create_state_version(state_id, state, metadata)
    
    def get_state_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的状态
        
        Args:
            version_id: 版本ID
            
        Returns:
            指定版本的状态，如果不存在则返回None
        """
        return self._version_manager.get_state_version(version_id)
    
    def get_state_versions(self, state_id: str) -> List[Dict[str, Any]]:
        """获取指定状态的所有版本
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态版本列表
        """
        return self._version_manager.get_state_versions(state_id)
    
    def get_version_metadata(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取版本元数据
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本元数据，如果不存在则返回None
        """
        return self._version_manager.get_version_metadata(version_id)
    
    def rollback_to_version(self, state_id: str, version_id: str) -> bool:
        """回滚到指定版本
        
        Args:
            state_id: 状态ID
            version_id: 版本ID
            
        Returns:
            是否成功回滚
        """
        return self._version_manager.rollback_to_version(state_id, version_id)


# 便捷的创建函数
def create_composite_state_manager(
    enable_pooling: bool = True,
    max_pool_size: int = 100,
    enable_diff_tracking: bool = True,
    conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
) -> CompositeStateManager:
    """创建组合状态管理器
    
    Args:
        enable_pooling: 是否启用对象池
        max_pool_size: 对象池最大大小
        enable_diff_tracking: 是否启用差异跟踪
        conflict_strategy: 冲突解决策略
        
    Returns:
        组合状态管理器实例
    """
    return CompositeStateManager(
        enable_pooling=enable_pooling,
        max_pool_size=max_pool_size,
        enable_diff_tracking=enable_diff_tracking,
        conflict_strategy=conflict_strategy
    )