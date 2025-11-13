"""增强的降级管理器"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .task_group_manager import TaskGroupManager
from .polling_pool import PollingPoolManager
from .interfaces import ILLMClient
from .exceptions import LLMError

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """降级策略"""
    ECHELON_DOWN = "echelon_down"  # 层级降级
    MODEL_ROTATE = "model_rotate"  # 模型轮询
    PROVIDER_FAILOVER = "provider_failover"  # 提供商故障转移
    TASK_GROUP_SWITCH = "task_group_switch"  # 任务组切换
    POLLING_POOL_SWITCH = "polling_pool_switch"  # 轮询池切换


@dataclass
class FallbackAttempt:
    """降级尝试记录"""
    attempt_number: int
    strategy: FallbackStrategy
    target: str
    success: bool
    error: Optional[str] = None
    response_time: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值
            recovery_time: 恢复时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                return True
            return False
        
        if self.state == "HALF_OPEN":
            return True
        
        return False
    
    def record_success(self) -> None:
        """记录成功"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self) -> None:
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_time


class EnhancedFallbackManager:
    """增强的降级管理器"""
    
    def __init__(self, 
                 task_group_manager: TaskGroupManager,
                 polling_pool_manager: Optional[PollingPoolManager] = None):
        """
        初始化降级管理器
        
        Args:
            task_group_manager: 任务组管理器
            polling_pool_manager: 轮询池管理器
        """
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallback_history: List[FallbackAttempt] = []
        
    def get_circuit_breaker(self, target: str) -> CircuitBreaker:
        """获取或创建熔断器"""
        if target not in self.circuit_breakers:
            self.circuit_breakers[target] = CircuitBreaker()
        return self.circuit_breakers[target]
    
    async def execute_with_fallback(self,
                                  primary_target: str,
                                  fallback_groups: List[str],
                                  prompt: str,
                                  **kwargs) -> Any:
        """
        执行带降级的LLM调用
        
        Args:
            primary_target: 主要目标
            fallback_groups: 降级组列表
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        attempts = []
        max_attempts = len(fallback_groups) + 1
        
        for attempt_num in range(max_attempts):
            if attempt_num == 0:
                target = primary_target
                strategy = FallbackStrategy.TASK_GROUP_SWITCH
            else:
                target = fallback_groups[attempt_num - 1]
                strategy = self._determine_strategy(target)
            
            try:
                # 检查熔断器
                circuit_breaker = self.get_circuit_breaker(target)
                if not circuit_breaker.can_execute():
                    logger.warning(f"熔断器开启，跳过目标: {target}")
                    continue
                
                # 执行调用
                start_time = datetime.now()
                result = await self._execute_target(target, prompt, **kwargs)
                end_time = datetime.now()
                
                response_time = (end_time - start_time).total_seconds()
                
                # 记录成功
                circuit_breaker.record_success()
                attempt = FallbackAttempt(
                    attempt_number=attempt_num + 1,
                    strategy=strategy,
                    target=target,
                    success=True,
                    response_time=response_time
                )
                attempts.append(attempt)
                
                logger.info(f"LLM调用成功: {target}, 响应时间: {response_time:.2f}s")
                return result
                
            except Exception as e:
                # 记录失败
                circuit_breaker = self.get_circuit_breaker(target)
                circuit_breaker.record_failure()
                
                attempt = FallbackAttempt(
                    attempt_number=attempt_num + 1,
                    strategy=strategy,
                    target=target,
                    success=False,
                    error=str(e)
                )
                attempts.append(attempt)
                
                logger.warning(f"LLM调用失败: {target}, 错误: {e}")
                
                # 如果是最后一次尝试，抛出异常
                if attempt_num == max_attempts - 1:
                    self.fallback_history.extend(attempts)
                    raise LLMError(f"所有降级尝试都失败了: {[a.target for a in attempts]}")
        
        # 记录降级历史
        self.fallback_history.extend(attempts)
        
        # 清理历史记录，保留最近100条
        if len(self.fallback_history) > 100:
            self.fallback_history = self.fallback_history[-100:]
        
        raise LLMError("降级执行失败")
    
    def _determine_strategy(self, target: str) -> FallbackStrategy:
        """确定降级策略"""
        # 根据目标格式确定策略
        if "." in target:
            parts = target.split(".")
            if len(parts) == 2 and parts[1].startswith("echelon"):
                return FallbackStrategy.ECHELON_DOWN
            else:
                return FallbackStrategy.TASK_GROUP_SWITCH
        else:
            return FallbackStrategy.PROVIDER_FAILOVER
    
    async def _execute_target(self, target: str, prompt: str, **kwargs) -> Any:
        """执行目标调用"""
        # 尝试从轮询池获取
        if self.polling_pool_manager:
            pool_name = self._extract_pool_name(target)
            if pool_name:
                pool = self.polling_pool_manager.get_pool(pool_name)
                if pool:
                    return await pool.call_llm(prompt, **kwargs)
        
        # 尝试从任务组获取
        models = self.task_group_manager.get_models_for_group(target)
        if models:
            # TODO: 实现实际的LLM调用
            # 这里应该根据模型名称创建LLM客户端并调用
            await asyncio.sleep(0.1)  # 模拟调用延迟
            return f"模拟响应: {prompt[:50]}..."
        
        raise LLMError(f"无法执行目标: {target}")
    
    def _extract_pool_name(self, target: str) -> Optional[str]:
        """从目标中提取轮询池名称"""
        # 这里可以实现更复杂的逻辑来提取轮询池名称
        # 暂时返回None
        return None
    
    def get_fallback_history(self, limit: int = 10) -> List[FallbackAttempt]:
        """获取降级历史"""
        return self.fallback_history[-limit:]
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """获取熔断器状态"""
        status = {}
        for target, breaker in self.circuit_breakers.items():
            status[target] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "failure_threshold": breaker.failure_threshold,
                "last_failure_time": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
            }
        return status
    
    def reset_circuit_breaker(self, target: str) -> None:
        """重置熔断器"""
        if target in self.circuit_breakers:
            self.circuit_breakers[target] = CircuitBreaker()
            logger.info(f"熔断器已重置: {target}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.fallback_history:
            return {
                "total_attempts": 0,
                "successful_attempts": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "most_used_strategy": None,
                "strategy_distribution": {},
                "circuit_breakers": len(self.circuit_breakers)
            }
        
        total_attempts = len(self.fallback_history)
        successful_attempts = len([a for a in self.fallback_history if a.success])
        success_rate = successful_attempts / total_attempts if total_attempts > 0 else 0.0
        
        avg_response_time = 0.0
        successful_response_times = [a.response_time for a in self.fallback_history if a.success and a.response_time > 0]
        if successful_response_times:
            avg_response_time = sum(successful_response_times) / len(successful_response_times)
        
        # 统计最常用的策略
        strategy_counts = {}
        for attempt in self.fallback_history:
            strategy = attempt.strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        most_used_strategy = max(strategy_counts.items(), key=lambda x: x[1])[0] if strategy_counts else None
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "most_used_strategy": most_used_strategy,
            "strategy_distribution": strategy_counts,
            "circuit_breakers": len(self.circuit_breakers)
        }


class FallbackConfigManager:
    """降级配置管理器"""
    
    def __init__(self, task_group_manager: TaskGroupManager):
        """
        初始化降级配置管理器
        
        Args:
            task_group_manager: 任务组管理器
        """
        self.task_group_manager = task_group_manager
        self.fallback_configs: Dict[str, Dict[str, Any]] = {}
    
    def load_fallback_config(self, config: Dict[str, Any]) -> None:
        """加载降级配置"""
        self.fallback_configs = config.get("fallback_configs", {})
    
    def get_fallback_groups(self, primary_group: str) -> List[str]:
        """获取降级组列表"""
        # 首先检查特定配置
        if primary_group in self.fallback_configs:
            config = self.fallback_configs[primary_group]
            return config.get("fallback_groups", [])
        
        # 使用任务组管理器的默认降级逻辑
        return self.task_group_manager.get_fallback_groups(primary_group)
    
    def get_max_attempts(self, primary_group: str) -> int:
        """获取最大尝试次数"""
        if primary_group in self.fallback_configs:
            config = self.fallback_configs[primary_group]
            return config.get("max_attempts", 3)
        
        return 3
    
    def get_retry_delay(self, primary_group: str) -> float:
        """获取重试延迟"""
        if primary_group in self.fallback_configs:
            config = self.fallback_configs[primary_group]
            return config.get("retry_delay", 1.0)
        
        return 1.0
    
    def should_enable_circuit_breaker(self, primary_group: str) -> bool:
        """检查是否启用熔断器"""
        if primary_group in self.fallback_configs:
            config = self.fallback_configs[primary_group]
            return config.get("circuit_breaker", {}).get("enabled", True)
        
        return True