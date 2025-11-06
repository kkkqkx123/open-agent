"""性能指标日志写入器

将性能指标直接写入日志，不保存在内存中。
"""

import json
import logging
import time
from typing import Dict, Any, Optional


class PerformanceMetricsLogger:
    """性能指标日志写入器
    
    负责将性能指标写入结构化日志，实现零内存存储。
    """
    
    def __init__(self, logger_name: str = "performance_metrics"):
        """初始化日志写入器
        
        Args:
            logger_name: 日志记录器名称
        """
        self.logger = logging.getLogger(logger_name)
        
        # 确保日志记录器配置正确
        if not self.logger.handlers:
            # 如果没有处理器，添加一个默认的处理器
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _write_log(self, metric_type: str, operation: str, data: Dict[str, Any]) -> None:
        """写入性能指标日志
        
        Args:
            metric_type: 指标类型 (timer, counter, gauge, histogram)
            operation: 操作名称
            data: 指标数据
        """
        log_entry = {
            "timestamp": time.time(),
            "metric_type": metric_type,
            "operation": operation,
            **data
        }
        
        # 使用结构化日志格式
        self.logger.info(json.dumps(log_entry))
    
    def log_timer(self, operation: str, duration: float, 
                  labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器指标
        
        Args:
            operation: 操作名称
            duration: 持续时间（秒）
            labels: 标签字典
        """
        data = {
            "duration": duration,
            "unit": "seconds"
        }
        
        if labels:
            data["labels"] = labels
            
        self._write_log("timer", operation, data)
    
    def log_counter(self, operation: str, value: float = 1.0,
                   labels: Optional[Dict[str, str]] = None) -> None:
        """记录计数器指标
        
        Args:
            operation: 操作名称
            value: 计数值
            labels: 标签字典
        """
        data = {
            "value": value,
            "unit": "count"
        }
        
        if labels:
            data["labels"] = labels
            
        self._write_log("counter", operation, data)
    
    def log_gauge(self, operation: str, value: float,
                 labels: Optional[Dict[str, str]] = None) -> None:
        """记录仪表值指标
        
        Args:
            operation: 操作名称
            value: 仪表值
            labels: 标签字典
        """
        data = {
            "value": value,
            "unit": "value"
        }
        
        if labels:
            data["labels"] = labels
            
        self._write_log("gauge", operation, data)
    
    def log_checkpoint_save(self, duration: float, size: int, success: bool) -> None:
        """记录检查点保存操作
        
        Args:
            duration: 保存耗时（秒）
            size: 检查点大小（字节）
            success: 是否成功
        """
        data = {
            "duration": duration,
            "size": size,
            "success": success,
            "module": "checkpoint"
        }
        
        self._write_log("timer", "checkpoint_save", data)
        
        # 同时记录成功/失败计数
        if success:
            self.log_counter("checkpoint_save_success", 1.0, {"module": "checkpoint"})
        else:
            self.log_counter("checkpoint_save_failure", 1.0, {"module": "checkpoint"})
    
    def log_checkpoint_load(self, duration: float, size: int, success: bool) -> None:
        """记录检查点加载操作
        
        Args:
            duration: 加载耗时（秒）
            size: 检查点大小（字节）
            success: 是否成功
        """
        data = {
            "duration": duration,
            "size": size,
            "success": success,
            "module": "checkpoint"
        }
        
        self._write_log("timer", "checkpoint_load", data)
        
        # 同时记录成功/失败计数
        if success:
            self.log_counter("checkpoint_load_success", 1.0, {"module": "checkpoint"})
        else:
            self.log_counter("checkpoint_load_failure", 1.0, {"module": "checkpoint"})
    
    def log_checkpoint_list(self, duration: float, count: int) -> None:
        """记录检查点列表操作
        
        Args:
            duration: 列表操作耗时（秒）
            count: 检查点数量
        """
        data = {
            "duration": duration,
            "count": count,
            "module": "checkpoint"
        }
        
        self._write_log("timer", "checkpoint_list", data)
    
    def log_llm_call(self, model: str, provider: str, response_time: float,
                    prompt_tokens: int, completion_tokens: int, total_tokens: int,
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
        data = {
            "model": model,
            "provider": provider,
            "response_time": response_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "success": success,
            "module": "llm"
        }
        
        # 计算token速率
        if response_time > 0:
            data["tokens_per_second"] = total_tokens / response_time
        
        self._write_log("timer", "llm_call", data)
        
        # 同时记录成功/失败计数
        if success:
            self.log_counter("llm_call_success", 1.0, {"module": "llm", "model": model, "provider": provider})
        else:
            self.log_counter("llm_call_failure", 1.0, {"module": "llm", "model": model, "provider": provider})
    
    def log_workflow_node_execution(self, node_type: str, execution_time: float,
                                   success: bool = True, error_type: Optional[str] = None) -> None:
        """记录工作流节点执行
        
        Args:
            node_type: 节点类型
            execution_time: 执行时间（秒）
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        data = {
            "node_type": node_type,
            "execution_time": execution_time,
            "success": success,
            "module": "workflow"
        }
        
        if error_type:
            data["error_type"] = error_type
            
        self._write_log("timer", "workflow_node_execution", data)
        
        # 同时记录成功/失败计数
        if success:
            self.log_counter("workflow_node_success", 1.0, {"module": "workflow", "node_type": node_type})
        else:
            self.log_counter("workflow_node_failure", 1.0, {"module": "workflow", "node_type": node_type})
    
    def log_tool_execution(self, tool_name: str, execution_time: float,
                         success: bool = True, error_type: Optional[str] = None) -> None:
        """记录工具执行
        
        Args:
            tool_name: 工具名称
            execution_time: 执行时间（秒）
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        data = {
            "tool_name": tool_name,
            "execution_time": execution_time,
            "success": success,
            "module": "tool"
        }
        
        if error_type:
            data["error_type"] = error_type
            
        self._write_log("timer", "tool_execution", data)
        
        # 同时记录成功/失败计数
        if success:
            self.log_counter("tool_success", 1.0, {"module": "tool", "tool_name": tool_name})
        else:
            self.log_counter("tool_failure", 1.0, {"module": "tool", "tool_name": tool_name})