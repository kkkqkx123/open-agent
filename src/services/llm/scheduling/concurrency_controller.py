"""并发控制器"""

import asyncio
import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class ConcurrencyLevel(Enum):
    """并发级别"""
    GROUP = "group"
    ECHELON = "echelon"
    MODEL = "model"
    NODE = "node"


@dataclass
class ConcurrencyLimit:
    """并发限制配置"""
    limit: int
    queue_size: int
    current_count: int = 0
    waiting_queue: List = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    
    def can_acquire(self) -> bool:
        """检查是否可以获取并发许可"""
        return self.current_count < self.limit
    
    def acquire(self) -> bool:
        """获取并发许可"""
        with self.lock:
            if self.can_acquire():
                self.current_count += 1
                return True
            return False
    
    def release(self) -> None:
        """释放并发许可"""
        with self.lock:
            if self.current_count > 0:
                self.current_count -= 1
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        with self.lock:
            return {
                "limit": self.limit,
                "current": self.current_count,
                "available": self.limit - self.current_count,
                "queue_size": len(self.waiting_queue)
            }


class ConcurrencyController:
    """并发控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化并发控制器
        
        Args:
            config: 并发控制配置
        """
        self.enabled = config.get("enabled", True)
        self.limits: Dict[str, ConcurrencyLimit] = {}
        
        if self.enabled:
            self._init_limits(config.get("levels", []))
    
    def _init_limits(self, levels: List[Dict[str, Any]]) -> None:
        """初始化并发限制"""
        for level_config in levels:
            level_name = list(level_config.keys())[0]
            level_data = level_config[level_name]
            
            self.limits[level_name] = ConcurrencyLimit(
                limit=level_data.get("limit", 100),
                queue_size=level_data.get("queue_size", 1000)
            )
    
    def can_execute(self, level: ConcurrencyLevel, identifier: str) -> bool:
        """
        检查是否可以执行
        
        Args:
            level: 并发级别
            identifier: 标识符
            
        Returns:
            是否可以执行
        """
        if not self.enabled:
            return True
        
        limit_key = f"{level.value}_{identifier}"
        limit = self.limits.get(limit_key)
        
        if not limit:
            return True
        
        return limit.can_acquire()
    
    async def acquire_permission(self, level: ConcurrencyLevel, identifier: str, timeout: float = 30.0) -> bool:
        """
        获取执行许可
        
        Args:
            level: 并发级别
            identifier: 标识符
            timeout: 超时时间
            
        Returns:
            是否获取成功
        """
        if not self.enabled:
            return True
        
        limit_key = f"{level.value}_{identifier}"
        limit = self.limits.get(limit_key)
        
        if not limit:
            return True
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if limit.acquire():
                return True
            
            # 等待一段时间后重试
            await asyncio.sleep(0.1)
        
        return False
    
    def release_permission(self, level: ConcurrencyLevel, identifier: str) -> None:
        """
        释放执行许可
        
        Args:
            level: 并发级别
            identifier: 标识符
        """
        if not self.enabled:
            return
        
        limit_key = f"{level.value}_{identifier}"
        limit = self.limits.get(limit_key)
        
        if limit:
            limit.release()
    
    def get_status(self) -> Dict[str, Any]:
        """获取并发控制状态"""
        if not self.enabled:
            return {"enabled": False}
        
        status = {"enabled": True, "limits": {}}
        
        for key, limit in self.limits.items():
            status["limits"][key] = limit.get_status()
        
        return status
    
    def update_limit(self, level: ConcurrencyLevel, identifier: str, limit: int, queue_size: int) -> None:
        """
        更新并发限制
        
        Args:
            level: 并发级别
            identifier: 标识符
            limit: 并发限制
            queue_size: 队列大小
        """
        limit_key = f"{level.value}_{identifier}"
        self.limits[limit_key] = ConcurrencyLimit(
            limit=limit,
            queue_size=queue_size
        )
    
    def get_limit(self, level: ConcurrencyLevel, identifier: str) -> Optional[ConcurrencyLimit]:
        """
        获取并发限制
        
        Args:
            level: 并发级别
            identifier: 标识符
            
        Returns:
            并发限制配置
        """
        limit_key = f"{level.value}_{identifier}"
        return self.limits.get(limit_key)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化速率限制器
        
        Args:
            config: 速率限制配置
        """
        self.enabled = config.get("enabled", True)
        self.algorithm = config.get("algorithm", "token_bucket")
        
        if self.enabled:
            if self.algorithm == "token_bucket":
                self._init_token_bucket(config.get("token_bucket", {}))
            elif self.algorithm == "sliding_window":
                self._init_sliding_window(config.get("sliding_window", {}))
    
    def _init_token_bucket(self, config: Dict[str, Any]) -> None:
        """初始化令牌桶"""
        self.bucket_size = config.get("bucket_size", 1000)
        self.refill_rate = config.get("refill_rate", 16.67)  # 1000/60
        self.tokens = self.bucket_size
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def _init_sliding_window(self, config: Dict[str, Any]) -> None:
        """初始化滑动窗口"""
        self.window_size = config.get("window_size", 60)
        self.max_requests = config.get("max_requests", 1000)
        self.requests = []
        self.lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """检查是否可以继续"""
        if not self.enabled:
            return True
        
        if self.algorithm == "token_bucket":
            return self._token_bucket_can_proceed()
        elif self.algorithm == "sliding_window":
            return self._sliding_window_can_proceed()
        
        return True
    
    def _token_bucket_can_proceed(self) -> bool:
        """令牌桶检查"""
        with self.lock:
            self._refill_tokens()
            return self.tokens >= 1
    
    def _sliding_window_can_proceed(self) -> bool:
        """滑动窗口检查"""
        with self.lock:
            now = time.time()
            # 清理过期的请求
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_size]
            return len(self.requests) < self.max_requests
    
    def consume(self) -> bool:
        """消费一个许可"""
        if not self.enabled:
            return True
        
        if self.algorithm == "token_bucket":
            return self._consume_token()
        elif self.algorithm == "sliding_window":
            return self._consume_window()
        
        return True
    
    def _consume_token(self) -> bool:
        """消费令牌"""
        with self.lock:
            self._refill_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def _consume_window(self) -> bool:
        """消费窗口许可"""
        with self.lock:
            now = time.time()
            # 清理过期的请求
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_size]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def _refill_tokens(self) -> None:
        """填充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        if not self.enabled:
            return {"enabled": False}
        
        status = {
            "enabled": True,
            "algorithm": self.algorithm
        }
        
        if self.algorithm == "token_bucket":
            with self.lock:
                status.update({
                    "bucket_size": self.bucket_size,
                    "current_tokens": self.tokens,
                    "refill_rate": self.refill_rate
                })
        elif self.algorithm == "sliding_window":
            with self.lock:
                now = time.time()
                recent_requests = [req_time for req_time in self.requests 
                                 if now - req_time < self.window_size]
                status.update({
                    "window_size": self.window_size,
                    "max_requests": self.max_requests,
                    "current_requests": len(recent_requests)
                })
        
        return status


class ConcurrencyAndRateLimitManager:
    """并发和速率限制管理器"""
    
    def __init__(self, concurrency_config: Dict[str, Any], rate_limit_config: Dict[str, Any]):
        """
        初始化管理器
        
        Args:
            concurrency_config: 并发控制配置
            rate_limit_config: 速率限制配置
        """
        self.concurrency_controller = ConcurrencyController(concurrency_config)
        self.rate_limiter = RateLimiter(rate_limit_config)
    
    async def check_and_acquire(self, 
                             concurrency_level: ConcurrencyLevel,
                             identifier: str,
                             timeout: float = 30.0) -> bool:
        """
        检查并获取执行许可
        
        Args:
            concurrency_level: 并发级别
            identifier: 标识符
            timeout: 超时时间
            
        Returns:
            是否获取成功
        """
        # 检查速率限制
        if not self.rate_limiter.can_proceed():
            return False
        
        # 检查并发限制
        if not self.concurrency_controller.can_execute(concurrency_level, identifier):
            return False
        
        # 获取并发许可
        concurrency_acquired = await self.concurrency_controller.acquire_permission(
            concurrency_level, identifier, timeout
        )
        
        if not concurrency_acquired:
            return False
        
        # 消费速率限制许可
        rate_limit_acquired = self.rate_limiter.consume()
        
        if not rate_limit_acquired:
            # 释放并发许可
            self.concurrency_controller.release_permission(concurrency_level, identifier)
            return False
        
        return True
    
    def release(self, concurrency_level: ConcurrencyLevel, identifier: str) -> None:
        """
        释放执行许可
        
        Args:
            concurrency_level: 并发级别
            identifier: 标识符
        """
        self.concurrency_controller.release_permission(concurrency_level, identifier)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "concurrency": self.concurrency_controller.get_status(),
            "rate_limit": self.rate_limiter.get_status()
        }