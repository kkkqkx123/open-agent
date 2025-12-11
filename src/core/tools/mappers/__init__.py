"""
工具配置映射器模块

提供工具配置数据和业务实体之间的映射功能。
注意：此模块已迁移到 src/core/config/mappers，此处保留向后兼容性。
"""

# 从集中位置导入
from src.core.config.mappers import ToolsConfigMapper

# 向后兼容别名
ToolConfigMapper = ToolsConfigMapper

# 提供向后兼容的函数
def get_tools_config_mapper() -> ToolsConfigMapper:
    """获取工具配置映射器实例（向后兼容）"""
    return ToolsConfigMapper()

__all__ = [
    "ToolsConfigMapper",
    "ToolConfigMapper",
    "get_tools_config_mapper"
]