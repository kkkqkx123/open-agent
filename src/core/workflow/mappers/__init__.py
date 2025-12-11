"""
工作流配置映射器模块

提供工作流配置数据和业务实体之间的映射功能。
注意：此模块已迁移到 src/core/config/mappers，此处保留向后兼容性。
"""

# 从集中位置导入
from src.core.config.mappers import WorkflowConfigMapper

# 提供向后兼容的函数
def get_workflow_config_mapper() -> WorkflowConfigMapper:
    """获取工作流配置映射器实例（向后兼容）"""
    return WorkflowConfigMapper()

__all__ = [
    "WorkflowConfigMapper",
    "get_workflow_config_mapper"
]