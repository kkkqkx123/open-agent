import pickle
import zlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from src.domain.state.interfaces import IStateCollaborationManager
from src.infrastructure.state.snapshot_store import StateSnapshotStore


class SimpleCollaborationManager(IStateCollaborationManager):
    """简单协作管理器实现"""
    
    def __init__(self, snapshot_store: StateSnapshotStore):
        self.snapshot_store = snapshot_store
        self.current_states: Dict[str, Any] = {}
    
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
    
    def create_snapshot(self, domain_state: Any, description: str = "") -> str:
        """创建快照"""
        snapshot_id = str(uuid.uuid4())
        agent_id = getattr(domain_state, 'agent_id', 'unknown')
        
        # 序列化状态
        state_dict = domain_state.to_dict() if hasattr(domain_state, 'to_dict') else vars(domain_state)
        compressed_data = zlib.compress(pickle.dumps(state_dict))
        
        from src.infrastructure.state.snapshot_store import StateSnapshot
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            agent_id=agent_id,
            domain_state=state_dict,
            timestamp=datetime.now(),
            snapshot_name=description,
            compressed_data=compressed_data,
            size_bytes=len(compressed_data)
        )
        
        # 保存快照
        self.snapshot_store.save_snapshot(snapshot)
        
        # 管理Agent的快照列表
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """恢复快照"""
        snapshot = self.snapshot_store.load_snapshot(snapshot_id)
        if snapshot:
            return snapshot.domain_state
        return None
    
    def record_state_change(self, agent_id: str, action: str, 
                          old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """记录状态变化 - 这里我们使用历史管理器来实现"""
        # 由于我们已经有历史管理器，这里可以调用历史管理器的相应方法
        # 但为了保持接口一致性，我们简单地生成一个ID
        history_id = str(uuid.uuid4())
        
        # 在实际实现中，这里应该调用历史管理器
        # 但目前我们只返回ID，因为历史管理器是独立的
        return history_id