"""回放策略实现"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from src.domain.replay.interfaces import IReplayStrategy, ReplayEvent, ReplayMode
from src.domain.replay.config import RealTimeConfig, FastForwardConfig, StepByStepConfig, AnalysisConfig

logger = logging.getLogger(__name__)


class RealTimeReplayStrategy(IReplayStrategy):
    """实时回放策略"""
    
    def __init__(self, config: RealTimeConfig):
        """初始化策略
        
        Args:
            config: 实时回放配置
        """
        self.config = config
        self._last_event_time: Optional[datetime] = None
    
    async def should_pause(self, event: ReplayEvent, context: Dict[str, Any]) -> bool:
        """判断是否应该暂停
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            bool: 是否应该暂停
        """
        # 实时模式下通常不自动暂停
        return False
    
    async def get_delay(self, event: ReplayEvent, context: Dict[str, Any]) -> float:
        """获取延迟时间
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            float: 延迟时间（秒）
        """
        if self._last_event_time is None:
            self._last_event_time = event.timestamp
            return 0.0
        
        # 计算实际时间间隔
        actual_interval = (event.timestamp - self._last_event_time).total_seconds()
        
        # 根据播放速度调整延迟
        speed = context.get('speed', self.config.default_speed)
        speed = max(self.config.min_speed, min(speed, self.config.max_speed))
        
        delay = actual_interval / speed if speed > 0 else 0
        
        self._last_event_time = event.timestamp
        
        return max(0, delay)
    
    async def process_event(self, event: ReplayEvent, context: Dict[str, Any]) -> ReplayEvent:
        """处理事件
        
        Args:
            event: 原始事件
            context: 上下文信息
            
        Returns:
            ReplayEvent: 处理后的事件
        """
        # 实时模式下不需要特殊处理
        return event


class FastForwardReplayStrategy(IReplayStrategy):
    """快进回放策略"""
    
    def __init__(self, config: FastForwardConfig):
        """初始化策略
        
        Args:
            config: 快进回放配置
        """
        self.config = config
    
    async def should_pause(self, event: ReplayEvent, context: Dict[str, Any]) -> bool:
        """判断是否应该暂停
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            bool: 是否应该暂停
        """
        # 快进模式下只在重要事件时暂停
        important_events = [
            "error",
            "workflow_end"
        ]
        return event.type.value in important_events
    
    async def get_delay(self, event: ReplayEvent, context: Dict[str, Any]) -> float:
        """获取延迟时间
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            float: 延迟时间（秒）
        """
        # 快进模式下使用固定的小延迟
        multiplier = context.get('multiplier', self.config.default_multiplier)
        multiplier = max(self.config.min_multiplier, min(multiplier, self.config.max_multiplier))
        
        # 基础延迟除以倍数
        base_delay = 0.1  # 100ms基础延迟
        return base_delay / multiplier
    
    async def process_event(self, event: ReplayEvent, context: Dict[str, Any]) -> ReplayEvent:
        """处理事件
        
        Args:
            event: 原始事件
            context: 上下文信息
            
        Returns:
            ReplayEvent: 处理后的事件
        """
        # 添加快进标记
        event.metadata['fast_forward'] = True
        event.metadata['multiplier'] = context.get('multiplier', self.config.default_multiplier)
        return event


class StepByStepReplayStrategy(IReplayStrategy):
    """逐步回放策略"""
    
    def __init__(self, config: StepByStepConfig):
        """初始化策略
        
        Args:
            config: 逐步回放配置
        """
        self.config = config
        self._paused = True
        self._current_event: Optional[ReplayEvent] = None
    
    async def should_pause(self, event: ReplayEvent, context: Dict[str, Any]) -> bool:
        """判断是否应该暂停
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            bool: 是否应该暂停
        """
        self._current_event = event
        
        # 检查是否是应该暂停的事件类型
        if self.config.auto_pause_on_events:
            if event.type.value in self.config.default_pause_types:
                return True
        
        # 逐步模式下默认在每个事件后暂停
        return True
    
    async def get_delay(self, event: ReplayEvent, context: Dict[str, Any]) -> float:
        """获取延迟时间
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            float: 延迟时间（秒）
        """
        # 逐步模式下不自动延迟，等待用户命令
        return 0.0
    
    async def process_event(self, event: ReplayEvent, context: Dict[str, Any]) -> ReplayEvent:
        """处理事件
        
        Args:
            event: 原始事件
            context: 上下文信息
            
        Returns:
            ReplayEvent: 处理后的事件
        """
        # 添加逐步回放标记
        event.metadata['step_by_step'] = True
        event.metadata['requires_input'] = True
        
        if self.config.show_event_details:
            # 添加事件详情
            event.metadata['event_details'] = self._generate_event_details(event)
        
        return event
    
    def _generate_event_details(self, event: ReplayEvent) -> Dict[str, Any]:
        """生成事件详情
        
        Args:
            event: 事件对象
            
        Returns:
            Dict[str, Any]: 事件详情
        """
        details = {
            'event_id': str(event.id),
            'type': event.type.value,
            'timestamp': event.timestamp.isoformat(),
            'summary': f"{event.type.value} - {event.timestamp}"
        }
        
        # 根据事件类型添加特定详情
        if event.type.value == "tool_call":
            details['tool_name'] = event.data.get('tool_name', 'Unknown')
            details['tool_input'] = str(event.data.get('tool_input', {}))
        elif event.type.value == "llm_call":
            details['model'] = event.data.get('model', 'Unknown')
            details['message_count'] = str(len(event.data.get('messages', [])))
        elif event.type.value == "error":
            details['error_type'] = event.data.get('error_type', 'Unknown')
            details['error_message'] = event.data.get('error_message', '')
        
        return details
    
    async def resume(self):
        """恢复回放"""
        self._paused = False
    
    async def pause(self):
        """暂停回放"""
        self._paused = True


class AnalysisReplayStrategy(IReplayStrategy):
    """分析模式回放策略"""
    
    def __init__(self, config: AnalysisConfig):
        """初始化策略
        
        Args:
            config: 分析模式配置
        """
        self.config = config
        self._analysis_data: Dict[str, Any] = {
            'event_count': 0,
            'event_types': {},
            'tool_calls': 0,
            'llm_calls': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': None,
            'end_time': None,
            'timeline': []
        }
    
    async def should_pause(self, event: ReplayEvent, context: Dict[str, Any]) -> bool:
        """判断是否应该暂停
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            bool: 是否应该暂停
        """
        # 分析模式下不暂停，快速处理所有事件
        return False
    
    async def get_delay(self, event: ReplayEvent, context: Dict[str, Any]) -> float:
        """获取延迟时间
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            float: 延迟时间（秒）
        """
        # 分析模式下最小延迟
        return 0.001  # 1ms
    
    async def process_event(self, event: ReplayEvent, context: Dict[str, Any]) -> ReplayEvent:
        """处理事件
        
        Args:
            event: 原始事件
            context: 上下文信息
            
        Returns:
            ReplayEvent: 处理后的事件
        """
        # 更新分析数据
        self._update_analysis_data(event)
        
        # 添加分析标记
        event.metadata['analysis_mode'] = True
        event.metadata['event_index'] = self._analysis_data['event_count']
        
        # 如果启用深度分析，添加更多分析信息
        if self.config.enable_deep_analysis:
            event.metadata['deep_analysis'] = self._perform_deep_analysis(event)
        
        return event
    
    def _update_analysis_data(self, event: ReplayEvent):
        """更新分析数据
        
        Args:
            event: 事件对象
        """
        self._analysis_data['event_count'] += 1
        
        # 统计事件类型
        event_type = event.type.value
        self._analysis_data['event_types'][event_type] = \
            self._analysis_data['event_types'].get(event_type, 0) + 1
        
        # 统计特定事件
        if event_type == "tool_call":
            self._analysis_data['tool_calls'] += 1
        elif event_type == "llm_call":
            self._analysis_data['llm_calls'] += 1
        elif event_type == "error":
            self._analysis_data['errors'] += 1
        elif event_type == "warning":
            self._analysis_data['warnings'] += 1
        
        # 更新时间范围
        if self._analysis_data['start_time'] is None:
            self._analysis_data['start_time'] = event.timestamp
        self._analysis_data['end_time'] = event.timestamp
        
        # 添加到时间线
        if len(self._analysis_data['timeline']) < 100:  # 限制时间线长度
            self._analysis_data['timeline'].append({
                'timestamp': event.timestamp.isoformat(),
                'type': event_type,
                'event_id': event.id
            })
    
    def _perform_deep_analysis(self, event: ReplayEvent) -> Dict[str, Any]:
        """执行深度分析
        
        Args:
            event: 事件对象
            
        Returns:
            Dict[str, Any]: 深度分析结果
        """
        analysis = {
            'complexity_score': 0.5,
            'performance_impact': 'low',
            'anomalies': []
        }
        
        # 根据事件类型进行特定分析
        if event.type.value == "tool_call":
            tool_input = event.data.get('tool_input', {})
            if isinstance(tool_input, dict):
                analysis['complexity_score'] = min(1.0, len(tool_input) / 10.0)
                analysis['performance_impact'] = 'medium' if len(tool_input) > 5 else 'low'
        
        elif event.type.value == "llm_call":
            messages = event.data.get('messages', [])
            analysis['complexity_score'] = min(1.0, len(messages) / 20.0)
            analysis['performance_impact'] = 'high' if len(messages) > 10 else 'medium'
        
        elif event.type.value == "error":
            analysis['complexity_score'] = 0.8
            analysis['performance_impact'] = 'high'
            analysis['anomalies'].append('error_detected')
        
        return analysis
    
    def get_analysis_data(self) -> Dict[str, Any]:
        """获取分析数据
        
        Returns:
            Dict[str, Any]: 分析数据
        """
        return self._analysis_data.copy()


class ReplayStrategyFactory:
    """回放策略工厂"""
    
    @staticmethod
    def create_strategy(
        mode: ReplayMode,
        config: Any
    ) -> IReplayStrategy:
        """创建回放策略
        
        Args:
            mode: 回放模式
            config: 模式配置
            
        Returns:
            IReplayStrategy: 回放策略实例
        """
        if mode == ReplayMode.REAL_TIME:
            return RealTimeReplayStrategy(config)
        elif mode == ReplayMode.FAST_FORWARD:
            return FastForwardReplayStrategy(config)
        elif mode == ReplayMode.STEP_BY_STEP:
            return StepByStepReplayStrategy(config)
        elif mode == ReplayMode.ANALYSIS:
            return AnalysisReplayStrategy(config)
        else:
            raise ValueError(f"不支持的回放模式: {mode}")