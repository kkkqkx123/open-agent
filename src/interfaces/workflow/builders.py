"""Workflow builder interfaces.

This module contains interfaces related to workflow building.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from .core import IWorkflow


class IWorkflowBuilder(ABC):
    """工作流构建器接口"""

    @abstractmethod
    def create_workflow(self, config: Dict[str, Any]) -> IWorkflow:
        """创建工作流"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        pass