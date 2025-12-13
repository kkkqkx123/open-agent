"""
验证结果缓存
"""

from typing import Dict, Any, Optional, Tuple, List
import hashlib
import json
import time
from src.interfaces.logger import ILogger


class ValidationCache:
    """验证结果缓存"""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        logger: Optional[ILogger] = None
    ):
        """初始化验证缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存生存时间（秒）
            logger: 日志记录器
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.logger = logger
        
        # 缓存存储：key -> (value, timestamp, access_count)
        self._cache: Dict[str, Tuple[Any, float, int]] = {}
        
        # 访问顺序记录，用于LRU淘汰
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回None
        """
        if key not in self._cache:
            if self.logger:
                self.logger.debug(f"缓存未命中: {key}")
            return None
        
        value, timestamp, access_count = self._cache[key]
        
        # 检查是否过期
        if self._is_expired(timestamp):
            self._remove_entry(key)
            
            if self.logger:
                self.logger.debug(f"缓存已过期: {key}")
            
            return None
        
        # 更新访问信息
        self._update_access(key)
        
        if self.logger:
            self.logger.debug(f"缓存命中: {key}")
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        current_time = time.time()
        
        # 如果缓存已满，淘汰最旧的条目
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()
        
        # 更新或添加条目
        if key in self._cache:
            # 更新现有条目
            _, _, access_count = self._cache[key]
            self._cache[key] = (value, current_time, access_count + 1)
            self._update_access_order(key)
        else:
            # 添加新条目
            self._cache[key] = (value, current_time, 1)
            self._access_order.append(key)
        
        if self.logger:
            self.logger.debug(f"缓存设置: {key}")
    
    def delete(self, key: str) -> bool:
        """删除缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        if key not in self._cache:
            return False
        
        self._remove_entry(key)
        
        if self.logger:
            self.logger.debug(f"缓存删除: {key}")
        
        return True
    
    def clear(self) -> None:
        """清除所有缓存"""
        self._cache.clear()
        self._access_order.clear()
        
        if self.logger:
            self.logger.info("已清除所有缓存")
    
    def cleanup_expired(self) -> int:
        """清理过期的缓存条目
        
        Returns:
            int: 清理的条目数
        """
        expired_keys = []
        
        for key, (_, timestamp, _) in self._cache.items():
            if self._is_expired(timestamp):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
        
        if self.logger and expired_keys:
            self.logger.info(f"清理了 {len(expired_keys)} 个过期缓存条目")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for _, timestamp, _ in self._cache.values()
            if self._is_expired(timestamp)
        )
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "usage_ratio": total_entries / self.max_size if self.max_size > 0 else 0
        }
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self._cache.keys())
    
    def _is_expired(self, timestamp: float) -> bool:
        """检查是否过期
        
        Args:
            timestamp: 时间戳
            
        Returns:
            bool: 是否过期
        """
        return time.time() - timestamp > self.ttl_seconds
    
    def _update_access(self, key: str) -> None:
        """更新访问信息
        
        Args:
            key: 缓存键
        """
        if key in self._cache:
            value, timestamp, access_count = self._cache[key]
            self._cache[key] = (value, timestamp, access_count + 1)
        
        self._update_access_order(key)
    
    def _update_access_order(self, key: str) -> None:
        """更新访问顺序
        
        Args:
            key: 缓存键
        """
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _evict_lru(self) -> None:
        """淘汰最近最少使用的条目"""
        if not self._access_order:
            return
        
        lru_key = self._access_order[0]
        self._remove_entry(lru_key)
        
        if self.logger:
            self.logger.debug(f"LRU淘汰缓存条目: {lru_key}")
    
    def _remove_entry(self, key: str) -> None:
        """移除缓存条目
        
        Args:
            key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]
        
        if key in self._access_order:
            self._access_order.remove(key)


class ValidationCacheKeyGenerator:
    """验证缓存键生成器"""
    
    @staticmethod
    def generate_config_key(tool_config: Any) -> str:
        """生成配置验证缓存键
        
        Args:
            tool_config: 工具配置
            
        Returns:
            str: 缓存键
        """
        # 将配置转换为可序列化的字典
        config_dict = ValidationCacheKeyGenerator._serialize_config(tool_config)
        
        # 生成哈希
        config_str = json.dumps(config_dict, sort_keys=True)
        hash_value = hashlib.md5(config_str.encode('utf-8')).hexdigest()
        
        return f"config:{hash_value}"
    
    @staticmethod
    def generate_loading_key(tool_name: str, tool_config: Any) -> str:
        """生成加载验证缓存键
        
        Args:
            tool_name: 工具名称
            tool_config: 工具配置
            
        Returns:
            str: 缓存键
        """
        config_dict = ValidationCacheKeyGenerator._serialize_config(tool_config)
        config_str = json.dumps(config_dict, sort_keys=True)
        hash_value = hashlib.md5(config_str.encode('utf-8')).hexdigest()
        
        return f"loading:{tool_name}:{hash_value}"
    
    @staticmethod
    def _serialize_config(config: Any) -> Dict[str, Any]:
        """序列化配置对象
        
        Args:
            config: 配置对象
            
        Returns:
            Dict[str, Any]: 序列化后的配置
        """
        if hasattr(config, '__dict__'):
            # 如果是对象，提取其属性
            result = {}
            for key, value in config.__dict__.items():
                if not key.startswith('_'):  # 跳过私有属性
                    result[key] = value
            return result
        elif isinstance(config, dict):
            return config
        else:
            # 其他类型，尝试直接转换
            return {"value": config}


# 导出缓存相关类
__all__ = [
    "ValidationCache",
    "ValidationCacheKeyGenerator",
]