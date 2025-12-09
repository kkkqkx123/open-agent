"""状态历史播放器

提供回放状态历史的功能。
"""

from typing import Any, Dict, List, Optional

from src.interfaces.state.base import IState
from ..factories.state_factory import StateFactory
from .history_recorder import HistoryEntry


class StateHistoryPlayer:
    """状态历史播放器
    
    负责根据历史记录重建状态。
    """
    
    def __init__(self) -> None:
        """初始化播放器"""
        pass
    
    def replay_state(self, history_entries: List[HistoryEntry]) -> Optional[IState]:
        """回放状态历史
        
        Args:
            history_entries: 历史记录条目列表
            
        Returns:
            Optional[IState]: 重建的状态对象
        """
        if not history_entries:
            return None
        
        # 按版本号排序
        sorted_entries = sorted(history_entries, key=lambda x: x.version or 0)
        
        # 获取最后一个条目的状态类型
        last_entry = sorted_entries[-1]
        state_type = self._extract_state_type(last_entry)
        
        if state_type is None:
            return None
        
        # 从第一个条目开始重建状态
        first_entry = sorted_entries[0]
        
        try:
            # 使用状态工厂创建状态
            state = StateFactory.create_state_from_dict(state_type, first_entry.data)
            
            # 应用后续的变化
            for entry in sorted_entries[1:]:
                if entry.operation == "delete":
                    # 如果是删除操作，返回None
                    return None
                elif entry.operation in ["create", "update", "rollback"]:
                    # 更新状态数据
                    self._apply_state_change(state, entry.data)
            
            return state
            
        except Exception:
            # 如果重建失败，返回None
            return None
    
    def replay_to_version(self,
                         history_entries: List[HistoryEntry],
                         target_version: int) -> Optional[IState]:
        """回放到指定版本
        
        Args:
            history_entries: 历史记录条目列表
            target_version: 目标版本
            
        Returns:
            Optional[IState]: 重建的状态对象
        """
        # 过滤出目标版本及之前的条目
        filtered_entries = [
            entry for entry in history_entries
            if (entry.version or 0) <= target_version
        ]
        
        return self.replay_state(filtered_entries)
    
    def replay_to_time(self,
                      history_entries: List[HistoryEntry],
                      target_time) -> Optional[IState]:
        """回放到指定时间点
        
        Args:
            history_entries: 历史记录条目列表
            target_time: 目标时间
            
        Returns:
            Optional[IState]: 重建的状态对象
        """
        # 过滤出目标时间及之前的条目
        filtered_entries = [
            entry for entry in history_entries
            if entry.timestamp <= target_time
        ]
        
        return self.replay_state(filtered_entries)
    
    def get_state_at_version(self,
                            history_entries: List[HistoryEntry],
                            version: int) -> Optional[Dict[str, Any]]:
        """获取指定版本的状态数据
        
        Args:
            history_entries: 历史记录条目列表
            version: 版本号
            
        Returns:
            Optional[Dict[str, Any]]: 状态数据
        """
        # 过滤出目标版本及之前的条目
        filtered_entries = [
            entry for entry in history_entries
            if (entry.version or 0) <= version
        ]
        
        if not filtered_entries:
            return None
        
        # 按版本号排序
        sorted_entries = sorted(filtered_entries, key=lambda x: x.version or 0)
        
        # 返回最后一个条目的数据
        return sorted_entries[-1].data
    
    def get_state_at_time(self,
                         history_entries: List[HistoryEntry],
                         target_time) -> Optional[Dict[str, Any]]:
        """获取指定时间点的状态数据
        
        Args:
            history_entries: 历史记录条目列表
            target_time: 目标时间
            
        Returns:
            Optional[Dict[str, Any]]: 状态数据
        """
        # 过滤出目标时间及之前的条目
        filtered_entries = [
            entry for entry in history_entries
            if entry.timestamp <= target_time
        ]
        
        if not filtered_entries:
            return None
        
        # 按时间排序
        sorted_entries = sorted(filtered_entries, key=lambda x: x.timestamp)
        
        # 返回最后一个条目的数据
        return sorted_entries[-1].data
    
    def calculate_diff(self,
                      history_entries: List[HistoryEntry],
                      from_version: int,
                      to_version: int) -> Optional[Dict[str, Any]]:
        """计算两个版本之间的差异
        
        Args:
            history_entries: 历史记录条目列表
            from_version: 起始版本
            to_version: 目标版本
            
        Returns:
            Optional[Dict[str, Any]]: 差异信息
        """
        from_state = self.get_state_at_version(history_entries, from_version)
        to_state = self.get_state_at_version(history_entries, to_version)
        
        if from_state is None or to_state is None:
            return None
        
        return self._calculate_state_diff(from_state, to_state)
    
    def _extract_state_type(self, entry: HistoryEntry) -> Optional[str]:
        """从历史记录条目中提取状态类型
        
        Args:
            entry: 历史记录条目
            
        Returns:
            Optional[str]: 状态类型
        """
        data = entry.data
        
        # 尝试从数据中提取状态类型
        if "state_type" in data:
            return data["state_type"]
        elif "type" in data:
            return data["type"]
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
    
    def _apply_state_change(self, state: IState, data: Dict[str, Any]) -> None:
        """应用状态变化
        
        Args:
            state: 状态对象
            data: 状态数据
        """
        # 如果状态有from_dict方法，使用它来更新状态
        if hasattr(state, 'from_dict'):
            try:
                # 创建新的状态实例
                new_state = state.__class__.from_dict(data)
                
                # 使用set_data方法更新状态数据
                for key, value in data.items():
                    state.set_data(key, value)
            except Exception:
                # 如果更新失败，忽略
                pass
    
    def _calculate_state_diff(self, from_data: Dict[str, Any], to_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态数据差异
        
        Args:
            from_data: 起始状态数据
            to_data: 目标状态数据
            
        Returns:
            Dict[str, Any]: 差异信息
        """
        diff = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # 找出添加的字段
        for key in to_data:
            if key not in from_data:
                diff["added"][key] = to_data[key]
        
        # 找出删除的字段
        for key in from_data:
            if key not in to_data:
                diff["removed"][key] = from_data[key]
        
        # 找出修改的字段
        for key in from_data:
            if key in to_data and from_data[key] != to_data[key]:
                diff["modified"][key] = {
                    "old": from_data[key],
                    "new": to_data[key]
                }
        
        return diff