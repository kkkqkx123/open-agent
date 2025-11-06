"""LLM性能监控器

专门用于监控LLM调用的性能指标。
"""

from typing import Optional, Dict, Any

from ..base_monitor import BasePerformanceMonitor


class LLMPerformanceMonitor(BasePerformanceMonitor):
    """LLM性能监控器"""
    
    def __init__(self, max_history_size: int = 1000):
        """初始化LLM性能监控器
        
        Args:
            max_history_size: 最大历史记录大小
        """
        super().__init__(max_history_size)
        self._config.update({
            "module": "llm",
            "description": "LLM性能监控"
        })
    
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
        labels = {
            "model": model,
            "provider": provider
        }
        
        # 记录响应时间
        self.record_timer("llm.response_time", response_time, labels)
        
        # 记录token使用情况
        self.set_gauge("llm.prompt_tokens", prompt_tokens, labels)
        self.set_gauge("llm.completion_tokens", completion_tokens, labels)
        self.set_gauge("llm.total_tokens", total_tokens, labels)
        
        # 记录token速率
        if response_time > 0:
            tokens_per_second = total_tokens / response_time
            self.set_gauge("llm.tokens_per_second", tokens_per_second, labels)
        
        # 记录成功/失败计数
        if success:
            self.increment_counter("llm.calls.success", 1, labels)
        else:
            self.increment_counter("llm.calls.failure", 1, labels)
    
    def record_llm_error(self, model: str, provider: str, error_type: str) -> None:
        """记录LLM错误
        
        Args:
            model: 模型名称
            provider: 提供商
            error_type: 错误类型
        """
        labels = {
            "model": model,
            "provider": provider,
            "error_type": error_type
        }
        
        # 记录错误计数
        self.increment_counter("llm.errors", 1, labels)