"""状态管理服务实现

提供增强的状态管理功能，整合CRUD操作、历史记录和快照管理。
"""

import asyncio
from src.services.logger import get_logger
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime

from src.interfaces.state.interfaces import IState
from src.interfaces.state.manager import (
    IStateManager,
    IStateHistoryManager,
    IStateSnapshotManager
)
from src.interfaces.state.serializer import IStateSerializer
from src.core.state.entities import StateStatistics
from src.core.state.core.base import BaseStateManager, StateValidationMixin


logger = get_logger(__name__)


class EnhancedStateManager(IStateManager, BaseStateManager, StateValidationMixin):
    """增强的状态管理器实现
    
    整合基础状态管理、历史记录和快照功能。
    """
    
    def __init__(self, 
                 history_manager: IStateHistoryManager,
                 snapshot_manager: IStateSnapshotManager,
                 serializer: Optional[IStateSerializer] = None):
        """初始化增强状态管理器
        
        Args:
            history_manager: 历史管理器
            snapshot_manager: 快照管理器
            serializer: 序列化器
        """
        super().__init__(serializer)
        self._history_manager = history_manager
        self._snapshot_manager = snapshot_manager
        
        # 状态到代理的映射
        self._state_agents: Dict[str, str] = {}
    
    @property
    def history_manager(self) -> IStateHistoryManager:
        """获取历史管理器"""
        return self._history_manager
    
    @property
    def snapshot_manager(self) -> IStateSnapshotManager:
        """获取快照管理器"""
        return self._snapshot_manager
    
    @property
    def serializer(self) -> IStateSerializer:
        """获取序列化器"""
        return self._serializer
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> IState:
        """创建状态"""
        self._validate_state_id(state_id)
        self._validate_state_data(initial_state)
        
        # 确保状态有ID
        state_data = initial_state.copy()
        state_data['id'] = state_id
        state_data['created_at'] = datetime.now().isoformat()
        state_data['updated_at'] = datetime.now().isoformat()
        
        self._states[state_id] = state_data
        
        logger.debug(f"状态创建成功: {state_id}")
        return self._create_state_wrapper(state_data)
    
    def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态"""
        state_data = self._states.get(state_id)
        if state_data:
            logger.debug(f"状态获取成功: {state_id}")
            return self._create_state_wrapper(state_data)
        else:
            logger.warning(f"状态不存在: {state_id}")
            return None
    
    def update_state(self, state_id: str, updates: Dict[str, Any]) -> IState:
        """更新状态"""
        if state_id not in self._states:
            raise ValueError(f"状态不存在: {state_id}")
        
        self._validate_state_data(updates)
        
        # 合并更新
        current_state = self._states[state_id]
        updated_state = self._merge_states(current_state, updates)
        updated_state['updated_at'] = datetime.now().isoformat()
        
        self._states[state_id] = updated_state
        
        logger.debug(f"状态更新成功: {state_id}")
        return self._create_state_wrapper(updated_state)
    
    def delete_state(self, state_id: str) -> bool:
        """删除状态"""
        if state_id in self._states:
            del self._states[state_id]
            if state_id in self._state_agents:
                del self._state_agents[state_id]
            logger.debug(f"状态删除成功: {state_id}")
            return True
        else:
            logger.warning(f"状态不存在，无法删除: {state_id}")
            return False
    
    def list_states(self) -> List[str]:
        """列出所有状态ID"""
        return list(self._states.keys())
    
    def create_state_with_history(self, state_id: str, initial_state: Dict[str, Any], 
                                 agent_id: str) -> IState:
        """创建状态并启用历史记录"""
        state = self.create_state(state_id, initial_state)
        self._state_agents[state_id] = agent_id
        
        # 记录初始状态
        self._history_manager.record_state_change(
            agent_id=agent_id,
            old_state={},
            new_state=initial_state,
            action="create"
        )
        
        return state
    
    def update_state_with_history(self, state_id: str, updates: Dict[str, Any], 
                                 agent_id: str, action: str = "update") -> IState:
        """更新状态并记录历史"""
        if state_id not in self._states:
            raise ValueError(f"状态不存在: {state_id}")
        
        # 获取当前状态
        old_state = self._states[state_id].copy()
        
        # 更新状态
        new_state = self.update_state(state_id, updates)
        
        # 记录历史
        self._history_manager.record_state_change(
            agent_id=agent_id,
            old_state=old_state,
            new_state=self._states[state_id],
            action=action
        )
        
        # 更新代理映射
        self._state_agents[state_id] = agent_id
        
        return new_state
    
    def create_state_snapshot(self, state_id: str, agent_id: str, 
                             snapshot_name: str = "") -> str:
        """为状态创建快照"""
        if state_id not in self._states:
            raise ValueError(f"状态不存在: {state_id}")
        
        state_data = self._states[state_id]
        
        # 创建快照
        snapshot_id = self._snapshot_manager.create_snapshot(
            agent_id=agent_id,
            state_data=state_data,
            snapshot_name=snapshot_name or f"snapshot_{state_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            metadata={
                "state_id": state_id,
                "created_by": "state_manager"
            }
        )
        
        logger.debug(f"快照创建成功: {snapshot_id}")
        return snapshot_id
    
    def restore_state_from_snapshot(self, snapshot_id: str, state_id: str) -> Optional[IState]:
        """从快照恢复状态"""
        snapshot = self._snapshot_manager.restore_snapshot(snapshot_id)
        if not snapshot:
            logger.warning(f"快照不存在: {snapshot_id}")
            return None
        
        # 恢复状态数据
        restored_state = snapshot.domain_state.copy()
        restored_state['id'] = state_id
        restored_state['updated_at'] = datetime.now().isoformat()
        
        self._states[state_id] = restored_state
        
        # 更新代理映射
        self._state_agents[state_id] = snapshot.agent_id
        
        logger.debug(f"状态从快照恢复成功: {state_id} <- {snapshot_id}")
        return self._create_state_wrapper(restored_state)
    
    def get_state_agent(self, state_id: str) -> Optional[str]:
        """获取状态关联的代理ID"""
        return self._state_agents.get(state_id)
    
    def get_agent_states(self, agent_id: str) -> List[str]:
        """获取代理关联的所有状态ID"""
        return [state_id for state_id, aid in self._state_agents.items() if aid == agent_id]
    
    def validate_state(self, state_id: str) -> List[str]:
        """验证状态"""
        if state_id not in self._states:
            return [f"状态不存在: {state_id}"]
        
        state_data = self._states[state_id]
        return self.validate_state_completeness(state_data)
    
    def get_statistics(self) -> StateStatistics:
        """获取状态统计信息"""
        base_stats = super().get_statistics()
        
        # 统计代理数量
        agent_counts: Dict[str, int] = {}
        for agent_id in self._state_agents.values():
            agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
        
        # 获取历史和快照统计
        history_stats = self._get_history_statistics()
        snapshot_stats = self._get_snapshot_statistics()
        
        return StateStatistics(
            total_states=base_stats.total_states,
            total_snapshots=snapshot_stats.get("total_snapshots", 0),
            total_history_entries=history_stats.get("total_history_entries", 0),
            storage_size_bytes=history_stats.get("storage_size_bytes", 0) +
                              snapshot_stats.get("storage_size_bytes", 0),
            agent_counts=agent_counts,
            last_updated=datetime.now()
        )
    
    def execute_with_state_management(
        self,
        state_id: str,
        executor: Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]],  # 返回(新状态, 是否成功)
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[IState], bool]:
        """带状态管理的执行
        Args:
            state_id: 状态ID
            executor: 执行函数，接收当前状态并返回(新状态, 是否成功)
            context: 执行上下文
            
        Returns:
            (执行后的状态, 是否成功)
        """
        try:
            # 1. 获取当前状态
            current_state = self.get_state(state_id)
            if not current_state:
                raise ValueError(f"状态不存在: {state_id}")
            
            current_state_dict = current_state.to_dict()
            
            # 2. 执行业务逻辑
            new_state_dict, success = executor(current_state_dict)
            
            if success:
                # 3. 更新状态
                updated_state = self.update_state(state_id, new_state_dict)
                
                return updated_state, True
            else:
                return current_state, False
            
        except Exception as e:
            logger.error(f"带状态管理的执行失败: {e}")
            raise
    
    def _create_state_wrapper(self, state_data: Dict[str, Any]) -> IState:
        """创建状态包装器"""
        return StateWrapper(state_data, self)
    
    def _get_history_statistics(self) -> Dict[str, Any]:
        """获取历史统计信息"""
        # 这里应该调用历史管理器的统计方法
        # 暂时返回默认值
        return {
            "total_history_entries": 0,
            "storage_size_bytes": 0
        }
    
    def _get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        # 这里应该调用快照管理器的统计方法
        # 暂时返回默认值
        return {
            "total_snapshots": 0,
            "storage_size_bytes": 0
        }
    

class StateWrapper(IState):
    """状态包装器实现
    
    将字典数据包装为IState接口实现。
    """
    
    def __init__(self, state_data: Dict[str, Any], manager: Optional[IStateManager] = None):
        """初始化状态包装器
        
        Args:
            state_data: 状态数据
            manager: 状态管理器
        """
        self._state_data = state_data
        self._manager = manager
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self._state_data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        self._state_data[key] = value
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        metadata = self._state_data.get('metadata', {})
        return metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        if 'metadata' not in self._state_data:
            self._state_data['metadata'] = {}
        self._state_data['metadata'][key] = value
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._state_data.get('id')
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._state_data['id'] = id
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        created_at = self._state_data.get('created_at')
        if created_at:
            return datetime.fromisoformat(created_at)
        return datetime.now()
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        updated_at = self._state_data.get('updated_at')
        if updated_at:
            return datetime.fromisoformat(updated_at)
        return datetime.now()
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return bool(self._state_data.get('complete', False))
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._state_data['complete'] = True
        self._state_data['updated_at'] = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._state_data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateWrapper':
        """从字典创建状态"""
        # 这里需要manager实例，但为了支持反序列化，我们创建一个没有管理器的包装器
        # 在实际使用中，应该通过状态管理器来创建和管理状态实例
        return cls(data, None)
    