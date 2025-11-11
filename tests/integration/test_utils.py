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
from src.infrastructure.graph.states import WorkflowState
from src.infrastructure.graph.config import WorkflowConfig
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
    
    async def create_session_with_threads(
        self,
        workflow_configs: Dict[str, str],  # 线程名 -> 工作流配置路径
        dependencies: Optional[Dict[str, List[str]]] = None,  # 线程依赖关系
        agent_config: Optional[dict[str, Any]] = None,
        initial_states: Optional[Dict[str, WorkflowState]] = None # 每个线程的初始状态
    ) -> str:
        """原子性创建Session和多个Thread"""
        # 简化实现，只创建一个会话
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # 使用第一个工作流配置
        first_config = next(iter(workflow_configs.values()))
        
        session_metadata = {
            "session_id": session_id,
            "workflow_configs": workflow_configs,
            "thread_info": {},
            "dependencies": dependencies or {},
            "agent_config": agent_config or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        session_data = {
            "metadata": session_metadata,
            "state": {}
        }
        
        self.session_store.save_session(session_id, session_data)
        self._sessions[session_id] = session_data
        
        return session_id
    
    def create_session_legacy(
        self,
        workflow_config_path: str,
        agent_config: Optional[dict[str, Any]] = None,
        initial_state: Optional[WorkflowState] = None
    ) -> str:
        """创建新会话（向后兼容）"""
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
    
    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话信息"""
        return self.session_store.get_session(session_id)
    
    def restore_session(self, session_id: str) -> Tuple[Any, WorkflowState]:
        """恢复会话"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            raise ValueError(f"会话 {session_id} 不存在")
        
        metadata = session_data.get("metadata", {})
        config_path = metadata.get("workflow_config_path")
        
        # 创建工作流
        workflow_id = self.workflow_manager.load_workflow(config_path)
        workflow = self.workflow_manager.create_workflow(workflow_id)
        
        # 返回工作流和状态
        return workflow, session_data.get("state", {})
    
    def save_session(self, session_id: str, state: WorkflowState, workflow: Any = None) -> bool:
        """保存会话"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return False
        
        session_data["state"] = state
        session_data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        self.session_store.save_session(session_id, session_data)
        self._sessions[session_id] = session_data
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        result = self.session_store.delete_session(session_id)
        if session_id in self._sessions:
            del self._sessions[session_id]
        return result
    
    async def list_sessions(self) -> List[dict[str, Any]]:
        """列出所有会话"""
        return self.session_store.list_sessions()
    
    async def get_session_history(self, session_id: str) -> List[dict[str, Any]]:
        """获取会话历史"""
        return []
    
    async def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话信息"""
        return await self.get_session(session_id)
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        session = await self.get_session(session_id)
        return session is not None
    
    def save_session_with_metrics(self, session_id: str, state: WorkflowState, 
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
    
    async def add_thread(self, session_id: str, thread_name: str, config_path: str) -> bool:
        """向Session添加新Thread"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return False
        
        # 简化实现，只返回True
        return True
    
    async def get_threads(self, session_id: str) -> Dict[str, Any]:
        """获取Session的所有Thread信息"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return {}
        
        return session_data.get("metadata", {}).get("thread_info", {})

    # === 新增必需的抽象方法实现 ===

    async def create_session(self, user_request: Any) -> str:  # type: ignore
        """创建用户会话"""
        from src.application.sessions.manager import UserRequest
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session_data = {
            "session_id": session_id,
            "user_id": user_request.user_id if isinstance(user_request, UserRequest) else None,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "interactions": [],
            "thread_ids": []
        }
        self.session_store.save_session(session_id, session_data)
        self._sessions[session_id] = session_data
        return session_id

    async def get_session_context(self, session_id: str) -> Optional[Any]:
        """获取会话上下文"""
        from src.application.sessions.manager import SessionContext
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return None
        
        return SessionContext(
            session_id=session_id,
            user_id=session_data.get("user_id"),
            thread_ids=session_data.get("thread_ids", []),
            status=session_data.get("status", "active"),
            created_at=datetime.fromisoformat(session_data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(session_data.get("updated_at", datetime.now().isoformat())),
            metadata={}
        )

    async def track_user_interaction(self, session_id: str, interaction: Any) -> None:
        """追踪用户交互"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return
        
        if "interactions" not in session_data:
            session_data["interactions"] = []
        
        # 序列化交互对象
        interaction_data = {
            "interaction_id": getattr(interaction, "interaction_id", str(uuid.uuid4())),
            "session_id": session_id,
            "thread_id": getattr(interaction, "thread_id", None),
            "interaction_type": getattr(interaction, "interaction_type", "unknown"),
            "content": getattr(interaction, "content", ""),
            "metadata": getattr(interaction, "metadata", {}),
            "timestamp": getattr(interaction, "timestamp", datetime.now()).isoformat()
        }
        session_data["interactions"].append(interaction_data)
        self.session_store.save_session(session_id, session_data)

    async def get_interaction_history(self, session_id: str, limit: Optional[int] = None) -> List[Any]:
        """获取交互历史"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return []
        
        interactions = session_data.get("interactions", [])
        if limit:
            interactions = interactions[-limit:]
        return interactions

    async def coordinate_threads(self, session_id: str, thread_configs: List[Dict[str, Any]]) -> Dict[str, str]:
        """协调多个Thread执行"""
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            return {}
        
        thread_ids = {}
        for config in thread_configs:
            thread_name = config.get("name", str(uuid.uuid4()))
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
            thread_ids[thread_name] = thread_id
        
        if "thread_ids" not in session_data:
            session_data["thread_ids"] = []
        session_data["thread_ids"].extend(thread_ids.values())
        self.session_store.save_session(session_id, session_data)
        
        return thread_ids

    async def execute_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """在会话中执行工作流"""
        return {"success": True, "session_id": session_id, "thread_name": thread_name}

    async def stream_workflow_in_session(  # type: ignore
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """在会话中流式执行工作流"""
        async def _stream() -> Any:
            yield {"session_id": session_id, "thread_name": thread_name}
        return _stream()