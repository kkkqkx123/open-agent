"""指标收集器"""

import json
import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class LLMMetric:
    """LLM指标数据"""
    
    def __init__(
        self, 
        model: str, 
        count: int = 1, 
        input_tokens: int = 0, 
        output_tokens: int = 0, 
        total_time: float = 0.0,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """初始化LLM指标
        
        Args:
            model: 模型名称
            count: 调用次数
            input_tokens: 输入token数
            output_tokens: 输出token数
            total_time: 总耗时（秒）
            success: 是否成功
            error_type: 错误类型
        """
        self.model = model
        self.count = count
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_time = total_time
        self.success = success
        self.error_type = error_type
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            'model': self.model,
            'count': self.count,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_time': self.total_time,
            'success': self.success,
            'error_type': self.error_type,
            'timestamp': self.timestamp.isoformat()
        }


class ToolMetric:
    """工具指标数据"""
    
    def __init__(
        self, 
        tool: str, 
        count: int = 1, 
        success_count: int = 0, 
        total_time: float = 0.0,
        error_type: Optional[str] = None
    ):
        """初始化工具指标
        
        Args:
            tool: 工具名称
            count: 调用次数
            success_count: 成功次数
            total_time: 总耗时（秒）
            error_type: 错误类型
        """
        self.tool = tool
        self.count = count
        self.success_count = success_count
        self.total_time = total_time
        self.error_type = error_type
        self.timestamp = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """成功率
        
        Returns:
            成功率（0-1）
        """
        if self.count == 0:
            return 0.0
        return self.success_count / self.count
    
    @property
    def avg_time(self) -> float:
        """平均耗时
        
        Returns:
            平均耗时（秒）
        """
        if self.count == 0:
            return 0.0
        return self.total_time / self.count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            'tool': self.tool,
            'count': self.count,
            'success_count': self.success_count,
            'success_rate': self.success_rate,
            'total_time': self.total_time,
            'avg_time': self.avg_time,
            'error_type': self.error_type,
            'timestamp': self.timestamp.isoformat()
        }


class SessionMetric:
    """会话指标数据"""
    
    def __init__(self, session_id: str):
        """初始化会话指标
        
        Args:
            session_id: 会话ID
        """
        self.session_id = session_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.llm_calls: List[LLMMetric] = []
        self.tool_calls: List[ToolMetric] = []
        self.total_messages = 0
        self.total_errors = 0
    
    @property
    def duration(self) -> float:
        """会话持续时间（秒）
        
        Returns:
            持续时间
        """
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def total_llm_calls(self) -> int:
        """总LLM调用次数
        
        Returns:
            调用次数
        """
        return sum(call.count for call in self.llm_calls)
    
    @property
    def total_tool_calls(self) -> int:
        """总工具调用次数
        
        Returns:
            调用次数
        """
        return sum(call.count for call in self.tool_calls)
    
    @property
    def total_tokens(self) -> int:
        """总token数
        
        Returns:
            token数
        """
        return sum(call.input_tokens + call.output_tokens for call in self.llm_calls)
    
    def end_session(self) -> None:
        """结束会话"""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'total_messages': self.total_messages,
            'total_errors': self.total_errors,
            'total_llm_calls': self.total_llm_calls,
            'total_tool_calls': self.total_tool_calls,
            'total_tokens': self.total_tokens,
            'llm_calls': [call.to_dict() for call in self.llm_calls],
            'tool_calls': [call.to_dict() for call in self.tool_calls]
        }


class IMetricsCollector(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    def record_llm_metric(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int, 
        duration: float,
        success: bool = True,
        error_type: Optional[str] = None
    ) -> None:
        """记录LLM调用指标"""
        pass
    
    @abstractmethod
    def record_tool_metric(
        self, 
        tool: str, 
        success: bool, 
        duration: float,
        error_type: Optional[str] = None
    ) -> None:
        """记录工具调用指标"""
        pass
    
    @abstractmethod
    def record_session_start(self, session_id: str) -> None:
        """记录会话开始"""
        pass
    
    @abstractmethod
    def record_session_end(self, session_id: str) -> None:
        """记录会话结束"""
        pass
    
    @abstractmethod
    def record_message(self, session_id: str) -> None:
        """记录消息"""
        pass
    
    @abstractmethod
    def record_error(self, session_id: str, error_type: str) -> None:
        """记录错误"""
        pass
    
    @abstractmethod
    def export_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """导出统计信息"""
        pass
    
    @abstractmethod
    def clear_metrics(self, session_id: Optional[str] = None) -> None:
        """清除指标数据"""
        pass


# 全局指标收集器实例
_global_metrics_collector: Optional['MetricsCollector'] = None


def get_global_metrics_collector() -> 'MetricsCollector':
    """获取全局指标收集器实例
    
    Returns:
        全局指标收集器实例
    """
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


class MetricsCollector(IMetricsCollector):
    """指标收集器实现"""
    
    def __init__(self, max_sessions: int = 1000, max_history: int = 100):
        """初始化指标收集器
        
        Args:
            max_sessions: 最大会话数
            max_history: 每个会话最大历史记录数
        """
        self.max_sessions = max_sessions
        self.max_history = max_history
        
        # 会话指标存储
        self._sessions: Dict[str, SessionMetric] = {}
        
        # 全局统计
        self._global_stats: Dict[str, Any] = {
            'total_sessions': 0,
            'total_llm_calls': 0,
            'total_tool_calls': 0,
            'total_tokens': 0,
            'total_errors': 0,
            'models': defaultdict(lambda: {'calls': 0, 'tokens': 0, 'errors': 0}),
            'tools': defaultdict(lambda: {'calls': 0, 'successes': 0, 'errors': 0})
        }
        
        # 时间序列数据（用于趋势分析）
        self._time_series: Dict[str, deque] = {
            'llm_calls': deque(maxlen=max_history),
            'tool_calls': deque(maxlen=max_history),
            'errors': deque(maxlen=max_history)
        }
        
        # 线程锁
        self._lock = threading.RLock()
    
    def record_llm_metric(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int, 
        duration: float,
        success: bool = True,
        error_type: Optional[str] = None
    ) -> None:
        """记录LLM调用指标"""
        with self._lock:
            # 创建LLM指标
            metric = LLMMetric(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_time=duration,
                success=success,
                error_type=error_type
            )
            
            # 更新全局统计
            self._global_stats['total_llm_calls'] += 1
            self._global_stats['total_tokens'] += input_tokens + output_tokens
            self._global_stats['models'][model]['calls'] += 1
            self._global_stats['models'][model]['tokens'] += input_tokens + output_tokens
            
            if not success:
                self._global_stats['total_errors'] += 1
                self._global_stats['models'][model]['errors'] += 1
            
            # 记录时间序列
            self._time_series['llm_calls'].append({
                'timestamp': datetime.now().isoformat(),
                'model': model,
                'tokens': input_tokens + output_tokens,
                'duration': duration,
                'success': success
            })
            
            # 添加到当前活跃会话（如果有）
            # 这里简化处理，实际应该有当前会话上下文
            # 可以通过record_session_start和record_session_end管理
    
    def record_tool_metric(
        self, 
        tool: str, 
        success: bool, 
        duration: float,
        error_type: Optional[str] = None
    ) -> None:
        """记录工具调用指标"""
        with self._lock:
            # 更新全局统计
            self._global_stats['total_tool_calls'] += 1
            self._global_stats['tools'][tool]['calls'] += 1
            
            if success:
                self._global_stats['tools'][tool]['successes'] += 1
            else:
                self._global_stats['total_errors'] += 1
                self._global_stats['tools'][tool]['errors'] += 1
            
            # 记录时间序列
            self._time_series['tool_calls'].append({
                'timestamp': datetime.now().isoformat(),
                'tool': tool,
                'duration': duration,
                'success': success
            })
    
    def record_session_start(self, session_id: str) -> None:
        """记录会话开始"""
        with self._lock:
            # 检查会话数限制
            if len(self._sessions) >= self.max_sessions:
                # 移除最旧的会话
                oldest_session = min(self._sessions.values(), key=lambda s: s.start_time)
                del self._sessions[oldest_session.session_id]
            
            # 创建新会话
            self._sessions[session_id] = SessionMetric(session_id)
            self._global_stats['total_sessions'] += 1
    
    def record_session_end(self, session_id: str) -> None:
        """记录会话结束"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].end_session()
    
    def record_message(self, session_id: str) -> None:
        """记录消息"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].total_messages += 1
    
    def record_error(self, session_id: str, error_type: str) -> None:
        """记录错误"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].total_errors += 1
    
    def export_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """导出统计信息"""
        with self._lock:
            if session_id:
                # 导出特定会话的统计
                if session_id in self._sessions:
                    return self._sessions[session_id].to_dict()
                else:
                    return {'error': f'Session {session_id} not found'}
            else:
                # 导出全局统计
                stats = {
                    'global': {
                        'total_sessions': self._global_stats['total_sessions'],
                        'total_llm_calls': self._global_stats['total_llm_calls'],
                        'total_tool_calls': self._global_stats['total_tool_calls'],
                        'total_tokens': self._global_stats['total_tokens'],
                        'total_errors': self._global_stats['total_errors'],
                        'models': dict(self._global_stats['models']),
                        'tools': dict(self._global_stats['tools'])
                    },
                    'sessions': {sid: session.to_dict() for sid, session in self._sessions.items()},
                    'time_series': {
                        'llm_calls': list(self._time_series['llm_calls']),
                        'tool_calls': list(self._time_series['tool_calls']),
                        'errors': list(self._time_series['errors'])
                    }
                }
                
                return stats
    
    def clear_metrics(self, session_id: Optional[str] = None) -> None:
        """清除指标数据"""
        with self._lock:
            if session_id:
                # 清除特定会话
                if session_id in self._sessions:
                    del self._sessions[session_id]
            else:
                # 清除所有数据
                self._sessions.clear()
                self._global_stats = {
                    'total_sessions': 0,
                    'total_llm_calls': 0,
                    'total_tool_calls': 0,
                    'total_tokens': 0,
                    'total_errors': 0,
                    'models': defaultdict(lambda: {'calls': 0, 'tokens': 0, 'errors': 0}),
                    'tools': defaultdict(lambda: {'calls': 0, 'successes': 0, 'errors': 0})
                }
                self._time_series = {
                    'llm_calls': deque(maxlen=self.max_history),
                    'tool_calls': deque(maxlen=self.max_history),
                    'errors': deque(maxlen=self.max_history)
                }
    
    def save_to_file(self, file_path: str) -> None:
        """保存指标到文件
        
        Args:
            file_path: 文件路径
        """
        stats = self.export_stats()
        
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, file_path: str) -> None:
        """从文件加载指标
        
        Args:
            file_path: 文件路径
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        # 这里简化处理，实际应该完整恢复状态
        # 可以根据需要实现更复杂的加载逻辑