"""线程协作接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IThreadCollaborationService(ABC):
    """线程协作服务接口 - 负责线程间的协作和交互"""
    
    @abstractmethod
    async def create_collaborative_thread(
        self, 
        graph_id: str, 
        participants: List[str], 
        collaboration_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建协作线程
        
        Args:
            graph_id: 关联的图ID
            participants: 参与者列表
            collaboration_config: 协作配置
            metadata: 线程元数据
            
        Returns:
            新创建的协作线程ID
        """
        pass
    
    @abstractmethod
    async def add_participant(self, thread_id: str, participant_id: str, role: str) -> bool:
        """添加参与者
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            role: 参与者角色
            
        Returns:
            添加成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    async def remove_participant(self, thread_id: str, participant_id: str) -> bool:
        """移除参与者
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            
        Returns:
            移除成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    async def get_thread_participants(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取线程的参与者
        
        Args:
            thread_id: 线程ID
            
        Returns:
            参与者信息列表
        """
        pass
    
    @abstractmethod
    async def update_participant_role(self, thread_id: str, participant_id: str, new_role: str) -> bool:
        """更新参与者角色
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            new_role: 新角色
            
        Returns:
            更新成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    async def get_thread_permissions(self, thread_id: str, participant_id: str) -> Dict[str, Any]:
        """获取参与者在线程中的权限
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            
        Returns:
            权限信息字典
        """
        pass
    
    @abstractmethod
    async def can_participant_access(self, thread_id: str, participant_id: str, action: str) -> bool:
        """检查参与者是否可以执行指定操作
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            action: 操作类型
            
        Returns:
            有权限返回True，否则返回False
        """
        pass