"""测试工具和模拟实现"""

from typing import Any, Optional, List, Tuple, Generator, Dict
from pathlib import Path
import uuid
import json
import logging
from datetime import datetime

from src.application.sessions.manager import ISessionManager
from src.application.workflow.manager import IWorkflowManager
from src.domain.sessions.store import ISessionStore
from src.infrastructure.graph.state import AgentState
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states.workflow import WorkflowState
from src.application.threads.session_thread_mapper import ISessionThreadMapper, MemorySessionThreadMapper
from src.domain.threads.interfaces import IThreadManager
from src.infrastructure.threads.metadata_store import MemoryThreadMetadataStore
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.application.checkpoint.manager import CheckpointManager
from src.domain.checkpoint.config import CheckpointConfig
from src.application.threads.query_manager import ThreadQueryManager


class MockWorkflowManager(IWorkflowManager):
    """模拟工作流管理器"""
    
    def __init__(self) -> None:
        self._workflows: Dict[str, Any] = {}
        self._configs: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
    
    def load_workflow(self, config_path: str) -> str:
        workflow_id = f"wf_{config_path.split('/')[-1].split('.')[0]}_{uuid.uuid4().hex[:8]}"
        self._workflows[workflow_id] = {"config_path": config_path}
        self._configs[workflow_id] = WorkflowConfig(
            name=config_path.split('/')[-1].split('.')[0],
            version="1.0",
            description="Mock workflow config",
            nodes={},
            edges=[],
            entry_point="start"
        )
        self._metadata[workflow_id] = {
            "name": config_path.split('/')[-1].split('.')[0],
            "version": "1.0",
            "config_path": config_path,
            "loaded_at": datetime.now().isoformat()
        }
        return workflow_id
    
    def create_workflow(self, workflow_id: str) -> Any:
        return {"id": workflow_id, "type": "mock"}
    
    def run_workflow(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> WorkflowState:
        # 模拟运行工作流
        if initial_state is None:
            from src.infrastructure.graph.states.workflow import WorkflowState
            initial_state = {"messages": [], "iteration_count": 0}
        return initial_state
    
    async def run_workflow_async(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> WorkflowState:
        # 模拟异步运行工作流
        if initial_state is None:
            from src.infrastructure.graph.states.workflow import WorkflowState
            initial_state = {"messages": [], "iteration_count": 0}
        return initial_state
    
    def stream_workflow(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> Generator[WorkflowState, None, None]:
        # 模拟流式工作流
        if initial_state is None:
            from src.infrastructure.graph.states.workflow import WorkflowState
            initial_state = {"messages": [], "iteration_count": 0}
        yield initial_state
    
    def list_workflows(self) -> List[str]:
        return list(self._workflows.keys())
    
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        return self._configs.get(workflow_id)
    
    def unload_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            if workflow_id in self._configs:
                del self._configs[workflow_id]
            if workflow_id in self._metadata:
                del self._metadata[workflow_id]
            return True
        return False
    
    def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        return {
            "workflow_id": workflow_id,
            "name": self._metadata.get(workflow_id, {}).get("name", "unknown"),
            "nodes": [],
            "edges": [],
            "entry_point": "start"
        }
    
    def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        metadata = self._metadata.get(workflow_id, {})
        return {
            "workflow_id": workflow_id,
            "name": metadata.get("name", "unknown"),
            "version": metadata.get("version", "1.0"),
            "description": "Mock workflow summary",
            "config_path": metadata.get("config_path", ""),
            "checksum": "mock_checksum",
            "loaded_at": metadata.get("loaded_at"),
            "last_used": None,
            "usage_count": 0
        }


class MockSessionStore(ISessionStore):
    """模拟会话存储"""
    
    def __init__(self) -> None:
        self._sessions: Dict[str, Any] = {}
    
    def save_session(self, session_id: str, session_data: dict) -> bool:
        self._sessions[session_id] = session_data
        return True
    
    def get_session(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[dict]:
        return list(self._sessions.values())
    
    def session_exists(self, session_id: str) -> bool:
        return session_id in self._sessions


class MockSessionManager(ISessionManager):
    """模拟会话管理器，用于测试"""
    
    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path or Path("./test_sessions")
        self._sessions: Dict[str, Any] = {}
        self.workflow_manager = MockWorkflowManager()
        self.session_store = MockSessionStore()
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_session(
        self,
        workflow_config_path: str,
        agent_config: Optional[dict[str, Any]] = None,
        initial_state: Optional[AgentState] = None
    ) -> str:
        """创建新会话"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        if initial_state is None:
            initial_state = {
                "messages": [],
                "tool_results": [],
                "iteration_count": 0,
                "max_iterations": 10,
                "start_time": None,
                "current_step": "",
                "workflow_name": "",
                "errors": []
            }
        
        session_metadata = {
            "session_id": session_id,
            "workflow_config_path": workflow_config_path,
            "agent_config": agent_config or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        session_data = {
            "metadata": session_metadata,
            "state": initial_state
        }
        
        self.session_store.save_session(session_id, session_data)
        self._sessions[session_id] = session_data
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话信息"""
        return self.session_store.get_session(session_id)
    
    def restore_session(self, session_id: str) -> Tuple[Any, AgentState]:
        """恢复会话"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            raise ValueError(f"会话 {session_id} 不存在")
        
        metadata = session_data["metadata"]
        config_path = metadata["workflow_config_path"]
        
        # 创建工作流
        workflow_id = self.workflow_manager.load_workflow(config_path)
        workflow = self.workflow_manager.create_workflow(workflow_id)
        
        # 返回工作流和状态
        return workflow, session_data["state"]
    
    def save_session(self, session_id: str, state: AgentState, workflow: Any = None) -> bool:
        """保存会话"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return False
        
        session_data["state"] = state
        session_data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        self.session_store.save_session(session_id, session_data)
        self._sessions[session_id] = session_data
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        result = self.session_store.delete_session(session_id)
        if session_id in self._sessions:
            del self._sessions[session_id]
        return result
    
    def list_sessions(self) -> List[dict[str, Any]]:
        """列出所有会话"""
        return self.session_store.list_sessions()
    
    def get_session_history(self, session_id: str) -> List[dict[str, Any]]:
        """获取会话历史"""
        return []
    
    def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话信息"""
        return self.get_session(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return self.get_session(session_id) is not None
    
    def save_session_with_metrics(self, session_id: str, state: AgentState, 
                                 workflow_metrics: dict[str, Any], workflow: Any = None) -> bool:
        """保存会话状态和工作流指标"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return False
        
        session_data["state"] = state
        session_data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        if "workflow_metrics" not in session_data:
            session_data["workflow_metrics"] = {}
        session_data["workflow_metrics"].update(workflow_metrics)
        
        self.session_store.save_session(session_id, session_data)
        self._sessions[session_id] = session_data
        
        return True


def create_test_components() -> Dict[str, Any]:
    """创建测试所需的组件"""
    # 创建模拟的SessionManager
    session_manager = MockSessionManager()
    
    # 创建模拟的ThreadManager
    from tests.integration.test_sdk_compatibility import MockThreadManager
    thread_manager = MockThreadManager()
    
    # 创建Session-Thread映射器
    session_thread_mapper = MemorySessionThreadMapper(session_manager, thread_manager)
    
    # 创建Checkpoint管理器
    checkpoint_store = MemoryCheckpointStore()
    checkpoint_config = CheckpointConfig(
        enabled=True,
        storage_type="memory",
        auto_save=True,
        save_interval=1,
        max_checkpoints=100
    )
    checkpoint_manager = CheckpointManager(checkpoint_store, checkpoint_config)
    
    # 创建查询管理器
    query_manager = ThreadQueryManager(thread_manager)
    
    return {
        "session_manager": session_manager,
        "thread_manager": thread_manager,
        "session_thread_mapper": session_thread_mapper,
        "checkpoint_manager": checkpoint_manager,
        "query_manager": query_manager
    }