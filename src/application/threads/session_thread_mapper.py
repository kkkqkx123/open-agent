"""Session与Thread映射管理器"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json
import logging

from ...domain.threads.interfaces import IThreadManager
from ...application.sessions.manager import ISessionManager
from ...infrastructure.graph.state import AgentState
from ...infrastructure.threads.metadata_store import IThreadMetadataStore

logger = logging.getLogger(__name__)


class ISessionThreadMapper(ABC):
    """Session-Thread映射器接口"""
    
    @abstractmethod
    async def create_session_with_thread(
        self,
        workflow_config_path: str,
        thread_metadata: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Any] = None
    ) -> Tuple[str, str]:
        """同时创建Session和Thread
        
        Args:
            workflow_config_path: 工作流配置路径
            thread_metadata: Thread元数据
            agent_config: Agent配置
            initial_state: 初始状态
            
        Returns:
            Tuple[str, str]: (session_id, thread_id)
        """
        pass
    
    @abstractmethod
    async def get_thread_for_session(self, session_id: str) -> Optional[str]:
        """获取Session对应的Thread ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[str]: Thread ID，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_session_for_thread(self, thread_id: str) -> Optional[str]:
        """获取Thread对应的Session ID
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Optional[str]: Session ID，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_mapping(self, session_id: str) -> bool:
        """删除映射关系
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_mappings(self) -> List[Dict[str, Any]]:
        """列出所有映射关系
        
        Returns:
            List[Dict[str, Any]]: 映射关系列表
        """
        pass
    
    @abstractmethod
    async def mapping_exists(self, session_id: str, thread_id: str) -> bool:
        """检查映射关系是否存在
        
        Args:
            session_id: Session ID
            thread_id: Thread ID
            
        Returns:
            bool: 映射关系是否存在
        """
        pass

    @abstractmethod
    async def fork_session_with_thread(
        self,
        source_session_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> Tuple[str, str]:
        """从现有session和thread创建分支"""
        pass

    @abstractmethod
    async def get_session_branches(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """获取session的所有分支"""
        pass


class SessionThreadMapper(ISessionThreadMapper):
    """Session与Thread映射管理器实现"""
    
    def __init__(
        self,
        session_manager: ISessionManager,
        thread_manager: IThreadManager,
        storage_path: Optional[Path] = None
    ):
        """初始化映射管理器
        
        Args:
            session_manager: Session管理器
            thread_manager: Thread管理器
            storage_path: 映射关系存储路径，如果为None则使用内存存储
        """
        self.session_manager = session_manager
        self.thread_manager = thread_manager
        self.storage_path = storage_path
        
        # 映射关系存储
        self._mappings: Dict[str, str] = {}  # session_id -> thread_id
        self._reverse_mappings: Dict[str, str] = {}  # thread_id -> session_id
        
        # 如果指定了存储路径，加载现有映射
        if storage_path:
            self._load_mappings()
    
    async def create_session_with_thread(
        self,
        workflow_config_path: str,
        thread_metadata: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Any] = None
    ) -> Tuple[str, str]:
        """同时创建Session和Thread"""
        # 创建Session
        session_id = self.session_manager.create_session(
            workflow_config_path,
            agent_config,
            initial_state
        )
        
        # 提取graph_id（从工作流配置路径）
        graph_id = self._extract_graph_id(workflow_config_path)
        
        # 创建Thread
        thread_id = await self.thread_manager.create_thread(
            graph_id,
            thread_metadata or {}
        )
        
        # 建立双向映射
        self._mappings[session_id] = thread_id
        self._reverse_mappings[thread_id] = session_id
        
        # 保存映射关系
        if self.storage_path:
            self._save_mappings()
        
        logger.info(f"创建Session-Thread映射成功: session={session_id}, thread={thread_id}")
        return session_id, thread_id
    
    async def get_thread_for_session(self, session_id: str) -> Optional[str]:
        """获取Session对应的Thread ID"""
        return self._mappings.get(session_id)
    
    async def get_session_for_thread(self, thread_id: str) -> Optional[str]:
        """获取Thread对应的Session ID"""
        return self._reverse_mappings.get(thread_id)
    
    async def delete_mapping(self, session_id: str) -> bool:
        """删除映射关系"""
        thread_id = self._mappings.get(session_id)
        if not thread_id:
            logger.warning(f"Session映射不存在: {session_id}")
            return False
        
        # 删除双向映射
        del self._mappings[session_id]
        if thread_id in self._reverse_mappings:
            del self._reverse_mappings[thread_id]
        
        # 保存更改
        if self.storage_path:
            self._save_mappings()
        
        logger.info(f"删除Session-Thread映射成功: session={session_id}, thread={thread_id}")
        return True
    
    async def list_mappings(self) -> List[Dict[str, Any]]:
        """列出所有映射关系"""
        mappings = []
        for session_id, thread_id in self._mappings.items():
            mappings.append({
                "session_id": session_id,
                "thread_id": thread_id,
                "created_at": datetime.now().isoformat()  # 这里可以扩展为存储创建时间
            })
        return mappings
    
    async def mapping_exists(self, session_id: str, thread_id: str) -> bool:
        """检查映射关系是否存在"""
        return (
            self._mappings.get(session_id) == thread_id and
            self._reverse_mappings.get(thread_id) == session_id
        )
    
    def _extract_graph_id(self, workflow_config_path: str) -> str:
        """从工作流配置路径提取graph ID"""
        # 实现逻辑：从路径中提取文件名作为graph ID
        from pathlib import Path
        return Path(workflow_config_path).stem
    
    def _save_mappings(self) -> None:
        """保存映射关系到文件"""
        if not self.storage_path:
            return
        
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            mappings_file = self.storage_path / "session_thread_mappings.json"
            
            mappings_data = {
                "mappings": self._mappings,
                "reverse_mappings": self._reverse_mappings,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(mappings_file, 'w', encoding='utf-8') as f:
                json.dump(mappings_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存映射关系失败: {e}")
    
    def _load_mappings(self) -> None:
        """从文件加载映射关系"""
        if not self.storage_path:
            return
        
        try:
            mappings_file = self.storage_path / "session_thread_mappings.json"
            if not mappings_file.exists():
                return
            
            with open(mappings_file, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
            
            self._mappings = mappings_data.get("mappings", {})
            self._reverse_mappings = mappings_data.get("reverse_mappings", {})
            
            logger.debug(f"加载映射关系成功: {len(self._mappings)} 个映射")
            
        except Exception as e:
            logger.error(f"加载映射关系失败: {e}")
            # 如果加载失败，使用空映射
            self._mappings = {}
            self._reverse_mappings = {}
    
    async def fork_session_with_thread(
        self,
        source_session_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> Tuple[str, str]:
        """从现有session和thread创建分支"""
        # 获取源thread ID
        source_thread_id = await self.get_thread_for_session(source_session_id)
        if not source_thread_id:
            raise ValueError(f"源session不存在对应的thread: {source_session_id}")
        
        # 获取源session信息
        source_session = self.session_manager.get_session(source_session_id)
        if not source_session:
            raise ValueError(f"源session不存在: {source_session_id}")
        
        # 使用ThreadManager创建分支
        new_thread_id = await self.thread_manager.fork_thread(
            source_thread_id,
            checkpoint_id,
            branch_name,
            metadata={"source_session_id": source_session_id}
        )
        
        # 创建新的session（基于源session的配置）
        thread_state = await self.thread_manager.get_thread_state(new_thread_id)
        initial_state = None
        if thread_state:
            # 将字典状态转换为AgentState TypedDict
            initial_state = AgentState(
                messages=thread_state.get("messages", []),
                metadata=thread_state.get("metadata", {}),
                input=thread_state.get("input", ""),
                output=thread_state.get("output"),
                tool_calls=thread_state.get("tool_calls", []),
                tool_results=thread_state.get("tool_results", []),
                iteration_count=thread_state.get("iteration_count", 0),
                max_iterations=thread_state.get("max_iterations", 10),
                errors=thread_state.get("errors", []),
                complete=thread_state.get("complete", False),
                start_time=thread_state.get("start_time"),
                current_step=thread_state.get("current_step"),
                workflow_name=thread_state.get("workflow_name")
            )
        
        new_session_id = self.session_manager.create_session(
            source_session.get("workflow_config_path", ""),
            source_session.get("agent_config"),
            initial_state
        )
        
        # 建立新的映射关系
        self._mappings[new_session_id] = new_thread_id
        self._reverse_mappings[new_thread_id] = new_session_id
        
        # 保存映射关系
        if self.storage_path:
            self._save_mappings()
        
        logger.info(f"创建分支Session-Thread映射成功: session={new_session_id}, thread={new_thread_id}")
        return new_session_id, new_thread_id
    
    async def get_session_branches(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """获取session的所有分支"""
        thread_id = await self.get_thread_for_session(session_id)
        if not thread_id:
            return []
        
        # 获取thread的所有分支
        branches = await self.thread_manager.get_thread_history(thread_id)
        
        # 转换为session分支信息
        session_branches = []
        for branch in branches:
            if isinstance(branch, dict) and branch.get("metadata", {}).get("branch_type") == "fork":
                session_branches.append({
                    "branch_id": branch.get("id"),
                    "session_id": session_id,
                    "thread_id": thread_id,
                    "branch_name": branch.get("metadata", {}).get("branch_name"),
                    "created_at": branch.get("created_at"),
                    "source_checkpoint_id": branch.get("metadata", {}).get("source_checkpoint_id")
                })
        
        return session_branches


class MemorySessionThreadMapper(ISessionThreadMapper):
    """基于内存的Session-Thread映射管理器（主要用于测试）"""
    
    def __init__(
        self,
        session_manager: ISessionManager,
        thread_manager: IThreadManager
    ):
        """初始化内存映射管理器
        
        Args:
            session_manager: Session管理器
            thread_manager: Thread管理器
        """
        self.session_manager = session_manager
        self.thread_manager = thread_manager
        
        # 映射关系存储
        self._mappings: Dict[str, str] = {}  # session_id -> thread_id
        self._reverse_mappings: Dict[str, str] = {}  # thread_id -> session_id
    
    async def create_session_with_thread(
        self,
        workflow_config_path: str,
        thread_metadata: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Any] = None
    ) -> Tuple[str, str]:
        """同时创建Session和Thread"""
        # 创建Session
        session_id = self.session_manager.create_session(
            workflow_config_path,
            agent_config,
            initial_state
        )
        
        # 提取graph_id（从工作流配置路径）
        graph_id = self._extract_graph_id(workflow_config_path)
        
        # 创建Thread
        thread_id = await self.thread_manager.create_thread(
            graph_id,
            thread_metadata or {}
        )
        
        # 建立双向映射
        self._mappings[session_id] = thread_id
        self._reverse_mappings[thread_id] = session_id
        
        logger.info(f"创建Session-Thread映射成功: session={session_id}, thread={thread_id}")
        return session_id, thread_id
    
    async def get_thread_for_session(self, session_id: str) -> Optional[str]:
        """获取Session对应的Thread ID"""
        return self._mappings.get(session_id)
    
    async def get_session_for_thread(self, thread_id: str) -> Optional[str]:
        """获取Thread对应的Session ID"""
        return self._reverse_mappings.get(thread_id)
    
    async def delete_mapping(self, session_id: str) -> bool:
        """删除映射关系"""
        thread_id = self._mappings.get(session_id)
        if not thread_id:
            logger.warning(f"Session映射不存在: {session_id}")
            return False
        
        # 删除双向映射
        del self._mappings[session_id]
        if thread_id in self._reverse_mappings:
            del self._reverse_mappings[thread_id]
        
        logger.info(f"删除Session-Thread映射成功: session={session_id}, thread={thread_id}")
        return True
    
    async def list_mappings(self) -> List[Dict[str, Any]]:
        """列出所有映射关系"""
        mappings = []
        for session_id, thread_id in self._mappings.items():
            mappings.append({
                "session_id": session_id,
                "thread_id": thread_id,
                "created_at": datetime.now().isoformat()  # 这里可以扩展为存储创建时间
            })
        return mappings
    
    async def mapping_exists(self, session_id: str, thread_id: str) -> bool:
        """检查映射关系是否存在"""
        return (
            self._mappings.get(session_id) == thread_id and
            self._reverse_mappings.get(thread_id) == session_id
        )
    
    def _extract_graph_id(self, workflow_config_path: str) -> str:
        """从工作流配置路径提取graph ID"""
        # 实现逻辑：从路径中提取文件名作为graph ID
        from pathlib import Path
        return Path(workflow_config_path).stem
    
    def clear(self) -> None:
        """清空所有映射关系（主要用于测试）"""
        self._mappings.clear()
        self._reverse_mappings.clear()
        logger.debug("内存映射关系已清空")
    
    async def fork_session_with_thread(
        self,
        source_session_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> Tuple[str, str]:
        """从现有session和thread创建分支"""
        # 获取源thread ID
        source_thread_id = await self.get_thread_for_session(source_session_id)
        if not source_thread_id:
            raise ValueError(f"源session不存在对应的thread: {source_session_id}")
        
        # 获取源session信息
        source_session = self.session_manager.get_session(source_session_id)
        if not source_session:
            raise ValueError(f"源session不存在: {source_session_id}")
        
        # 使用ThreadManager创建分支
        new_thread_id = await self.thread_manager.fork_thread(
            source_thread_id,
            checkpoint_id,
            branch_name,
            metadata={"source_session_id": source_session_id}
        )
        
        # 创建新的session（基于源session的配置）
        thread_state = await self.thread_manager.get_thread_state(new_thread_id)
        initial_state = None
        if thread_state:
            # 将字典状态转换为AgentState TypedDict
            initial_state = AgentState(
                messages=thread_state.get("messages", []),
                metadata=thread_state.get("metadata", {}),
                input=thread_state.get("input", ""),
                output=thread_state.get("output"),
                tool_calls=thread_state.get("tool_calls", []),
                tool_results=thread_state.get("tool_results", []),
                iteration_count=thread_state.get("iteration_count", 0),
                max_iterations=thread_state.get("max_iterations", 10),
                errors=thread_state.get("errors", []),
                complete=thread_state.get("complete", False),
                start_time=thread_state.get("start_time"),
                current_step=thread_state.get("current_step"),
                workflow_name=thread_state.get("workflow_name")
            )
        
        new_session_id = self.session_manager.create_session(
            source_session.get("workflow_config_path", ""),
            source_session.get("agent_config"),
            initial_state
        )
        
        # 建立新的映射关系
        self._mappings[new_session_id] = new_thread_id
        self._reverse_mappings[new_thread_id] = new_session_id
        
        logger.info(f"创建分支Session-Thread映射成功: session={new_session_id}, thread={new_thread_id}")
        return new_session_id, new_thread_id
    
    async def get_session_branches(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """获取session的所有分支"""
        thread_id = await self.get_thread_for_session(session_id)
        if not thread_id:
            return []
        
        # 获取thread的所有分支
        branches = await self.thread_manager.get_thread_history(thread_id)
        
        # 转换为session分支信息
        session_branches = []
        for branch in branches:
            if isinstance(branch, dict) and branch.get("metadata", {}).get("branch_type") == "fork":
                session_branches.append({
                    "branch_id": branch.get("id"),
                    "session_id": session_id,
                    "thread_id": thread_id,
                    "branch_name": branch.get("metadata", {}).get("branch_name"),
                    "created_at": branch.get("created_at"),
                    "source_checkpoint_id": branch.get("metadata", {}).get("source_checkpoint_id")
                })
        
        return session_branches