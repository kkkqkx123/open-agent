"""增强降级管理器

基于configs/llms/groups和configs/llms/polling_pools配置的降级系统。
使用组配置时失败达到次数限制/429后先尝试同一层级，失败后再尝试下一层级。
轮询池则直接轮换。
"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List, Tuple
from langchain_core.messages import BaseMessage

from ....services.llm.task_group_manager import TaskGroupManager
from ....services.llm.polling_pool import PollingPoolManager
from ....services.llm.fallback_system.fallback_manager import FallbackManager, DefaultFallbackLogger
from ....services.llm.fallback_system.fallback_config import FallbackConfig
from ....services.llm.fallback_system.interfaces import IClientFactory
from ..models import LLMResponse
from ..exceptions import LLMCallError


class GroupBasedFallbackStrategy:
    """基于任务组的降级策略"""
    
    def __init__(self, task_group_manager: TaskGroupManager):
        """
        初始化基于任务组的降级策略
        
        Args:
            task_group_manager: 任务组管理器
        """
        self.task_group_manager = task_group_manager
        self._failure_counts: Dict[str, int] = {}  # 记录每个目标的失败次数
        self._last_failure_time: Dict[str, float] = {}  # 记录最后失败时间
    
    def get_fallback_targets(self, primary_target: str, error: Exception) -> List[str]:
        """
        获取降级目标列表
        
        Args:
            primary_target: 主要目标，格式为 "group_name.echelon_name"
            error: 发生的错误
            
        Returns:
            降级目标列表
        """
        # 解析主要目标
        group_name, echelon_name = self.task_group_manager.parse_group_reference(primary_target)
        
        if not group_name:
            return []
        
        # 检查错误类型
        error_str = str(error).lower()
        is_rate_limit = "rate limit" in error_str or "429" in error_str
        is_failure_limit = self._check_failure_limit(primary_target)
        
        fallback_targets = []
        
        # 策略1: 如果是429错误或达到失败次数限制，先尝试同一层级的其他模型
        if is_rate_limit or is_failure_limit:
            same_echelon_targets = self._get_same_echelon_targets(group_name, echelon_name)
            fallback_targets.extend(same_echelon_targets)
        
        # 策略2: 如果同一层级失败，尝试下一层级
        if not fallback_targets or is_failure_limit:
            next_echelon_targets = self._get_next_echelon_targets(group_name, echelon_name)
            fallback_targets.extend(next_echelon_targets)
        
        # 策略3: 如果还是没有，尝试其他任务组
        if not fallback_targets:
            other_group_targets = self._get_other_group_targets(group_name)
            fallback_targets.extend(other_group_targets)
        
        return fallback_targets
    
    def _check_failure_limit(self, target: str) -> bool:
        """
        检查是否达到失败次数限制
        
        Args:
            target: 目标名称
            
        Returns:
            是否达到失败次数限制
        """
        failure_count = self._failure_counts.get(target, 0)
        # 默认失败次数限制为3次
        return failure_count >= 3
    
    def _get_same_echelon_targets(self, group_name: str, echelon_name: str) -> List[str]:
        """
        获取同一层级的其他目标
        
        Args:
            group_name: 组名称
            echelon_name: 层级名称
            
        Returns:
            同一层级的目标列表
        """
        try:
            echelon_config = self.task_group_manager.get_echelon_config(group_name, echelon_name)
            if not echelon_config:
                return []
            
            # 获取同一层级的所有模型
            models = echelon_config.models
            # 返回同一层级的其他模型（排除当前模型）
            return [f"{group_name}.{echelon_name}" for _ in models if len(models) > 1]
        except Exception:
            return []
    
    def _get_next_echelon_targets(self, group_name: str, echelon_name: str) -> List[str]:
        """
        获取下一层级的目标
        
        Args:
            group_name: 组名称
            echelon_name: 层级名称
            
        Returns:
            下一层级的目标列表
        """
        try:
            # 获取任务组的所有层级，按优先级排序
            echelons = self.task_group_manager.get_group_models_by_priority(group_name)
            
            # 找到当前层级的索引
            current_index = -1
            for i, (echelon, priority, models) in enumerate(echelons):
                if echelon == echelon_name:
                    current_index = i
                    break
            
            # 返回下一层级
            if current_index >= 0 and current_index + 1 < len(echelons):
                next_echelon = echelons[current_index + 1][0]
                return [f"{group_name}.{next_echelon}"]
            
            return []
        except Exception:
            return []
    
    def _get_other_group_targets(self, group_name: str) -> List[str]:
        """
        获取其他任务组的目标
        
        Args:
            group_name: 组名称
            
        Returns:
            其他任务组的目标列表
        """
        try:
            # 获取所有任务组
            all_groups = self.task_group_manager.list_task_groups()
            
            # 获取其他任务组的第一个层级
            targets = []
            for other_group in all_groups:
                if other_group != group_name:
                    echelons = self.task_group_manager.get_group_models_by_priority(other_group)
                    if echelons:
                        first_echelon = echelons[0][0]
                        targets.append(f"{other_group}.{first_echelon}")
            
            return targets
        except Exception:
            return []
    
    def record_failure(self, target: str, error: Exception) -> None:
        """
        记录失败
        
        Args:
            target: 目标名称
            error: 错误信息
        """
        self._failure_counts[target] = self._failure_counts.get(target, 0) + 1
        self._last_failure_time[target] = time.time()
    
    def record_success(self, target: str) -> None:
        """
        记录成功
        
        Args:
            target: 目标名称
        """
        # 成功时重置失败计数
        if target in self._failure_counts:
            del self._failure_counts[target]
        if target in self._last_failure_time:
            del self._last_failure_time[target]


class PollingPoolFallbackStrategy:
    """基于轮询池的降级策略"""
    
    def __init__(self, polling_pool_manager: PollingPoolManager):
        """
        初始化基于轮询池的降级策略
        
        Args:
            polling_pool_manager: 轮询池管理器
        """
        self.polling_pool_manager = polling_pool_manager
    
    def get_fallback_targets(self, primary_target: str, error: Exception) -> List[str]:
        """
        获取降级目标列表（轮询池直接轮换）
        
        Args:
            primary_target: 主要目标（轮询池名称）
            error: 发生的错误
            
        Returns:
            降级目标列表（对于轮询池，返回空列表，由轮询池内部处理轮换）
        """
        # 轮询池内部处理实例轮换，不需要外部降级目标
        return []


class EnhancedFallbackManager:
    """增强降级管理器"""
    
    def __init__(self, 
                 task_group_manager: TaskGroupManager,
                 polling_pool_manager: PollingPoolManager,
                 client_factory: IClientFactory,
                 logger: Optional[Any] = None):
        """
        初始化增强降级管理器
        
        Args:
            task_group_manager: 任务组管理器
            polling_pool_manager: 轮询池管理器
            client_factory: 客户端工厂
            logger: 日志记录器
        """
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        self.client_factory = client_factory
        self.logger = logger or DefaultFallbackLogger()
        
        # 创建降级策略
        self.group_strategy = GroupBasedFallbackStrategy(task_group_manager)
        self.pool_strategy = PollingPoolFallbackStrategy(polling_pool_manager)
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }
    
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        执行带降级的请求
        
        Args:
            primary_target: 主要目标
            fallback_groups: 降级组列表
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
            
        Raises:
            LLMCallError: 所有尝试都失败
        """
        self._stats["total_requests"] += 1
        
        try:
            # 判断是任务组还是轮询池
            if self._is_polling_pool_target(primary_target):
                return await self._execute_with_pool_fallback(primary_target, prompt, parameters, **kwargs)
            else:
                return await self._execute_with_group_fallback(primary_target, prompt, parameters, **kwargs)
                
        except Exception as e:
            self._stats["failed_requests"] += 1
            self.logger.log_fallback_failure(primary_target, e, 1)
            raise LLMCallError(f"降级执行失败: {e}")
    
    async def _execute_with_group_fallback(
        self,
        primary_target: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        使用任务组降级策略执行
        
        Args:
            primary_target: 主要目标
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        current_target = primary_target
        attempt = 0
        last_error = None
        
        while attempt < 5:  # 最大尝试5次
            try:
                # 获取目标模型列表
                models = self.task_group_manager.get_models_for_group(current_target)
                if not models:
                    raise ValueError(f"没有找到模型: {current_target}")
                
                # 选择第一个模型
                model_name = models[0]
                
                # 创建客户端并执行
                client = self.client_factory.create_client(model_name)
                messages = [BaseMessage(content=prompt)]
                response = await client.generate_async(messages, parameters or {}, **kwargs)
                
                # 记录成功
                self.group_strategy.record_success(current_target)
                self._stats["successful_requests"] += 1
                
                if attempt > 0:
                    self._stats["group_fallbacks"] += 1
                    self.logger.log_fallback_success(primary_target, current_target, response, attempt + 1)
                
                return response
                
            except Exception as e:
                last_error = e
                self.group_strategy.record_failure(current_target, e)
                
                # 获取降级目标
                fallback_targets = self.group_strategy.get_fallback_targets(current_target, e)
                
                if not fallback_targets or attempt >= 4:
                    break
                
                # 选择下一个降级目标
                current_target = fallback_targets[0]
                attempt += 1
                
                # 记录降级尝试
                self.logger.log_fallback_attempt(primary_target, current_target, e, attempt + 1)
        
        # 所有尝试都失败
        raise last_error or LLMCallError("任务组降级失败")
    
    async def _execute_with_pool_fallback(
        self,
        primary_target: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        使用轮询池降级策略执行
        
        Args:
            primary_target: 主要目标（轮询池名称）
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        pool = self.polling_pool_manager.get_pool(primary_target)
        if not pool:
            raise ValueError(f"轮询池不存在: {primary_target}")
        
        try:
            # 轮询池内部处理实例轮换和降级
            result = await pool.call_llm(prompt, **kwargs)
            
            self._stats["successful_requests"] += 1
            self._stats["pool_fallbacks"] += 1
            
            return result
            
        except Exception as e:
            raise LLMCallError(f"轮询池执行失败: {e}")
    
    def _is_polling_pool_target(self, target: str) -> bool:
        """
        判断目标是否是轮询池
        
        Args:
            target: 目标名称
            
        Returns:
            是否是轮询池
        """
        # 检查是否是已知的轮询池
        pools = self.polling_pool_manager.list_all_status()
        return target in pools
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }