"""
存储事务接口定义

定义存储系统的事务管理功能，包括分布式事务、事务恢复和一致性保证。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, AsyncContextManager
from datetime import datetime
from contextlib import asynccontextmanager


class IStorageTransaction(ABC):
    """存储事务接口
    
    定义存储系统的事务功能，支持ACID特性。
    """
    
    @abstractmethod
    async def begin(self) -> str:
        """开始事务
        
        Returns:
            事务ID
        """
        pass
    
    @abstractmethod
    async def commit(self, transaction_id: str) -> bool:
        """提交事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否提交成功
        """
        pass
    
    @abstractmethod
    async def rollback(self, transaction_id: str) -> bool:
        """回滚事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否回滚成功
        """
        pass
    
    @abstractmethod
    async def add_operation(
        self, 
        transaction_id: str, 
        operation: Dict[str, Any]
    ) -> bool:
        """添加操作到事务
        
        Args:
            transaction_id: 事务ID
            operation: 存储操作
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """获取事务状态
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            事务状态信息
        """
        pass
    
    @abstractmethod
    async def list_active_transactions(self) -> List[Dict[str, Any]]:
        """列出活跃事务
        
        Returns:
            活跃事务列表
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_transactions(self) -> int:
        """清理过期事务
        
        Returns:
            清理的事务数量
        """
        pass


class IDistributedTransaction(ABC):
    """分布式事务接口
    
    定义跨多个存储实例的分布式事务功能。
    """
    
    @abstractmethod
    async def begin_distributed(
        self, 
        participants: List[str],
        timeout: Optional[int] = None
    ) -> str:
        """开始分布式事务
        
        Args:
            participants: 参与者存储ID列表
            timeout: 超时时间（秒）
            
        Returns:
            分布式事务ID
        """
        pass
    
    @abstractmethod
    async def prepare(self, transaction_id: str) -> bool:
        """准备阶段（两阶段提交）
        
        Args:
            transaction_id: 分布式事务ID
            
        Returns:
            是否准备成功
        """
        pass
    
    @abstractmethod
    async def commit_distributed(self, transaction_id: str) -> bool:
        """提交分布式事务
        
        Args:
            transaction_id: 分布式事务ID
            
        Returns:
            是否提交成功
        """
        pass
    
    @abstractmethod
    async def rollback_distributed(self, transaction_id: str) -> bool:
        """回滚分布式事务
        
        Args:
            transaction_id: 分布式事务ID
            
        Returns:
            是否回滚成功
        """
        pass
    
    @abstractmethod
    async def get_participant_status(self, transaction_id: str) -> Dict[str, Any]:
        """获取参与者状态
        
        Args:
            transaction_id: 分布式事务ID
            
        Returns:
            参与者状态信息
        """
        pass


class ITransactionRecovery(ABC):
    """事务恢复接口
    
    定义事务失败后的恢复机制。
    """
    
    @abstractmethod
    async def detect_incomplete_transactions(self) -> List[Dict[str, Any]]:
        """检测未完成的事务
        
        Returns:
            未完成事务列表
        """
        pass
    
    @abstractmethod
    async def recover_transaction(self, transaction_id: str) -> bool:
        """恢复事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    async def force_rollback(self, transaction_id: str) -> bool:
        """强制回滚事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否强制回滚成功
        """
        pass
    
    @abstractmethod
    async def get_recovery_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取恢复日志
        
        Args:
            limit: 限制返回数量
            
        Returns:
            恢复日志列表
        """
        pass


class ITransactionManager(ABC):
    """事务管理器接口
    
    提供高级事务管理功能。
    """
    
    @abstractmethod
    async def transaction(self) -> AsyncContextManager[str]:
        """事务上下文管理器
        
        Returns:
            异步上下文管理器，yield 事务ID
        """
        pass
    
    @abstractmethod
    async def execute_in_transaction(
        self, 
        operations: List[Callable],
        isolation_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """在事务中执行操作
        
        Args:
            operations: 操作函数列表
            isolation_level: 隔离级别
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    async def set_transaction_timeout(self, timeout: int) -> bool:
        """设置事务超时时间
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def get_transaction_statistics(self) -> Dict[str, Any]:
        """获取事务统计信息
        
        Returns:
            事务统计信息
        """
        pass


class IConsistencyManager(ABC):
    """一致性管理器接口
    
    定义数据一致性保证机制。
    """
    
    @abstractmethod
    async def check_consistency(self, storage_ids: List[str]) -> Dict[str, Any]:
        """检查数据一致性
        
        Args:
            storage_ids: 存储ID列表
            
        Returns:
            一致性检查结果
        """
        pass
    
    @abstractmethod
    async def repair_inconsistency(
        self, 
        inconsistency_report: Dict[str, Any]
    ) -> bool:
        """修复不一致性
        
        Args:
            inconsistency_report: 不一致性报告
            
        Returns:
            是否修复成功
        """
        pass
    
    @abstractmethod
    async def enable_consistency_checks(self, config: Dict[str, Any]) -> bool:
        """启用一致性检查
        
        Args:
            config: 检查配置
            
        Returns:
            是否启用成功
        """
        pass
    
    @abstractmethod
    async def get_consistency_report(self) -> Dict[str, Any]:
        """获取一致性报告
        
        Returns:
            一致性报告
        """
        pass