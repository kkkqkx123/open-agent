"""过期时间策略管理

提供统一的数据过期时间检查和处理策略。
"""

import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class ExpirationPolicy(ABC):
    """过期策略基类
    
    定义数据过期的检查方式。
    """
    
    @abstractmethod
    def is_expired(self, data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选，默认使用系统时间）
            
        Returns:
            是否已过期
        """
        pass


class StandardExpirationPolicy(ExpirationPolicy):
    """标准过期策略
    
    基于 expires_at 字段的过期检查。
    """
    
    EXPIRATION_FIELD = "expires_at"
    
    def is_expired(self, data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期
        
        检查 expires_at 字段是否存在且小于当前时间。
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            是否已过期
        """
        if current_time is None:
            current_time = time.time()
        
        expires_at = data.get(self.EXPIRATION_FIELD)
        if expires_at and isinstance(expires_at, (int, float)):
            return expires_at < current_time
        
        return False


class TTLExpirationPolicy(ExpirationPolicy):
    """TTL 过期策略
    
    基于创建时间和 TTL 的过期检查。
    """
    
    def __init__(self, ttl_seconds: int):
        """初始化 TTL 策略
        
        Args:
            ttl_seconds: TTL 秒数
        """
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self, data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期
        
        基于 created_at + ttl_seconds 是否小于当前时间。
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            是否已过期
        """
        if current_time is None:
            current_time = time.time()
        
        created_at = data.get("created_at")
        if not created_at or not isinstance(created_at, (int, float)):
            return False
        
        return created_at + self.ttl_seconds < current_time


class CustomExpirationPolicy(ExpirationPolicy):
    """自定义过期策略
    
    允许通过回调函数自定义过期检查。
    """
    
    def __init__(self, check_func):
        """初始化自定义策略
        
        Args:
            check_func: 检查函数，签名为 check_func(data, current_time) -> bool
        """
        self.check_func = check_func
    
    def is_expired(self, data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            是否已过期
        """
        if current_time is None:
            current_time = time.time()
        
        return self.check_func(data, current_time)


class ExpirationManager:
    """过期时间管理器
    
    统一管理数据的过期检查。
    """
    
    def __init__(self, policy: Optional[ExpirationPolicy] = None):
        """初始化管理器
        
        Args:
            policy: 过期策略（可选，默认使用标准策略）
        """
        self.policy = policy or StandardExpirationPolicy()
    
    def is_expired(self, data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否已过期
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            是否已过期
        """
        return self.policy.is_expired(data, current_time)
    
    def set_policy(self, policy: ExpirationPolicy) -> None:
        """设置过期策略
        
        Args:
            policy: 新的过期策略
        """
        self.policy = policy
    
    @staticmethod
    def calculate_cutoff_time(retention_days: int, current_time: Optional[float] = None) -> float:
        """计算保留期限的截止时间
        
        用于清理指定天数前的数据。
        
        Args:
            retention_days: 保留天数
            current_time: 当前时间戳（可选）
            
        Returns:
            截止时间戳（之前的数据应被删除）
        """
        if current_time is None:
            current_time = time.time()
        
        return current_time - (retention_days * 24 * 3600)
    
    @staticmethod
    def get_data_age_seconds(data: Dict[str, Any], current_time: Optional[float] = None) -> Optional[float]:
        """获取数据的年龄（秒）
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            数据年龄（秒），如果没有创建时间则返回 None
        """
        if current_time is None:
            current_time = time.time()
        
        created_at = data.get("created_at")
        if not created_at or not isinstance(created_at, (int, float)):
            return None
        
        return current_time - created_at
    
    @staticmethod
    def get_remaining_ttl(data: Dict[str, Any], current_time: Optional[float] = None) -> Optional[float]:
        """获取剩余 TTL（秒）
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            剩余 TTL（秒），如果没有 expires_at 则返回 None
        """
        if current_time is None:
            current_time = time.time()
        
        expires_at = data.get("expires_at")
        if not expires_at or not isinstance(expires_at, (int, float)):
            return None
        
        remaining = expires_at - current_time
        return max(0, remaining)  # 不返回负数
