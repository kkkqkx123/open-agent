"""存储事务管理器

提供统一的存储事务管理功能。
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import threading


class TransactionState(Enum):
    """事务状态枚举"""
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class OperationType(Enum):
    """操作类型枚举"""
    SAVE = "save"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_SAVE = "batch_save"
    BATCH_DELETE = "batch_delete"


@dataclass
class TransactionOperation:
    """事务操作数据类"""
    operation_id: str
    operation_type: OperationType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    executed: bool = False
    result: Any = None
    error: Optional[Exception] = None


@dataclass
class Transaction:
    """事务数据类"""
    transaction_id: str
    state: TransactionState = TransactionState.ACTIVE
    operations: List[TransactionOperation] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_operation(self, operation: TransactionOperation) -> None:
        """添加操作到事务"""
        self.operations.append(operation)
        self.updated_at = time.time()
    
    def mark_executed(self, operation_id: str, result: Any = None) -> None:
        """标记操作已执行"""
        for op in self.operations:
            if op.operation_id == operation_id:
                op.executed = True
                op.result = result
                self.updated_at = time.time()
                break
    
    def mark_failed(self, operation_id: str, error: Exception) -> None:
        """标记操作失败"""
        for op in self.operations:
            if op.operation_id == operation_id:
                op.executed = True
                op.error = error
                self.state = TransactionState.FAILED
                self.updated_at = time.time()
                break


class TransactionManager:
    """事务管理器
    
    提供事务的创建、执行、提交和回滚功能。
    """
    
    def __init__(
        self,
        max_concurrent_transactions: int = 100,
        transaction_timeout: float = 300.0,  # 5分钟
        auto_cleanup_interval: float = 60.0  # 1分钟
    ) -> None:
        """初始化事务管理器
        
        Args:
            max_concurrent_transactions: 最大并发事务数
            transaction_timeout: 事务超时时间（秒）
            auto_cleanup_interval: 自动清理间隔（秒）
        """
        self.max_concurrent_transactions = max_concurrent_transactions
        self.transaction_timeout = transaction_timeout
        self.auto_cleanup_interval = auto_cleanup_interval
        
        # 活动事务
        self._active_transactions: Dict[str, Transaction] = {}
        
        # 事务历史
        self._transaction_history: List[Transaction] = []
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """启动事务管理器"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
    
    async def stop(self) -> None:
        """停止事务管理器"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None
            
            # 回滚所有活动事务
            for transaction in list(self._active_transactions.values()):
                await self.rollback_transaction(transaction.transaction_id)
    
    def create_transaction(
        self,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建新事务
        
        Args:
            metadata: 事务元数据
            
        Returns:
            事务ID
            
        Raises:
            RuntimeError: 超过最大并发事务数
        """
        with self._lock:
            if len(self._active_transactions) >= self.max_concurrent_transactions:
                raise RuntimeError(
                    f"Maximum concurrent transactions ({self.max_concurrent_transactions}) exceeded"
                )
            
            transaction_id = str(uuid.uuid4())
            transaction = Transaction(
                transaction_id=transaction_id,
                metadata=metadata or {}
            )
            
            self._active_transactions[transaction_id] = transaction
            return transaction_id
    
    def add_operation(
        self,
        transaction_id: str,
        operation_type: Union[OperationType, str],
        data: Dict[str, Any]
    ) -> str:
        """添加操作到事务
        
        Args:
            transaction_id: 事务ID
            operation_type: 操作类型
            data: 操作数据
            
        Returns:
            操作ID
            
        Raises:
            ValueError: 事务不存在或状态无效
        """
        with self._lock:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.state != TransactionState.ACTIVE:
                raise ValueError(
                    f"Transaction {transaction_id} is not active (state: {transaction.state})"
                )
            
            if isinstance(operation_type, str):
                operation_type = OperationType(operation_type)
            
            operation_id = str(uuid.uuid4())
            operation = TransactionOperation(
                operation_id=operation_id,
                operation_type=operation_type,
                data=data
            )
            
            transaction.add_operation(operation)
            return operation_id
    
    async def execute_transaction(
        self,
        transaction_id: str,
        executor: Callable[[List[TransactionOperation]], Any]
    ) -> Any:
        """执行事务
        
        Args:
            transaction_id: 事务ID
            executor: 事务执行器函数
            
        Returns:
            执行结果
            
        Raises:
            ValueError: 事务不存在或状态无效
            Exception: 执行失败
        """
        with self._lock:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.state != TransactionState.ACTIVE:
                raise ValueError(
                    f"Transaction {transaction_id} is not active (state: {transaction.state})"
                )
        
        try:
            # 执行事务
            result = await executor(transaction.operations)
            
            # 标记事务为已提交
            with self._lock:
                transaction.state = TransactionState.COMMITTED
                transaction.updated_at = time.time()
                
                # 移动到历史记录
                self._transaction_history.append(transaction)
                self._active_transactions.pop(transaction_id, None)
            
            return result
            
        except Exception as e:
            # 标记事务为失败
            with self._lock:
                transaction.state = TransactionState.FAILED
                transaction.updated_at = time.time()
            
            # 自动回滚
            await self.rollback_transaction(transaction_id)
            raise
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """提交事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否提交成功
        """
        with self._lock:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                return False
            
            if transaction.state != TransactionState.ACTIVE:
                return False
            
            transaction.state = TransactionState.COMMITTED
            transaction.updated_at = time.time()
            
            # 移动到历史记录
            self._transaction_history.append(transaction)
            self._active_transactions.pop(transaction_id, None)
            
            return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """回滚事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否回滚成功
        """
        with self._lock:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                return False
            
            transaction.state = TransactionState.ROLLED_BACK
            transaction.updated_at = time.time()
            
            # 移动到历史记录
            self._transaction_history.append(transaction)
            self._active_transactions.pop(transaction_id, None)
            
            return True
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """获取事务信息
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            事务对象，如果不存在则返回None
        """
        with self._lock:
            # 先查找活动事务
            transaction = self._active_transactions.get(transaction_id)
            if transaction:
                return transaction
            
            # 再查找历史事务
            for hist_transaction in self._transaction_history:
                if hist_transaction.transaction_id == transaction_id:
                    return hist_transaction
            
            return None
    
    def get_active_transactions(self) -> List[Transaction]:
        """获取所有活动事务
        
        Returns:
            活动事务列表
        """
        with self._lock:
            return list(self._active_transactions.values())
    
    def get_transaction_history(
        self,
        limit: Optional[int] = None,
        state_filter: Optional[TransactionState] = None
    ) -> List[Transaction]:
        """获取事务历史
        
        Args:
            limit: 限制返回数量
            state_filter: 状态过滤器
            
        Returns:
            事务历史列表
        """
        with self._lock:
            history = self._transaction_history.copy()
            
            # 应用状态过滤器
            if state_filter:
                history = [t for t in history if t.state == state_filter]
            
            # 按时间倒序排序
            history.sort(key=lambda t: t.updated_at, reverse=True)
            
            # 应用数量限制
            if limit:
                history = history[:limit]
            
            return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取事务统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            stats = {
                "active_transactions": len(self._active_transactions),
                "total_history": len(self._transaction_history),
                "max_concurrent": self.max_concurrent_transactions,
                "timeout": self.transaction_timeout,
                "state_counts": {},
                "operation_counts": {},
            }
            
            # 统计状态分布
            for transaction in self._transaction_history:
                state_name = transaction.state.value
                stats["state_counts"][state_name] = stats["state_counts"].get(state_name, 0) + 1
                
                # 统计操作类型分布
                for operation in transaction.operations:
                    op_type = operation.operation_type.value
                    stats["operation_counts"][op_type] = stats["operation_counts"].get(op_type, 0) + 1
            
            return stats
    
    async def _cleanup_worker(self) -> None:
        """清理工作线程"""
        while self._running:
            try:
                await asyncio.sleep(self.auto_cleanup_interval)
                await self._cleanup_expired_transactions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但继续运行
                print(f"Error in transaction cleanup worker: {e}")
    
    async def _cleanup_expired_transactions(self) -> None:
        """清理过期事务"""
        current_time = time.time()
        expired_transactions = []
        
        with self._lock:
            for transaction_id, transaction in self._active_transactions.items():
                if current_time - transaction.created_at > self.transaction_timeout:
                    expired_transactions.append(transaction_id)
            
            for transaction_id in expired_transactions:
                await self.rollback_transaction(transaction_id)


class TransactionContext:
    """事务上下文管理器
    
    用于自动管理事务生命周期的上下文管理器。
    """
    
    def __init__(
        self,
        transaction_manager: TransactionManager,
        executor: Callable[[List[TransactionOperation]], Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化事务上下文
        
        Args:
            transaction_manager: 事务管理器
            executor: 事务执行器
            metadata: 事务元数据
        """
        self.transaction_manager = transaction_manager
        self.executor = executor
        self.metadata = metadata
        self.transaction_id = None
    
    async def __aenter__(self) -> 'TransactionContext':
        """进入异步上下文"""
        self.transaction_id = self.transaction_manager.create_transaction(self.metadata)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出异步上下文"""
        if self.transaction_id is None:
            return
        
        if exc_type is None:
            # 没有异常，尝试提交
            await self.transaction_manager.commit_transaction(self.transaction_id)
        else:
            # 有异常，回滚事务
            await self.transaction_manager.rollback_transaction(self.transaction_id)
    
    def add_operation(
        self,
        operation_type: Union[OperationType, str],
        data: Dict[str, Any]
    ) -> str:
        """添加操作到事务
        
        Args:
            operation_type: 操作类型
            data: 操作数据
            
        Returns:
            操作ID
        """
        if self.transaction_id is None:
            raise RuntimeError("Transaction not started")
        
        return self.transaction_manager.add_operation(
            self.transaction_id,
            operation_type,
            data
        )
    
    async def execute(self) -> Any:
        """执行事务
        
        Returns:
            执行结果
        """
        if self.transaction_id is None:
            raise RuntimeError("Transaction not started")
        
        return await self.transaction_manager.execute_transaction(
            self.transaction_id,
            self.executor
        )