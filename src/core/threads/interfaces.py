"""Threads核心接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadCore(ABC):
    """Thread核心接口 - 定义Thread实体的基础行为"""
    
    @abstractmethod
    def create_thread(
        self,
        thread_id: str,
        graph_id: Optional[str] = None,
        thread_type: str = "main",
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建新的Thread实体
        
        Args:
            thread_id: 线程唯一标识
            graph_id: 关联的图ID
            thread_type: 线程类型
            metadata: 线程元数据
            config: 线程配置
            
        Returns:
            创建的Thread实体数据
        """
        pass
    
    @abstractmethod
    def get_thread_status(self, thread_data: Dict[str, Any]) -> str:
        """获取线程状态
        
        Args:
            thread_data: 线程数据
            
        Returns:
            线程状态
        """
        pass
    
    @abstractmethod
    def update_thread_status(self, thread_data: Dict[str, Any], new_status: str) -> bool:
        """更新线程状态
        
        Args:
            thread_data: 线程数据
            new_status: 新状态
            
        Returns:
            更新成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def can_transition_status(self, thread_data: Dict[str, Any], target_status: str) -> bool:
        """检查状态是否可以转换
        
        Args:
            thread_data: 当前线程数据
            target_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        pass
    
    @abstractmethod
    def validate_thread_data(self, thread_data: Dict[str, Any]) -> bool:
        """验证线程数据的有效性
        
        Args:
            thread_data: 线程数据
            
        Returns:
            数据有效返回True，无效返回False
        """
        pass


class IThreadBranchCore(ABC):
    """Thread分支核心接口 - 定义Thread分支实体的基础行为"""
    
    @abstractmethod
    def create_branch(
        self,
        branch_id: str,
        thread_id: str,
        parent_thread_id: str,
        source_checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建分支实体
        
        Args:
            branch_id: 分支唯一标识
            thread_id: 所属线程ID
            parent_thread_id: 父线程ID
            source_checkpoint_id: 源检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            创建的分支数据
        """
        pass
    
    @abstractmethod
    def validate_branch_data(self, branch_data: Dict[str, Any]) -> bool:
        """验证分支数据的有效性
        
        Args:
            branch_data: 分支数据
            
        Returns:
            数据有效返回True，无效返回False
        """
        pass


class IThreadSnapshotCore(ABC):
    """Thread快照核心接口 - 定义Thread快照实体的基础行为"""
    
    @abstractmethod
    def create_snapshot(
        self,
        snapshot_id: str,
        thread_id: str,
        checkpoint_id: str,
        snapshot_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建快照实体
        
        Args:
            snapshot_id: 快照唯一标识
            thread_id: 所属线程ID
            checkpoint_id: 关联的检查点ID
            snapshot_data: 快照数据
            metadata: 快照元数据
            
        Returns:
            创建的快照数据
        """
        pass
    
    @abstractmethod
    def validate_snapshot_data(self, snapshot_data: Dict[str, Any]) -> bool:
        """验证快照数据的有效性
        
        Args:
            snapshot_data: 快照数据
            
        Returns:
            数据有效返回True，无效返回False
        """
        pass