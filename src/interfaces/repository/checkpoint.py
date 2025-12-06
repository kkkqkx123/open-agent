"""检查点Repository接口

定义检查点数据的存储和检索接口，实现数据访问层的抽象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class ICheckpointRepository(ABC):
    """检查点仓库接口
    
    专注于检查点数据的存储和检索，不包含业务逻辑。
    """
    
    @abstractmethod
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存检查点
        
        Args:
            checkpoint_data: 检查点数据，包含id、thread_id、workflow_id、state_data等字段
            
        Returns:
            保存的检查点ID
        """
        pass
    
    @abstractmethod
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list_checkpoints(
        self, 
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出指定线程的所有检查点
        
        Args:
            thread_id: 线程ID
            limit: 要返回的最大检查点数
            
        Returns:
            检查点列表，按创建时间倒序排列
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程的最新检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最新检查点，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有检查点
        
        Args:
            thread_id: 线程ID
            workflow_id: 工作流ID
            
        Returns:
            检查点列表，按创建时间倒序排列
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点，保留最新的max_count个
        
        Args:
            thread_id: 线程ID
            max_count: 保留的最大数量
            
        Returns:
            删除的检查点数量
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_statistics(self) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Returns:
            统计信息字典，包含总检查点数、线程数量等
        """
        pass
    
    @abstractmethod
    async def get_checkpoints_by_timerange(
        self, 
        thread_id: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """按时间范围获取检查点
        
        Args:
            thread_id: 线程ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def search_checkpoints(
        self, 
        thread_id: str, 
        query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """搜索检查点
        
        Args:
            thread_id: 线程ID
            query: 搜索条件
            
        Returns:
            符合条件的检查点列表
        """
        pass
    
    @abstractmethod
    async def save_writes(
        self,
        checkpoint_id: str,
        writes: List[tuple[str, Any]],
        task_id: str,
        task_path: str = ""
    ) -> None:
        """保存与检查点关联的中间写入
        
        Args:
            checkpoint_id: 检查点ID
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        pass