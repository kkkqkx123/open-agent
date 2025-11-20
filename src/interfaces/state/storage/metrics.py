"""存储指标接口定义

定义存储性能指标收集的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IStorageMetrics(ABC):
    """存储指标接口
    
    定义了存储性能指标收集的接口。
    """
    
    @abstractmethod
    async def record_operation(
        self, 
        operation: str, 
        duration: float, 
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作指标
        
        Args:
            operation: 操作类型
            duration: 操作耗时（秒）
            success: 是否成功
            metadata: 元数据
        """
        pass
    
    @abstractmethod
    async def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取指标数据
        
        Args:
            operation: 操作类型，None表示获取所有
            
        Returns:
            指标数据
        """
        pass
    
    @abstractmethod
    async def reset_metrics(self) -> None:
        """重置指标数据"""
        pass