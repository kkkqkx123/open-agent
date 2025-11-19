"""Workflow adapters module

此目录已重构，仅保留真正的外部适配器。

工作流相关的实现已迁移到：
- src/services/workflow/ - 业务逻辑和LangGraph集成
- src/core/llm/ - 消息转换
- src/core/workflow/interfaces/ - 公共接口定义

本目录仅保留：
- WorkflowVisualizer - 工作流可视化适配器
"""

from .visualizer import WorkflowVisualizer

__all__ = [
    "WorkflowVisualizer",
]
