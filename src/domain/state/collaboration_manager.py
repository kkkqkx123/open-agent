import pickle
import zlib
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid
from src.domain.state.interfaces import IStateCollaborationManager, IStateManager
from src.infrastructure.state.snapshot_store import StateSnapshotStore
from src.infrastructure.state.history_manager import StateHistoryManager
from src.infrastructure.graph.states import WorkflowState


logger = logging.getLogger(__name__)


class CollaborationManager(IStateCollaborationManager):
    """协作管理器实现 - 支持快照、历史记录和内存管理
    
    该类专注于高级状态管理功能，完全依赖StateManager进行基础状态操作。
    职责：
    1. 状态执行流程管理
    2. 快照创建和恢复
    3. 状态变化历史记录
    4. 内存使用监控
    """
    
    def __init__(
        self, 
        state_manager: IStateManager,
        snapshot_store: Optional[StateSnapshotStore] = None,
        history_manager: Optional[StateHistoryManager] = None,
        max_memory_usage: int = 50 * 1024 * 1024,  # 50MB
        max_snapshots_per_agent: int = 20,
        max_history_per_agent: int = 100,
        storage_backend: str = "memory"
    ):
        """初始化协作管理器
        
        Args:
            state_manager: 状态管理器实例（必需）
            snapshot_store: 快照存储实例
            history_manager: 历史管理器实例
            max_memory_usage: 最大内存使用量
            max_snapshots_per_agent: 每个代理的最大快照数
            max_history_per_agent: 每个代理的最大历史记录数
            storage_backend: 存储后端类型
        """
        self._state_manager = state_manager
        self.snapshot_store = snapshot_store or StateSnapshotStore(storage_backend)
        self.history_manager = history_manager or StateHistoryManager(max_history_per_agent)
        self.max_memory_usage = max_memory_usage
        self.max_snapshots_per_agent = max_snapshots_per_agent
        self.max_history_per_agent = max_history_per_agent
        self.storage_backend = storage_backend
        
        # 内存管理
        self._memory_lock = threading.Lock()
        self._agent_snapshots: Dict[str, List[str]] = {}
        self._agent_history: Dict[str, List[str]] = {}
        
        logger.info(f"CollaborationManager初始化完成 - 存储后端: {storage_backend}, "
                   f"最大内存: {max_memory_usage / 1024 / 1024:.1f}MB")
    
    @property
    def state_manager(self) -> IStateManager:
        """获取底层状态管理器实例"""
        return self._state_manager
    
    def execute_with_state_management(
        self,
        domain_state: Any,
        executor: Callable[[Any], Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """带状态管理的执行
        
        该方法提供完整的状态管理执行流程：
        1. 状态验证
        2. 创建执行前快照
        3. 执行业务逻辑
        4. 记录状态变化
        5. 创建执行后快照
        6. 内存使用检查
        
        Args:
            domain_state: 域状态对象
            executor: 执行函数，接收状态并返回修改后的状态
            context: 执行上下文
            
        Returns:
            执行后的状态对象
            
        Raises:
            ValueError: 当状态验证失败时
        """
        # 1. 状态验证
        validation_errors = self.validate_domain_state(domain_state)
        if validation_errors:
            raise ValueError(f"状态验证失败: {validation_errors}")
        
        # 2. 获取agent_id
        agent_id = self._extract_agent_id(domain_state)
        
        # 3. 创建执行前快照
        pre_snapshot_id = self.create_snapshot(domain_state, "pre_execution")
        logger.debug(f"创建执行前快照: {pre_snapshot_id}")
        
        # 4. 记录执行前状态
        old_state = self._extract_state_dict(domain_state)
        
        try:
            # 5. 执行业务逻辑
            result_state = executor(domain_state)
            
            # 6. 记录执行成功
            new_state = self._extract_state_dict(result_state)
            self.record_state_change(
                agent_id,
                "execution_success",
                old_state,
                new_state
            )
            
            # 7. 创建执行后快照
            post_snapshot_id = self.create_snapshot(result_state, "post_execution")
            logger.debug(f"创建执行后快照: {post_snapshot_id}")
            
            # 8. 检查内存使用
            self._check_memory_usage(agent_id)
            
            return result_state
            
        except Exception as e:
            # 9. 记录执行失败
            logger.error(f"执行失败: {e}")
            self.record_state_change(
                agent_id,
                "execution_error",
                old_state,
                {"error": str(e), "pre_snapshot_id": pre_snapshot_id}
            )
            raise
    
    def validate_domain_state(self, domain_state: Any) -> List[str]:
        """验证域层状态完整性
        
        该方法基于StateManager的验证结果，添加协作管理器特定的验证逻辑。
        
        Args:
            domain_state: 要验证的域状态对象
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 1. 提取状态字典
        state_dict = self._extract_state_dict(domain_state)
        
        # 2. 如果是WorkflowState类型，使用StateManager的验证
        if isinstance(domain_state, dict) and self._is_workflow_state(state_dict):
            # 检查StateManager是否有validate_state方法
            if hasattr(self.state_manager, 'validate_state'):
                # 使用StateManager验证WorkflowState
                if not self.state_manager.validate_state(state_dict):  # type: ignore
                    errors.append("StateManager验证失败")
        
        # 3. 协作管理器特定的验证
        # 检查必需字段
        if not isinstance(domain_state, dict):
            # 非字典类型，检查属性
            if not hasattr(domain_state, 'agent_id') or not domain_state.agent_id:
                errors.append("缺少agent_id字段")
            
            # 检查字段类型
            if hasattr(domain_state, 'messages') and not isinstance(domain_state.messages, list):
                errors.append("messages字段必须是列表类型")
            
            # 检查业务逻辑约束
            if (hasattr(domain_state, 'iteration_count') and 
                hasattr(domain_state, 'max_iterations') and
                domain_state.iteration_count > domain_state.max_iterations):
                errors.append("迭代计数超过最大限制")
        else:
            # 字典类型，检查键值
            if 'agent_id' not in state_dict or not state_dict['agent_id']:
                errors.append("缺少agent_id字段")
            
            if 'messages' in state_dict and not isinstance(state_dict['messages'], list):
                errors.append("messages字段必须是列表类型")
            
            if ('iteration_count' in state_dict and 'max_iterations' in state_dict and
                state_dict['iteration_count'] > state_dict['max_iterations']):
                errors.append("迭代计数超过最大限制")
        
        return errors
    
    def create_snapshot(self, domain_state: Any, description: str = "") -> str:
        """创建状态快照
        
        使用StateManager进行状态序列化，然后创建压缩快照。
        
        Args:
            domain_state: 域状态对象
            description: 快照描述
            
        Returns:
            快照ID
        """
        snapshot_id = str(uuid.uuid4())
        agent_id = self._extract_agent_id(domain_state)
        
        # 提取状态字典并处理序列化
        state_dict = self._extract_state_dict(domain_state)
        
        # 处理不可序列化的对象
        import json
        def make_serializable(obj) -> Any:
            """递归处理对象，使其可序列化"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'content') and hasattr(obj, 'type'):
                # 处理消息对象
                return {
                    "content": obj.content,
                    "type": getattr(obj, 'type', getattr(obj, '__class__', type(obj)).__name__.lower()),
                    "tool_call_id": getattr(obj, "tool_call_id", "")
                }
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return make_serializable(obj.__dict__)
            else:
                return str(obj)  # 确保返回可序列化的类型
        
        # 创建可序列化的状态字典副本
        serializable_state: Dict[str, Any] = make_serializable(state_dict)
        
        # 使用pickle序列化处理后的状态
        serialized_state = pickle.dumps(serializable_state)
        compressed_data = zlib.compress(serialized_state)
        
        from src.infrastructure.state.interfaces import StateSnapshot
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            agent_id=agent_id,
            domain_state=serializable_state,
            timestamp=datetime.now(),
            snapshot_name=description,
            compressed_data=compressed_data,
            size_bytes=len(compressed_data)
        )
        
        # 保存快照
        self.snapshot_store.save_snapshot(snapshot)
        
        # 管理Agent的快照列表
        with self._memory_lock:
            if agent_id not in self._agent_snapshots:
                self._agent_snapshots[agent_id] = []
            self._agent_snapshots[agent_id].append(snapshot_id)
            
            # 限制快照数量
            if len(self._agent_snapshots[agent_id]) > self.max_snapshots_per_agent:
                excess = len(self._agent_snapshots[agent_id]) - self.max_snapshots_per_agent
                self._agent_snapshots[agent_id] = self._agent_snapshots[agent_id][excess:]
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """恢复状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的状态对象，如果快照不存在则返回None
        """
        snapshot = self.snapshot_store.load_snapshot(snapshot_id)
        if snapshot:
            logger.info(f"恢复快照: {snapshot_id}")
            return snapshot.domain_state
        logger.warning(f"快照不存在: {snapshot_id}")
        return None
    
    def record_state_change(
        self, 
        agent_id: str, 
        action: str,
        old_state: Dict[str, Any], 
        new_state: Dict[str, Any]
    ) -> str:
        """记录状态变化
        
        委托给历史管理器记录变化，并维护内部的历史记录列表。
        
        Args:
            agent_id: 代理ID
            action: 执行的动作
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            历史记录ID
        """
        # 调用历史管理器记录变化
        history_id = self.history_manager.record_state_change(
            agent_id, old_state, new_state, action
        )
        
        # 管理历史记录列表
        with self._memory_lock:
            if agent_id not in self._agent_history:
                self._agent_history[agent_id] = []
            self._agent_history[agent_id].append(history_id)
            
            # 限制历史记录数量
            if len(self._agent_history[agent_id]) > self.max_history_per_agent:
                excess = len(self._agent_history[agent_id]) - self.max_history_per_agent
                self._agent_history[agent_id] = self._agent_history[agent_id][excess:]
        
        logger.debug(f"记录状态变化: {history_id}, action={action}")
        return history_id
    
    def _extract_agent_id(self, domain_state: Any) -> str:
        """提取代理ID
        
        Args:
            domain_state: 域状态对象
            
        Returns:
            代理ID字符串
        """
        return getattr(domain_state, 'agent_id', 'unknown')
    
    def _extract_state_dict(self, domain_state: Any) -> Dict[str, Any]:
        """提取状态字典，完全依赖StateManager
        
        该方法将各种类型的状态对象转换为字典，以便统一处理。
        
        Args:
            domain_state: 域状态对象
            
        Returns:
            状态字典
        """
        # 1. 如果是字典类型（包括WorkflowState），直接返回
        if isinstance(domain_state, dict):
            return domain_state.copy()
        
        # 2. 如果有to_dict方法，使用它
        if hasattr(domain_state, 'to_dict'):
            return domain_state.to_dict()
        
        # 3. 如果有__dict__属性，使用它
        elif hasattr(domain_state, '__dict__'):
            return domain_state.__dict__.copy()
        
        # 4. 其他情况返回空字典
        else:
            logger.warning(f"无法提取状态字典: {type(domain_state)}")
            return {}
    
    def _is_workflow_state(self, state_dict: Dict[str, Any]) -> bool:
        """检查是否为WorkflowState类型
        
        Args:
            state_dict: 状态字典
            
        Returns:
            是否为WorkflowState
        """
        # 检查WorkflowState的必需字段
        required_fields = ["messages", "tool_results", "current_step", "max_iterations", "iteration_count"]
        return all(field in state_dict for field in required_fields)
    
    def _check_memory_usage(self, agent_id: str) -> None:
        """检查内存使用情况
        
        Args:
            agent_id: 代理ID
        """
        with self._memory_lock:
            # 简单的内存检查：基于快照和历史数量
            snapshot_count = len(self._agent_snapshots.get(agent_id, []))
            history_count = len(self._agent_history.get(agent_id, []))
            
            if snapshot_count > self.max_snapshots_per_agent:
                logger.warning(f"Agent {agent_id} 快照数量超限: {snapshot_count}")
            
            if history_count > self.max_history_per_agent:
                logger.warning(f"Agent {agent_id} 历史记录数量超限: {history_count}")
    
    def get_memory_usage(self) -> int:
        """获取当前内存使用量（估算）
        
        Returns:
            内存使用量（字节）
        """
        total_size = 0
        
        # 估算快照内存使用
        for agent_id, snapshot_ids in self._agent_snapshots.items():
            for snapshot_id in snapshot_ids:
                snapshot = self.snapshot_store.load_snapshot(snapshot_id)
                if snapshot:
                    total_size += snapshot.size_bytes
        
        return total_size
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            性能统计字典
        """
        with self._memory_lock:
            total_snapshots = sum(len(ids) for ids in self._agent_snapshots.values())
            total_history = sum(len(ids) for ids in self._agent_history.values())
            
            return {
                "total_agents": len(self._agent_snapshots),
                "total_snapshots": total_snapshots,
                "total_history": total_history,
                "memory_usage_bytes": self.get_memory_usage(),
                "storage_backend": self.storage_backend
            }