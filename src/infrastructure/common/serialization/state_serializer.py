"""状态序列化器

提供专门用于状态管理的序列化功能，包括差异序列化等高级特性。
"""

import json
import pickle
import time
from typing import Dict, Any, Union, Optional, Set, List
from dataclasses import dataclass

from .serializer import Serializer


@dataclass
class StateDiff:
    """状态差异"""
    added: Dict[str, Any]
    modified: Dict[str, Any]
    removed: Set[str]
    timestamp: float


class StateSerializer(Serializer):
    """状态序列化器
    
    继承自通用序列化器，提供状态管理相关的特殊功能：
    - 状态差异序列化
    - 差异应用
    - 状态验证
    """
    
    def __init__(self, enable_cache: bool = True, cache_size: int = 1000, enable_diff_serialization: bool = True):
        """初始化状态序列化器
        
        Args:
            enable_cache: 是否启用缓存
            cache_size: 缓存大小限制
            enable_diff_serialization: 是否启用差异序列化
        """
        super().__init__(enable_cache=enable_cache, cache_size=cache_size)
        self._enable_diff_serialization = enable_diff_serialization
    
    def serialize_diff(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        format: str = Serializer.FORMAT_COMPACT_JSON
    ) -> Union[str, bytes]:
        """序列化状态差异
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            format: 序列化格式
            
        Returns:
            序列化后的差异数据
        """
        if not self._enable_diff_serialization:
            # 如果禁用差异序列化，回退到完整序列化
            return self.serialize(new_state, format)
        
        start_time = time.time()
        
        # 计算差异
        diff = self._compute_state_diff(old_state, new_state)
        
        # 序列化差异
        diff_dict = {
            "added": diff.added,
            "modified": diff.modified,
            "removed": list(diff.removed),  # 转换set为list
            "timestamp": diff.timestamp
        }
        
        result = self.serialize(diff_dict, format, enable_cache=False)
        
        # 更新统计
        if hasattr(self, '_stats'):
            self._stats["total_diff_computations"] = self._stats.get("total_diff_computations", 0) + 1
        
        return result
    
    def apply_diff(
        self,
        base_state: Dict[str, Any],
        diff_data: Union[str, bytes],
        format: str = Serializer.FORMAT_COMPACT_JSON
    ) -> Dict[str, Any]:
        """应用状态差异
        
        Args:
            base_state: 基础状态
            diff_data: 差异数据
            format: 序列化格式
            
        Returns:
            应用差异后的状态
        """
        # 反序列化差异
        diff_dict = self.deserialize(diff_data, format)
        
        # 创建状态的副本
        result_state = base_state.copy()
        
        # 应用添加的字段
        if "added" in diff_dict:
            result_state.update(diff_dict["added"])
        
        # 应用修改的字段
        if "modified" in diff_dict:
            result_state.update(diff_dict["modified"])
        
        # 移除删除的字段
        if "removed" in diff_dict:
            for key in diff_dict["removed"]:
                result_state.pop(key, None)
        
        return result_state
    
    def _compute_state_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> StateDiff:
        """计算状态差异
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            状态差异对象
        """
        added = {}
        modified = {}
        removed = set()
        
        # 找出新增的字段
        for key, value in new_state.items():
            if key not in old_state:
                added[key] = value
            elif old_state[key] != value:
                modified[key] = value
        
        # 找出删除的字段
        for key in old_state.keys():
            if key not in new_state:
                removed.add(key)
        
        return StateDiff(
            added=added,
            modified=modified,
            removed=removed,
            timestamp=time.time()
        )
    
    def validate_state(self, state: Dict[str, Any], required_fields: Optional[List[str]] = None) -> List[str]:
        """验证状态
        
        Args:
            state: 要验证的状态
            required_fields: 必需字段列表
            
        Returns:
            验证错误列表，如果为空则表示验证通过
        """
        errors = []
        
        if not isinstance(state, dict):
            errors.append("状态必须是字典类型")
            return errors
        
        if required_fields:
            missing_fields = [field for field in required_fields if field not in state]
            if missing_fields:
                errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        return errors