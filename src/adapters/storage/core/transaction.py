"""事务管理器

提供专门的存储事务管理功能。
"""

import asyncio
import logging
import threading
from typing import Optional, Any, Dict, List, Protocol
from contextlib import contextmanager

from src.interfaces.storage import IUnifiedStorage


class ITransactionalStorage(Protocol):
    """事务性存储协议
    
    定义存储后端需要支持的事务方法。
    """
    
    async def begin_transaction(self) -> None:
        """开始事务"""
        ...
    
    async def commit_transaction(self) -> None:
        """提交事务"""
        ...
    
    async def rollback_transaction(self) -> None:
        """回滚事务"""
        ...

logger = logging.getLogger(__name__)


class TransactionManager:
    """专门的事务管理器
    
    管理存储操作的事务生命周期。
    """
    
    def __init__(self, backend: ITransactionalStorage):
        """初始化事务管理器
        
        Args:
            backend: 存储后端
        """
        self._backend = backend
        self._active_transactions = threading.local()
        self._transaction_stack = threading.local()
    
    async def begin_transaction(self) -> str:
        """开始事务
        
        Returns:
            事务ID
        """
        if not hasattr(self._active_transactions, 'active'):
            self._active_transactions.active = []
            self._transaction_stack.stack = []
        
        # 生成事务ID
        transaction_id = f"tx_{id(self)}_{len(self._active_transactions.active)}"
        
        # 如果没有活跃事务，开始新事务
        if not self._active_transactions.active:
            await self._backend.begin_transaction()
            logger.debug(f"Begin new transaction: {transaction_id}")
        else:
            logger.debug(f"Join existing transaction: {transaction_id}")
        
        # 记录事务
        self._active_transactions.active.append(transaction_id)
        self._transaction_stack.stack.append(transaction_id)
        
        return transaction_id
    
    async def commit_transaction(self, transaction_id: Optional[str] = None) -> bool:
        """提交事务
        
        Args:
            transaction_id: 事务ID，如果为None则提交最顶层事务
            
        Returns:
            是否提交成功
        """
        if not hasattr(self._active_transactions, 'active') or not self._active_transactions.active:
            logger.warning("No active transaction to commit")
            return False
        
        if transaction_id is None:
            # 提交最顶层事务
            if self._transaction_stack.stack:
                transaction_id = self._transaction_stack.stack[-1]
            else:
                logger.warning("No transaction in stack to commit")
                return False
        
        if transaction_id not in self._active_transactions.active:
            logger.warning(f"Transaction {transaction_id} not found in active transactions")
            return False
        
        try:
            # 只有最顶层事务才能真正提交
            if (self._transaction_stack.stack and 
                self._transaction_stack.stack[-1] == transaction_id):
                await self._backend.commit_transaction()
                logger.debug(f"Commit transaction: {transaction_id}")
            
            # 从活跃事务列表中移除
            self._active_transactions.active.remove(transaction_id)
            if (hasattr(self._transaction_stack, 'stack') and 
                transaction_id in self._transaction_stack.stack):
                self._transaction_stack.stack.remove(transaction_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to commit transaction {transaction_id}: {e}")
            return False
    
    async def rollback_transaction(self, transaction_id: Optional[str] = None) -> bool:
        """回滚事务
        
        Args:
            transaction_id: 事务ID，如果为None则回滚最顶层事务
            
        Returns:
            是否回滚成功
        """
        if not hasattr(self._active_transactions, 'active') or not self._active_transactions.active:
            logger.warning("No active transaction to rollback")
            return False
        
        if transaction_id is None:
            # 回滚最顶层事务
            if self._transaction_stack.stack:
                transaction_id = self._transaction_stack.stack[-1]
            else:
                logger.warning("No transaction in stack to rollback")
                return False
        
        if transaction_id not in self._active_transactions.active:
            logger.warning(f"Transaction {transaction_id} not found in active transactions")
            return False
        
        try:
            # 只有最顶层事务才能真正回滚
            if (self._transaction_stack.stack and 
                self._transaction_stack.stack[-1] == transaction_id):
                await self._backend.rollback_transaction()
                logger.debug(f"Rollback transaction: {transaction_id}")
            
            # 从活跃事务列表中移除
            self._active_transactions.active.remove(transaction_id)
            if (hasattr(self._transaction_stack, 'stack') and 
                transaction_id in self._transaction_stack.stack):
                self._transaction_stack.stack.remove(transaction_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback transaction {transaction_id}: {e}")
            return False
    
    def is_transaction_active(self) -> bool:
        """检查是否有活跃事务
        
        Returns:
            是否有活跃事务
        """
        return (hasattr(self._active_transactions, 'active') and 
                bool(self._active_transactions.active))
    
    def get_active_transactions(self) -> List[str]:
        """获取活跃事务列表
        
        Returns:
            活跃事务ID列表
        """
        if hasattr(self._active_transactions, 'active'):
            return list(self._active_transactions.active)
        return []
    
    def get_current_transaction(self) -> Optional[str]:
        """获取当前事务ID
        
        Returns:
            当前事务ID，如果没有则返回None
        """
        if (hasattr(self._transaction_stack, 'stack') and 
            self._transaction_stack.stack):
            return self._transaction_stack.stack[-1]
        return None


class TransactionContext:
    """事务上下文管理器
    
    用于自动管理事务生命周期。
    """
    
    def __init__(self, transaction_manager: TransactionManager):
        """初始化事务上下文
        
        Args:
            transaction_manager: 事务管理器
        """
        self._transaction_manager = transaction_manager
        self._transaction_id = None
        self._should_commit = True
    
    async def __aenter__(self) -> 'TransactionContext':
        """进入异步上下文"""
        self._transaction_id = await self._transaction_manager.begin_transaction()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文"""
        if self._transaction_id is None:
            return
        
        if exc_type is not None:
            # 发生异常，回滚事务
            self._should_commit = False
            await self._transaction_manager.rollback_transaction(self._transaction_id)
        else:
            # 正常退出，提交事务
            if self._should_commit:
                await self._transaction_manager.commit_transaction(self._transaction_id)
    
    def rollback(self):
        """标记事务需要回滚"""
        self._should_commit = False
    
    @property
    def transaction_id(self) -> Optional[str]:
        """获取事务ID"""
        return self._transaction_id


@contextmanager
def transaction_context(transaction_manager: TransactionManager):
    """同步事务上下文管理器
    
    Args:
        transaction_manager: 事务管理器
        
    Yields:
        事务上下文
    """
    context = TransactionContext(transaction_manager)
    
    # 在新的事件循环中运行异步上下文
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已经在事件循环中，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, context.__aenter__())
                transaction_context_obj = future.result()
                try:
                    yield transaction_context_obj
                    if transaction_context_obj._should_commit:
                        future = executor.submit(asyncio.run, context.__aexit__(None, None, None))
                    else:
                        future = executor.submit(asyncio.run, context.__aexit__(Exception, Exception("Rollback"), None))
                    future.result()
                except Exception as e:
                    future = executor.submit(asyncio.run, context.__aexit__(Exception, e, None))
                    future.result()
                    raise
        else:
            # 如果没有运行的事件循环，直接运行
            transaction_context_obj = asyncio.run(context.__aenter__())
            try:
                yield transaction_context_obj
                if transaction_context_obj._should_commit:
                    asyncio.run(context.__aexit__(None, None, None))
                else:
                    asyncio.run(context.__aexit__(Exception, Exception("Rollback"), None))
            except Exception as e:
                asyncio.run(context.__aexit__(Exception, e, None))
                raise
    except Exception as e:
        logger.error(f"Transaction context failed: {e}")
        raise