"""
工具配置映射器模块

提供工具配置数据和业务实体之间的映射功能。
"""

from .config_mapper import ToolsConfigMapper, get_tools_config_mapper

# 向后兼容别名
ToolConfigMapper = ToolsConfigMapper

__all__ = [
    "ToolsConfigMapper",
    "ToolConfigMapper",
    "get_tools_config_mapper"
]