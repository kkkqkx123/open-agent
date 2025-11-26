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
from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
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
        self._validator = WorkflowConfigValidator()
        # 使用核心层的UnifiedGraphBuilder替代GraphBuilder
        self._graph_builder = UnifiedGraphBuilder(
            node_registry=node_registry,
            function_registry=function_registry,
            enable_function_fallback=True,
            enable_iteration_management=False  # 暂时禁用迭代管理
        )
        
        # 初始化提示词服务
        from src.core.workflow.services.prompt_service import get_workflow_prompt_service_sync
        self._prompt_service = get_workflow_prompt_service_sync()
        
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

            # 预处理配置（应用提示词处理）
            processed_config = self._preprocess_config(config)

            # 提取工作流信息
            workflow_id = processed_config.get("workflow_id") or processed_config.get("id")
            if not workflow_id:
                raise ValueError("workflow_id 是必需的")

            name = processed_config.get("name", workflow_id)
            logger.info(f"开始构建工作流: {workflow_id} ({name})")

            # 延迟导入避免循环依赖
            from src.core.workflow.workflow_instance import Workflow
            from src.core.workflow.config.config import GraphConfig

            # 创建工作流
            workflow = Workflow(workflow_id, name)

            # 从字典创建 GraphConfig 对象
            graph_config = GraphConfig.from_dict(processed_config)

            # 使用核心层的UnifiedGraphBuilder构建图
            graph = self._graph_builder.build_graph(graph_config)
            workflow.set_graph(graph)

            # 配置节点的提示词系统
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._configure_node_prompts(graph, processed_config))
            finally:
                loop.close()

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
            result = self._validator.validate_config(config_obj)
            
            if result.has_errors():
                logger.warning(f"配置验证失败: {result.errors}")
            
            # 验证提示词配置
            prompt_errors = self._validate_prompt_config(config)
            result.errors.extend(prompt_errors)
            
            return result.errors
            
        except Exception as e:
            logger.error(f"配置验证过程中发生异常: {e}")
            return [f"配置验证异常: {e}"]
    
    def _validate_prompt_config(self, config: Dict[str, Any]) -> List[str]:
        """验证提示词相关配置"""
        try:
            import asyncio
            
            # 在同步方法中运行异步验证
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._prompt_service.validate_prompt_configuration(config)
                )
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"提示词配置验证失败: {e}")
            return [f"提示词配置验证异常: {e}"]

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
    
    def configure_prompt_system(self, prompt_registry, prompt_injector):
        """配置提示词系统
        
        Args:
            prompt_registry: 提示词注册表
            prompt_injector: 提示词注入器
        """
        self._prompt_service.configure(prompt_registry, prompt_injector)
        logger.info("构建器服务已配置提示词系统")
    
    async def inject_prompts_to_messages(
        self,
        messages: List[Any],
        prompt_ids: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """注入提示词到消息列表
        
        Args:
            messages: 基础消息列表
            prompt_ids: 提示词ID列表
            context: 上下文变量
            
        Returns:
            包含提示词的消息列表
        """
        return await self._prompt_service.build_messages(
            messages, prompt_ids, None, context or {}
        )
    
    async def resolve_prompt_references(
        self,
        prompt_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """解析提示词引用
        
        Args:
            prompt_content: 包含引用的提示词内容
            context: 上下文变量
            
        Returns:
            解析后的内容
        """
        return await self._prompt_service.process_prompt_content(
            prompt_content, context or {}
        )
    
    def _preprocess_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """预处理配置，应用提示词处理"""
        try:
            import asyncio
            
            # 在同步方法中运行异步逻辑
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._prompt_service.preprocess_workflow_config(config)
                )
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"配置预处理失败，使用原始配置: {e}")
            return config
    
    async def _configure_node_prompts(self, graph, config: Dict[str, Any]):
        """配置节点的提示词系统"""
        try:
            # 使用提示词服务统一配置节点
            await self._prompt_service.configure_workflow_nodes(graph, config)
        except Exception as e:
            logger.warning(f"配置节点提示词系统失败: {e}")
    
    
    def get_prompt_service_info(self) -> Dict[str, Any]:
        """获取提示词服务信息"""
        return self._prompt_service.get_service_info()