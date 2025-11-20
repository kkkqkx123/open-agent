"""Workflow visualization interfaces.

This module contains interfaces related to workflow visualization.
"""

from abc import ABC, abstractmethod
from typing import Any


class IWorkflowVisualizer(ABC):
    """工作流可视化器接口"""
    
    @abstractmethod
    def generate_visualization(self, config: Any, layout: str = "hierarchical") -> dict:
        """生成可视化数据"""
        pass
    
    @abstractmethod
    def export_diagram(self, config: Any, format: str = "json") -> bytes:
        """导出图表"""
        pass