"""降级策略和日志记录器

基于configs/llms/groups和configs/llms/polling_pools配置的降级系统。
使用组配置时失败达到次数限制/429后先尝试同一层级，失败后再尝试下一层级。
轮询池则直接轮换。

注：Core层只定义策略算法，具体的执行编排在Services层实现。
"""

import time
from typing import Any, Dict, List

from ....interfaces.llm import ITaskGroupManager, IPollingPoolManager, IFallbackLogger, LLMResponse


class GroupBasedFallbackStrategy:
    """基于任务组的降级策略"""
    
    def __init__(self, task_group_manager: ITaskGroupManager):
        """
        初始化基于任务组的降级策略
        
        Args:
            task_group_manager: 任务组管理器接口
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
            if echelon_name:  # 确保echelon_name不为None
                same_echelon_targets = self._get_same_echelon_targets(group_name, echelon_name)
                fallback_targets.extend(same_echelon_targets)
        
        # 策略2: 如果同一层级失败，尝试下一层级
        if not fallback_targets or is_failure_limit:
            if echelon_name:  # 确保echelon_name不为None
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
            models = echelon_config.get("models", [])
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
    
    def __init__(self, polling_pool_manager: IPollingPoolManager):
        """
        初始化基于轮询池的降级策略
        
        Args:
            polling_pool_manager: 轮询池管理器接口
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


class DefaultFallbackLogger(IFallbackLogger):
    """默认降级日志记录器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化默认降级日志记录器
        
        Args:
            enabled: 是否启用日志记录
        """
        self.enabled = enabled
    
    def log_fallback_attempt(self, primary_model: str, fallback_model: str, 
                            error: Exception, attempt: int) -> None:
        """
        记录降级尝试
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            error: 发生的错误
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Fallback] 尝试 {attempt}: {primary_model} -> {fallback_model}, 错误: {error}")
    
    def log_fallback_success(self, primary_model: str, fallback_model: str,
                           response: LLMResponse, attempt: int) -> None:
        """
        记录降级成功
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            response: 响应结果
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Fallback] 成功: {primary_model} -> {fallback_model}, 尝试: {attempt}")
    
    def log_fallback_failure(self, primary_model: str, error: Exception, 
                           total_attempts: int) -> None:
        """
        记录降级失败
        
        Args:
            primary_model: 主模型名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Fallback] 失败: {primary_model}, 总尝试: {total_attempts}, 错误: {error}")
    
    def log_retry_success(self, func_name: str, result: Any, attempt: int) -> None:
        """
        记录重试成功
        
        Args:
            func_name: 函数名称
            result: 结果
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Retry] 成功: {func_name}, 尝试: {attempt}")
    
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """
        记录重试失败
        
        Args:
            func_name: 函数名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Retry] 失败: {func_name}, 总尝试: {total_attempts}, 错误: {error}")


