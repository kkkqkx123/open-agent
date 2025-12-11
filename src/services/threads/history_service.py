"""线程历史记录管理服务"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.history import IHistoryManager
from src.core.history.entities import RecordType
from .base_service import BaseThreadService

logger = get_logger(__name__)


@dataclass
class HistoryFilters:
    """历史记录过滤器"""
    record_type: Optional[RecordType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    model: Optional[str] = None


@dataclass
class ThreadOperation:
    """线程操作记录"""
    operation_id: str
    thread_id: str
    operation_type: str
    description: str
    metadata: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None


class ThreadHistoryService(BaseThreadService):
    """线程历史记录管理服务"""
    
    def __init__(
        self,
        thread_repository: IThreadRepository,
        history_manager: Optional[IHistoryManager] = None
    ):
        """初始化历史服务
        
        Args:
            thread_repository: 线程仓储接口
            history_manager: 历史管理器（可选）
        """
        super().__init__(thread_repository)
        self._history_manager = history_manager
        self._operation_store: Dict[str, List[ThreadOperation]] = {}  # 简化存储，实际应使用数据库
    
    async def get_thread_history(self, thread_id: str, filters: Optional[HistoryFilters] = None) -> List[Dict[str, Any]]:
        """获取线程历史记录
        
        Args:
            thread_id: 线程ID
            filters: 过滤条件
            
        Returns:
            历史记录列表
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                logger.warning(f"Thread {thread_id} not found")
                return []
            
            # 使用默认过滤器
            if not filters:
                filters = HistoryFilters()
            
            # 如果有history_manager，使用它查询历史记录
            if self._history_manager:
                history_result = await self._history_manager.query_history_by_thread(
                    thread_id=thread_id,
                    limit=filters.limit,
                    offset=filters.offset,
                    record_type=filters.record_type,
                    start_time=filters.start_time,
                    end_time=filters.end_time,
                    model=filters.model
                )
                
                # 将历史记录转换为字典格式
                history_list = []
                for record in history_result.records:
                    record_dict = record.to_dict()
                    history_list.append(record_dict)
                
                return history_list
            
            # 如果没有history_manager，返回操作历史
            return await self._get_operation_history(thread_id, filters)
            
        except Exception as e:
            logger.error(f"获取线程历史记录失败: {e}")
            return []
    
    async def get_branch_history(self, branch_id: str, filters: Optional[HistoryFilters] = None) -> List[Dict[str, Any]]:
        """获取分支历史记录
        
        Args:
            branch_id: 分支ID
            filters: 过滤条件
            
        Returns:
            历史记录列表
        """
        try:
            # 使用默认过滤器
            if not filters:
                filters = HistoryFilters()
            
            # 如果有history_manager，使用它查询分支历史
            if self._history_manager:
                # 假设分支ID可以作为thread_id查询
                history_result = await self._history_manager.query_history_by_thread(
                    thread_id=branch_id,
                    limit=filters.limit,
                    offset=filters.offset,
                    record_type=filters.record_type,
                    start_time=filters.start_time,
                    end_time=filters.end_time,
                    model=filters.model
                )
                
                # 将历史记录转换为字典格式
                history_list = []
                for record in history_result.records:
                    record_dict = record.to_dict()
                    history_list.append(record_dict)
                
                return history_list
            
            # 如果没有history_manager，返回空列表
            logger.warning("History manager not available, returning empty branch history")
            return []
            
        except Exception as e:
            logger.error(f"获取分支历史记录失败: {e}")
            return []
    
    async def record_operation(self, operation: ThreadOperation) -> None:
        """记录线程操作
        
        Args:
            operation: 操作记录
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(operation.thread_id)
            if not thread:
                logger.warning(f"Thread {operation.thread_id} not found, cannot record operation")
                return
            
            # 存储操作记录
            if operation.thread_id not in self._operation_store:
                self._operation_store[operation.thread_id] = []
            
            self._operation_store[operation.thread_id].append(operation)
            
            # 如果有history_manager，也记录到历史管理器
            if self._history_manager:
                from src.core.history.entities import MessageRecord
                
                # 创建消息记录来表示操作
                message_record = MessageRecord(
                    record_id=f"op_{operation.operation_id}",
                    session_id=operation.thread_id,  # 使用thread_id作为session_id
                    workflow_id=operation.thread_id,
                    role="system",
                    content=f"Operation: {operation.operation_type} - {operation.description}",
                    metadata={
                        "operation_id": operation.operation_id,
                        "operation_type": operation.operation_type,
                        "user_id": operation.user_id,
                        **operation.metadata
                    }
                )
                
                await self._history_manager.record_message(message_record)
            
            logger.info(f"Recorded operation {operation.operation_id} for thread {operation.thread_id}")
            
        except Exception as e:
            logger.error(f"记录线程操作失败: {e}")
    
    async def get_operation_timeline(self, thread_id: str) -> List[ThreadOperation]:
        """获取操作时间线
        
        Args:
            thread_id: 线程ID
            
        Returns:
            操作时间线
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                logger.warning(f"Thread {thread_id} not found")
                return []
            
            # 获取操作记录
            operations = self._operation_store.get(thread_id, [])
            
            # 按时间排序
            operations.sort(key=lambda op: op.timestamp)
            
            return operations
            
        except Exception as e:
            logger.error(f"获取操作时间线失败: {e}")
            return []
    
    async def get_thread_statistics(self, thread_id: str) -> Dict[str, Any]:
        """获取线程统计信息
        
        Args:
            thread_id: 线程ID
            
        Returns:
            统计信息
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                logger.warning(f"Thread {thread_id} not found")
                return {}
            
            # 基本统计信息
            stats = {
                "thread_id": thread_id,
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "message_count": thread.message_count,
                "checkpoint_count": thread.checkpoint_count,
                "branch_count": thread.branch_count,
                "status": thread.status
            }
            
            # 操作统计
            operations = self._operation_store.get(thread_id, [])
            if operations:
                operation_types: Dict[str, int] = {}
                for op in operations:
                    op_type = op.operation_type
                    operation_types[op_type] = operation_types.get(op_type, 0) + 1
                
                stats["operation_count"] = len(operations)
                stats["operation_types"] = operation_types
                stats["last_operation"] = operations[-1].timestamp.isoformat()
            
            # 如果有history_manager，获取更详细的统计
            if self._history_manager:
                try:
                    token_stats = await self._history_manager.get_token_statistics(thread_id)
                    stats["token_statistics"] = token_stats
                    
                    cost_stats = await self._history_manager.get_cost_statistics(thread_id)
                    stats["cost_statistics"] = cost_stats
                    
                    llm_stats = await self._history_manager.get_llm_statistics(thread_id)
                    stats["llm_statistics"] = llm_stats
                except Exception as e:
                    logger.warning(f"Failed to get history manager statistics: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"获取线程统计信息失败: {e}")
            return {}
    
    async def cleanup_old_history(self, thread_id: str, days_to_keep: int = 30) -> int:
        """清理旧历史记录
        
        Args:
            thread_id: 线程ID
            days_to_keep: 保留天数
            
        Returns:
            清理的记录数量
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                logger.warning(f"Thread {thread_id} not found")
                return 0
            
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            
            # 清理操作记录
            operations = self._operation_store.get(thread_id, [])
            original_count = len(operations)
            
            # 过滤掉旧记录
            filtered_operations = [op for op in operations if op.timestamp > cutoff_time]
            self._operation_store[thread_id] = filtered_operations
            
            cleaned_count = original_count - len(filtered_operations)
            
            # 如果有history_manager，也清理历史记录
            if self._history_manager:
                try:
                    from src.core.history.entities import HistoryQuery
                    
                    query = HistoryQuery(
                        session_id=thread_id,
                        end_time=cutoff_time
                    )
                    
                    delete_result = await self._history_manager.delete_history(query)
                    cleaned_count += delete_result.deleted_count
                    
                except Exception as e:
                    logger.warning(f"Failed to cleanup history manager records: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old history records for thread {thread_id}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧历史记录失败: {e}")
            return 0
    
    async def _get_operation_history(self, thread_id: str, filters: HistoryFilters) -> List[Dict[str, Any]]:
        """获取操作历史（当没有history_manager时使用）
        
        Args:
            thread_id: 线程ID
            filters: 过滤条件
            
        Returns:
            操作历史列表
        """
        operations = self._operation_store.get(thread_id, [])
        
        # 应用过滤器
        if filters.start_time:
            operations = [op for op in operations if op.timestamp >= filters.start_time]
        
        if filters.end_time:
            operations = [op for op in operations if op.timestamp <= filters.end_time]
        
        # 按时间排序
        operations.sort(key=lambda op: op.timestamp, reverse=True)
        
        # 应用分页
        start_idx = filters.offset
        end_idx = start_idx + filters.limit
        operations = operations[start_idx:end_idx]
        
        # 转换为字典格式
        return [
            {
                "record_id": f"op_{op.operation_id}",
                "thread_id": op.thread_id,
                "operation_type": op.operation_type,
                "description": op.description,
                "metadata": op.metadata,
                "timestamp": op.timestamp.isoformat(),
                "user_id": op.user_id,
                "record_type": "operation"
            }
            for op in operations
        ]