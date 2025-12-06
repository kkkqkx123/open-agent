"""消息可靠性

提供消息传递的可靠性保证，包括重试、去重和传递确认。
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .message_processor import Message
from ..types import errors


class DeliveryMode(Enum):
    """消息传递模式"""
    AT_LEAST_ONCE = "at_least_once"  # 至少一次
    AT_MOST_ONCE = "at_most_once"    # 最多一次
    EXACTLY_ONCE = "exactly_once"    # 恰好一次


class RetryPolicy:
    """重试策略"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """获取重试延迟
        
        Args:
            attempt: 当前尝试次数（从1开始）
            
        Returns:
            延迟时间（秒）
        """
        if attempt <= 1:
            return self.initial_delay
        
        delay = min(self.initial_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
        
        if self.jitter:
            # 添加随机抖动，避免雷群效应
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay


class DeliveryTracker:
    """传递跟踪器"""
    
    def __init__(self) -> None:
        self.pending_deliveries: Dict[int, Dict[str, Any]] = {}
        self.completed_deliveries: Set[int] = set()
        self.failed_deliveries: Dict[int, Exception] = {}
    
    def track_delivery(
        self,
        message_id: int,
        targets: List[str],
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        """跟踪消息传递
        
        Args:
            message_id: 消息ID
            targets: 目标列表
            retry_policy: 重试策略
        """
        self.pending_deliveries[message_id] = {
            "targets": targets.copy(),
            "remaining_targets": targets.copy(),
            "completed_targets": [],
            "failed_targets": {},
            "retry_policy": retry_policy or RetryPolicy(),
            "attempts": {target: 0 for target in targets},
            "start_time": time.time(),
        }
    
    def mark_target_completed(self, message_id: int, target: str) -> None:
        """标记目标已完成
        
        Args:
            message_id: 消息ID
            target: 目标
        """
        if message_id in self.pending_deliveries:
            delivery = self.pending_deliveries[message_id]
            if target in delivery["remaining_targets"]:
                delivery["remaining_targets"].remove(target)
                delivery["completed_targets"].append(target)
    
    def mark_target_failed(
        self,
        message_id: int,
        target: str,
        error: Exception,
    ) -> None:
        """标记目标失败
        
        Args:
            message_id: 消息ID
            target: 目标
            error: 错误信息
        """
        if message_id in self.pending_deliveries:
            delivery = self.pending_deliveries[message_id]
            delivery["failed_targets"][target] = error
    
    def get_delivery_status(self, message_id: int) -> Optional[Dict[str, Any]]:
        """获取传递状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            传递状态信息
        """
        if message_id not in self.pending_deliveries:
            return None
        
        delivery = self.pending_deliveries[message_id]
        return {
            "message_id": message_id,
            "total_targets": len(delivery["targets"]),
            "completed_targets": delivery["completed_targets"],
            "failed_targets": delivery["failed_targets"],
            "remaining_targets": delivery["remaining_targets"],
            "is_complete": len(delivery["remaining_targets"]) == 0,
        }
    
    def cleanup_delivery(self, message_id: int) -> None:
        """清理传递记录
        
        Args:
            message_id: 消息ID
        """
        if message_id in self.pending_deliveries:
            delivery = self.pending_deliveries[message_id]
            if len(delivery["remaining_targets"]) == 0:
                self.completed_deliveries.add(message_id)
                del self.pending_deliveries[message_id]
    
    def get_retry_targets(self, message_id: int) -> List[str]:
        """获取需要重试的目标
        
        Args:
            message_id: 消息ID
            
        Returns:
            需要重试的目标列表
        """
        if message_id not in self.pending_deliveries:
            return []
        
        delivery = self.pending_deliveries[message_id]
        retry_policy = delivery["retry_policy"]
        retry_targets = []
        
        for target in delivery["remaining_targets"]:
            attempts = delivery["attempts"][target]
            if attempts < retry_policy.max_attempts:
                retry_targets.append(target)
        
        return retry_targets


class MessageReliability:
    """消息可靠性保证
    
    提供消息传递的可靠性保证，包括重试、去重和传递确认。
    """
    
    def __init__(
        self,
        delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE,
        retry_policy: Optional[RetryPolicy] = None,
        deduplication: bool = True,
    ) -> None:
        """初始化消息可靠性保证
        
        Args:
            delivery_mode: 传递模式
            retry_policy: 重试策略
            deduplication: 是否启用去重
        """
        self.delivery_mode = delivery_mode
        self.retry_policy = retry_policy or RetryPolicy()
        self.deduplication = deduplication
        self.delivery_tracker = DeliveryTracker()
        self.deduplication_cache: Set[int] = set()
        self.message_handlers: Dict[str, Callable[[Message, str], Any]] = {}
    
    def register_message_handler(self, message_type: str, handler: Callable[[Message, str], Any]) -> None:
        """注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self.message_handlers[message_type] = handler
    
    async def ensure_delivery(
        self,
        message: Message,
        targets: List[str],
    ) -> bool:
        """确保消息传递
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功传递到所有目标
        """
        # 去重检查
        if self.deduplication and message.id in self.deduplication_cache:
            return True
        
        # 跟踪传递
        self.delivery_tracker.track_delivery(message.id, targets, self.retry_policy)
        
        # 根据传递模式处理
        if self.delivery_mode == DeliveryMode.AT_LEAST_ONCE:
            success = await self._deliver_at_least_once(message, targets)
        elif self.delivery_mode == DeliveryMode.AT_MOST_ONCE:
            success = await self._deliver_at_most_once(message, targets)
        else:  # EXACTLY_ONCE
            success = await self._deliver_exactly_once(message, targets)
        
        # 清理传递记录
        self.delivery_tracker.cleanup_delivery(message.id)
        
        # 添加到去重缓存
        if success and self.deduplication:
            self.deduplication_cache.add(message.id)
            # 限制缓存大小
            if len(self.deduplication_cache) > 10000:
                self.deduplication_cache.clear()
        
        return success
    
    async def _deliver_at_least_once(
        self,
        message: Message,
        targets: List[str],
    ) -> bool:
        """至少一次传递
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功传递到所有目标
        """
        all_success = True
        
        for target in targets:
            success = await self._deliver_to_target(message, target)
            if success:
                self.delivery_tracker.mark_target_completed(message.id, target)
            else:
                all_success = False
                self.delivery_tracker.mark_target_failed(
                    message.id,
                    target,
                    errors.DeliveryFailedError(f"传递到 {target} 失败"),
                )
        
        return all_success
    
    async def _deliver_at_most_once(
        self,
        message: Message,
        targets: List[str],
    ) -> bool:
        """最多一次传递
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功传递到所有目标
        """
        # 检查是否已经传递过
        if message.id in self.deduplication_cache:
            return True
        
        all_success = True
        
        for target in targets:
            success = await self._deliver_to_target(message, target)
            if success:
                self.delivery_tracker.mark_target_completed(message.id, target)
            else:
                all_success = False
                self.delivery_tracker.mark_target_failed(
                    message.id,
                    target,
                    errors.DeliveryFailedError(f"传递到 {target} 失败"),
                )
                # 最多一次模式下，失败就不再重试
                break
        
        return all_success
    
    async def _deliver_exactly_once(
        self,
        message: Message,
        targets: List[str],
    ) -> bool:
        """恰好一次传递
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功传递到所有目标
        """
        # 检查是否已经传递过
        if message.id in self.deduplication_cache:
            return True
        
        all_success = True
        
        for target in targets:
            success = await self._deliver_to_target_with_retry(message, target)
            if success:
                self.delivery_tracker.mark_target_completed(message.id, target)
            else:
                all_success = False
                self.delivery_tracker.mark_target_failed(
                    message.id,
                    target,
                    errors.DeliveryFailedError(f"传递到 {target} 失败"),
                )
        
        return all_success
    
    async def _deliver_to_target_with_retry(
        self,
        message: Message,
        target: str,
    ) -> bool:
        """带重试的传递到目标
        
        Args:
            message: 消息
            target: 目标
            
        Returns:
            是否成功传递
        """
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                success = await self._deliver_to_target(message, target)
                if success:
                    return True
                
                # 如果失败且不是最后一次尝试，等待重试
                if attempt < self.retry_policy.max_attempts:
                    delay = self.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
            except Exception as e:
                if attempt == self.retry_policy.max_attempts:
                    raise e
                
                delay = self.retry_policy.get_delay(attempt)
                await asyncio.sleep(delay)
        
        return False
    
    async def _deliver_to_target(self, message: Message, target: str) -> bool:
        """传递到目标
        
        Args:
            message: 消息
            target: 目标
            
        Returns:
            是否成功传递
        """
        try:
            # 获取消息处理器
            handler = self.message_handlers.get(message.message_type)
            if handler is None:
                return False
            
            # 调用处理器
            if asyncio.iscoroutinefunction(handler):
                await handler(message, target)
            else:
                handler(message, target)
            
            return True
        except Exception:
            return False
    
    def handle_delivery_failure(
        self,
        message: Message,
        error: Exception,
    ) -> None:
        """处理传递失败
        
        Args:
            message: 消息
            error: 错误信息
        """
        # 记录失败信息
        if isinstance(message.id, int):
            self.delivery_tracker.failed_deliveries[message.id] = error
    
    def deduplicate_message(self, message: Message) -> bool:
        """消息去重
        
        Args:
            message: 消息
            
        Returns:
            True表示消息是重复的，False表示不是重复的
        """
        if not self.deduplication:
            return False
        
        if message.id in self.deduplication_cache:
            return True
        
        self.deduplication_cache.add(message.id)
        return False
    
    def get_delivery_status(self, message_id: int) -> Optional[Dict[str, Any]]:
        """获取传递状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            传递状态信息
        """
        return self.delivery_tracker.get_delivery_status(message_id)
    
    def clear_deduplication_cache(self) -> None:
        """清空去重缓存"""
        self.deduplication_cache.clear()