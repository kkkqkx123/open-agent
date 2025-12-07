"""工作流注册表实现

已迁移到统一注册表架构，此文件保留用于向后兼容。
"""

import warnings
from typing import Dict, Any, List
from src.services.logger.injection import get_logger
from .registry import UnifiedRegistry, create_unified_registry
from ..node_registry import NodeRegistry
from ..function_registry import FunctionRegistry

logger = get_logger(__name__)


class WorkflowRegistryAdapter:
    """工作流注册表适配器
    
    为旧代码提供向后兼容性。
    """
    
    def __init__(self, unified_registry: UnifiedRegistry = None):
        """初始化适配器
        
        Args:
            unified_registry: 统一注册表实例，如果为None则创建新实例
        """
        self._unified_registry = unified_registry or create_unified_registry()
        self._logger = get_logger(f"{__name__}.WorkflowRegistryAdapter")
    
    @property
    def component_registry(self):
        """组件注册表（适配为节点注册表）"""
        return self._unified_registry.nodes
    
    @property
    def function_registry(self):
        """函数注册表"""
        return self._unified_registry.functions
    
    def validate_dependencies(self) -> List[str]:
        """验证依赖完整性"""
        return self._unified_registry.validate_dependencies()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        return self._unified_registry.get_registry_stats()
    
    def clear_all(self) -> None:
        """清除所有注册表"""
        self._unified_registry.clear_all()


# 便捷函数
def create_workflow_registry():
    """创建工作流注册表实例
    
    Returns:
        WorkflowRegistryAdapter: 工作流注册表适配器实例
    """
    warnings.warn(
        "create_workflow_registry 已弃用，请使用 create_unified_registry",
        DeprecationWarning,
        stacklevel=2
    )
    return WorkflowRegistryAdapter()


# 导出所有实现
__all__ = [
    "WorkflowRegistryAdapter",
    "create_workflow_registry",
]