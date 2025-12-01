"""历史Repository接口

定义历史记录数据的存储和检索接口，实现数据访问层的抽象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.core.history.entities import (
        BaseHistoryRecord, WorkflowTokenStatistics,
        RecordType, HistoryQuery
    )


class IHistoryRepository(ABC):
    """历史记录仓库接口
    
    专注于历史记录数据的存储和检索，不包含业务逻辑。
    """
    
    # === 基础CRUD操作 ===
    
    @abstractmethod
    async def save_record(self, record: 'BaseHistoryRecord') -> bool:
        """保存历史记录
        
        Args:
            record: 要保存的历史记录
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def save_records(self, records: List['BaseHistoryRecord']) -> List[bool]:
        """批量保存历史记录
        
        Args:
            records: 要保存的历史记录列表
            
        Returns:
            List[bool]: 每条记录的保存结果
        """
        pass
    
    @abstractmethod
    async def get_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        record_type: Optional['RecordType'] = None,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List['BaseHistoryRecord']:
        """获取历史记录
        
        Args:
            session_id: 会话ID过滤
            workflow_id: 工作流ID过滤
            record_type: 记录类型过滤
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            List[BaseHistoryRecord]: 历史记录列表
        """
        pass
    
    @abstractmethod
    async def get_record_by_id(self, record_id: str) -> Optional['BaseHistoryRecord']:
        """根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            Optional[BaseHistoryRecord]: 历史记录，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional[datetime] = None
    ) -> int:
        """删除历史记录
        
        Args:
            session_id: 会话ID过滤
            workflow_id: 工作流ID过滤
            older_than: 删除早于此时间的记录
            
        Returns:
            int: 删除的记录数量
        """
        pass
    
    @abstractmethod
    async def delete_records_by_query(self, query: 'HistoryQuery') -> int:
        """根据查询条件删除历史记录
        
        Args:
            query: 查询条件对象
            
        Returns:
            int: 删除的记录数量
        """
        pass
    
    # === 统计相关操作 ===
    
    @abstractmethod
    async def get_workflow_token_stats(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List['WorkflowTokenStatistics']:
        """获取工作流Token统计
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            List[WorkflowTokenStatistics]: 统计信息列表
        """
        pass
    
    @abstractmethod
    async def update_workflow_token_stats(
        self,
        stats: 'WorkflowTokenStatistics'
    ) -> bool:
        """更新工作流Token统计
        
        Args:
            stats: 统计信息
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        pass
    
    # === 兼容性方法（向后兼容旧的接口） ===
    
    @abstractmethod
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录
        
        Args:
            entry: 历史记录条目，包含thread_id、timestamp、action等字段
            
        Returns:
            保存的历史记录ID
        """
        pass
    
    @abstractmethod
    async def get_history(self, thread_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录
        
        Args:
            thread_id: 线程ID
            limit: 返回记录数限制
            
        Returns:
            历史记录列表，按时间倒序排列
        """
        pass
    
    @abstractmethod
    async def get_history_by_timerange(
        self,
        thread_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录
        
        Args:
            thread_id: 线程ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            历史记录列表
        """
        pass
    
    @abstractmethod
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录（兼容性方法）
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear_thread_history(self, thread_id: str) -> bool:
        """清空线程的历史记录
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息
        
        Returns:
            统计信息字典，包含总记录数、线程数量等
        """
        pass
    
    @abstractmethod
    async def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取历史记录（兼容性方法）
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            历史记录，如果不存在则返回None
        """
        pass