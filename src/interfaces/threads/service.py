"""线程业务逻辑接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadService(ABC):
    """线程业务服务接口 - 定义线程相关的业务逻辑"""
    
    @abstractmethod
    async def create_thread_with_session(
        self,
        thread_config: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """创建线程并关联会话
        
        Args:
            thread_config: 线程配置
            session_id: 会话ID（可选）
            
        Returns:
            线程ID
        """
        pass
    
    @abstractmethod
    async def fork_thread_from_checkpoint(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支
        
        Args:
            source_thread_id: 源Thread ID
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新分支的Thread ID
        """
        pass
    
    @abstractmethod
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新线程元数据
        
        Args:
            thread_id: 线程ID
            metadata: 新的元数据
            
        Returns:
            更新成功返回True
        """
        pass
    
    @abstractmethod
    async def increment_message_count(self, thread_id: str) -> int:
        """增加消息计数
        
        Args:
            thread_id: 线程ID
            
        Returns:
            更新后的消息数量
        """
        pass
    
    @abstractmethod
    async def increment_checkpoint_count(self, thread_id: str) -> int:
        """增加检查点计数
        
        Args:
            thread_id: 线程ID
            
        Returns:
            更新后的检查点数量
        """
        pass
    
    @abstractmethod
    async def increment_branch_count(self, thread_id: str) -> int:
        """增加分支计数
        
        Args:
            thread_id: 线程ID
            
        Returns:
            更新后的分支数量
        """
        pass
    
    @abstractmethod
    async def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """获取线程摘要信息
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程摘要信息
        """
        pass
    
    @abstractmethod
    async def list_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]:
        """按类型列线程
        
        Args:
            thread_type: 线程类型
            
        Returns:
            线程列表
        """
        pass
    
    @abstractmethod
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证Thread状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            状态有效返回True，无效返回False
        """
        pass
    
    @abstractmethod
    async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool:
        """检查是否可以转换到指定状态
        
        Args:
            thread_id: 线程ID
            new_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        pass