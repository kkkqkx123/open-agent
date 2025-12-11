"""JSON处理工具类

提供Repository中JSON序列化和反序列化的通用方法，基于全局MetadataManager。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional

from src.infrastructure.common.utils.metadata import MetadataManager

logger = get_logger(__name__)


class JsonUtils:
    """JSON处理工具类"""
    
    @staticmethod
    def serialize(data: Dict[str, Any], ensure_ascii: bool = False) -> str:
        """序列化数据为JSON字符串
        
        Args:
            data: 要序列化的数据
            ensure_ascii: 是否确保ASCII编码
            
        Returns:
            JSON字符串
        """
        try:
            return MetadataManager.to_json(data, indent=0).replace('\n', '').replace(' ', '')
        except Exception as e:
            logger.error(f"JSON序列化失败: {e}")
            raise
    
    @staticmethod
    def deserialize(json_str: str) -> Dict[str, Any]:
        """反序列化JSON字符串为字典
        
        Args:
            json_str: JSON字符串
            
        Returns:
            字典数据
        """
        try:
            if not json_str:
                return {}
            return MetadataManager.from_json(json_str)
        except Exception as e:
            logger.error(f"JSON反序列化失败: {e}")
            raise
    
    @staticmethod
    def safe_serialize(data: Dict[str, Any], ensure_ascii: bool = False) -> str:
        """安全序列化，处理None值
        
        Args:
            data: 要序列化的数据
            ensure_ascii: 是否确保ASCII编码
            
        Returns:
            JSON字符串
        """
        if data is None:
            data = {}
        return JsonUtils.serialize(data, ensure_ascii)
    
    @staticmethod
    def safe_deserialize(json_str: Optional[str]) -> Dict[str, Any]:
        """安全反序列化，处理None值
        
        Args:
            json_str: JSON字符串，可以为None
            
        Returns:
            字典数据
        """
        if not json_str:
            return {}
        return JsonUtils.deserialize(json_str)