"""图工作流基类

提供基于图的工作流统一接口，封装LangGraph图的创建、配置和执行。
"""

from typing import Dict, Any, Optional, List, Union, AsyncIterator, Iterator
from abc import ABC, abstractmethod
import logging
from pathlib import Path

from src.infrastructure.graph.config import GraphConfig
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.function_registry import FunctionRegistry, get_global_function_registry
from src.infrastructure.graph.registry import NodeRegistry, get_global_registry
from infrastructure.config.core.loader import IConfigLoader
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
        container: Optional[Any] = None,
        config_loader: Optional[Any] = None,
        enable_auto_registration: bool = True,
        **kwargs
    ):
        """初始化图工作流
        
        Args:
            config: 配置数据（字典、GraphConfig对象或文件路径）
            function_registry: 函数注册表
            container: 依赖容器
            config_loader: 配置加载器
            enable_auto_registration: 是否启用自动注册
            **kwargs: 其他参数（向后兼容）
        """
        logger.info(f"初始化图工作流: {config}")
        
        # 设置依赖
        self.function_registry = function_registry or get_global_function_registry()
        self.container = container
        self.config_loader = config_loader
        self.enable_auto_registration = enable_auto_registration
        
        # 初始化加载器
        self._loader = UniversalWorkflowLoader(
            config_loader=self.config_loader,
            container=self.container,
            enable_auto_registration=True,
            function_registry=self.function_registry
        )
        
        # 加载配置（延迟实例创建）
        self._config = self._load_config(config)
        self._instance = None  # 延迟实例创建
        
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
            
            # 使用加载器从文件加载配置
            loaded_config = self._loader._load_config_from_file(str(config_path))
            return loaded_config
        else:
            raise GraphWorkflowConfigError(f"不支持的配置类型: {type(config)}")
    
    def _create_workflow_instance(self) -> WorkflowInstance:
        """创建工作流实例
        
        Returns:
            WorkflowInstance: 工作流实例
        """
        try:
            # 使用加载器创建实例
            config_dict = self._config.to_dict()
            return self._loader.load_from_dict(config_dict)
        except Exception as e:
            raise GraphWorkflowConfigError(f"创建工作流实例失败: {e}") from e
    
    def _create_instance(self) -> WorkflowInstance:
        """创建工作流实例（内部方法，供测试使用）
        
        Returns:
            WorkflowInstance: 工作流实例
            
        Raises:
            GraphWorkflowConfigError: 配置错误时抛出
        """
        if self._instance is None:
            # 使用加载器创建实例
            try:
                config_dict = self._config.to_dict()
                self._instance = self._loader.load_from_dict(config_dict)
            except Exception as e:
                raise GraphWorkflowConfigError(f"创建工作流实例失败: {e}") from e
        return self._instance
    
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
        if self._instance is None:
            self._instance = self._create_workflow_instance()
        return self._instance
    
    @property
    def entry_point(self) -> Optional[str]:
        """获取工作流入口点"""
        return self._config.entry_point
    
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
            return self.instance.run(initial_data, run_config)
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
            return await self.instance.run_async(initial_data, run_config)
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
            yield from self.instance.stream(initial_data, run_config)
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
            async for chunk in self.instance.stream_async(initial_data, run_config):
                yield chunk
        except Exception as e:
            raise GraphWorkflowExecutionError(f"工作流异步流式执行失败: {e}") from e
    
    def validate(self) -> List[Dict[str, Any]]:
        """验证工作流配置
        
        Returns:
            List[Dict[str, Any]]: 验证错误列表
        """
        errors = []
        
        # 验证配置
        if hasattr(self._config, 'validate'):
            config_errors = self._config.validate()
            errors.extend(config_errors)
        
        # 验证实例
        if self._instance is None:
            try:
                # 尝试创建实例以获取详细的验证错误
                self._instance = self._create_workflow_instance()
            except GraphWorkflowConfigError as e:
                # 将配置错误添加到错误列表
                errors.append({
                    "type": "config_error", 
                    "message": str(e)
                })
        
        return errors
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """获取工作流可视化数据
        
        Returns:
            Dict[str, Any]: 可视化数据
        """
        return self.instance.get_visualization()
    
    def get_state_schema(self) -> Dict[str, Any]:
        """获取工作流状态模式
        
        Returns:
            Dict[str, Any]: 状态模式定义
        """
        config = self.instance.get_config()
        return {
            "name": config.state_schema.name,
            "fields": {
                name: {
                    "type": field.type,
                    "default": field.default,
                    "reducer": field.reducer,
                    "description": field.description
                }
                for name, field in config.state_schema.fields.items()
            }
        }
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """获取工作流节点列表
        
        Returns:
            List[Dict[str, Any]]: 节点定义列表
        """
        config = self.instance.get_config()
        return [
            {
                "id": node_id,
                "name": node.name,
                "function_name": node.function_name,
                "description": node.description,
                "config": node.config
            }
            for node_id, node in config.nodes.items()
        ]
    
    def get_edges(self) -> List[Dict[str, Any]]:
        """获取工作流边列表
        
        Returns:
            List[Dict[str, Any]]: 边定义列表
        """
        config = self.instance.get_config()
        return [
            {
                "from": edge.from_node,
                "to": edge.to_node,
                "type": edge.type if isinstance(edge.type, str) else edge.type.value,
                "condition": edge.condition,
                "description": edge.description
            }
            for edge in config.edges
        ]
    
    def export_config(self) -> Dict[str, Any]:
        """导出配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self._config.to_dict()
    
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