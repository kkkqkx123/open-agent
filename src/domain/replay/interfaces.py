"""重放功能领域接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, Union, Callable, AsyncGenerator, Coroutine
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ReplayMode(Enum):
    """回放模式枚举"""
    REAL_TIME = "real_time"        # 实时回放
    FAST_FORWARD = "fast_forward"  # 快进
    STEP_BY_STEP = "step_by_step"  # 逐步
    ANALYSIS = "analysis"          # 分析模式


class ReplayStatus(Enum):
    """回放状态枚举"""
    PENDING = "pending"            # 等待中
    RUNNING = "running"            # 运行中
    PAUSED = "paused"              # 已暂停
    COMPLETED = "completed"        # 已完成
    ERROR = "error"                # 错误
    STOPPED = "stopped"            # 已停止


class EventType(Enum):
    """事件类型枚举"""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    NODE_START = "node_start"
    NODE_END = "node_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    USER_MESSAGE = "user_message"
    SYSTEM_RESPONSE = "system_response"


@dataclass
class ReplayEvent:
    """回放事件数据模型"""
    id: str
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    session_id: str
    thread_id: Optional[str] = None
    workflow_id: Optional[str] = None


@dataclass
class ReplaySession:
    """回放会话数据模型"""
    id: str
    session_id: str
    mode: ReplayMode
    status: ReplayStatus
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 - 1.0


@dataclass
class ReplayFilter:
    """回放过滤器"""
    event_types: Optional[List[EventType]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    thread_ids: Optional[List[str]] = None
    workflow_ids: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None


@dataclass
class ReplayConfig:
    """回放配置"""
    mode: ReplayMode
    speed: float = 1.0
    filters: Optional[ReplayFilter] = None
    auto_start: bool = False
    max_events: Optional[int] = None
    enable_analysis: bool = False
    export_format: Optional[str] = None


@dataclass
class ReplayAnalysis:
    """回放分析结果"""
    session_id: str
    total_events: int
    event_types: Dict[str, int]
    duration_seconds: float
    tool_calls: int
    llm_calls: int
    errors: int
    warnings: int
    performance_metrics: Dict[str, Any]
    cost_analysis: Dict[str, Any]
    recommendations: List[str]
    timeline: List[Dict[str, Any]]


class IReplaySource(ABC):
    """回放数据源接口"""
    
    @abstractmethod
    def get_events(
        self, 
        session_id: str, 
        filters: Optional[ReplayFilter] = None
    ) -> AsyncGenerator[ReplayEvent, None]:
        """获取事件流
        
        Args:
            session_id: 会话ID
            filters: 过滤器
            
        Yields:
            ReplayEvent: 事件对象
        """
        ...
    
    @abstractmethod
    async def get_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """获取检查点列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 检查点列表
        """
        pass
    
    @abstractmethod
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话信息
        """
        pass


class IReplayStrategy(ABC):
    """回放策略接口"""
    
    @abstractmethod
    async def should_pause(self, event: ReplayEvent, context: Dict[str, Any]) -> bool:
        """判断是否应该暂停
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            bool: 是否应该暂停
        """
        pass
    
    @abstractmethod
    async def get_delay(self, event: ReplayEvent, context: Dict[str, Any]) -> float:
        """获取延迟时间
        
        Args:
            event: 当前事件
            context: 上下文信息
            
        Returns:
            float: 延迟时间（秒）
        """
        pass
    
    @abstractmethod
    async def process_event(self, event: ReplayEvent, context: Dict[str, Any]) -> ReplayEvent:
        """处理事件
        
        Args:
            event: 原始事件
            context: 上下文信息
            
        Returns:
            ReplayEvent: 处理后的事件
        """
        pass


class IReplayEngine(ABC):
    """回放引擎接口"""
    
    @abstractmethod
    async def start_replay(
        self, 
        session_id: str, 
        config: ReplayConfig
    ) -> str:
        """开始回放
        
        Args:
            session_id: 会话ID
            config: 回放配置
            
        Returns:
            str: 回放会话ID
        """
        pass
    
    @abstractmethod
    def get_replay_stream(self, replay_id: str) -> AsyncGenerator[ReplayEvent, None]:
        """获取回放事件流
        
        Args:
            replay_id: 回放会话ID
            
        Yields:
            ReplayEvent: 回放事件
        """
        ...
    
    @abstractmethod
    async def pause_replay(self, replay_id: str) -> bool:
        """暂停回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            bool: 是否成功暂停
        """
        pass
    
    @abstractmethod
    async def resume_replay(self, replay_id: str) -> bool:
        """恢复回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            bool: 是否成功恢复
        """
        pass
    
    @abstractmethod
    async def stop_replay(self, replay_id: str) -> bool:
        """停止回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            bool: 是否成功停止
        """
        pass
    
    @abstractmethod
    async def get_replay_session(self, replay_id: str) -> Optional[ReplaySession]:
        """获取回放会话信息
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            Optional[ReplaySession]: 回放会话信息
        """
        pass
    
    @abstractmethod
    async def list_active_replays(self) -> List[ReplaySession]:
        """列出活跃的回放会话
        
        Returns:
            List[ReplaySession]: 活跃回放会话列表
        """
        pass


class IReplayAnalyzer(ABC):
    """回放分析器接口"""
    
    @abstractmethod
    async def analyze_session(self, session_id: str) -> ReplayAnalysis:
        """分析会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            ReplayAnalysis: 分析结果
        """
        pass
    
    @abstractmethod
    async def analyze_replay(self, replay_id: str) -> ReplayAnalysis:
        """分析回放
        
        Args:
            replay_id: 回放会话ID
            
        Returns:
            ReplayAnalysis: 分析结果
        """
        pass
    
    @abstractmethod
    async def get_analysis_history(self, session_id: str) -> List[ReplayAnalysis]:
        """获取分析历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[ReplayAnalysis]: 分析历史列表
        """
        pass
    
    @abstractmethod
    async def generate_recommendations(self, analysis: ReplayAnalysis) -> List[str]:
        """生成优化建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[str]: 建议列表
        """
        pass


class IReplayExporter(ABC):
    """回放导出器接口"""
    
    @abstractmethod
    async def export_replay(
        self, 
        replay_id: str, 
        format: str, 
        output_path: Optional[str] = None
    ) -> str:
        """导出回放
        
        Args:
            replay_id: 回放会话ID
            format: 导出格式
            output_path: 输出路径
            
        Returns:
            str: 导出文件路径
        """
        pass
    
    @abstractmethod
    async def export_analysis(
        self, 
        analysis: ReplayAnalysis, 
        format: str, 
        output_path: Optional[str] = None
    ) -> str:
        """导出分析结果
        
        Args:
            analysis: 分析结果
            format: 导出格式
            output_path: 输出路径
            
        Returns:
            str: 导出文件路径
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的导出格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        pass


class IInteractiveReplayHandler(ABC):
    """交互式回放处理器接口"""
    
    @abstractmethod
    async def handle_command(self, replay_id: str, command: str, args: List[str]) -> Dict[str, Any]:
        """处理交互命令
        
        Args:
            replay_id: 回放会话ID
            command: 命令
            args: 命令参数
            
        Returns:
            Dict[str, Any]: 命令结果
        """
        pass
    
    @abstractmethod
    async def get_available_commands(self) -> List[Dict[str, str]]:
        """获取可用命令列表
        
        Returns:
            List[Dict[str, str]]: 命令列表
        """
        pass
    
    @abstractmethod
    async def show_help(self, command: Optional[str] = None) -> str:
        """显示帮助信息
        
        Args:
            command: 命令名称，None表示显示所有命令
            
        Returns:
            str: 帮助信息
        """
        pass