"""线程协调器服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadCoordinatorService(ABC):
    """线程协调器业务服务接口 - 定义线程协调相关的业务逻辑"""
    
    @abstractmethod
    async def coordinate_thread_creation(
        self,
        thread_config: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """协调线程创建
        
        Args:
            thread_config: 线程配置
            session_context: 会话上下文
            
        Returns:
            协调结果
        """
        pass
    
    @abstractmethod
    async def coordinate_thread_transition(
        self,
        thread_id: str,
        current_status: str,
        target_status: str,
        transition_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """协调线程状态转换
        
        Args:
            thread_id: 线程ID
            current_status: 当前状态
            target_status: 目标状态
            transition_context: 转换上下文
            
        Returns:
            转换成功返回True
        """
        pass
    
    @abstractmethod
    async def coordinate_checkpoint_creation(
        self,
        thread_id: str,
        checkpoint_config: Dict[str, Any],
        coordination_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """协调检查点创建
        
        Args:
            thread_id: 线程ID
            checkpoint_config: 检查点配置
            coordination_context: 协调上下文
            
        Returns:
            检查点ID
        """
        pass
    
    @abstractmethod
    async def coordinate_thread_recovery(
        self,
        thread_id: str,
        recovery_point: str,
        recovery_strategy: str = "latest_checkpoint"
    ) -> bool:
        """协调线程恢复
        
        Args:
            thread_id: 线程ID
            recovery_point: 恢复点
            recovery_strategy: 恢复策略
            
        Returns:
            恢复成功返回True
        """
        pass
    
    @abstractmethod
    async def get_coordination_status(self, thread_id: str) -> Dict[str, Any]:
        """获取协调状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            协调状态信息
        """
        pass
    
    @abstractmethod
    async def validate_coordination_integrity(self, thread_id: str) -> bool:
        """验证协调完整性
        
        Args:
            thread_id: 线程ID
            
        Returns:
            协调完整返回True，否则返回False
        """
        pass