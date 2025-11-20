"""工作流构建服务实现，遵循新架构。

此模块提供工作流构建服务，处理从配置创建工作流和验证功能。
"""

from typing import Dict, Any, List
from src.core.workflow.interfaces import IWorkflow
from src.core.workflow.workflow import Workflow
from src.core.workflow.graph.builder import GraphBuilder
from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
from src.core.workflow.config.config import GraphConfig
from ..interfaces import IWorkflowBuilderService


class WorkflowBuilderService(IWorkflowBuilderService):
    """工作流构建服务实现。

    此类提供从配置构建工作流的方法，
    验证配置，并管理工作流构建过程。
    """

    def __init__(self):
        """初始化工作流构建服务。"""
        self._validator = WorkflowConfigValidator()
        self._graph_builder = GraphBuilder()

    def build_workflow(self, config: Dict[str, Any]) -> IWorkflow:
        """从配置构建工作流。

        Args:
            config: 工作流配置

        Returns:
            构建的工作流实例
        """
        # 验证配置
        errors = self.validate_config(config)
        if errors:
            raise ValueError(f"配置无效: {', '.join(errors)}")

        # 提取工作流信息
        workflow_id = config.get("workflow_id")
        if not workflow_id:
            raise ValueError("workflow_id 是必需的")

        name = config.get("name", workflow_id)

        # 创建工作流
        workflow = Workflow(workflow_id, name)

        # 从字典创建 GraphConfig 对象
        graph_config = GraphConfig.from_dict(config)

        # 构建图
        graph = self._graph_builder.build_graph(graph_config)
        workflow.set_graph(graph)

        # 如果指定了入口点，则设置
        if "entry_point" in config:
            workflow.set_entry_point(config["entry_point"])

        # 如果指定了元数据，则设置
        if "metadata" in config:
            workflow.metadata = config["metadata"]

        return workflow

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流配置。

        Args:
            config: 要验证的配置

        Returns:
            验证错误列表
        """
        # 使用 validate_config 方法，传入 GraphConfig 对象
        config_obj = GraphConfig.from_dict(config)
        result = self._validator.validate_config(config_obj)
        return result.errors

    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式。

        Returns:
            配置模式
        """
        # 返回验证规则作为模式
        return self._validator.get_validation_rules()