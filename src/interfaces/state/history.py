"""状态历史管理接口定义

定义状态历史管理相关的接口，包括历史记录、查询和回放功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

# 使用接口定义，遵循分层架构
from .entities import IStateHistoryEntry


class IStateHistoryManager(ABC):
    """状态历史管理器接口
    
    负责管理状态变更历史，包括记录、查询和回放功能。
    """
    
    @abstractmethod
    def record_state_change(self, thread_id: str, old_state: Dict[str, Any],
                          new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化
        
        Args:
            thread_id: 线程ID
            old_state: 旧状态
            new_state: 新状态
            action: 执行的动作
            
        Returns:
            历史记录ID
        """
        pass
    
    @abstractmethod
    def get_state_history(self, thread_id: str, limit: Optional[int] = None) -> List[IStateHistoryEntry]:
        """获取线程的状态历史
        
        Args:
            thread_id: 线程ID
            limit: 返回记录的数量限制
            
        Returns:
            状态历史记录列表
        """
        pass
    
    @abstractmethod
    def replay_history(self, thread_id: str, base_state: Dict[str, Any],
                      until_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """重放历史记录到指定时间点
        
        Args:
            thread_id: 线程ID
            base_state: 基础状态
            until_timestamp: 重放到的指定时间点
            
        Returns:
            重放后的状态
        """
        pass
    
    @abstractmethod
    def cleanup_old_entries(self, thread_id: str, max_entries: int = 1000) -> int:
        """清理旧的历史记录
        
        Args:
            thread_id: 线程ID
            max_entries: 保留的最大记录数
            
        Returns:
            清理的记录数量
        """
        pass