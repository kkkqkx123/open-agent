"""映射器模块

提供配置数据和业务实体之间的转换功能。
"""

from .config_mapper import (
    ConfigMapper,
    get_config_mapper,
    dict_to_graph,
    graph_to_dict
)

__all__ = [
    "ConfigMapper",
    "get_config_mapper",
    "dict_to_graph",
    "graph_to_dict"
]