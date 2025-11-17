"""内置插件模块

包含所有内置的START和END节点插件。
"""

# 导入START插件
from .start import (
    ContextSummaryPlugin,
    EnvironmentCheckPlugin,
    MetadataCollectorPlugin
)

# 导入END插件
from .end import (
    ResultSummaryPlugin,
    ExecutionStatsPlugin,
    FileTrackerPlugin,
    CleanupManagerPlugin
)

__all__ = [
    # START插件
    "ContextSummaryPlugin",
    "EnvironmentCheckPlugin", 
    "MetadataCollectorPlugin",
    
    # END插件
    "ResultSummaryPlugin",
    "ExecutionStatsPlugin",
    "FileTrackerPlugin",
    "CleanupManagerPlugin"
]