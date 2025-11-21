"""Sessions核心接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class ISessionCore(ABC):
    """Session核心接口 - 定义Session实体的基础行为"""
    
    @abstractmethod
    def create_session( 
        self, 
        session_id: str,
        graph_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建新的Session实体
        
        Args:
            session_id: 会话唯一标识
            graph_id: 关联的图ID
            thread_id: 关联的线程ID
            metadata: 会话元数据
            config: 会话配置
            
        Returns:
            创建的Session实体数据
        """
        pass
    
    @abstractmethod
    def get_session_status(self, session_data: Dict[str, Any]) -> str:
        """获取会话状态
        
        Args:
            session_data: 会话数据
            
        Returns:
            会话状态
        """
        pass
    
    @abstractmethod
    def update_session_status(self, session_data: Dict[str, Any], new_status: str) -> bool:
        """更新会话状态
        
        Args:
            session_data: 会话数据
            new_status: 新状态
            
        Returns:
            更新成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def can_transition_status(self, session_data: Dict[str, Any], target_status: str) -> bool:
        """检查状态是否可以转换
        
        Args:
            session_data: 当前会话数据
            target_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        pass
    
    @abstractmethod
    def validate_session_data(self, session_data: Dict[str, Any]) -> bool:
        """验证会话数据的有效性
        
        Args:
            session_data: 会话数据
            
        Returns:
            数据有效返回True，无效返回False
        """
        pass