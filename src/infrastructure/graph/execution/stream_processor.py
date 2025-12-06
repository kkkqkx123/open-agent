"""流处理器实现

提供流式处理和中间结果输出功能。
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from ..types import StreamMode

__all__ = ("StreamProcessor",)


class StreamProcessor:
    """流处理器，提供流式处理和中间结果输出功能。"""
    
    def __init__(self):
        """初始化流处理器。"""
        self.stream_mode: StreamMode = "values"
        self.stream_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000
    
    def set_stream_mode(self, mode: StreamMode) -> None:
        """设置流模式。
        
        Args:
            mode: 流模式
        """
        self.stream_mode = mode
    
    def set_max_buffer_size(self, max_size: int) -> None:
        """设置最大缓冲区大小。
        
        Args:
            max_size: 最大缓冲区大小
        """
        self.max_buffer_size = max_size
    
    async def process_stream(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理流数据。
        
        Args:
            data: 流数据
            metadata: 元数据
            
        Yields:
            处理后的流数据
        """
        if self.stream_mode == "values":
            yield await self._process_values(data, metadata)
        elif self.stream_mode == "updates":
            yield await self._process_updates(data, metadata)
        elif self.stream_mode == "debug":
            async for result in self._process_debug(data, metadata):
                yield result
        elif self.stream_mode == "custom":
            async for result in self._process_custom(data, metadata):
                yield result
        else:
            # 默认处理
            yield await self._process_default(data, metadata)
    
    async def _process_values(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理值模式流数据。
        
        Args:
            data: 流数据
            metadata: 元数据
            
        Returns:
            处理后的数据
        """
        result = {
            "type": "value",
            "data": data,
            "metadata": metadata or {}
        }
        
        # 添加到缓冲区
        self._add_to_buffer(result)
        
        return result
    
    async def _process_updates(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理更新模式流数据。
        
        Args:
            data: 流数据
            metadata: 元数据
            
        Returns:
            处理后的数据
        """
        result = {
            "type": "update",
            "data": data,
            "metadata": metadata or {}
        }
        
        # 添加到缓冲区
        self._add_to_buffer(result)
        
        return result
    
    async def _process_debug(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理调试模式流数据。
        
        Args:
            data: 流数据
            metadata: 元数据
            
        Yields:
            处理后的数据
        """
        # 生成详细的调试信息
        debug_info = {
            "type": "debug",
            "data": data,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp(),
            "data_type": type(data).__name__,
            "data_size": len(str(data)) if data else 0
        }
        
        # 添加到缓冲区
        self._add_to_buffer(debug_info)
        
        yield debug_info
    
    async def _process_custom(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理自定义模式流数据。
        
        Args:
            data: 流数据
            metadata: 元数据
            
        Yields:
            处理后的数据
        """
        # 自定义处理逻辑
        if hasattr(data, '__iter__') and not isinstance(data, (str, bytes)):
            # 如果数据是可迭代的，逐个yield
            for item in data:
                result = {
                    "type": "custom",
                    "data": item,
                    "metadata": metadata or {}
                }
                self._add_to_buffer(result)
                yield result
        else:
            # 否则直接yield
            result = {
                "type": "custom",
                "data": data,
                "metadata": metadata or {}
            }
            self._add_to_buffer(result)
            yield result
    
    async def _process_default(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理默认模式流数据。
        
        Args:
            data: 流数据
            metadata: 元数据
            
        Returns:
            处理后的数据
        """
        result = {
            "type": "default",
            "data": data,
            "metadata": metadata or {}
        }
        
        # 添加到缓冲区
        self._add_to_buffer(result)
        
        return result
    
    def _add_to_buffer(self, item: Dict[str, Any]) -> None:
        """添加项目到缓冲区。
        
        Args:
            item: 要添加的项目
        """
        self.stream_buffer.append(item)
        
        # 检查缓冲区大小限制
        if len(self.stream_buffer) > self.max_buffer_size:
            # 移除最旧的项目
            self.stream_buffer.pop(0)
    
    def get_buffer(self) -> List[Dict[str, Any]]:
        """获取缓冲区内容。
        
        Returns:
            缓冲区内容
        """
        return self.stream_buffer.copy()
    
    def clear_buffer(self) -> None:
        """清除缓冲区。"""
        self.stream_buffer.clear()
    
    def _get_timestamp(self) -> str:
        """获取时间戳。
        
        Returns:
            时间戳字符串
        """
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """获取流统计信息。
        
        Returns:
            统计信息字典
        """
        return {
            "stream_mode": self.stream_mode,
            "buffer_size": len(self.stream_buffer),
            "max_buffer_size": self.max_buffer_size,
            "buffer_types": self._get_buffer_types()
        }
    
    def _get_buffer_types(self) -> Dict[str, int]:
        """获取缓冲区类型统计。
        
        Returns:
            类型统计字典
        """
        type_counts = {}
        for item in self.stream_buffer:
            item_type = item.get("type", "unknown")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        return type_counts