"""ID处理工具类

提供Repository中ID生成的通用方法，基于全局IDGenerator。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Optional

from src.infrastructure.common.utils.id_generator import IDGenerator

logger = get_logger(__name__)


class IdUtils:
    """ID处理工具类"""
    
    @staticmethod
    def generate_checkpoint_id() -> str:
        """生成检查点ID
        
        Returns:
            检查点ID
        """
        return IDGenerator.generate_checkpoint_id()
    
    @staticmethod
    def generate_history_id() -> str:
        """生成历史记录ID
        
        Returns:
            历史记录ID
        """
        return f"history_{IDGenerator.generate_short_uuid()}"
    
    @staticmethod
    def generate_snapshot_id() -> str:
        """生成快照ID
        
        Returns:
            快照ID
        """
        return f"snapshot_{IDGenerator.generate_short_uuid()}"
    
    @staticmethod
    def generate_uuid() -> str:
        """生成通用UUID
        
        Returns:
            UUID字符串
        """
        return IDGenerator.generate_uuid()
    
    @staticmethod
    def get_or_generate_id(data: dict, id_field: str, id_generator_func) -> str:
        """获取或生成ID
        
        Args:
            data: 数据字典
            id_field: ID字段名
            id_generator_func: ID生成函数
            
        Returns:
            ID字符串
        """
        existing_id = data.get(id_field)
        if existing_id:
            return existing_id
        return id_generator_func()