"""时间处理工具类

提供Repository中时间相关的通用方法，基于全局TemporalManager。
"""

from src.interfaces.dependency_injection import get_logger
from datetime import datetime as dt
from typing import Any, Dict, List, Optional

from src.infrastructure.common.utils.temporal import TemporalManager

logger = get_logger(__name__)


class TimeUtils:
    """时间处理工具类"""
    
    @staticmethod
    def now_iso() -> str:
        """获取当前时间的ISO格式字符串
        
        Returns:
            ISO格式时间字符串
        """
        return TemporalManager.format_timestamp(TemporalManager.now(), "iso")
    
    @staticmethod
    def parse_iso(time_str: str) -> dt:
        """解析ISO格式时间字符串
        
        Args:
            time_str: ISO格式时间字符串
            
        Returns:
            datetime对象
        """
        try:
            return TemporalManager.parse_timestamp(time_str, "iso")
        except Exception as e:
            logger.error(f"时间解析失败: {e}")
            raise
    
    @staticmethod
    def is_time_in_range(time_str: str, start_time: dt, end_time: dt) -> bool:
        """检查时间是否在指定范围内
        
        Args:
            time_str: ISO格式时间字符串
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            是否在范围内
        """
        try:
            time = TimeUtils.parse_iso(time_str)
            return start_time <= time <= end_time
        except Exception as e:
            logger.error(f"时间范围检查失败: {e}")
            return False
    
    @staticmethod
    def sort_by_time(items: List[Dict[str, Any]], time_key: str = "created_at", reverse: bool = True) -> List[Dict[str, Any]]:
        """按时间排序项目列表
        
        Args:
            items: 要排序的项目列表
            time_key: 时间字段名
            reverse: 是否倒序
            
        Returns:
            排序后的列表
        """
        try:
            return sorted(
                items,
                key=lambda x: x.get(time_key) or "",
                reverse=reverse
            )
        except Exception as e:
            logger.error(f"时间排序失败: {e}")
            return items
    
    @staticmethod
    def add_timestamp(data: Dict[str, Any], created_at: Optional[str] = None, updated_at: Optional[str] = None) -> Dict[str, Any]:
        """为数据添加时间戳
        
        Args:
            data: 原始数据
            created_at: 创建时间，如果为None则使用当前时间
            updated_at: 更新时间，如果为None则使用当前时间
            
        Returns:
            添加时间戳后的数据
        """
        created_at = created_at or TimeUtils.now_iso()
        updated_at = updated_at or TimeUtils.now_iso()
            
        result = data.copy()
        result["created_at"] = created_at
        result["updated_at"] = updated_at
        return result