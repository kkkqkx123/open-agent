"""会话业务服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING, Callable
from datetime import datetime

if TYPE_CHECKING:
    from ...core.sessions.entities import UserRequestEntity as UserRequest, UserInteractionEntity as UserInteraction, SessionContext
    from ...core.state import WorkflowState


class ISessionService(ABC):
    """会话业务服务接口"""
    
    # === 会话生命周期管理 ===
    
    @abstractmethod
    async def create_session(self, user_request: 'UserRequest') -> str:
        """创建用户会话
        
        Args:
            user_request: 用户请求信息
            
        Returns:
            创建的会话ID
        """
        pass
    
    @abstractmethod
    async def get_session_context(self, session_id: str) -> Optional['SessionContext']:
        """获取会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话上下文，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话
        
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否存在
        """
        pass
    
    @abstractmethod
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息，如果不存在则返回None
        """
        pass
    
    # === 用户交互管理 ===
    
    @abstractmethod
    async def track_user_interaction(self, session_id: str, interaction: 'UserInteraction') -> None:
        """追踪用户交互
        
        Args:
            session_id: 会话ID
            interaction: 用户交互信息
        """
        pass
    
    @abstractmethod
    async def get_interaction_history(self, session_id: str, limit: Optional[int] = None) -> List['UserInteraction']:
        """获取交互历史
        
        Args:
            session_id: 会话ID
            limit: 返回记录数量限制
            
        Returns:
            交互历史列表
        """
        pass
    
    @abstractmethod
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史记录
        """
        pass
    
    # === 多线程协调 ===
    
    @abstractmethod
    async def coordinate_threads(self, session_id: str, thread_configs: List[Dict[str, Any]]) -> Dict[str, str]:
        """协调多个Thread执行
        
        Args:
            session_id: 会话ID
            thread_configs: Thread配置列表
            
        Returns:
            Thread名称到Thread ID的映射
        """
        pass
    
    # === 工作流执行 ===
    
    @abstractmethod
    async def execute_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """在会话中执行工作流
        
        Args:
            session_id: 会话ID
            thread_name: Thread名称
            config: 执行配置
            
        Returns:
            工作流执行结果
        """
        pass
    
    @abstractmethod
    def stream_workflow_in_session(
        self,
        session_id: str,
        thread_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Callable[[], AsyncGenerator[Dict[str, Any], None]]:
        """在会话中流式执行工作流
        
        Args:
            session_id: 会话ID
            thread_name: Thread名称
            config: 执行配置
            
        Returns:
            返回异步生成器的可调用对象
        """
        pass
    
    # === 会话管理 ===
    
    @abstractmethod
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要信息
        """
        pass
    
    @abstractmethod
    async def create_session_with_threads(
        self,
        workflow_configs: Dict[str, str],
        dependencies: Optional[Dict[str, List[str]]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_states: Optional[Dict[str, WorkflowState]] = None
    ) -> str:
        """创建会话并关联多个Thread（向后兼容）
        
        Args:
            workflow_configs: 工作流配置映射
            dependencies: Thread依赖关系
            agent_config: 代理配置
            initial_states: 初始状态
            
        Returns:
            创建的会话ID
        """
        pass