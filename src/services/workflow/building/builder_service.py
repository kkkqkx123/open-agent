"""工作流构建服务实现，遵循新架构。

此模块提供工作流构建服务，处理从配置创建工作流和验证功能。
优化后使用核心层的UnifiedGraphBuilder，消除重复代码。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.core.workflow.interfaces import IWorkflow
    from src.core.workflow.config.config import GraphConfig

from src.core.workflow.graph.builder.base import UnifiedGraphBuilder
from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
from ..interfaces import IWorkflowBuilderService

logger = logging.getLogger(__name__)


class WorkflowBuilderService(IWorkflowBuilderService):
    """工作流构建服务实现。

    此类提供从配置构建工作流的方法，
    验证配置，并管理工作流构建过程。
    
    优化后：
    - 使用核心层的UnifiedGraphBuilder
    - 简化配置验证逻辑
    - 增强错误处理和日志记录
    """

    def __init__(self, node_registry=None, function_registry=None):
        """初始化工作流构建服务。
        
        Args:
            node_registry: 节点注册表（可选）
            function_registry: 函数注册表（可选）
        """
        self._validator = WorkflowConfigValidator()
        # 使用核心层的UnifiedGraphBuilder替代GraphBuilder
        self._graph_builder = UnifiedGraphBuilder(
            node_registry=node_registry,
            function_registry=function_registry,
            enable_function_fallback=True,
            enable_iteration_management=False  # 暂时禁用迭代管理
        )
        
        logger.info("工作流构建服务初始化完成")

    def build_workflow(self, config: Dict[str, Any]) -> 'IWorkflow':
        """从配置构建工作流。

        Args:
            config: 工作流配置

        Returns:
            构建的工作流实例
            
        Raises:
            ValueError: 配置无效时
            RuntimeError: 构建失败时
        """
        try:
            # 验证配置
            errors = self.validate_config(config)
            if errors:
                error_msg = f"配置无效: {', '.join(errors)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 提取工作流信息
            workflow_id = config.get("workflow_id") or config.get("id")
            if not workflow_id:
                raise ValueError("workflow_id 是必需的")

            name = config.get("name", workflow_id)
            logger.info(f"开始构建工作流: {workflow_id} ({name})")

            # 延迟导入避免循环依赖
            from src.core.workflow.workflow import Workflow
            from src.core.workflow.config.config import GraphConfig

            # 创建工作流
            workflow = Workflow(workflow_id, name)

            # 从字典创建 GraphConfig 对象
            graph_config = GraphConfig.from_dict(config)

            # 使用核心层的UnifiedGraphBuilder构建图
            graph = self._graph_builder.build_graph(graph_config)
            workflow.set_graph(graph)

            # 如果指定了入口点，则设置
            if "entry_point" in config:
                workflow.set_entry_point(config["entry_point"])

            # 如果指定了元数据，则设置
            if "metadata" in config:
                workflow.metadata = config["metadata"]

            logger.info(f"工作流构建完成: {workflow_id}")
            return workflow

        except Exception as e:
            logger.error(f"构建工作流失败: {e}")
            raise RuntimeError(f"构建工作流失败: {e}") from e

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流配置。

        Args:
            config: 要验证的配置

        Returns:
            验证错误列表，空列表表示验证通过
        """
        try:
            # 延迟导入避免循环依赖
            from src.core.workflow.config.config import GraphConfig
            
            # 使用核心层的配置验证
            config_obj = GraphConfig.from_dict(config)
            result = self._validator.validate_config(config_obj)
            
            if result.has_errors():
                logger.warning(f"配置验证失败: {result.errors}")
            
            return result.errors
            
        except Exception as e:
            logger.error(f"配置验证过程中发生异常: {e}")
            return [f"配置验证异常: {e}"]

    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式。

        Returns:
            配置模式
        """
        try:
            # 返回核心层验证器的验证规则作为模式
            schema = self._validator.get_validation_rules()
            logger.debug("返回配置模式")
            return schema
        except Exception as e:
            logger.error(f"获取配置模式失败: {e}")
            return {}