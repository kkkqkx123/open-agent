"""状态管理器实现

提供执行状态的管理和更新功能。
"""

from typing import Any, Dict, List, Optional, Type

__all__ = ("StateManager",)


class StateManager:
    """状态管理器，提供执行状态的管理和更新功能。"""
    
    def __init__(self, state_schema: Type):
        """初始化状态管理器。
        
        Args:
            state_schema: 状态模式类型
        """
        self.state_schema = state_schema
        self.current_state: Optional[Dict[str, Any]] = None
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
    
    async def initialize_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """初始化状态。
        
        Args:
            input_data: 输入数据
            
        Returns:
            初始化后的状态
        """
        # 创建初始状态
        if self.state_schema:
            try:
                # 如果状态模式是类，尝试实例化
                if hasattr(self.state_schema, '__dict__'):
                    self.current_state = self.state_schema(**input_data).__dict__
                else:
                    self.current_state = input_data
            except Exception:
                # 如果实例化失败，直接使用输入数据
                self.current_state = input_data
        else:
            self.current_state = input_data
        
        # 添加到历史记录
        if self.current_state is not None:
            self._add_to_history(self.current_state)
        
        return self.current_state if self.current_state is not None else {}
    
    async def update_state(
        self,
        current_state: Dict[str, Any],
        updates: Any
    ) -> Dict[str, Any]:
        """更新状态。
        
        Args:
            current_state: 当前状态
            updates: 更新数据
            
        Returns:
            更新后的状态
        """
        # 更新当前状态
        if isinstance(updates, dict):
            # 合并字典更新
            self.current_state = {**current_state, **updates}
        else:
            # 如果更新不是字典，尝试将其转换为字典
            if hasattr(updates, '__dict__'):
                self.current_state = {**current_state, **updates.__dict__}
            else:
                # 其他情况，保持原状态
                self.current_state = current_state
        
        # 添加到历史记录
        self._add_to_history(self.current_state)
        
        return self.current_state
    
    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """获取当前状态。
        
        Returns:
            当前状态
        """
        return self.current_state
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """获取状态历史。
        
        Returns:
            状态历史列表
        """
        return self.state_history.copy()
    
    def rollback_to_state(self, index: int) -> Dict[str, Any]:
        """回滚到指定状态。
        
        Args:
            index: 状态索引
            
        Returns:
            回滚后的状态
        """
        if 0 <= index < len(self.state_history):
            self.current_state = self.state_history[index].copy()
            # 截断历史记录到回滚点
            self.state_history = self.state_history[:index + 1]
            return self.current_state if self.current_state is not None else {}
        else:
            raise ValueError(f"无效的状态索引: {index}")
    
    def clear_history(self) -> None:
        """清除状态历史。"""
        self.state_history.clear()
        if self.current_state:
            self.state_history.append(self.current_state.copy())
    
    def set_max_history_size(self, max_size: int) -> None:
        """设置最大历史记录大小。
        
        Args:
            max_size: 最大历史记录大小
        """
        self.max_history_size = max_size
        # 如果当前历史记录超过限制，截断
        if len(self.state_history) > max_size:
            self.state_history = self.state_history[-max_size:]
    
    def _add_to_history(self, state: Dict[str, Any]) -> None:
        """添加状态到历史记录。
        
        Args:
            state: 要添加的状态
        """
        if state is not None:
            self.state_history.append(state.copy())
        
        # 检查历史记录大小限制
        if len(self.state_history) > self.max_history_size:
            # 移除最旧的记录
            self.state_history.pop(0)
    
    def get_state_diff(self, from_index: int, to_index: int) -> Dict[str, Any]:
        """获取状态差异。
        
        Args:
            from_index: 起始索引
            to_index: 结束索引
            
        Returns:
            状态差异字典
        """
        if not (0 <= from_index < len(self.state_history) and 
                0 <= to_index < len(self.state_history)):
            raise ValueError("无效的索引范围")
        
        from_state = self.state_history[from_index]
        to_state = self.state_history[to_index]
        
        diff = {}
        
        # 找出变化的键
        all_keys = set(from_state.keys()) | set(to_state.keys())
        
        for key in all_keys:
            from_value = from_state.get(key)
            to_value = to_state.get(key)
            
            if from_value != to_value:
                diff[key] = {
                    "from": from_value,
                    "to": to_value
                }
        
        return diff
    
    def get_state_stats(self) -> Dict[str, Any]:
        """获取状态统计信息。
        
        Returns:
            统计信息字典
        """
        return {
            "current_state_keys": len(self.current_state) if self.current_state else 0,
            "history_size": len(self.state_history),
            "max_history_size": self.max_history_size,
            "state_schema": self.state_schema.__name__ if self.state_schema else None
        }