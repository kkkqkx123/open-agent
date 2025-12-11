"""工作流构建服务实现，遵循新架构。

此模块提供工作流构建服务，处理从配置创建工作流和验证功能。
"""

from typing import Dict, Any, List, TYPE_CHECKING, Optional
from src.interfaces.dependency_injection import get_logger
import asyncio

if TYPE_CHECKING:
    from src.interfaces.workflow.core import IWorkflow
    from src.core.workflow.graph_entities import GraphConfig

from src.interfaces.workflow.services import IWorkflowBuilderService
from src.services.workflow.graph_cache import GraphCache, create_graph_cache, calculate_config_hash

logger = get_logger(__name__)


class WorkflowBuilderService(IWorkflowBuilderService):
    """工作流构建服务实现。

    此类提供从配置构建工作流的方法，
    验证配置，并管理工作流构建过程。
    """

    def __init__(self,
                 node_registry=None,
                 function_registry=None,
                 graph_engine=None,
                 graph_cache=None):
        """初始化工作流构建服务。
        
        Args:
            node_registry: 节点注册表（可选）
            function_registry: 函数注册表（可选）
            graph_engine: 图引擎类（可选）
            graph_cache: 图缓存实例（可选）
        """
        # 延迟导入避免循环依赖
        self._validator = None
        
        # 保存函数注册表引用
        self._function_registry = function_registry
        
        # 初始化图引擎类
        if graph_engine:
            self._graph_engine_class = graph_engine
        else:
            # 使用基础设施层的图引擎
            from src.infrastructure.graph.engine.state_graph import StateGraphEngine
            self._graph_engine_class = StateGraphEngine
        
        # 初始化图缓存
        if graph_cache:
            self._graph_cache = graph_cache
        else:
            self._graph_cache = create_graph_cache(
                max_size=100,
                ttl_seconds=3600,
                eviction_policy="lru"
            )
        
        # 初始化提示词服务
        self._prompt_service = self._init_prompt_service()
        
        logger.info("工作流构建服务初始化完成（集成StateGraphEngine和图缓存）")
    
    def _init_prompt_service(self):
        """初始化提示词服务"""
        try:
            # 在同步方法中运行异步创建
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from src.services.prompts import create_prompt_system
                prompt_system = loop.run_until_complete(create_prompt_system())
                return prompt_system["injector"]  # 使用注入器作为提示词服务
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"创建提示词系统失败，使用 None: {e}")
            return None

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

            # 检查缓存
            config_hash = calculate_config_hash(config)
            cached_graph = self._graph_cache.get_graph(config_hash)
            
            if cached_graph:
                logger.info(f"使用缓存图: {workflow_id}")
                graph = cached_graph
            else:
                # 使用基础设施层图引擎创建图
                from src.core.workflow.graph_entities import GraphConfig
                graph_config = GraphConfig.from_dict(config)
                
                # 创建状态模式
                state_schema_class = graph_config.get_state_class()
                
                # 创建图引擎实例
                graph = self._graph_engine_class(state_schema_class)
                
                # 添加节点
                for node_name, node_config in graph_config.nodes.items():
                    # 从函数注册表获取函数
                    if self._function_registry and node_config.function_name:
                        node_func = self._function_registry.get(node_config.function_name)
                        if node_func:
                            graph.add_node(node_name, node_func)
                
                # 添加边
                for edge in graph_config.edges:
                    if edge.type.value == "simple":
                        graph.add_edge(edge.from_node, edge.to_node)
                    elif edge.type.value == "conditional" and edge.condition:
                        # 对于条件边，需要从函数注册表获取条件函数
                        if self._function_registry and edge.condition:
                            condition_func = self._function_registry.get(edge.condition)
                            if condition_func:
                                graph.add_conditional_edges(edge.from_node, condition_func, edge.path_map)
                
                # 设置入口点
                if graph_config.entry_point:
                    graph.set_entry_point(graph_config.entry_point)
                
                # 缓存图
                self._graph_cache.cache_graph(config_hash, graph, config)
                logger.info(f"图已缓存: {workflow_id}")

            # 创建工作流实例
            workflow = self._create_workflow_instance(workflow_id, name)
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
            from src.core.workflow.graph_entities import GraphConfig
            
            # 使用核心层的配置验证
            config_obj = GraphConfig.from_dict(config)
            
            # 延迟导入验证器避免循环依赖
            if self._validator is None:
                try:
                    from src.infrastructure.graph.builders.validation_rules import get_validation_registry
                    self._validator = get_validation_registry()
                except ImportError:
                    # 如果验证规则模块不存在，使用None
                    self._validator = None
            
            # 使用新的验证规则系统进行基础验证
            validation_errors = []
            
            # 基础配置验证
            if not config_obj.name or not config_obj.name.strip():
                validation_errors.append("工作流名称不能为空")
            
            if not config_obj.nodes:
                validation_errors.append("工作流必须定义至少一个节点")
            
            if not config_obj.state_schema:
                validation_errors.append("工作流必须定义状态模式")
            
            # 过滤掉内置函数的错误
            builtin_functions = {"start_node", "end_node", "passthrough_node"}
            filtered_errors = []
            for error in validation_errors:
                # 检查是否是内置函数不存在的错误
                is_builtin_function_error = False
                for builtin_func in builtin_functions:
                    if f"函数 '{builtin_func}' 不存在" in error:
                        is_builtin_function_error = True
                        break
                
                if not is_builtin_function_error:
                    filtered_errors.append(error)
            
            if filtered_errors:
                logger.warning(f"配置验证失败: {filtered_errors}")
            
            # 提示词配置验证应该在 prompt 模块中实现，这里不再重复验证
            
            return filtered_errors
            
        except Exception as e:
            logger.error(f"配置验证过程中发生异常: {e}")
            return [f"配置验证异常: {e}"]
    

    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式。

        Returns:
            配置模式
        """
        try:
            # 返回简化的配置模式
            schema = {
                "required_fields": {
                    "name": "工作流名称（必需）",
                    "nodes": "节点定义（必需）",
                    "state_schema": "状态模式（必需）"
                },
                "optional_fields": {
                    "description": "工作流描述",
                    "version": "版本号",
                    "edges": "边定义",
                    "entry_point": "入口点",
                    "checkpointer": "检查点配置"
                }
            }
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
        from src.core.workflow.workflow import Workflow
        from src.core.workflow.graph_entities import GraphConfig
        
        # 创建基础配置
        config = GraphConfig(
            name=workflow_id,
            nodes={},
            edges=[],
            entry_point="__start__"
        )
        
        return Workflow(config)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return self._graph_cache.get_cache_stats()
    
    def clear_cache(self) -> None:
        """清除图缓存"""
        self._graph_cache.clear()
        logger.info("图缓存已清除")
    
    def invalidate_cache_by_pattern(self, pattern: str) -> int:
        """按模式失效缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            int: 失效的缓存条目数量
        """
        count = self._graph_cache.invalidate_by_pattern(pattern)
        logger.info(f"按模式 {pattern} 失效了 {count} 个缓存条目")
        return count
    
    def get_graph_engine(self):
        """获取图引擎类
        
        Returns:
            图引擎类
        """
        return self._graph_engine_class
    