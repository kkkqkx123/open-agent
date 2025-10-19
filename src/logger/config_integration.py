"""日志系统与配置系统集成"""

import threading
from typing import Dict, Any, Optional

from ..config import ConfigChangeContext, register_config_callback, CallbackPriority
from .logger import get_logger, set_global_config
from .error_handler import get_global_error_handler, ErrorType
from .metrics import get_global_metrics_collector, MetricsCollector


class LoggingConfigIntegration:
    """日志系统与配置系统集成"""

    def __init__(self) -> None:
        """初始化集成"""
        self._logger = get_logger("logging_integration")
        self._error_handler = get_global_error_handler()
        self._metrics_collector = get_global_metrics_collector()
        self._lock = threading.RLock()
        self._initialized = False

    def initialize(self) -> None:
        """初始化集成"""
        with self._lock:
            if self._initialized:
                return

            # 加载初始配置
            self._load_initial_config()

            # 注册配置变更回调
            register_config_callback(
                "logging_config_integration",
                self._handle_config_change,
                priority=CallbackPriority.HIGHEST,
                filter_paths=["global.yaml"],
            )

            self._initialized = True
            self._logger.info("日志系统与配置系统集成已初始化")

    def _load_initial_config(self) -> None:
        """加载初始配置"""
        try:
            # 尝试从配置文件加载
            from ..infrastructure.config_loader import IConfigLoader
            from ..config.models.global_config import GlobalConfig

            # 尝试从容器获取配置加载器
            config_loader = None
            try:
                from ..infrastructure.container import DependencyContainer

                container = DependencyContainer()
                if container.has_service(IConfigLoader):
                    config_loader = container.get(IConfigLoader)
            except:
                pass

            # 如果无法从容器获取，创建新的实例
            if config_loader is None:
                from ..infrastructure.config_loader import YamlConfigLoader

                config_loader = YamlConfigLoader()

            config_data = config_loader.load("global.yaml")

            # 创建全局配置对象
            global_config = GlobalConfig(**config_data)

            # 设置全局配置
            set_global_config(global_config)

        except Exception as e:
            # 如果加载配置失败，使用默认配置
            self._error_handler.handle_error(
                ErrorType.SYSTEM_ERROR, e, {"operation": "load_initial_config"}
            )

            # 使用默认配置
            from ..config.models.global_config import GlobalConfig, LogOutputConfig

            default_config = GlobalConfig(
                log_level="INFO",
                log_outputs=[
                    LogOutputConfig(
                        type="console",
                        level="INFO",
                        format="text",
                        path=None,
                        rotation=None,
                        max_size=None,
                    )
                ],
                env="development",
                debug=True,
                env_prefix="AGENT_",
                hot_reload=True,
                watch_interval=5,
            )
            set_global_config(default_config)

    def _handle_config_change(self, context: ConfigChangeContext) -> None:
        """处理配置变更

        Args:
            context: 配置变更上下文
        """
        try:
            # 检查是否是全局配置变更
            if context.config_path == "global.yaml":
                self._handle_global_config_change(context)

        except Exception as e:
            self._error_handler.handle_error(
                ErrorType.SYSTEM_ERROR,
                e,
                {
                    "operation": "handle_config_change",
                    "config_path": context.config_path,
                },
            )

    def _handle_global_config_change(self, context: ConfigChangeContext) -> None:
        """处理全局配置变更

        Args:
            context: 配置变更上下文
        """
        try:
            # 检查日志相关配置是否有变化
            old_config = context.old_config or {}
            new_config = context.new_config

            # 检查日志级别变化
            old_level = old_config.get("log_level", "INFO")
            new_level = new_config.get("log_level", "INFO")

            if old_level != new_level:
                self._logger.info(f"日志级别已变更: {old_level} -> {new_level}")

            # 检查日志输出配置变化
            old_outputs = old_config.get("log_outputs", [])
            new_outputs = new_config.get("log_outputs", [])

            if old_outputs != new_outputs:
                self._logger.info("日志输出配置已变更")

            # 检查脱敏模式变化
            old_patterns = old_config.get("secret_patterns", [])
            new_patterns = new_config.get("secret_patterns", [])

            if old_patterns != new_patterns:
                self._logger.info("敏感信息脱敏模式已变更")

            # 更新全局配置
            from ..config.models.global_config import GlobalConfig

            global_config = GlobalConfig(**new_config)
            set_global_config(global_config)

            # 记录配置变更指标
            if hasattr(self._metrics_collector, "record_config_change"):
                self._metrics_collector.record_config_change(  # type: ignore
                    "global.yaml", old_config, new_config
                )

        except Exception as e:
            self._error_handler.handle_error(
                ErrorType.SYSTEM_ERROR,
                e,
                {
                    "operation": "handle_global_config_change",
                    "config_path": context.config_path,
                },
            )


# 全局集成实例
_logging_integration: Optional[LoggingConfigIntegration] = None
_integration_lock = threading.Lock()


def get_logging_integration() -> LoggingConfigIntegration:
    """获取日志集成实例

    Returns:
        日志集成实例
    """
    global _logging_integration
    if _logging_integration is None:
        with _integration_lock:
            if _logging_integration is None:
                _logging_integration = LoggingConfigIntegration()
    return _logging_integration


def initialize_logging_integration() -> None:
    """初始化日志系统与配置系统集成"""
    integration = get_logging_integration()
    integration.initialize()


# 扩展指标收集器以支持配置变更指标
def _extend_metrics_collector() -> None:
    """扩展指标收集器"""

    def record_config_change(
        self: "MetricsCollector",
        config_path: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
    ) -> None:
        """记录配置变更指标

        Args:
            config_path: 配置路径
            old_config: 旧配置
            new_config: 新配置
        """
        # 这里可以添加配置变更的指标记录逻辑
        pass

    # 动态添加方法到指标收集器
    from .metrics import MetricsCollector

    MetricsCollector.record_config_change = record_config_change  # type: ignore


# 初始化时扩展指标收集器
_extend_metrics_collector()
