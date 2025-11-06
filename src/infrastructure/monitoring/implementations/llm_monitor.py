"""LLM性能监控器

专门用于监控LLM调用的性能指标，使用零内存存储。
"""

from typing import Optional

from ..lightweight_monitor import LightweightPerformanceMonitor
from ..logger_writer import PerformanceMetricsLogger


class LLMPerformanceMonitor(LightweightPerformanceMonitor):
    """LLM性能监控器 - 零内存存储版本"""
    
    def __init__(self, logger: Optional[PerformanceMetricsLogger] = None):
        """初始化LLM性能监控器
        
        Args:
            logger: 性能指标日志写入器，如果为None则创建默认实例
        """
        super().__init__(logger or PerformanceMetricsLogger("llm_metrics"))
    
    def record_llm_call(self, 
                       model: str,
                       provider: str,
                       response_time: float,
                       prompt_tokens: int,
                       completion_tokens: int,
                       total_tokens: int,
                       success: bool = True) -> None:
        """记录LLM调用
        
        Args:
            model: 模型名称
            provider: 提供商
            response_time: 响应时间（秒）
            prompt_tokens: 提示token数量
            completion_tokens: 完成token数量
            total_tokens: 总token数量
            success: 是否成功
        """
        self.logger.log_llm_call(
            model=model,
            provider=provider,
            response_time=response_time,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            success=success
        )
    
    def record_llm_error(self, model: str, provider: str, error_type: str) -> None:
        """记录LLM错误
        
        Args:
            model: 模型名称
            provider: 提供商
            error_type: 错误类型
        """
        # 记录错误计数
        self.logger.log_counter(
            "llm_error", 
            1.0, 
            {"model": model, "provider": provider, "error_type": error_type}
        )