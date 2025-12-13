"""工作流构建器 - 专门负责图构建

只负责将配置编译为可执行的图，不包含加载、验证等逻辑。
"""

from typing import Any, List, Optional, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.core.workflow.workflow import Workflow
from src.interfaces.workflow.element_builder import BuildContext
from src.infrastructure.graph.builders.element_builder_factory import get_builder_factory
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.workflow.builders import IWorkflowBuilder

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class WorkflowBuilder(IWorkflowBuilder):
    """工作流构建器实现 - 专门负责图构建
    
    将配置编译为可执行的图，不包含其他业务逻辑。
    """
    
    def __init__(self,
                 function_registry: Optional[Any] = None,
                 builder_factory: Optional[Any] = None):
        """初始化工作流构建器
        
        Args:
            function_registry: 函数注册表
            builder_factory: 构建器工厂
        """
        # 使用构建器工厂
        self.builder_factory = builder_factory or get_builder_factory()
        
        # 创建构建上下文
        if function_registry:
            self.build_context = BuildContext(
                graph_config=None,
                function_resolver=function_registry,
                logger=logger
            )
        else:
            # 如果没有提供函数注册表，创建空的上下文
            logger.warning("未提供函数注册表，使用空上下文")
            self.build_context = BuildContext(
                graph_config=None,
                function_resolver=None,
                logger=logger
            )
        
        logger.debug("工作流构建器初始化完成")
    
    def build_graph(self, workflow: Workflow) -> Any:
        """构建工作流图
        
        Args:
            workflow: 工作流实例
            
        Returns:
            Any: 编译后的图
            
        Raises:
            WorkflowConfigError: 构建失败
        """
        try:
            config = workflow.config
            
            # 更新构建上下文
            self.build_context.graph_config = config
            
            # 使用构建器工厂创建节点和边构建器
            node_builder = self.builder_factory.create_node_builder("node", self.build_context)
            edge_builder = self.builder_factory.create_edge_builder("edge", self.build_context)
            
            # 创建StateGraphEngine
            from src.infrastructure.graph.engine.state_graph import StateGraphEngine
            from typing import cast, Any
            builder = StateGraphEngine(cast(Any, config.get_state_class()))
            
            # 添加节点
            for node_name, node_config in config.nodes.items():
                try:
                    node_function = node_builder.build_element(node_config, self.build_context)
                    if node_function:
                        node_builder.add_to_graph(node_function, builder, node_config, self.build_context)
                except Exception as e:
                    logger.error(f"添加节点失败: {node_name}, 错误: {e}")
                    from src.interfaces.workflow.exceptions import WorkflowConfigError
                    raise WorkflowConfigError(f"添加节点失败: {node_name}") from e
            
            # 添加边
            for edge in config.edges:
                try:
                    edge_element = edge_builder.build_element(edge, self.build_context)
                    edge_builder.add_to_graph(edge_element, builder, edge, self.build_context)
                except Exception as e:
                    logger.error(f"添加边失败: {edge}, 错误: {e}")
                    from src.interfaces.workflow.exceptions import WorkflowConfigError
                    raise WorkflowConfigError(f"添加边失败: {edge}") from e
            
            # 设置入口点
            if config.entry_point:
                from src.infrastructure.graph.types import START
                builder.add_edge(START, config.entry_point)
            
            # 编译图
            compiled_graph = builder.compile({})
            
            logger.info(f"成功构建工作流图: {config.name}")
            return compiled_graph
            
        except Exception as e:
           logger.error(f"构建工作流图失败: {workflow.name}, 错误: {e}")
           from src.interfaces.workflow.exceptions import WorkflowConfigError
           raise WorkflowConfigError(f"构建图失败: {e}") from e
    
    def build_and_set_graph(self, workflow: IWorkflow) -> None:
        """构建图并设置到工作流实例
        
        Args:
            workflow: 工作流实例
        """
        compiled_graph = self.build_graph(workflow)  # type: ignore
        workflow.set_graph(compiled_graph)
    
    def validate_build_requirements(self, workflow: Workflow) -> List[str]:
        """验证构建要求
        
        Args:
            workflow: 工作流实例
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        config = workflow.config
        
        # 检查基本要求
        if not config.nodes:
            errors.append("工作流必须包含至少一个节点")
        
        if not config.edges:
            errors.append("工作流必须包含至少一个边")
        
        if not config.entry_point:
            errors.append("工作流必须指定入口点")
        
        # 检查节点配置
        for node_name, node_config in config.nodes.items():
            if not hasattr(node_config, 'type') and not hasattr(node_config, 'function_name'):
                errors.append(f"节点 '{node_name}' 缺少类型或函数定义")
        
        # 检查边配置
        for edge in config.edges:
            if not hasattr(edge, 'from_node') or not hasattr(edge, 'to_node'):
                errors.append(f"边缺少起始节点或目标节点: {edge}")
            
            if not hasattr(edge, 'type'):
                errors.append(f"边缺少类型定义: {edge}")
        
        return errors
    
    def create_workflow(self, config: dict[str, Any]) -> IWorkflow:
        """创建工作流
        
        Args:
            config: 工作流配置字典
            
        Returns:
            IWorkflow: 工作流实例
        """
        from src.core.workflow.graph_entities import Graph
        
        # 创建图实体
        graph = Graph(
            graph_id=config.get('workflow_id', 'default'),
            name=config.get('name', 'Default Workflow'),
            description=config.get('description'),
            version=config.get('version', '1.0'),
            entry_point=config.get('entry_point')
        )
        
        # 创建工作流实例
        workflow = Workflow(graph=graph, config=config)
        
        logger.info(f"创建工作流: {workflow.name}")
        return workflow
    
    def validate_config(self, config: dict[str, Any]) -> List[str]:
        """验证工作流配置
        
        Args:
            config: 工作流配置字典
            
        Returns:
            List[str]: 验证错误列表 (空列表表示有效)
        """
        errors = []
        
        # 检查必要字段
        if not config.get('name'):
            errors.append("工作流名称是必需的")
        
        if not config.get('workflow_id'):
            errors.append("工作流ID是必需的")
        
        # 检查节点配置
        nodes = config.get('nodes', {})
        if not nodes:
            errors.append("工作流必须包含至少一个节点")
        
        # 检查边配置
        edges = config.get('edges', [])
        if not edges:
            errors.append("工作流必须包含至少一个边")
        
        # 检查入口点
        if not config.get('entry_point'):
            errors.append("工作流必须指定入口点")
        
        logger.debug(f"配置验证完成，错误数: {len(errors)}")
        return errors