"""执行上下文工具

提供执行上下文相关的工具类和帮助函数。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class ExecutionContextBuilder:
    """执行上下文构建器
    
    负责构建和配置执行上下文。
    """
    
    def __init__(self) -> None:
        """初始化构建器"""
        self._workflow_id: Optional[str] = None
        self._execution_id: Optional[str] = None
        self._config: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
    
    def with_workflow_id(self, workflow_id: str) -> "ExecutionContextBuilder":
        """设置工作流ID
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            ExecutionContextBuilder: 构建器实例
        """
        self._workflow_id = workflow_id
        return self
    
    def with_execution_id(self, execution_id: str) -> "ExecutionContextBuilder":
        """设置执行ID
        
        Args:
            execution_id: 执行ID
            
        Returns:
            ExecutionContextBuilder: 构建器实例
        """
        self._execution_id = execution_id
        return self
    
    def with_config(self, config: Dict[str, Any]) -> "ExecutionContextBuilder":
        """设置配置
        
        Args:
            config: 配置字典
            
        Returns:
            ExecutionContextBuilder: 构建器实例
        """
        self._config.update(config)
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> "ExecutionContextBuilder":
        """设置元数据
        
        Args:
            metadata: 元数据字典
            
        Returns:
            ExecutionContextBuilder: 构建器实例
        """
        self._metadata.update(metadata)
        return self
    
    def build(self):
        """构建执行上下文
        
        Returns:
            ExecutionContext: 执行上下文实例
        """
        from src.interfaces.workflow.core import ExecutionContext
        
        # 生成默认ID
        if not self._workflow_id:
            self._workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        if not self._execution_id:
            self._execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        # 添加默认元数据
        default_metadata = {
            "created_at": datetime.now().isoformat(),
            "workflow_id": self._workflow_id,
            "execution_id": self._execution_id
        }
        default_metadata.update(self._metadata)
        
        return ExecutionContext(
            workflow_id=self._workflow_id,
            execution_id=self._execution_id,
            config=self._config,
            metadata=default_metadata
        )


class TimestampHelper:
    """时间戳帮助类
    
    提供时间戳相关的工具方法。
    """
    
    @staticmethod
    def get_timestamp() -> str:
        """获取当前时间戳
        
        Returns:
            str: ISO格式的时间戳
        """
        return datetime.now().isoformat()
    
    @staticmethod
    def get_timestamp_ms() -> int:
        """获取当前时间戳（毫秒）
        
        Returns:
            int: 毫秒时间戳
        """
        return int(datetime.now().timestamp() * 1000)
    
    @staticmethod
    def format_duration(start_ms: int, end_ms: Optional[int] = None) -> str:
        """格式化持续时间
        
        Args:
            start_ms: 开始时间（毫秒）
            end_ms: 结束时间（毫秒），如果为None则使用当前时间
            
        Returns:
            str: 格式化的持续时间
        """
        if end_ms is None:
            end_ms = TimestampHelper.get_timestamp_ms()
        
        duration_ms = end_ms - start_ms
        
        if duration_ms < 1000:
            return f"{duration_ms}ms"
        elif duration_ms < 60000:
            return f"{duration_ms / 1000:.2f}s"
        else:
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) / 1000
            return f"{minutes}m {seconds:.2f}s"