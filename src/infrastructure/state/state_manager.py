"""状态管理器实现

提供状态CRUD操作的核心实现。
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.domain.state.interfaces import IStateCrudManager
from src.infrastructure.state.interfaces import IStateSnapshotStore, IStateHistoryManager

logger = logging.getLogger(__name__)


class StateManager(IStateCrudManager):
    """状态管理器实现类
    
    负责状态的CRUD操作和基本管理功能。
    """
    
    def __init__(self):
        """初始化状态管理器"""
        self._states: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, List[str]] = {}
        logger.debug("StateManager初始化完成")
    
    def create_state(self, state: Any) -> str:
        """创建新状态
        
        Args:
            state: 状态对象
            
        Returns:
            状态ID
        """
        state_id = getattr(state, 'id', None) or f"state_{datetime.now().timestamp()}"
        
        # 将状态转换为字典格式存储
        if hasattr(state, '__dict__'):
            state_dict = vars(state)
        elif isinstance(state, dict):
            state_dict = state.copy()
        else:
            state_dict = {"data": state}
        
        # 确保状态有ID
        state_dict['id'] = state_id
        
        self._states[state_id] = state_dict
        self._snapshots[state_id] = []
        
        logger.debug(f"状态创建成功: {state_id}")
        return state_id
    
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态字典，如果不存在则返回None
        """
        state_data = self._states.get(state_id)
        if state_data:
            logger.debug(f"状态获取成功: {state_id}")
        else:
            logger.warning(f"状态不存在: {state_id}")
        return state_data
    
    def update_state(self, state_id: str, state: Any) -> bool:
        """更新状态
        
        Args:
            state_id: 状态ID
            state: 新状态对象
            
        Returns:
            更新是否成功
        """
        if state_id not in self._states:
            logger.error(f"状态不存在，无法更新: {state_id}")
            return False
        
        # 将状态转换为字典格式
        if hasattr(state, '__dict__'):
            state_dict = vars(state)
        elif isinstance(state, dict):
            state_dict = state.copy()
        else:
            state_dict = {"data": state}
        
        # 保持ID一致
        state_dict['id'] = state_id
        
        self._states[state_id] = state_dict
        logger.debug(f"状态更新成功: {state_id}")
        return True
    
    def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            删除是否成功
        """
        if state_id in self._states:
            del self._states[state_id]
            if state_id in self._snapshots:
                del self._snapshots[state_id]
            logger.debug(f"状态删除成功: {state_id}")
            return True
        else:
            logger.warning(f"状态不存在，无法删除: {state_id}")
            return False
    
    def list_states(self) -> List[str]:
        """列出所有状态ID
        
        Returns:
            状态ID列表
        """
        return list(self._states.keys())
    
    def state_exists(self, state_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态是否存在
        """
        exists = state_id in self._states
        logger.debug(f"状态存在检查: {state_id} -> {exists}")
        return exists
    
    def get_state_count(self) -> int:
        """获取状态数量
        
        Returns:
            状态数量
        """
        count = len(self._states)
        logger.debug(f"状态数量: {count}")
        return count
    
    def clear_all_states(self) -> None:
        """清除所有状态"""
        self._states.clear()
        self._snapshots.clear()
        logger.debug("所有状态已清除")