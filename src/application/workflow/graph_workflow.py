"""图工作流基类

提供基于图的工作流统一接口，封装LangGraph图的创建、配置和执行。
"""

from typing import Dict, Any, Optional, List, Union, AsyncIterator, Iterator
from abc import ABC, abstractmethod
import logging
from pathlib import Path

from src.infrastructure.graph.config import GraphConfig
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.enhanced_builder import EnhancedGraphBuilder
from src.infrastructure.graph.function_registry import FunctionRegistry, get_global_function_registry
from src.infrastructure.graph.registry import NodeRegistry, get_global_registry
from src.infrastructure.config_loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer
from .universal_loader import UniversalWorkflowLoader, WorkflowInstance

logger = logging.getLogger(__name__)


class GraphWorkflowError(Exception):
    """图工作流异常基类"""
    pass


class GraphWorkflowConfigError(GraphWorkflowError):
    """图工作流配置异常"""
    pass


class GraphWorkflowExecutionError(GraphWorkflowError):
    """图工作流执行异常"""
    pass


class GraphWorkflow(ABC):
    """图工作流基类
    
    提供基于LangGraph的工作流统一接口，支持配置驱动的图构建和执行。
    该类封装了图工作流的核心功能，提供简洁的API供业务代码使用。
    """
    
    def __init__(
        self,
        config: Union[GraphConfig, Dict[str, Any], str, Path],
        function_registry: Optional[FunctionRegistry] = None,
        node_registry: Optional[NodeRegistry] = None,
        config_loader: Optional[IConfigLoader] = None,
        container: Optional[IDependencyContainer] = None,
        use_enhanced_builder: bool = True
    ):
        """初始化图工作流
        
        Args:
            config: 工作流配置，可以是GraphConfig对象、配置字典、配置文件路径
            function_registry: 函数注册表
            node_registry: 节点注册表
            config_loader: 配置加载器
            container: 依赖注入容器
            use_enhanced_builder: 是否使用增强的图构建器
        """
        self.function_registry = function_registry or get_global_function_registry()
        self.node_registry = node_registry or get_global_registry()
        self.config_loader = config_loader
        self.container = container
        self.use_enhanced_builder = use_enhanced_builder
        
        # 初始化加载器
        self._loader = UniversalWorkflowLoader(
            function_registry=self.function_registry,
            node_registry=self.node_registry,
            config_loader=self.config_loader,
            container=self.container
        )
        
        # 加载配置和工作流实例
        self._config = self._load_config(config)
        self._instance = self._create_workflow_instance()
        
        logger.info(f"图工作流初始化完成: {self._config.name}")
    
    def _load_config(self, config: Union[GraphConfig, Dict[str, Any], str, Path]) -> GraphConfig:
        """加载配置
        
        Args:
            config: 配置数据
            
        Returns:
            GraphConfig: 图配置对象
        """
        if isinstance(config, GraphConfig):
            return config
        elif isinstance(config, dict):
            return GraphConfig.from_dict(config)
        elif isinstance(config, (str, Path)):
            # 从文件加载
            config_path = Path(config)
            if not config_path.exists():
                raise GraphWorkflowConfigError(f"配置文件不存在: {config_path}")
            
            # 使用加载器从文件加载
            loaded_config = self._loader.load_config_from_file(str(config_path))
            if isinstance(loaded_config, dict):
                return GraphConfig.from_dict(loaded_config)
            elif isinstance(loaded_config, GraphConfig):
                return loaded_config
            else:
                raise GraphWorkflowConfigError(f"不支持的配置格式: {type(loaded_config)}")
        else:
            raise GraphWorkflowConfigError(f"不支持的配置类型: {type(config)}")
    
    def _create_workflow_instance(self) -> WorkflowInstance:
        """创建工作流实例
        
        Returns:
            WorkflowInstance: 工作流实例
        """
        try:
            # 使用加载器创建实例
            return self._loader.load_from_dict(self._config.to_dict() if hasattr(self._config, 'to_dict') else self._config)
        except Exception as e:
            raise GraphWorkflowConfigError(f"创建工作流实例失败: {e}") from e
    
    @property
    def name(self) -> str:
        """获取工作流名称"""
        return self._config.name
    
    @property
    def description(self) -> str:
        """获取工作流描述"""
        return self._config.description
    
    @property
    def version(self) -> str:
        """获取工作流版本"""
        return self._config.version
    
    @property
    def config(self) -> GraphConfig:
        """获取工作流配置"""
        return self._config
    
    @property
    def instance(self) -> WorkflowInstance:
        """获取工作流实例"""
        return self._instance
    
    def run(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            **kwargs: 其他参数（向后兼容）
            
        Returns:
            Dict[str, Any]: 最终状态
            
        Raises:
            GraphWorkflowExecutionError: 执行失败时抛出
        """
        try:
            # 合并配置
            run_config = {**(config or {}), **kwargs}
            return self._instance.run(initial_data, run_config)
        except Exception as e:
            raise GraphWorkflowExecutionError(f"工作流执行失败: {e}") from e
    
    async def run_async(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            **kwargs: 其他参数（向后兼容）
            
        Returns:
            Dict[str, Any]: 最终状态
            
        Raises:
            GraphWorkflowExecutionError: 执行失败时抛出
        """
        try:
            # 合并配置
            run_config = {**(config or {}), **kwargs}
            return await self._instance.run_async(initial_data, run_config)
        except Exception as e:
            raise GraphWorkflowExecutionError(f"工作流异步执行失败: {e}") from e
    
    def stream(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """流式运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            **kwargs: 其他参数（向后兼容）
            
        Yields:
            Dict[str, Any]: 中间状态
            
        Raises:
            GraphWorkflowExecutionError: 执行失败时抛出
        """
        try:
            # 合并配置
            run_config = {**(config or {}), **kwargs}
            yield from self._instance.stream(initial_data, run_config)
        except Exception as e:
            raise GraphWorkflowExecutionError(f"工作流流式执行失败: {e}") from e
    
    async def stream_async(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            **kwargs: 其他参数（向后兼容）
            
        Yields:
            Dict[str, Any]: 中间状态
            
        Raises:
            GraphWorkflowExecutionError: 执行失败时抛出
        """
        try:
            # 合并配置
            run_config = {**(config or {}), **kwargs}
            async for chunk in self._instance.stream_async(initial_data, run_config):
                yield chunk
        except Exception as e:
            raise GraphWorkflowExecutionError(f"工作流异步流式执行失败: {e}") from e
    
    def validate(self) -> List[str]:
        """验证工作流配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证配置
        if hasattr(self._config, 'validate'):
            config_errors = self._config.validate()
            errors.extend(config_errors)
        
        # 验证实例
        if not self._instance:
            errors.append("工作流实例未创建")
        
        return errors
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """获取可视化数据
        
        Returns:
            Dict[str, Any]: 可视化数据
        """
        return self._instance.get_visualization()
    
    def get_state_schema(self) -> Dict[str, Any]:
        """获取状态模式
        
        Returns:
            Dict[str, Any]: 状态模式定义
        """
        if hasattr(self._config, 'state_schema'):
            schema = self._config.state_schema
            return {
                "name": schema.name,
                "fields": {
                    field_name: {
                        "type": field_config.type,
                        "default": field_config.default,
                        "description": field_config.description
                    }
                    for field_name, field_config in schema.fields.items()
                }
            }
        return {}
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """获取节点列表
        
        Returns:
            List[Dict[str, Any]]: 节点信息列表
        """
        if hasattr(self._config, 'nodes'):
            return [
                {
                    "name": node.name,
                    "function_name": node.function_name,
                    "description": node.description,
                    "config": node.config
                }
                for node in self._config.nodes.values()
            ]
        return []
    
    def get_edges(self) -> List[Dict[str, Any]]:
        """获取边列表
        
        Returns:
            List[Dict[str, Any]]: 边信息列表
        """
        if hasattr(self._config, 'edges'):
            return [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "type": edge.type.value,
                    "condition": edge.condition,
                    "description": edge.description
                }
                for edge in self._config.edges
            ]
        return []
    
    def export_config(self) -> Dict[str, Any]:
        """导出配置
        
        Returns:
            Dict[str, Any]: 配置数据
        """
        if hasattr(self._config, 'to_dict'):
            return self._config.to_dict()
        else:
            # 手动构建配置字典
            return {
                "name": self._config.name,
                "description": self._config.description,
                "version": self._config.version,
                "entry_point": getattr(self._config, 'entry_point', None),
                "nodes": self.get_nodes(),
                "edges": self.get_edges(),
                "state_schema": self.get_state_schema()
            }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"GraphWorkflow(name='{self.name}', version='{self.version}')"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"GraphWorkflow(name='{self.name}', description='{self.description}', version='{self.version}')"


class SimpleGraphWorkflow(GraphWorkflow):
    """简单图工作流 - 快速创建和使用"""
    
    def __init__(
        self,
        name: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        state_schema: Optional[Dict[str, Any]] = None,
        description: str = "",
        version: str = "1.0",
        entry_point: Optional[str] = None,
        **kwargs
    ):
        """初始化简单图工作流
        
        Args:
            name: 工作流名称
            nodes: 节点列表
            edges: 边列表
            state_schema: 状态模式
            description: 描述
            version: 版本
            entry_point: 入口点
            **kwargs: 其他参数
        """
        # 构建配置
        config = {
            "name": name,
            "description": description,
            "version": version,
            "entry_point": entry_point,
            "nodes": {node["name"]: node for node in nodes},
            "edges": edges,
            "state_schema": state_schema or {
                "name": "WorkflowState",
                "fields": {
                    "messages": {
                        "type": "List[dict]",
                        "default": []
                    }
                }
            }
        }
        
        super().__init__(config, **kwargs)