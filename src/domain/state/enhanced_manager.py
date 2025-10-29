from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging
from src.domain.state.interfaces import IEnhancedStateManager, IStateCollaborationManager
from src.infrastructure.state.interfaces import IStateSnapshotStore, IStateHistoryManager, StateHistoryEntry


logger = logging.getLogger(__name__)


class EnhancedStateManager(IEnhancedStateManager, IStateCollaborationManager):
    """增强状态管理器实现 - 重构版本"""
    
    def __init__(self, snapshot_store: IStateSnapshotStore,
                 history_manager: IStateHistoryManager):
        self.snapshot_store = snapshot_store
        self.history_manager = history_manager
        self.current_states: Dict[str, Any] = {}
    
    def execute_with_state_management(
        self,
        domain_state: Any,
        executor: Callable[[Any], Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """带状态管理的执行"""
        # 1. 验证状态
        validation_errors = self.validate_domain_state(domain_state)
        if validation_errors:
            raise ValueError(f"状态验证失败: {validation_errors}")
        
        # 2. 创建快照
        snapshot_id = self.create_snapshot(domain_state, "pre_execution")
        
        # 3. 记录开始
        old_state = domain_state.to_dict() if hasattr(domain_state, 'to_dict') else vars(domain_state)
        
        try:
            # 4. 执行业务逻辑
            result_state = executor(domain_state)
            
            # 5. 记录成功
            new_state = result_state.to_dict() if hasattr(result_state, 'to_dict') else vars(result_state)
            self.record_state_change(
                domain_state.agent_id if hasattr(domain_state, 'agent_id') else "unknown",
                "execution_success",
                old_state,
                new_state
            )
            
            return result_state
            
        except Exception as e:
            # 6. 记录失败
            self.record_state_change(
                domain_state.agent_id if hasattr(domain_state, 'agent_id') else "unknown",
                "execution_error",
                old_state,
                {"error": str(e), "snapshot_id": snapshot_id}
            )
            raise
    
    def validate_domain_state(self, domain_state: Any) -> List[str]:
        """验证域层状态完整性"""
        errors = []
        
        # 检查必需字段
        if not hasattr(domain_state, 'agent_id') or not domain_state.agent_id:
            errors.append("缺少agent_id字段")
        
        if not hasattr(domain_state, 'messages'):
            errors.append("缺少messages字段")
        
        # 检查字段类型
        if hasattr(domain_state, 'messages') and not isinstance(domain_state.messages, list):
            errors.append("messages字段必须是列表类型")
        
        # 检查业务逻辑约束
        if (hasattr(domain_state, 'iteration_count') and 
            hasattr(domain_state, 'max_iterations') and
            domain_state.iteration_count > domain_state.max_iterations):
            errors.append("迭代计数超过最大限制")
        
        return errors
    
    def save_snapshot(self, domain_state: Any, snapshot_name: str = "") -> str:
        """保存状态快照"""
        from src.infrastructure.state.interfaces import StateSnapshot
        snapshot = StateSnapshot(
            snapshot_id=self._generate_snapshot_id(),
            agent_id=domain_state.agent_id,
            domain_state=domain_state.to_dict() if hasattr(domain_state, 'to_dict') else vars(domain_state),
            timestamp=datetime.now(),
            snapshot_name=snapshot_name
        )
        
        success = self.snapshot_store.save_snapshot(snapshot)
        if success:
            return snapshot.snapshot_id
        else:
            raise Exception("保存快照失败")
    
    def load_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """加载状态快照"""
        snapshot = self.snapshot_store.load_snapshot(snapshot_id)
        if snapshot:
            return snapshot.domain_state
        return None
    
    def get_snapshot_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取快照历史"""
        snapshots = self.snapshot_store.get_snapshots_by_agent(agent_id)
        return [
            {
                "snapshot_id": s.snapshot_id,
                "timestamp": s.timestamp,
                "snapshot_name": s.snapshot_name,
                "size_bytes": s.size_bytes
            }
            for s in snapshots
        ]
    
    def create_state_history_entry(self, domain_state: Any, action: str) -> str:
        """创建状态历史记录"""
        current_state = self.current_states.get(domain_state.agent_id, {})
        new_state = domain_state.to_dict() if hasattr(domain_state, 'to_dict') else vars(domain_state)
        
        history_id = self.history_manager.record_state_change(
            domain_state.agent_id, current_state, new_state, action
        )
        
        # 更新当前状态
        self.current_states[domain_state.agent_id] = new_state
        
        return history_id
    
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取状态历史"""
        history_entries = self.history_manager.get_state_history(agent_id, limit)
        # Convert StateHistoryEntry objects to dictionaries to match interface
        return [
            {
                "history_id": entry.history_id,
                "agent_id": entry.agent_id,
                "timestamp": entry.timestamp,
                "action": entry.action,
                "state_diff": entry.state_diff,
                "metadata": entry.metadata
            }
            for entry in history_entries
        ]
    
    def _generate_snapshot_id(self) -> str:
        """生成快照ID"""
        import uuid
        return str(uuid.uuid4())
    
    # 实现IStateCollaborationManager接口的方法
    
    def create_snapshot(self, domain_state: Any, description: str = "") -> str:
        """创建快照"""
        return self.save_snapshot(domain_state, description)
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """恢复快照"""
        return self.load_snapshot(snapshot_id)
    
    def record_state_change(self, agent_id: str, action: str,
                          old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """记录状态变化"""
        # 创建一个临时的域状态对象来调用历史记录功能
        class TempDomainState:
            def __init__(self, agent_id, state_dict):
                self.agent_id = agent_id
                self.state_dict = state_dict
            
            def to_dict(self):
                return self.state_dict
        
        temp_state = TempDomainState(agent_id, new_state)
        return self.create_state_history_entry(temp_state, action)