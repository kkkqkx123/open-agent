"""
Token计算缓存机制

提供高效的Token计算结果缓存，支持LRU策略和TTL过期。
"""

import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from threading import RLock
from collections import OrderedDict

from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    
    value: int
    timestamp: float
    access_count: int = 0
    ttl: Optional[float] = None  # 生存时间（秒）
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def touch(self) -> None:
        """更新访问时间和计数"""
        self.timestamp = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计信息"""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    current_size: int = 0
    max_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    @property
    def utilization_rate(self) -> float:
        """缓存利用率"""
        if self.max_size == 0:
            return 0.0
        return (self.current_size / self.max_size) * 100


class TokenCache:
    """Token计算缓存
    
    提供LRU缓存策略，支持TTL过期和统计功能。
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = 3600,  # 1小时
        enable_stats: bool = True
    ):
        """
        初始化Token缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒），None表示永不过期
            enable_stats: 是否启用统计功能
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._stats = CacheStats(max_size=max_size)
        
        logger.debug(f"Token缓存初始化完成: max_size={max_size}, ttl={default_ttl}")
    
    def _generate_key(self, text: str, model_name: str, extra_params: Optional[Dict[str, Any]] = None) -> str:
        """
        生成缓存键
        
        Args:
            text: 输入文本
            model_name: 模型名称
            extra_params: 额外参数
            
        Returns:
            str: 缓存键
        """
        # 创建基础键
        key_data = f"{model_name}:{text}"
        
        # 添加额外参数
        if extra_params:
            sorted_params = sorted(extra_params.items())
            key_data += ":" + ":".join(f"{k}={v}" for k, v in sorted_params)
        
        # 使用MD5哈希确保键长度合理
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def get(self, text: str, model_name: str, extra_params: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        获取缓存的token数量
        
        Args:
            text: 输入文本
            model_name: 模型名称
            extra_params: 额外参数
            
        Returns:
            Optional[int]: 缓存的token数量，如果不存在或过期则返回None
        """
        key = self._generate_key(text, model_name, extra_params)
        
        with self._lock:
            if self.enable_stats:
                self._stats.total_requests += 1
            
            if key not in self._cache:
                if self.enable_stats:
                    self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.is_expired():
                # 移除过期条目
                del self._cache[key]
                if self.enable_stats:
                    self._stats.misses += 1
                    self._stats.current_size -= 1
                logger.debug(f"缓存条目过期: {key[:8]}...")
                return None
            
            # 更新访问信息（LRU）
            entry.touch()
            self._cache.move_to_end(key)
            
            if self.enable_stats:
                self._stats.hits += 1
            
            logger.debug(f"缓存命中: {key[:8]}... = {entry.value}")
            return entry.value
    
    def put(
        self,
        text: str,
        model_name: str,
        token_count: int,
        extra_params: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None
    ) -> None:
        """
        存储token计算结果
        
        Args:
            text: 输入文本
            model_name: 模型名称
            token_count: token数量
            extra_params: 额外参数
            ttl: 自定义TTL（秒）
        """
        key = self._generate_key(text, model_name, extra_params)
        
        with self._lock:
            # 如果键已存在，更新值
            if key in self._cache:
                self._cache[key].value = token_count
                self._cache[key].touch()
                self._cache.move_to_end(key)
                return
            
            # 检查缓存容量
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # 创建新条目
            entry = CacheEntry(
                value=token_count,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            if self.enable_stats:
                self._stats.current_size += 1
            
            logger.debug(f"缓存存储: {key[:8]}... = {token_count}")
    
    def get_batch(self, items: List[Tuple[str, str, Optional[Dict[str, Any]]]]) -> List[Optional[int]]:
        """
        批量获取缓存值
        
        Args:
            items: (text, model_name, extra_params) 元组列表
            
        Returns:
            List[Optional[int]]: 对应的token数量列表
        """
        results = []
        for text, model_name, extra_params in items:
            result = self.get(text, model_name, extra_params)
            results.append(result)
        return results
    
    def put_batch(
        self,
        items: List[Tuple[str, str, int, Optional[Dict[str, Any]], Optional[float]]]
    ) -> None:
        """
        批量存储缓存值
        
        Args:
            items: (text, model_name, token_count, extra_params, ttl) 元组列表
        """
        for text, model_name, token_count, extra_params, ttl in items:
            self.put(text, model_name, token_count, extra_params, ttl)
    
    def _evict_lru(self) -> None:
        """移除最少使用的条目"""
        if not self._cache:
            return
        
        # 移除最旧的条目
        key, entry = self._cache.popitem(last=False)
        
        if self.enable_stats:
            self._stats.evictions += 1
            self._stats.current_size -= 1
        
        logger.debug(f"LRU淘汰: {key[:8]}... (访问次数: {entry.access_count})")
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            
            if self.enable_stats:
                self._stats.current_size = 0
            
            logger.info(f"缓存已清空，清除了 {cleared_count} 个条目")
    
    def remove_expired(self) -> int:
        """移除过期的缓存条目
        
        Returns:
            int: 移除的条目数量
        """
        with self._lock:
            expired_keys = []
            current_time = time.time()
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if self.enable_stats:
                    self._stats.current_size -= 1
            
            if expired_keys:
                logger.info(f"移除了 {len(expired_keys)} 个过期缓存条目")
            
            return len(expired_keys)
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计信息"""
        with self._lock:
            if self.enable_stats:
                self._stats.current_size = len(self._cache)
            return self._stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._lock:
            self._stats = CacheStats(max_size=self.max_size)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息"""
        with self._lock:
            stats = self.get_stats()
            
            # 计算缓存条目的年龄分布
            current_time = time.time()
            age_distribution = {
                "0-1小时": 0,
                "1-6小时": 0,
                "6-24小时": 0,
                "24小时+": 0
            }
            
            for entry in self._cache.values():
                age_hours = (current_time - entry.timestamp) / 3600
                if age_hours <= 1:
                    age_distribution["0-1小时"] += 1
                elif age_hours <= 6:
                    age_distribution["1-6小时"] += 1
                elif age_hours <= 24:
                    age_distribution["6-24小时"] += 1
                else:
                    age_distribution["24小时+"] += 1
            
            return {
                "max_size": self.max_size,
                "current_size": stats.current_size,
                "hit_rate": stats.hit_rate,
                "utilization_rate": stats.utilization_rate,
                "total_requests": stats.total_requests,
                "hits": stats.hits,
                "misses": stats.misses,
                "evictions": stats.evictions,
                "age_distribution": age_distribution,
                "default_ttl": self.default_ttl
            }
    
    def cleanup(self) -> None:
        """清理缓存，移除过期条目"""
        removed_count = self.remove_expired()
        if removed_count > 0:
            logger.info(f"缓存清理完成，移除了 {removed_count} 个过期条目")
    
    def __len__(self) -> int:
        """返回缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            return key in self._cache