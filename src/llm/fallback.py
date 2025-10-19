"""LLM降级策略实现"""

import time
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from .interfaces import ILLMClient
from .models import LLMResponse, LLMError
from .exceptions import (
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
    LLMFallbackError,
)

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """降级策略枚举"""

    SEQUENTIAL = "sequential"  # 顺序降级
    PARALLEL = "parallel"  # 并行降级
    RANDOM = "random"  # 随机降级
    PRIORITY = "priority"  # 优先级降级


@dataclass
class FallbackModel:
    """降级模型配置"""

    name: str
    priority: int = 0  # 优先级，数字越小优先级越高
    weight: float = 1.0  # 权重，用于随机选择
    enabled: bool = True  # 是否启用
    conditions: Optional[List[Callable[[Exception], bool]]] = None  # 触发条件


class FallbackManager:
    """降级管理器"""

    def __init__(
        self,
        fallback_models: List[FallbackModel],
        strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
        max_attempts: int = 3,
        timeout: float = 30.0,
    ) -> None:
        """
        初始化降级管理器

        Args:
            fallback_models: 降级模型列表
            strategy: 降级策略
            max_attempts: 最大尝试次数
            timeout: 超时时间
        """
        self.fallback_models = sorted(fallback_models, key=lambda m: m.priority)
        self.strategy = strategy
        self.max_attempts = max_attempts
        self.timeout = timeout

        # 统计信息
        self.stats = {
            "total_fallbacks": 0,
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "model_usage": {},
        }

    def execute_fallback(
        self,
        primary_client: ILLMClient,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        执行降级策略

        Args:
            primary_client: 主客户端
            messages: 消息列表
            parameters: 参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应结果

        Raises:
            LLMFallbackError: 降级失败
        """
        self.stats["total_fallbacks"] += 1

        try:
            # 首先尝试主客户端
            return primary_client.generate(messages, parameters, **kwargs)
        except Exception as primary_error:
            logger.warning(f"主客户端调用失败: {primary_error}")

            # 根据策略执行降级
            if self.strategy == FallbackStrategy.SEQUENTIAL:
                return self._sequential_fallback(
                    messages, parameters, primary_error, **kwargs
                )
            elif self.strategy == FallbackStrategy.PARALLEL:
                return self._parallel_fallback(
                    messages, parameters, primary_error, **kwargs
                )
            elif self.strategy == FallbackStrategy.RANDOM:
                return self._random_fallback(
                    messages, parameters, primary_error, **kwargs
                )
            elif self.strategy == FallbackStrategy.PRIORITY:
                return self._priority_fallback(
                    messages, parameters, primary_error, **kwargs
                )
            else:
                raise LLMFallbackError(f"不支持的降级策略: {self.strategy}")

    def _sequential_fallback(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        primary_error: Exception,
        **kwargs,
    ) -> LLMResponse:
        """顺序降级"""
        last_error = primary_error

        for i, model in enumerate(self.fallback_models):
            if not model.enabled:
                continue

            # 检查触发条件
            if model.conditions and not any(
                condition(primary_error) for condition in model.conditions
            ):
                continue

            try:
                logger.info(f"尝试降级到模型: {model.name} (第 {i+1} 个模型)")

                # 获取降级客户端
                fallback_client = self._get_fallback_client(model.name)

                # 调用降级客户端
                response = fallback_client.generate(messages, parameters, **kwargs)

                # 标记降级成功
                response.metadata["fallback_model"] = model.name
                response.metadata["fallback_strategy"] = self.strategy.value
                response.metadata["fallback_attempt"] = i + 1

                # 更新统计
                self.stats["successful_fallbacks"] += 1
                self._update_model_usage(model.name, True)

                logger.info(f"降级成功: {model.name}")
                return response

            except Exception as fallback_error:
                logger.warning(f"降级到模型 {model.name} 失败: {fallback_error}")
                last_error = fallback_error
                self._update_model_usage(model.name, False)

        # 所有降级都失败
        self.stats["failed_fallbacks"] += 1
        raise LLMFallbackError("所有降级模型都失败", last_error)

    def _parallel_fallback(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        primary_error: Exception,
        **kwargs,
    ) -> LLMResponse:
        """并行降级"""
        import concurrent.futures

        # 获取可用的降级模型
        available_models = [
            model
            for model in self.fallback_models
            if model.enabled
            and (
                not model.conditions
                or any(condition(primary_error) for condition in model.conditions)
            )
        ]

        if not available_models:
            raise LLMFallbackError("没有可用的降级模型", primary_error)

        # 并行调用所有降级模型
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(available_models)
        ) as executor:
            # 提交所有任务
            future_to_model = {
                executor.submit(
                    self._try_fallback_model, model.name, messages, parameters, **kwargs
                ): model
                for model in available_models
            }

            # 等待第一个成功的结果
            for future in concurrent.futures.as_completed(
                future_to_model, timeout=self.timeout
            ):
                model = future_to_model[future]

                try:
                    response = future.result()

                    # 标记降级成功
                    response.metadata["fallback_model"] = model.name
                    response.metadata["fallback_strategy"] = self.strategy.value

                    # 更新统计
                    self.stats["successful_fallbacks"] += 1
                    self._update_model_usage(model.name, True)

                    logger.info(f"并行降级成功: {model.name}")
                    return response

                except Exception as fallback_error:
                    logger.warning(
                        f"并行降级到模型 {model.name} 失败: {fallback_error}"
                    )
                    self._update_model_usage(model.name, False)

        # 所有降级都失败
        self.stats["failed_fallbacks"] += 1
        raise LLMFallbackError("所有并行降级模型都失败", primary_error)

    def _random_fallback(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        primary_error: Exception,
        **kwargs,
    ) -> LLMResponse:
        """随机降级"""
        import random

        # 获取可用的降级模型
        available_models = [
            model
            for model in self.fallback_models
            if model.enabled
            and (
                not model.conditions
                or any(condition(primary_error) for condition in model.conditions)
            )
        ]

        if not available_models:
            raise LLMFallbackError("没有可用的降级模型", primary_error)

        # 根据权重随机选择模型
        weights = [model.weight for model in available_models]
        selected_models = random.choices(
            available_models, weights=weights, k=self.max_attempts
        )

        last_error = primary_error

        for i, model in enumerate(selected_models):
            try:
                logger.info(f"随机降级到模型: {model.name} (第 {i+1} 次尝试)")

                # 获取降级客户端
                fallback_client = self._get_fallback_client(model.name)

                # 调用降级客户端
                response = fallback_client.generate(messages, parameters, **kwargs)

                # 标记降级成功
                response.metadata["fallback_model"] = model.name
                response.metadata["fallback_strategy"] = self.strategy.value
                response.metadata["fallback_attempt"] = i + 1

                # 更新统计
                self.stats["successful_fallbacks"] += 1
                self._update_model_usage(model.name, True)

                logger.info(f"随机降级成功: {model.name}")
                return response

            except Exception as fallback_error:
                logger.warning(f"随机降级到模型 {model.name} 失败: {fallback_error}")
                last_error = fallback_error
                self._update_model_usage(model.name, False)

        # 所有降级都失败
        self.stats["failed_fallbacks"] += 1
        raise LLMFallbackError("所有随机降级模型都失败", last_error)

    def _priority_fallback(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        primary_error: Exception,
        **kwargs,
    ) -> LLMResponse:
        """优先级降级"""
        # 按优先级排序的模型已经存储在self.fallback_models中
        return self._sequential_fallback(messages, parameters, primary_error, **kwargs)

    def _try_fallback_model(
        self,
        model_name: str,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        **kwargs,
    ) -> LLMResponse:
        """尝试调用降级模型"""
        fallback_client = self._get_fallback_client(model_name)
        return fallback_client.generate(messages, parameters, **kwargs)

    def _get_fallback_client(self, model_name: str) -> ILLMClient:
        """获取降级客户端"""
        from .factory import get_global_factory

        factory = get_global_factory()

        # 尝试从缓存获取
        client = factory.get_cached_client(model_name)
        if client is not None:
            return client

        # 创建新客户端
        model_type = self._get_model_type(model_name)
        config = {"model_type": model_type, "model_name": model_name}

        client = factory.create_client(config)
        factory.cache_client(model_name, client)

        return client

    def _get_model_type(self, model_name: str) -> str:
        """根据模型名称获取模型类型"""
        if "gpt" in model_name.lower():
            return "openai"
        elif "gemini" in model_name.lower():
            return "gemini"
        elif "claude" in model_name.lower():
            return "anthropic"
        else:
            return "mock"

    def _update_model_usage(self, model_name: str, success: bool) -> None:
        """更新模型使用统计"""
        if model_name not in self.stats["model_usage"]:
            self.stats["model_usage"][model_name] = {"success": 0, "failure": 0}

        if success:
            self.stats["model_usage"][model_name]["success"] += 1
        else:
            self.stats["model_usage"][model_name]["failure"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_fallbacks"]
        if total == 0:
            return self.stats.copy()

        success_rate = self.stats["successful_fallbacks"] / total

        return {**self.stats, "success_rate": success_rate}

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_fallbacks": 0,
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "model_usage": {},
        }


class ConditionalFallback:
    """条件降级"""

    @staticmethod
    def on_timeout(error: Exception) -> bool:
        """超时条件"""
        return isinstance(error, LLMTimeoutError)

    @staticmethod
    def on_rate_limit(error: Exception) -> bool:
        """频率限制条件"""
        return isinstance(error, LLMRateLimitError)

    @staticmethod
    def on_service_unavailable(error: Exception) -> bool:
        """服务不可用条件"""
        return isinstance(error, LLMServiceUnavailableError)

    @staticmethod
    def on_authentication_error(error: Exception) -> bool:
        """认证错误条件"""
        return isinstance(error, LLMAuthenticationError)

    @staticmethod
    def on_model_not_found(error: Exception) -> bool:
        """模型未找到条件"""
        return isinstance(error, LLMModelNotFoundError)

    @staticmethod
    def on_token_limit(error: Exception) -> bool:
        """Token限制条件"""
        return isinstance(error, LLMTokenLimitError)

    @staticmethod
    def on_content_filter(error: Exception) -> bool:
        """内容过滤条件"""
        return isinstance(error, LLMContentFilterError)

    @staticmethod
    def on_invalid_request(error: Exception) -> bool:
        """无效请求条件"""
        return isinstance(error, LLMInvalidRequestError)

    @staticmethod
    def on_any_error(error: Exception) -> bool:
        """任意错误条件"""
        return isinstance(error, LLMCallError)

    @staticmethod
    def on_retryable_error(error: Exception) -> bool:
        """可重试错误条件"""
        retryable_errors = (
            LLMTimeoutError,
            LLMRateLimitError,
            LLMServiceUnavailableError,
        )
        return isinstance(error, retryable_errors)
