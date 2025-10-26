"""LLM调用钩子实现"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple, Sequence
from datetime import datetime

from langchain_core.messages import BaseMessage

from .interfaces import ILLMCallHook
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


class LoggingHook(ILLMCallHook):
    """日志记录钩子"""

    def __init__(
        self,
        log_requests: bool = True,
        log_responses: bool = True,
        log_errors: bool = True,
        structured_logging: bool = True,
        include_sensitive_data: bool = False,
    ) -> None:
        """
        初始化日志钩子

        Args:
            log_requests: 是否记录请求
            log_responses: 是否记录响应
            log_errors: 是否记录错误
            structured_logging: 是否使用结构化日志
            include_sensitive_data: 是否包含敏感数据
        """
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_errors = log_errors
        self.structured_logging = structured_logging
        self.include_sensitive_data = include_sensitive_data

    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用前的日志"""
        if not self.log_requests:
            return

        if self.structured_logging:
            self._log_structured_request(messages, parameters, **kwargs)
        else:
            self._log_simple_request(messages, parameters, **kwargs)

    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用后的日志"""
        if not self.log_responses or response is None:
            return

        if self.structured_logging:
            self._log_structured_response(response, messages, parameters, **kwargs)
        else:
            self._log_simple_response(response, messages, parameters, **kwargs)

    def on_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """记录错误日志"""
        if not self.log_errors:
            return None

        if self.structured_logging:
            self._log_structured_error(error, messages, parameters, **kwargs)
        else:
            self._log_simple_error(error, messages, parameters, **kwargs)

        # 不尝试恢复错误
        return None

    def _log_structured_request(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录结构化请求日志"""
        log_data = {
            "event": "llm_call_start",
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "model": kwargs.get("model", "unknown"),
            "request_id": kwargs.get("request_id"),
        }

        # 添加参数信息（脱敏）
        if parameters:
            log_data["parameters"] = self._sanitize_parameters(parameters)

        # 添加消息摘要
        if messages:
            log_data["messages_summary"] = {
                "count": len(messages),
                "types": [type(msg).__name__ for msg in messages],
                "total_chars": sum(len(str(getattr(msg, 'content', ''))) for msg in messages),
            }

        # 添加额外上下文
        if "retry_count" in kwargs:
            log_data["retry_count"] = kwargs["retry_count"]
        if "fallback_attempts" in kwargs:
            log_data["fallback_attempts"] = kwargs["fallback_attempts"]

        logger.info("LLM调用开始", extra={"structured_data": log_data})

    def _log_structured_response(
        self,
        response: LLMResponse,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录结构化响应日志"""
        log_data = {
            "event": "llm_call_complete",
            "timestamp": datetime.now().isoformat(),
            "model": response.model,
            "finish_reason": response.finish_reason,
            "response_time": response.response_time,
            "token_usage": {
                "prompt_tokens": response.token_usage.prompt_tokens,
                "completion_tokens": response.token_usage.completion_tokens,
                "total_tokens": response.token_usage.total_tokens,
            },
            "request_id": kwargs.get("request_id"),
        }

        # 添加性能指标
        if response.response_time:
            log_data["performance"] = {
                "tokens_per_second": response.token_usage.total_tokens / response.response_time,
                "response_time_ms": response.response_time * 1000,
            }

        # 添加函数调用信息
        if response.function_call:
            log_data["function_call"] = {
                "name": response.function_call.get("name"),
                "arguments": response.function_call.get("arguments"),
            }

        # 添加元数据
        if response.metadata:
            log_data["metadata"] = response.metadata

        logger.info("LLM调用完成", extra={"structured_data": log_data})

    def _log_structured_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录结构化错误日志"""
        log_data = {
            "event": "llm_call_error",
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "message_count": len(messages),
            "model": kwargs.get("model", "unknown"),
            "request_id": kwargs.get("request_id"),
        }

        # 添加错误特定信息
        if hasattr(error, 'status_code'):
            log_data["status_code"] = getattr(error, 'status_code', None)
        if hasattr(error, 'retry_after'):
            log_data["retry_after"] = getattr(error, 'retry_after', None)
        if hasattr(error, 'error_code'):
            log_data["error_code"] = getattr(error, 'error_code', None)

        # 添加重试和降级信息
        if "retry_count" in kwargs:
            log_data["retry_count"] = kwargs["retry_count"]
        if "fallback_attempts" in kwargs:
            log_data["fallback_attempts"] = kwargs["fallback_attempts"]

        # 添加请求上下文
        if parameters:
            log_data["request_parameters"] = self._sanitize_parameters(parameters)

        logger.error("LLM调用失败", extra={"structured_data": log_data})

    def _log_simple_request(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录简单请求日志"""
        logger.info(f"LLM调用开始 - 消息数量: {len(messages)}, 参数: {parameters}")

        # 记录消息内容（调试级别）
        if logger.isEnabledFor(logging.DEBUG):
            for i, message in enumerate(messages):
                logger.debug(f"消息 {i+1}: {str(getattr(message, 'content', ''))[:100]}...")

    def _log_simple_response(
        self,
        response: LLMResponse,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录简单响应日志"""
        logger.info(
            f"LLM调用完成 - 模型: {response.model}, "
            f"响应时间: {response.response_time:.2f}s, "
            f"Token使用: {response.token_usage.total_tokens}"
        )

        # 记录响应内容（调试级别）
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"响应内容: {response.content[:200]}...")

    def _log_simple_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录简单错误日志"""
        logger.error(
            f"LLM调用失败 - 错误类型: {type(error).__name__}, 错误信息: {str(error)}"
        )

    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏处理参数"""
        if self.include_sensitive_data:
            return parameters

        sanitized = {}
        sensitive_keys = ["api_key", "authorization", "token", "password", "secret"]
        
        for key, value in parameters.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            else:
                sanitized[key] = value
                
        return sanitized


class StructuredLoggingHook(LoggingHook):
    """结构化日志钩子（专门用于结构化日志）"""
    
    def __init__(
        self,
        logger_name: str = "llm.structured",
        include_sensitive_data: bool = False,
        log_level: str = "INFO",
    ) -> None:
        """
        初始化结构化日志钩子
        
        Args:
            logger_name: 日志记录器名称
            include_sensitive_data: 是否包含敏感数据
            log_level: 日志级别
        """
        super().__init__(
            log_requests=True,
            log_responses=True,
            log_errors=True,
            structured_logging=True,
            include_sensitive_data=include_sensitive_data,
        )
        
        self.logger = logging.getLogger(logger_name)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)


class MetricsHook(ILLMCallHook):
    """增强的指标收集钩子"""

    def __init__(
        self,
        enable_performance_tracking: bool = True,
        enable_detailed_metrics: bool = True,
        max_history_size: int = 1000,
    ) -> None:
        """
        初始化指标钩子
        
        Args:
            enable_performance_tracking: 是否启用性能追踪
            enable_detailed_metrics: 是否启用详细指标
            max_history_size: 最大历史记录大小
        """
        self.enable_performance_tracking = enable_performance_tracking
        self.enable_detailed_metrics = enable_detailed_metrics
        self.max_history_size = max_history_size
        
        # 基础指标
        self.metrics: Dict[str, Any] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "error_counts": {},
            "model_usage": {},
            "hourly_stats": {},
        }
        
        # 性能指标
        self.performance_metrics: Dict[str, Any] = {
            "response_times": [],
            "token_per_second_rates": [],
            "latency_percentiles": {},
            "throughput_metrics": {},
        }
        
        # 历史记录
        self.call_history: List[Dict[str, Any]] = []
        
        # 时间窗口统计
        self.windowed_stats: Dict[str, Any] = {
            "last_minute": {"calls": 0, "tokens": 0, "errors": 0},
            "last_hour": {"calls": 0, "tokens": 0, "errors": 0},
            "last_day": {"calls": 0, "tokens": 0, "errors": 0},
        }

    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用开始"""
        self.metrics["total_calls"] = int(self.metrics["total_calls"]) + 1
        kwargs["_start_time"] = time.time()
        kwargs["_call_id"] = f"{int(time.time() * 1000)}_{self.metrics['total_calls']}"

    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用完成"""
        if response is None:
            return

        self.metrics["successful_calls"] = int(self.metrics["successful_calls"]) + 1

        # 记录Token使用
        total_tokens = response.token_usage.total_tokens
        self.metrics["total_tokens"] = int(self.metrics["total_tokens"]) + total_tokens

        # 记录响应时间
        if response.response_time:
            response_time = response.response_time
            self.metrics["total_response_time"] = (
                float(self.metrics["total_response_time"]) + response_time
            )
            
            # 性能追踪
            if self.enable_performance_tracking:
                self._track_performance(response, response_time, total_tokens, **kwargs)

        # 模型使用统计
        model_key = response.model
        self.metrics["model_usage"][model_key] = self.metrics["model_usage"].get(model_key, 0) + 1

        # 按小时统计
        if self.enable_detailed_metrics:
            self._update_hourly_stats(response, total_tokens)

        # 历史记录
        if self.enable_detailed_metrics:
            self._add_to_history(response, messages, parameters, **kwargs)

        # 时间窗口统计
        self._update_windowed_stats(success=True, tokens=total_tokens)

    def on_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """记录错误"""
        self.metrics["failed_calls"] = int(self.metrics["failed_calls"]) + 1

        # 记录错误类型计数
        error_type = type(error).__name__
        error_counts = self.metrics["error_counts"]
        if isinstance(error_counts, dict):
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        else:
            error_counts = {error_type: 1}
        self.metrics["error_counts"] = error_counts

        # 时间窗口统计
        self._update_windowed_stats(success=False, tokens=0)

        # 记录错误历史
        if self.enable_detailed_metrics:
            self._add_error_to_history(error, messages, parameters, **kwargs)

        # 不尝试恢复错误
        return None

    def _track_performance(
        self,
        response: LLMResponse,
        response_time: float,
        total_tokens: int,
        **kwargs: Any,
    ) -> None:
        """追踪性能指标"""
        # 响应时间记录
        self.performance_metrics["response_times"].append(response_time)
        
        # Token每秒速率
        if response_time > 0:
            tokens_per_second = total_tokens / response_time
            self.performance_metrics["token_per_second_rates"].append(tokens_per_second)
        
        # 保持历史大小
        if len(self.performance_metrics["response_times"]) > self.max_history_size:
            self.performance_metrics["response_times"].pop(0)
        if len(self.performance_metrics["token_per_second_rates"]) > self.max_history_size:
            self.performance_metrics["token_per_second_rates"].pop(0)
        
        # 计算延迟百分位数
        self._calculate_latency_percentiles()
        
        # 计算吞吐量指标
        self._calculate_throughput_metrics()

    def _calculate_latency_percentiles(self) -> None:
        """计算延迟百分位数"""
        response_times = self.performance_metrics["response_times"]
        if not response_times:
            return
        
        import statistics
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        self.performance_metrics["latency_percentiles"] = {
            "p50": sorted_times[n // 2],
            "p90": sorted_times[int(n * 0.9)],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)],
            "min": min(sorted_times),
            "max": max(sorted_times),
            "mean": statistics.mean(sorted_times),
            "median": statistics.median(sorted_times),
        }

    def _calculate_throughput_metrics(self) -> None:
        """计算吞吐量指标"""
        if not self.call_history:
            return
        
        now = time.time()
        
        # 最近1分钟的吞吐量
        recent_calls = [
            call for call in self.call_history
            if now - call.get("timestamp", 0) <= 60
        ]
        
        if recent_calls:
            calls_per_minute = len(recent_calls)
            tokens_per_minute = sum(call.get("tokens", 0) for call in recent_calls)
            
            self.performance_metrics["throughput_metrics"] = {
                "calls_per_minute": calls_per_minute,
                "tokens_per_minute": tokens_per_minute,
                "avg_tokens_per_call": tokens_per_minute / max(calls_per_minute, 1),
            }

    def _update_hourly_stats(self, response: LLMResponse, total_tokens: int) -> None:
        """更新按小时统计"""
        hour_key = response.timestamp.strftime("%Y-%m-%d %H:00")
        
        if hour_key not in self.metrics["hourly_stats"]:
            self.metrics["hourly_stats"][hour_key] = {
                "calls": 0,
                "tokens": 0,
                "errors": 0,
                "avg_response_time": 0.0,
            }
        
        stats = self.metrics["hourly_stats"][hour_key]
        stats["calls"] += 1
        stats["tokens"] += total_tokens
        
        if response.response_time:
            # 更新平均响应时间
            current_avg = stats["avg_response_time"]
            stats["avg_response_time"] = (
                (current_avg * (stats["calls"] - 1) + response.response_time) / stats["calls"]
            )

    def _add_to_history(
        self,
        response: LLMResponse,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """添加到历史记录"""
        history_entry = {
            "timestamp": time.time(),
            "call_id": kwargs.get("_call_id"),
            "model": response.model,
            "tokens": response.token_usage.total_tokens,
            "response_time": response.response_time,
            "success": True,
            "message_count": len(messages),
        }
        
        self.call_history.append(history_entry)
        
        # 保持历史大小
        if len(self.call_history) > self.max_history_size:
            self.call_history.pop(0)

    def _add_error_to_history(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """添加错误到历史记录"""
        history_entry = {
            "timestamp": time.time(),
            "call_id": kwargs.get("_call_id"),
            "model": kwargs.get("model", "unknown"),
            "tokens": 0,
            "response_time": None,
            "success": False,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "message_count": len(messages),
        }
        
        self.call_history.append(history_entry)
        
        # 保持历史大小
        if len(self.call_history) > self.max_history_size:
            self.call_history.pop(0)

    def _update_windowed_stats(self, success: bool, tokens: int) -> None:
        """更新时间窗口统计"""
        now = time.time()
        
        # 更新各个时间窗口
        for window_name, duration in [("last_minute", 60), ("last_hour", 3600), ("last_day", 86400)]:
            # 这里简化处理，实际应该基于时间戳过滤
            self.windowed_stats[window_name]["calls"] += 1
            if success:
                self.windowed_stats[window_name]["tokens"] += tokens
            else:
                self.windowed_stats[window_name]["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取完整指标"""
        total_calls = int(self.metrics["total_calls"])

        if total_calls == 0:
            return {**self.metrics, **self.performance_metrics, **self.windowed_stats}

        # 计算基础平均值
        total_response_time = float(self.metrics["total_response_time"])
        successful_calls = int(self.metrics["successful_calls"])
        total_tokens = int(self.metrics["total_tokens"])

        avg_response_time = total_response_time / max(float(successful_calls), 1.0)
        avg_tokens = float(total_tokens) / max(float(successful_calls), 1.0)
        success_rate = float(successful_calls) / float(total_calls)

        return {
            **self.metrics,
            "average_response_time": avg_response_time,
            "average_tokens_per_call": avg_tokens,
            "success_rate": success_rate,
            **self.performance_metrics,
            **self.windowed_stats,
        }

    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """获取特定模型的性能指标"""
        model_calls = [
            call for call in self.call_history
            if call.get("model") == model_name
        ]
        
        if not model_calls:
            return {}
        
        successful_calls = [call for call in model_calls if call["success"]]
        
        # 计算模型特定指标
        total_calls = len(model_calls)
        successful_count = len(successful_calls)
        total_tokens = sum(call["tokens"] for call in successful_calls)
        total_response_time = sum(call["response_time"] for call in successful_calls if call["response_time"])
        
        return {
            "model": model_name,
            "total_calls": total_calls,
            "successful_calls": successful_count,
            "success_rate": successful_count / total_calls if total_calls > 0 else 0,
            "total_tokens": total_tokens,
            "average_tokens_per_call": total_tokens / successful_count if successful_count > 0 else 0,
            "average_response_time": total_response_time / successful_count if successful_count > 0 else 0,
        }

    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        metrics = self.get_metrics()
        
        # 健康指标
        success_rate = metrics.get("success_rate", 0)
        avg_response_time = metrics.get("average_response_time", 0)
        error_rate = 1 - success_rate
        
        # 健康状态判断
        health_status = "healthy"
        if success_rate < 0.9:
            health_status = "degraded"
        if success_rate < 0.8 or avg_response_time > 30:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "average_response_time": avg_response_time,
            "total_calls": metrics.get("total_calls", 0),
            "recent_errors": metrics.get("error_counts", {}),
            "recommendations": self._get_health_recommendations(success_rate, avg_response_time),
        }

    def _get_health_recommendations(self, success_rate: float, avg_response_time: float) -> List[str]:
        """获取健康建议"""
        recommendations = []
        
        if success_rate < 0.9:
            recommendations.append("成功率较低，建议检查错误日志和网络连接")
        
        if avg_response_time > 10:
            recommendations.append("响应时间较长，建议优化请求或考虑使用更快的模型")
        
        if avg_response_time > 30:
            recommendations.append("响应时间过长，建议检查系统负载和网络状况")
        
        return recommendations

    def reset_metrics(self) -> None:
        """重置所有指标"""
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "error_counts": {},
            "model_usage": {},
            "hourly_stats": {},
        }
        
        self.performance_metrics = {
            "response_times": [],
            "token_per_second_rates": [],
            "latency_percentiles": {},
            "throughput_metrics": {},
        }
        
        self.call_history.clear()
        
        self.windowed_stats = {
            "last_minute": {"calls": 0, "tokens": 0, "errors": 0},
            "last_hour": {"calls": 0, "tokens": 0, "errors": 0},
            "last_day": {"calls": 0, "tokens": 0, "errors": 0},
        }

    def export_metrics(self, format: str = "json") -> str:
        """导出指标数据"""
        metrics = self.get_metrics()
        
        if format.lower() == "json":
            import json
            return json.dumps(metrics, indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            return self._export_to_csv()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def _export_to_csv(self) -> str:
        """导出为CSV格式"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题
        writer.writerow([
            "Timestamp", "Call_ID", "Model", "Success", "Tokens",
            "Response_Time", "Message_Count", "Error_Type"
        ])
        
        # 写入数据
        for call in self.call_history:
            writer.writerow([
                call.get("timestamp", ""),
                call.get("call_id", ""),
                call.get("model", ""),
                call.get("success", ""),
                call.get("tokens", ""),
                call.get("response_time", ""),
                call.get("message_count", ""),
                call.get("error_type", ""),
            ])
        
        return output.getvalue()


class FallbackHook(ILLMCallHook):
    """降级处理钩子"""

    def __init__(self, fallback_models: List[str], max_attempts: int = 3) -> None:
        """
        初始化降级钩子

        Args:
            fallback_models: 降级模型列表
            max_attempts: 最大尝试次数
        """
        self.fallback_models = fallback_models
        self.max_attempts = max_attempts

    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用开始"""
        # 记录当前尝试次数
        if parameters is None:
            parameters = {}

        if "_attempt_count" not in parameters:
            parameters["_attempt_count"] = 1
        else:
            parameters["_attempt_count"] += 1

    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用成功"""
        # 成功调用，不需要降级
        pass

    def on_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """尝试降级处理"""
        # 检查是否应该重试
        retry_decision = self._should_retry(error, **kwargs)
        if not retry_decision["should_retry"]:
            return None

        # 获取当前尝试次数
        attempt_count = (
            parameters.get("_attempt_count", 1)
            if parameters
            else kwargs.get("_attempt_count", 1)
        )

        # 检查是否超过最大尝试次数
        if attempt_count >= self.max_attempts:
            logger.error(f"降级失败：已达到最大尝试次数 {self.max_attempts}")
            return None

        # 获取下一个降级模型
        fallback_model = self._get_next_fallback_model(attempt_count)
        if not fallback_model:
            logger.error("降级失败：没有可用的降级模型")
            return None

        logger.info(f"尝试降级到模型: {fallback_model} (第 {attempt_count + 1} 次尝试)")

        try:
            # 这里需要重新创建客户端并调用
            # 实际实现中需要依赖注入或工厂模式
            # 这里只是示例，实际实现会更复杂
            from .factory import get_global_factory

            factory = get_global_factory()

            # 创建降级模型配置
            fallback_config = {
                "model_type": self._get_model_type(fallback_model),
                "model_name": fallback_model,
            }

            # 创建降级客户端
            fallback_client = factory.create_client(fallback_config)

            # 调用降级客户端
            response = fallback_client.generate(messages, parameters)

            # 标记为降级响应
            response.metadata["fallback_model"] = fallback_model
            response.metadata["fallback_attempt"] = attempt_count + 1

            return response

        except Exception as fallback_error:
            logger.error(f"降级到模型 {fallback_model} 失败: {fallback_error}")
            return None

    def _should_retry(self, error: Exception, **kwargs: Any) -> Dict[str, Any]:
        """判断是否应该重试"""
        # 检查错误类型是否可重试
        retryable_errors = (
            LLMTimeoutError,
            LLMRateLimitError,
            LLMServiceUnavailableError,
        )

        should_retry = isinstance(error, retryable_errors)
        return {
            "should_retry": should_retry,
            "reason": f"Error type: {type(error).__name__}" if should_retry else f"Non-retryable error: {type(error).__name__}"
        }

    def _get_next_fallback_model(self, attempt_count: int) -> Optional[str]:
        """获取下一个降级模型"""
        if attempt_count - 1 < len(self.fallback_models):
            return self.fallback_models[attempt_count - 1]
        return None

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


class SmartRetryHook(ILLMCallHook):
    """智能重试钩子"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        exponential_base: float = 2.0,
        retry_on_status_codes: Optional[List[int]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
        retry_on_errors: Optional[List[str]] = None,
    ) -> None:
        """
        初始化智能重试钩子

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            jitter: 是否添加随机抖动
            exponential_base: 指数退避基数
            retry_on_status_codes: 需要重试的HTTP状态码列表
            retry_config: 重试配置字典（新的配置格式）
            retry_on_errors: 需要重试的错误类型列表
        """
        # 如果提供了新的重试配置，使用它
        if retry_config:
            self.max_retries = retry_config.get("max_retries", max_retries)
            self.base_delay = retry_config.get("base_delay", base_delay)
            self.max_delay = retry_config.get("max_delay", max_delay)
            self.jitter = retry_config.get("jitter", jitter)
            self.exponential_base = retry_config.get("exponential_base", exponential_base)
            self.retry_on_status_codes = retry_config.get("retry_on_status_codes", retry_on_status_codes or [429, 500, 502, 503, 504])
            self.retry_on_errors = retry_config.get("retry_on_errors", retry_on_errors or ["timeout", "rate_limit", "service_unavailable"])
        else:
            # 使用传统参数
            self.max_retries = max_retries
            self.base_delay = base_delay
            self.max_delay = max_delay
            self.jitter = jitter
            self.exponential_base = exponential_base
            self.retry_on_status_codes = retry_on_status_codes or [429, 500, 502, 503, 504]
            self.retry_on_errors = retry_on_errors or ["timeout", "rate_limit", "service_unavailable"]
        
        # 错误统计
        self.retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "error_type_counts": {},
        }

    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用开始"""
        if parameters is None:
            parameters = {}

        if "_retry_count" not in parameters:
            parameters["_retry_count"] = 0
        if "_retry_start_time" not in parameters:
            parameters["_retry_start_time"] = time.time()

    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录调用成功"""
        if response is not None and parameters and parameters.get("_retry_count", 0) > 0:
            # 重试成功
            self.retry_stats["successful_retries"] += 1
            retry_count = parameters.get("_retry_count", 0)
            total_time = time.time() - parameters.get("_retry_start_time", time.time())
            logger.info(f"重试成功，共重试 {retry_count} 次，耗时 {total_time:.2f} 秒")

    def on_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """智能重试处理"""
        # 检查是否应该重试
        retry_decision = self._should_retry(error, parameters, **kwargs)
        if not retry_decision["should_retry"]:
            if parameters and parameters.get("_retry_count", 0) > 0:
                self.retry_stats["failed_retries"] += 1
            logger.error(f"不重试：{retry_decision['reason']}")
            return None

        # 获取当前重试次数
        retry_count = (
            parameters.get("_retry_count", 0)
            if parameters
            else kwargs.get("_retry_count", 0)
        )

        # 检查是否超过最大重试次数
        if retry_count >= self.max_retries:
            self.retry_stats["failed_retries"] += 1
            logger.error(f"重试失败：已达到最大重试次数 {self.max_retries}")
            return None

        # 计算延迟时间
        delay = self._calculate_delay(retry_count, error)
        
        # 更新统计
        self.retry_stats["total_retries"] += 1
        error_type = type(error).__name__
        self.retry_stats["error_type_counts"][error_type] = (
            self.retry_stats["error_type_counts"].get(error_type, 0) + 1
        )

        logger.info(
            f"等待 {delay:.2f} 秒后重试 (第 {retry_count + 1} 次重试) "
            f"- 错误类型: {error_type}, 原因: {retry_decision['reason']}"
        )

        # 等待
        time.sleep(delay)

        # 更新重试计数
        if parameters is not None:
            parameters["_retry_count"] = retry_count + 1
        else:
            kwargs["_retry_count"] = retry_count + 1

        # 这里不能直接重试，因为钩子不能重新调用原方法
        # 实际实现需要在客户端中处理重试逻辑
        # 这里只是记录重试意图
        return None

    def _calculate_delay(self, attempt: int, error: Exception) -> float:
        """计算重试延迟时间"""
        # 指数退避
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        
        # 根据错误类型调整延迟
        if isinstance(error, LLMRateLimitError):
            # 频率限制错误，使用更长的延迟
            if hasattr(error, 'retry_after') and error.retry_after:
                delay = max(delay, float(error.retry_after))
            else:
                delay *= 2
        elif isinstance(error, LLMTimeoutError):
            # 超时错误，适度增加延迟
            delay *= 1.5
        
        # 添加随机抖动
        if self.jitter:
            import random
            jitter_factor = 0.8 + random.random() * 0.4  # 0.8-1.2倍抖动
            delay *= jitter_factor
        
        return delay

    def _should_retry(
        self,
        error: Exception,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """判断是否应该重试"""
        # 检查错误类型是否可重试
        retryable_errors = (
            LLMTimeoutError,
            LLMRateLimitError,
            LLMServiceUnavailableError,
        )
        
        # 如果配置了retry_on_errors，使用配置的错误类型
        if hasattr(self, 'retry_on_errors') and self.retry_on_errors:
            # 检查错误类型是否在配置的可重试错误列表中
            error_type = type(error).__name__.lower()
            for retry_error in self.retry_on_errors:
                if retry_error.lower() in error_type or retry_error.lower() in str(error).lower():
                    return {"should_retry": True, "reason": f"配置的可重试错误类型: {retry_error}"}
        elif isinstance(error, retryable_errors):
            return {"should_retry": True, "reason": f"可重试错误类型: {type(error).__name__}"}
        
        # 检查HTTP状态码
        if hasattr(error, 'status_code'):
            status_code = getattr(error, 'status_code', None)
            if status_code in self.retry_on_status_codes:
                return {"should_retry": True, "reason": f"可重试状态码: {status_code}"}
        
        # 检查错误消息中的状态码
        error_str = str(error).lower()
        for code in self.retry_on_status_codes:
            if str(code) in error_str:
                return {"should_retry": True, "reason": f"错误消息包含可重试状态码: {code}"}
        
        # 检查特定错误关键词
        retryable_keywords = [
            "timeout", "timed out", "time out",
            "rate limit", "too many requests", "rate_limit_exceeded",
            "service unavailable", "temporary error", "internal server error"
        ]
        
        for keyword in retryable_keywords:
            if keyword in error_str:
                return {"should_retry": True, "reason": f"错误消息包含可重试关键词: {keyword}"}
        
        return {"should_retry": False, "reason": f"不可重试错误: {type(error).__name__}"}

    def get_retry_stats(self) -> Dict[str, Any]:
        """获取重试统计信息"""
        total = self.retry_stats["total_retries"]
        successful = self.retry_stats["successful_retries"]
        failed = self.retry_stats["failed_retries"]
        
        success_rate = successful / max(total, 1)
        
        return {
            **self.retry_stats,
            "success_rate": success_rate,
            "average_retries_per_failure": total / max(failed, 1),
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "error_type_counts": {},
        }


# 保持向后兼容的RetryHook
class RetryHook(SmartRetryHook):
    """重试钩子（向后兼容）"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> None:
        """
        初始化重试钩子

        Args:
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 退避因子
        """
        super().__init__(
            max_retries=max_retries,
            base_delay=retry_delay,
            exponential_base=backoff_factor,
            jitter=False,  # 保持向后兼容，不使用抖动
        )


class CompositeHook(ILLMCallHook):
    """组合钩子"""

    def __init__(self, hooks: List[ILLMCallHook]) -> None:
        """
        初始化组合钩子

        Args:
            hooks: 钩子列表
        """
        self.hooks = list(hooks)  # 创建副本以避免引用问题

    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """调用所有钩子的before_call方法"""
        for hook in self.hooks:
            try:
                hook.before_call(messages, parameters, **kwargs)
            except Exception as e:
                logger.error(f"钩子 {type(hook).__name__} before_call 失败: {e}")

    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """调用所有钩子的after_call方法"""
        for hook in self.hooks:
            try:
                hook.after_call(response, messages, parameters, **kwargs)
            except Exception as e:
                logger.error(f"钩子 {type(hook).__name__} after_call 失败: {e}")

    def on_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """调用所有钩子的on_error方法，返回第一个非None结果"""
        for hook in self.hooks:
            try:
                result = hook.on_error(error, messages, parameters, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"钩子 {type(hook).__name__} on_error 失败: {e}")

        return None

    def add_hook(self, hook: ILLMCallHook) -> None:
        """添加钩子"""
        if hook not in self.hooks:
            self.hooks.append(hook)

    def remove_hook(self, hook: ILLMCallHook) -> None:
        """移除钩子"""
        if hook in self.hooks:
            self.hooks.remove(hook)
