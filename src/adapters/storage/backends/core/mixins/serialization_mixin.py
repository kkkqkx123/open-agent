"""存储序列化混入类

提供数据序列化和反序列化功能。
"""

import json
import pickle
import base64
import zlib
from typing import Dict, Any, Optional, Union
from src.services.logger.injection import get_logger


logger = get_logger(__name__)


class StorageSerializationMixin:
    """存储序列化混入类
    
    提供通用的数据序列化和反序列化功能。
    """
    
    def __init__(self, enable_compression: bool = False, compression_threshold: int = 1024):
        """初始化序列化混入
        
        Args:
            enable_compression: 是否启用压缩
            compression_threshold: 压缩阈值（字节）
        """
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        
        # 序列化方法映射
        self._serializers = {
            "json": self._serialize_json,
            "pickle": self._serialize_pickle,
            "base64": self._serialize_base64
        }
        
        # 反序列化方法映射
        self._deserializers = {
            "json": self._deserialize_json,
            "pickle": self._deserialize_pickle,
            "base64": self._deserialize_base64
        }
    
    def serialize_data(self, data: Dict[str, Any], method: str = "json") -> str:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            method: 序列化方法（json, pickle, base64）
            
        Returns:
            序列化后的字符串
        """
        if method not in self._serializers:
            raise ValueError(f"Unknown serialization method: {method}")
        
        serializer = self._serializers[method]
        serialized_data = serializer(data)
        
        # 压缩处理
        if self.enable_compression and len(serialized_data.encode('utf-8')) > self.compression_threshold:
            compressed_data = self._compress_data(serialized_data)
            return f"COMPRESSED:{method}:{compressed_data}"
        
        return f"{method}:{serialized_data}"
    
    def deserialize_data(self, serialized_data: str) -> Dict[str, Any]:
        """反序列化数据
        
        Args:
            serialized_data: 序列化后的字符串
            
        Returns:
            反序列化后的数据
        """
        # 检查是否为压缩数据
        if serialized_data.startswith("COMPRESSED:"):
            parts = serialized_data.split(":", 3)
            if len(parts) != 4:
                raise ValueError("Invalid compressed data format")
            
            method = parts[2]
            compressed_data = parts[3]
            
            # 解压缩
            decompressed_data = self._decompress_data(compressed_data)
            
            # 反序列化
            if method not in self._deserializers:
                raise ValueError(f"Unknown deserialization method: {method}")
            
            deserializer = self._deserializers[method]
            return deserializer(decompressed_data)
        
        # 普通数据
        parts = serialized_data.split(":", 1)
        if len(parts) != 2:
            raise ValueError("Invalid serialized data format")
        
        method = parts[0]
        data = parts[1]
        
        if method not in self._deserializers:
            raise ValueError(f"Unknown deserialization method: {method}")
        
        deserializer = self._deserializers[method]
        return deserializer(data)
    
    def _serialize_json(self, data: Dict[str, Any]) -> str:
        """JSON序列化
        
        Args:
            data: 要序列化的数据
            
        Returns:
            JSON字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization failed: {e}")
            raise ValueError(f"Failed to serialize data to JSON: {e}")
    
    def _deserialize_json(self, data: str) -> Dict[str, Any]:
        """JSON反序列化
        
        Args:
            data: JSON字符串
            
        Returns:
            反序列化后的数据
        """
        try:
            result = json.loads(data)
            if isinstance(result, dict):
                return result
            raise ValueError(f"Expected dict, got {type(result)}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON deserialization failed: {e}")
            raise ValueError(f"Failed to deserialize JSON data: {e}")
    
    def _serialize_pickle(self, data: Dict[str, Any]) -> str:
        """Pickle序列化
        
        Args:
            data: 要序列化的数据
            
        Returns:
            Base64编码的pickle字符串
        """
        try:
            pickled_data = pickle.dumps(data)
            return base64.b64encode(pickled_data).decode('utf-8')
        except (pickle.PicklingError, TypeError) as e:
            logger.error(f"Pickle serialization failed: {e}")
            raise ValueError(f"Failed to serialize data with pickle: {e}")
    
    def _deserialize_pickle(self, data: str) -> Dict[str, Any]:
        """Pickle反序列化
        
        Args:
            data: Base64编码的pickle字符串
            
        Returns:
            反序列化后的数据
        """
        try:
            pickled_data = base64.b64decode(data.encode('utf-8'))
            result = pickle.loads(pickled_data)
            if isinstance(result, dict):
                return result
            raise ValueError(f"Expected dict, got {type(result)}")
        except (pickle.UnpicklingError, base64.binascii.Error, ValueError) as e:
            logger.error(f"Pickle deserialization failed: {e}")
            raise ValueError(f"Failed to deserialize pickle data: {e}")
    
    def _serialize_base64(self, data: Dict[str, Any]) -> str:
        """Base64序列化
        
        Args:
            data: 要序列化的数据
            
        Returns:
            Base64编码的字符串
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            return base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        except (TypeError, ValueError) as e:
            logger.error(f"Base64 serialization failed: {e}")
            raise ValueError(f"Failed to serialize data with base64: {e}")
    
    def _deserialize_base64(self, data: str) -> Dict[str, Any]:
        """Base64反序列化
        
        Args:
            data: Base64编码的字符串
            
        Returns:
            反序列化后的数据
        """
        try:
            decoded_data = base64.b64decode(data.encode('utf-8')).decode('utf-8')
            result = json.loads(decoded_data)
            if isinstance(result, dict):
                return result
            raise ValueError(f"Expected dict, got {type(result)}")
        except (base64.binascii.Error, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Base64 deserialization failed: {e}")
            raise ValueError(f"Failed to deserialize base64 data: {e}")
    
    def _compress_data(self, data: str) -> str:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的Base64编码字符串
        """
        try:
            compressed_bytes = zlib.compress(data.encode('utf-8'))
            return base64.b64encode(compressed_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Data compression failed: {e}")
            raise ValueError(f"Failed to compress data: {e}")
    
    def _decompress_data(self, compressed_data: str) -> str:
        """解压缩数据
        
        Args:
            compressed_data: 压缩后的Base64编码字符串
            
        Returns:
            解压缩后的字符串
        """
        try:
            compressed_bytes = base64.b64decode(compressed_data.encode('utf-8'))
            decompressed_bytes = zlib.decompress(compressed_bytes)
            return decompressed_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Data decompression failed: {e}")
            raise ValueError(f"Failed to decompress data: {e}")
    
    def add_serializer(self, name: str, serializer: Callable, deserializer: Callable) -> None:
        """添加自定义序列化器
        
        Args:
            name: 序列化器名称
            serializer: 序列化函数
            deserializer: 反序列化函数
        """
        self._serializers[name] = serializer
        self._deserializers[name] = deserializer
    
    def get_compression_ratio(self, original_data: str, compressed_data: str) -> float:
        """获取压缩比率
        
        Args:
            original_data: 原始数据
            compressed_data: 压缩数据
            
        Returns:
            压缩比率（压缩后大小/原始大小）
        """
        original_size = len(original_data.encode('utf-8'))
        compressed_size = len(compressed_data.encode('utf-8'))
        
        if original_size == 0:
            return 0.0
        
        return compressed_size / original_size
    
    def is_compressed(self, serialized_data: str) -> bool:
        """检查数据是否已压缩
        
        Args:
            serialized_data: 序列化后的数据
            
        Returns:
            是否已压缩
        """
        return serialized_data.startswith("COMPRESSED:")
    
    def get_serialization_info(self, serialized_data: str) -> Dict[str, Any]:
        """获取序列化信息
        
        Args:
            serialized_data: 序列化后的数据
            
        Returns:
            序列化信息
        """
        if self.is_compressed(serialized_data):
            parts = serialized_data.split(":", 3)
            return {
                "compressed": True,
                "method": parts[2],
                "size": len(serialized_data),
                "compression_ratio": None  # 需要原始数据才能计算
            }
        else:
            parts = serialized_data.split(":", 1)
            return {
                "compressed": False,
                "method": parts[0],
                "size": len(serialized_data),
                "compression_ratio": 1.0
            }