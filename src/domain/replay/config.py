"""重放功能配置模型"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class ReplayMode(Enum):
    """回放模式枚举"""
    REAL_TIME = "real_time"
    FAST_FORWARD = "fast_forward"
    STEP_BY_STEP = "step_by_step"
    ANALYSIS = "analysis"


@dataclass
class RealTimeConfig:
    """实时回放配置"""
    default_speed: float = 1.0
    min_speed: float = 0.1
    max_speed: float = 10.0
    allow_skip: bool = True


@dataclass
class FastForwardConfig:
    """快进回放配置"""
    default_multiplier: float = 5.0
    min_multiplier: float = 2.0
    max_multiplier: float = 100.0


@dataclass
class StepByStepConfig:
    """逐步回放配置"""
    auto_pause_on_events: bool = True
    default_pause_types: List[str] = field(default_factory=lambda: [
        "tool_call", "error", "workflow_end"
    ])
    show_event_details: bool = True


@dataclass
class AnalysisConfig:
    """分析模式配置"""
    enable_deep_analysis: bool = True
    analysis_level: str = "detailed"  # basic, detailed, comprehensive
    generate_recommendations: bool = True
    include_performance_metrics: bool = True


@dataclass
class ModeConfigs:
    """回放模式配置集合"""
    real_time: RealTimeConfig = field(default_factory=RealTimeConfig)
    fast_forward: FastForwardConfig = field(default_factory=FastForwardConfig)
    step_by_step: StepByStepConfig = field(default_factory=StepByStepConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)


@dataclass
class ProcessorConfig:
    """回放处理器配置"""
    max_concurrent_replays: int = 10
    session_timeout: int = 3600
    batch_size: int = 100
    enable_performance_monitoring: bool = True


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = 1800
    max_entries: int = 1000
    key_prefix: str = "replay:"


@dataclass
class EventFilterConfig:
    """事件过滤配置"""
    default_included_types: List[str] = field(default_factory=lambda: [
        "workflow_start", "workflow_end", "node_start", "node_end",
        "tool_call", "tool_result", "llm_call", "llm_response", "error"
    ])
    default_excluded_types: List[str] = field(default_factory=lambda: [
        "debug", "trace"
    ])
    allow_custom_filters: bool = True


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    enable_statistics: bool = True
    enable_performance_analysis: bool = True
    enable_cost_analysis: bool = True
    enable_error_analysis: bool = True
    cache_ttl: int = 600
    max_analysis_history: int = 100


@dataclass
class InteractiveConfig:
    """交互式回放配置"""
    enable_commands: bool = True
    supported_commands: List[str] = field(default_factory=lambda: [
        "next", "skip", "pause", "resume", "speed", "jump", 
        "detail", "analyze", "quit"
    ])
    prompt: str = "> "
    show_help: bool = True
    enable_autocomplete: bool = True


@dataclass
class ExportConfig:
    """导出配置"""
    supported_formats: List[str] = field(default_factory=lambda: [
        "json", "csv", "html", "markdown"
    ])
    default_format: str = "json"
    include_raw_events: bool = True
    include_analysis: bool = True
    filename_template: str = "replay_{session_id}_{timestamp}.{format}"


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    log_events: bool = False
    log_performance: bool = True
    log_errors: bool = True
    format: str = "[{timestamp}] {level} - {message}"


@dataclass
class ReplayConfig:
    """重放功能主配置"""
    enabled: bool = True
    default_mode: ReplayMode = ReplayMode.REAL_TIME
    processor: ProcessorConfig = field(default_factory=ProcessorConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    modes: ModeConfigs = field(default_factory=ModeConfigs)
    event_filters: EventFilterConfig = field(default_factory=EventFilterConfig)
    analyzer: AnalyzerConfig = field(default_factory=AnalyzerConfig)
    interactive: InteractiveConfig = field(default_factory=InteractiveConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReplayConfig':
        """从字典创建配置对象"""
        # 处理主配置
        replay_data = data.get('replay', {})
        
        # 处理回放模式
        default_mode = ReplayMode(replay_data.get('default_mode', 'real_time'))
        
        # 处理处理器配置
        processor_data = replay_data.get('processor', {})
        processor = ProcessorConfig(
            max_concurrent_replays=processor_data.get('max_concurrent_replays', 10),
            session_timeout=processor_data.get('session_timeout', 3600),
            batch_size=processor_data.get('batch_size', 100),
            enable_performance_monitoring=processor_data.get('enable_performance_monitoring', True)
        )
        
        # 处理缓存配置
        cache_data = replay_data.get('cache', {})
        cache = CacheConfig(
            enabled=cache_data.get('enabled', True),
            ttl=cache_data.get('ttl', 1800),
            max_entries=cache_data.get('max_entries', 1000),
            key_prefix=cache_data.get('key_prefix', 'replay:')
        )
        
        # 处理模式配置
        modes_data = replay_data.get('modes', {})
        
        # 实时模式配置
        real_time_data = modes_data.get('real_time', {})
        real_time = RealTimeConfig(
            default_speed=real_time_data.get('default_speed', 1.0),
            min_speed=real_time_data.get('min_speed', 0.1),
            max_speed=real_time_data.get('max_speed', 10.0),
            allow_skip=real_time_data.get('allow_skip', True)
        )
        
        # 快进模式配置
        fast_forward_data = modes_data.get('fast_forward', {})
        fast_forward = FastForwardConfig(
            default_multiplier=fast_forward_data.get('default_multiplier', 5.0),
            min_multiplier=fast_forward_data.get('min_multiplier', 2.0),
            max_multiplier=fast_forward_data.get('max_multiplier', 100.0)
        )
        
        # 逐步模式配置
        step_by_step_data = modes_data.get('step_by_step', {})
        step_by_step = StepByStepConfig(
            auto_pause_on_events=step_by_step_data.get('auto_pause_on_events', True),
            default_pause_types=step_by_step_data.get('default_pause_types', [
                "tool_call", "error", "workflow_end"
            ]),
            show_event_details=step_by_step_data.get('show_event_details', True)
        )
        
        # 分析模式配置
        analysis_data = modes_data.get('analysis', {})
        analysis = AnalysisConfig(
            enable_deep_analysis=analysis_data.get('enable_deep_analysis', True),
            analysis_level=analysis_data.get('analysis_level', 'detailed'),
            generate_recommendations=analysis_data.get('generate_recommendations', True),
            include_performance_metrics=analysis_data.get('include_performance_metrics', True)
        )
        
        modes = ModeConfigs(
            real_time=real_time,
            fast_forward=fast_forward,
            step_by_step=step_by_step,
            analysis=analysis
        )
        
        # 处理事件过滤配置
        filters_data = replay_data.get('event_filters', {})
        event_filters = EventFilterConfig(
            default_included_types=filters_data.get('default_included_types', [
                "workflow_start", "workflow_end", "node_start", "node_end",
                "tool_call", "tool_result", "llm_call", "llm_response", "error"
            ]),
            default_excluded_types=filters_data.get('default_excluded_types', [
                "debug", "trace"
            ]),
            allow_custom_filters=filters_data.get('allow_custom_filters', True)
        )
        
        # 处理分析器配置
        analyzer_data = replay_data.get('analyzer', {})
        analyzer = AnalyzerConfig(
            enable_statistics=analyzer_data.get('enable_statistics', True),
            enable_performance_analysis=analyzer_data.get('enable_performance_analysis', True),
            enable_cost_analysis=analyzer_data.get('enable_cost_analysis', True),
            enable_error_analysis=analyzer_data.get('enable_error_analysis', True),
            cache_ttl=analyzer_data.get('cache_ttl', 600),
            max_analysis_history=analyzer_data.get('max_analysis_history', 100)
        )
        
        # 处理交互式配置
        interactive_data = replay_data.get('interactive', {})
        interactive = InteractiveConfig(
            enable_commands=interactive_data.get('enable_commands', True),
            supported_commands=interactive_data.get('supported_commands', [
                "next", "skip", "pause", "resume", "speed", "jump", 
                "detail", "analyze", "quit"
            ]),
            prompt=interactive_data.get('prompt', '> '),
            show_help=interactive_data.get('show_help', True),
            enable_autocomplete=interactive_data.get('enable_autocomplete', True)
        )
        
        # 处理导出配置
        export_data = replay_data.get('export', {})
        export = ExportConfig(
            supported_formats=export_data.get('supported_formats', [
                "json", "csv", "html", "markdown"
            ]),
            default_format=export_data.get('default_format', 'json'),
            include_raw_events=export_data.get('include_raw_events', True),
            include_analysis=export_data.get('include_analysis', True),
            filename_template=export_data.get('filename_template', 'replay_{session_id}_{timestamp}.{format}')
        )
        
        # 处理日志配置
        logging_data = replay_data.get('logging', {})
        logging = LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            log_events=logging_data.get('log_events', False),
            log_performance=logging_data.get('log_performance', True),
            log_errors=logging_data.get('log_errors', True),
            format=logging_data.get('format', '[{timestamp}] {level} - {message}')
        )
        
        return cls(
            enabled=replay_data.get('enabled', True),
            default_mode=default_mode,
            processor=processor,
            cache=cache,
            modes=modes,
            event_filters=event_filters,
            analyzer=analyzer,
            interactive=interactive,
            export=export,
            logging=logging
        )