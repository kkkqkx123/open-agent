"""监控触发器基类

提供计时、监控和模式匹配功能的触发器基类。
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, List, Pattern
from dataclasses import dataclass, field
from datetime import datetime
import re
import psutil
import threading

from .base import BaseTrigger, TriggerType, TriggerEvent

from src.interfaces.state.workflow import IWorkflowState


@dataclass
class TimingInfo:
    """计时信息"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 秒
    is_active: bool = True
    
    def finish(self) -> None:
        """完成计时"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.is_active = False
    
    def get_duration(self) -> float:
        """获取持续时间"""
        if self.duration is not None:
            return self.duration
        elif self.is_active:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0


@dataclass
class StateChangeInfo:
    """状态变更信息"""
    previous_state: Optional[str] = None
    current_state: Optional[str] = None
    change_time: datetime = field(default_factory=datetime.now)
    state_data: Dict[str, Any] = field(default_factory=dict)
    
    def update_state(self, new_state: str, state_data: Dict[str, Any]) -> None:
        """更新状态"""
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_data = state_data.copy()
        self.change_time = datetime.now()


@dataclass
class MemoryInfo:
    """内存信息"""
    timestamp: datetime = field(default_factory=datetime.now)
    process_memory_mb: float = 0.0
    system_memory_mb: float = 0.0
    process_memory_percent: float = 0.0
    system_memory_percent: float = 0.0
    
    @classmethod
    def collect(cls) -> "MemoryInfo":
        """收集内存信息"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return cls(
            process_memory_mb=memory_info.rss / 1024 / 1024,
            system_memory_mb=system_memory.used / 1024 / 1024,
            process_memory_percent=process.memory_percent(),
            system_memory_percent=system_memory.percent
        )


class MonitoringTrigger(BaseTrigger):
    """监控触发器基类
    
    提供计时、状态监控和模式匹配功能的基类。
    """
    
    def __init__(
        self,
        trigger_id: str,
        trigger_type: TriggerType,
        config: Dict[str, Any],
        enabled: bool = True
    ) -> None:
        """初始化监控触发器
        
        Args:
            trigger_id: 触发器ID
            trigger_type: 触发器类型
            config: 触发器配置
            enabled: 是否启用
        """
        super().__init__(trigger_id, trigger_type, config, enabled)
        
        # 计时相关
        self._timing_sessions: Dict[str, TimingInfo] = {}
        self._timing_lock = threading.Lock()
        
        # 状态监控相关
        self._state_info = StateChangeInfo()
        self._state_history: List[StateChangeInfo] = []
        self._max_history_size = config.get("max_history_size", 100)
        
        # 模式匹配相关
        self._patterns: Dict[str, Pattern] = {}
        self._compile_patterns()
        
        # 内存监控相关
        self._memory_history: List[MemoryInfo] = []
        self._memory_threshold_mb = config.get("memory_threshold_mb", 1024)
        self._memory_check_interval = config.get("memory_check_interval", 60)
        self._last_memory_check: Optional[datetime] = None
    
    def start_timing(self, session_id: str) -> None:
        """开始计时
        
        Args:
            session_id: 计时会话ID
        """
        with self._timing_lock:
            self._timing_sessions[session_id] = TimingInfo(start_time=datetime.now())
    
    def stop_timing(self, session_id: str) -> Optional[float]:
        """停止计时
        
        Args:
            session_id: 计时会话ID
            
        Returns:
            Optional[float]: 持续时间（秒），如果会话不存在返回None
        """
        with self._timing_lock:
            timing_info = self._timing_sessions.get(session_id)
            if timing_info and timing_info.is_active:
                timing_info.finish()
                return timing_info.get_duration()
            return None
    
    def get_timing_info(self, session_id: str) -> Optional[TimingInfo]:
        """获取计时信息
        
        Args:
            session_id: 计时会话ID
            
        Returns:
            Optional[TimingInfo]: 计时信息，如果会话不存在返回None
        """
        with self._timing_lock:
            return self._timing_sessions.get(session_id)
    
    def get_active_timings(self) -> Dict[str, TimingInfo]:
        """获取活跃的计时会话
        
        Returns:
            Dict[str, TimingInfo]: 活跃的计时会话
        """
        with self._timing_lock:
            return {
                session_id: timing_info
                for session_id, timing_info in self._timing_sessions.items()
                if timing_info.is_active
            }
    
    def update_state(self, new_state: str, state_data: Dict[str, Any]) -> None:
        """更新状态
        
        Args:
            new_state: 新状态
            state_data: 状态数据
        """
        self._state_info.update_state(new_state, state_data)
        
        # 添加到历史记录
        self._state_history.append(StateChangeInfo(
            previous_state=self._state_info.previous_state,
            current_state=self._state_info.current_state,
            change_time=self._state_info.change_time,
            state_data=self._state_info.state_data.copy()
        ))
        
        # 限制历史记录大小
        if len(self._state_history) > self._max_history_size:
            self._state_history = self._state_history[-self._max_history_size:]
    
    def get_current_state(self) -> Optional[str]:
        """获取当前状态
        
        Returns:
            Optional[str]: 当前状态
        """
        return self._state_info.current_state
    
    def get_state_history(self, limit: Optional[int] = None) -> List[StateChangeInfo]:
        """获取状态历史
        
        Args:
            limit: 限制返回的历史记录数量
            
        Returns:
            List[StateChangeInfo]: 状态历史
        """
        if limit:
            return self._state_history[-limit:]
        return self._state_history.copy()
    
    def get_time_since_last_state_change(self) -> Optional[float]:
        """获取距离上次状态变更的时间
        
        Returns:
            Optional[float]: 时间（秒），如果没有状态变更返回None
        """
        if self._state_info.change_time:
            return (datetime.now() - self._state_info.change_time).total_seconds()
        return None
    
    def _compile_patterns(self) -> None:
        """编译正则表达式模式"""
        patterns_config = self._config.get("patterns", {})
        for pattern_name, pattern_str in patterns_config.items():
            try:
                self._patterns[pattern_name] = re.compile(pattern_str)
            except re.error as e:
                # 记录错误但继续处理其他模式
                pass
    
    def match_pattern(self, pattern_name: str, text: str) -> bool:
        """匹配模式
        
        Args:
            pattern_name: 模式名称
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        pattern = self._patterns.get(pattern_name)
        if pattern:
            return bool(pattern.search(text))
        return False
    
    def add_pattern(self, pattern_name: str, pattern_str: str) -> bool:
        """添加模式
        
        Args:
            pattern_name: 模式名称
            pattern_str: 模式字符串
            
        Returns:
            bool: 是否成功添加
        """
        try:
            self._patterns[pattern_name] = re.compile(pattern_str)
            return True
        except re.error:
            return False
    
    def check_memory_usage(self) -> Optional[MemoryInfo]:
        """检查内存使用情况
        
        Returns:
            Optional[MemoryInfo]: 内存信息，如果不需要检查返回None
        """
        now = datetime.now()
        
        # 检查是否到了检查时间
        if (self._last_memory_check and 
            (now - self._last_memory_check).total_seconds() < self._memory_check_interval):
            return None
        
        self._last_memory_check = now
        memory_info = MemoryInfo.collect()
        self._memory_history.append(memory_info)
        
        # 限制历史记录大小
        if len(self._memory_history) > self._max_history_size:
            self._memory_history = self._memory_history[-self._max_history_size:]
        
        return memory_info
    
    def is_memory_threshold_exceeded(self) -> bool:
        """检查是否超过内存阈值
        
        Returns:
            bool: 是否超过阈值
        """
        if not self._memory_history:
            return False
        
        latest_memory = self._memory_history[-1]
        return latest_memory.process_memory_mb > self._memory_threshold_mb
    
    def get_memory_history(self, limit: Optional[int] = None) -> List[MemoryInfo]:
        """获取内存历史
        
        Args:
            limit: 限制返回的历史记录数量
            
        Returns:
            List[MemoryInfo]: 内存历史
        """
        if limit:
            return self._memory_history[-limit:]
        return self._memory_history.copy()
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要
        
        Returns:
            Dict[str, Any]: 监控摘要
        """
        with self._timing_lock:
            active_timings = len(self.get_active_timings())
            total_timings = len(self._timing_sessions)
        
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type.value,
            "timing": {
                "active_sessions": active_timings,
                "total_sessions": total_timings
            },
            "state": {
                "current_state": self.get_current_state(),
                "state_changes": len(self._state_history),
                "time_since_last_change": self.get_time_since_last_state_change()
            },
            "patterns": {
                "compiled_patterns": list(self._patterns.keys())
            },
            "memory": {
                "latest_usage": self._memory_history[-1].process_memory_mb if self._memory_history else 0,
                "threshold_exceeded": self.is_memory_threshold_exceeded(),
                "history_size": len(self._memory_history)
            }
        }
    
    def reset_monitoring_data(self) -> None:
        """重置监控数据"""
        with self._timing_lock:
            self._timing_sessions.clear()
        
        self._state_history.clear()
        self._memory_history.clear()
        self._state_info = StateChangeInfo()
        self._last_memory_check = None