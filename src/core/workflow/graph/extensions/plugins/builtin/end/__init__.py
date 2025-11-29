"""END节点内置插件模块

包含所有用于END节点的内置插件。
"""

from .result_summary import ResultSummaryPlugin
from .execution_stats import ExecutionStatsPlugin
from .file_tracker import FileTrackerPlugin
from .cleanup_manager import CleanupManagerPlugin

__all__ = [
    "ResultSummaryPlugin",
    "ExecutionStatsPlugin",
    "FileTrackerPlugin",
    "CleanupManagerPlugin"
]