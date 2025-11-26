"""工作流构建服务实现，遵循新架构。

此模块提供工作流构建服务，处理从配置创建工作流和验证功能。
优化后使用核心层的UnifiedGraphBuilder，消除重复代码。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.interfaces.workflow.core import IWorkflow
    from src.core.workflow.config.config import GraphConfig

from src.core.workflow.graph.builder.base import UnifiedGraphBuilder
from src.interfaces import IWorkflowBuilderService

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
        # 延迟导入避免循环依赖
        self._validator = None
        # 使用核心层的UnifiedGraphBuilder替代GraphBuilder
        self._graph_builder = UnifiedGraphBuilder(
            node_registry=node_registry,
            function_registry=function_registry,
            enable_function_fallback=True,
            enable_iteration_management=False  # 暂时禁用迭代管理
        )
        
        # 初始化提示词服务
        try:
            import asyncio
            from src.services.prompts import create_prompt_system
            
            # 在同步方法中运行异步创建
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                prompt_system = loop.run_until_complete(create_prompt_system())
                self._prompt_service = prompt_system["injector"]  # 使用注入器作为提示词服务
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"创建提示词系统失败，使用 None: {e}")
            self._prompt_service = None
        
        logger.info("工作流构建服务初始化完成（集成提示词系统）")

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

            # 跳过配置预处理（应该在 prompt 模块中实现）
            processed_config = config

            # 提取工作流信息
            workflow_id = processed_config.get("workflow_id") or processed_config.get("id")
            if not workflow_id:
                raise ValueError("workflow_id 是必需的")

            name = processed_config.get("name", workflow_id)
            logger.info(f"开始构建工作流: {workflow_id} ({name})")

            # 延迟导入避免循环依赖
            from src.core.workflow.config.config import GraphConfig

            # 创建工作流 - 使用工厂方法避免直接导入
            workflow = self._create_workflow_instance(workflow_id, name)

            # 从字典创建 GraphConfig 对象
            graph_config = GraphConfig.from_dict(processed_config)

            # 使用核心层的UnifiedGraphBuilder构建图
            graph = self._graph_builder.build_graph(graph_config)
            workflow.set_graph(graph)

            # 跳过节点的提示词系统配置（应该在 prompt 模块中实现）

            # 如果指定了入口点，则设置
            if "entry_point" in processed_config:
                workflow.set_entry_point(processed_config["entry_point"])

            # 如果指定了元数据，则设置
            if "metadata" in processed_config:
                workflow.metadata = processed_config["metadata"]

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
            
            # 延迟导入验证器避免循环依赖
            if self._validator is None:
                from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
                self._validator = WorkflowConfigValidator()
            
            result = self._validator.validate_config(config_obj)
            
            if result.has_errors():
                logger.warning(f"配置验证失败: {result.errors}")
            
            # 提示词配置验证应该在 prompt 模块中实现，这里不再重复验证
            
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
            # 延迟导入验证器避免循环依赖
            if self._validator is None:
                from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
                self._validator = WorkflowConfigValidator()
            
            # 返回核心层验证器的验证规则作为模式
            schema = self._validator.get_validation_rules()
            logger.debug("返回配置模式")
            return schema
        except Exception as e:
            logger.error(f"获取配置模式失败: {e}")
            return {}
    
    def _create_workflow_instance(self, workflow_id: str, name: str) -> 'IWorkflow':
        """创建工作流实例，避免循环导入
        
        Args:
            workflow_id: 工作流ID
            name: 工作流名称
            
        Returns:
            IWorkflow: 工作流实例
        """
        # 延迟导入避免循环依赖
        from src.core.workflow.workflow_instance import Workflow
        return Workflow(workflow_id, name)
    
    