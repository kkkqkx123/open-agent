"""通用工作流加载器

统一加载和解析工作流配置，管理函数注册表，创建完整的工作流实例。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING, AsyncIterator
from pathlib import Path
import logging
import yaml

from src.infrastructure.graph.config import GraphConfig
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.function_registry import FunctionRegistry, FunctionType, get_global_function_registry
from src.infrastructure.graph.config_validator import WorkflowConfigValidator, ValidationResult
from src.infrastructure.graph.registry import NodeRegistry, get_global_registry
from infrastructure.config.core.loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer
from .state_machine.state_templates import StateTemplateManager, get_global_template_manager

if TYPE_CHECKING:
    from src.domain.state.interfaces import IStateCollaborationManager

logger = logging.getLogger(__name__)


class UniversalLoaderError(Exception):
    """通用加载器异常"""
    pass


class ConfigValidationError(UniversalLoaderError):
    """配置验证异常"""
    pass


class FunctionRegistrationError(UniversalLoaderError):
    """函数注册异常"""
    pass


class WorkflowInstance:
    """工作流实例
    
    封装工作流图和配置，提供简化的执行接口。
    """
    
    def __init__(
        self,
        graph: Any,
        config: GraphConfig,
        loader: 'UniversalWorkflowLoader'
    ):
        """初始化工作流实例
        
        Args:
            graph: 工作流图
            config: 工作流配置
            loader: 加载器实例
        """
        self.graph = graph
        self.config = config
        self.loader = loader
        self._template_manager = get_global_template_manager()
    
    def run(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            
        Returns:
            Dict[str, Any]: 最终状态
        """
        # 创建初始状态
        initial_state = self._create_initial_state(initial_data)
        
        # 合并运行配置
        run_config = config or {}
        
        # 设置递归限制
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = self.config.additional_config.get("recursion_limit", 10)
        
        try:
            # 执行工作流
            logger.info(f"开始执行工作流: {self.config.name}")
            result = self.graph.invoke(initial_state, config=run_config)
            logger.info(f"工作流执行完成: {self.config.name}")
            
            return result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {self.config.name}, 错误: {e}")
            raise UniversalLoaderError(f"工作流执行失败: {e}") from e
    
    async def run_async(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """异步运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            
        Returns:
            Dict[str, Any]: 最终状态
        """
        # 创建初始状态
        initial_state = self._create_initial_state(initial_data)
        
        # 合并运行配置
        run_config = config or {}
        
        # 设置递归限制
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = self.config.additional_config.get("recursion_limit", 10)
        
        try:
            # 异步执行工作流
            logger.info(f"开始异步执行工作流: {self.config.name}")
            
            if hasattr(self.graph, 'ainvoke'):
                result = await self.graph.ainvoke(initial_state, config=run_config)
            else:
                # 如果不支持异步，使用同步方式
                result = self.graph.invoke(initial_state, config=run_config)
            
            logger.info(f"工作流异步执行完成: {self.config.name}")
            return result
            
        except Exception as e:
            logger.error(f"工作流异步执行失败: {self.config.name}, 错误: {e}")
            raise UniversalLoaderError(f"工作流异步执行失败: {e}") from e
    
    def stream(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """流式运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        # 创建初始状态
        initial_state = self._create_initial_state(initial_data)
        
        # 合并运行配置
        run_config = config or {}
        
        try:
            # 流式执行工作流
            logger.info(f"开始流式执行工作流: {self.config.name}")
            
            if hasattr(self.graph, 'stream'):
                for chunk in self.graph.stream(initial_state, config=run_config):
                    yield chunk
            else:
                # 如果不支持流式，直接返回最终结果
                result = self.graph.invoke(initial_state, config=run_config)
                yield result
            
            logger.info(f"工作流流式执行完成: {self.config.name}")
            
        except Exception as e:
            logger.error(f"工作流流式执行失败: {self.config.name}, 错误: {e}")
            raise UniversalLoaderError(f"工作流流式执行失败: {e}") from e
    
    async def stream_async(
        self, 
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式运行工作流
        
        Args:
            initial_data: 初始数据
            config: 运行配置
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        # 创建初始状态
        initial_state = self._create_initial_state(initial_data)
        
        # 合并运行配置
        run_config = config or {}
        
        try:
            # 异步流式执行工作流
            logger.info(f"开始异步流式执行工作流: {self.config.name}")
            
            if hasattr(self.graph, 'astream'):
                async for chunk in self.graph.astream(initial_state, config=run_config):
                    yield chunk
            else:
                # 如果不支持异步流式，使用同步流式
                for chunk in self.stream(initial_data, config):
                    yield chunk
            
            logger.info(f"工作流异步流式执行完成: {self.config.name}")
            
        except Exception as e:
            logger.error(f"工作流异步流式执行失败: {self.config.name}, 错误: {e}")
            raise UniversalLoaderError(f"工作流异步流式执行失败: {e}") from e
    
    def get_config(self) -> GraphConfig:
        """获取工作流配置
        
        Returns:
            GraphConfig: 工作流配置
        """
        return self.config
    
    def get_visualization(self) -> Dict[str, Any]:
        """获取工作流可视化数据
        
        Returns:
            Dict[str, Any]: 可视化数据
        """
        return {
            "name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "nodes": [
                {
                    "id": node_id,
                    "type": node.function_name,
                    "config": node.config,
                    "description": node.description
                }
                for node_id, node in self.config.nodes.items()
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "type": edge.type.value,
                    "condition": edge.condition,
                    "description": edge.description
                }
                for edge in self.config.edges
            ],
            "entry_point": self.config.entry_point
        }
    
    def _create_initial_state(self, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建初始状态
        
        Args:
            initial_data: 初始数据
            
        Returns:
            Dict[str, Any]: 初始状态
        """
        return self._template_manager.create_state_from_config(self.config, initial_data)


class UniversalWorkflowLoader:
    """通用工作流加载器
    
    统一加载和解析工作流配置，管理函数注册表，创建完整的工作流实例。
    """
    
    def __init__(
        self,
        config_loader: Optional[IConfigLoader] = None,
        container: Optional[IDependencyContainer] = None,
        enable_auto_registration: bool = True,
        function_registry: Optional[FunctionRegistry] = None
    ):
        """初始化通用工作流加载器
        
        Args:
            config_loader: 配置加载器
            container: 依赖注入容器
            enable_auto_registration: 是否启用自动函数注册
            function_registry: 函数注册表，如果为None则创建新的
        """
        self.config_loader = config_loader
        self.container = container
        self.enable_auto_registration = enable_auto_registration
        
        # 初始化组件
        self.function_registry = function_registry or FunctionRegistry(enable_auto_discovery=enable_auto_registration)
        self.node_registry = get_global_registry()
        self.template_manager = get_global_template_manager()
        self.config_validator = WorkflowConfigValidator(self.function_registry)
        
        # 创建统一图构建器
        self.graph_builder = GraphBuilder(
            node_registry=self.node_registry,
            function_registry=self.function_registry,
            enable_function_fallback=True,
            enable_iteration_management=True
        )
        
        # 缓存
        self._config_cache: Dict[str, GraphConfig] = {}
        self._graph_cache: Dict[str, Any] = {}
        
        logger.debug("通用工作流加载器初始化完成")
    
    def load_from_file(
        self, 
        config_path: str, 
        initial_state_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowInstance:
        """从文件加载工作流
        
        Args:
            config_path: 配置文件路径
            initial_state_data: 初始状态数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowInstance: 工作流实例
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ConfigValidationError: 配置验证失败
        """
        if not Path(config_path).exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        # 加载配置
        config = self._load_config_from_file(config_path)
        
        # 创建工作流实例
        return self._create_workflow_instance(config, initial_state_data, **kwargs)
    
    def load_from_dict(
        self, 
        config_dict: Dict[str, Any], 
        initial_state_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowInstance:
        """从字典加载工作流
        
        Args:
            config_dict: 配置字典
            initial_state_data: 初始状态数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowInstance: 工作流实例
        """
        # 解析配置
        config = GraphConfig.from_dict(config_dict)
        
        # 创建工作流实例
        return self._create_workflow_instance(config, initial_state_data, **kwargs)
    
    def register_function(
        self, 
        name: str, 
        function: Any, 
        function_type: FunctionType
    ) -> None:
        """注册函数
        
        Args:
            name: 函数名称
            function: 函数对象
            function_type: 函数类型
        """
        try:
            self.function_registry.register(name, function, function_type)
            logger.debug(f"注册函数: {name} ({function_type.value})")
        except Exception as e:
            raise FunctionRegistrationError(f"注册函数失败: {e}") from e
    
    def register_functions_from_module(self, module_path: str) -> Dict[str, List[str]]:
        """从模块注册函数
        
        Args:
            module_path: 模块路径
            
        Returns:
            Dict[str, List[str]]: 注册的函数统计信息
        """
        try:
            return self.function_registry.discover_functions([module_path])
        except Exception as e:
            raise FunctionRegistrationError(f"从模块注册函数失败: {e}") from e
    
    def validate_config(self, config: Union[str, Dict[str, Any], GraphConfig]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置路径或配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        return self.config_validator.validate_config(config)
    
    def list_registered_functions(self, function_type: Optional[FunctionType] = None) -> Dict[str, List[str]]:
        """列出已注册的函数
        
        Args:
            function_type: 函数类型过滤器
            
        Returns:
            Dict[str, List[str]]: 函数分类列表
        """
        return self.function_registry.list_functions(function_type)
    
    def get_function_info(self, name: str, function_type: FunctionType) -> Optional[Dict[str, Any]]:
        """获取函数信息
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息
        """
        return self.function_registry.get_function_info(name, function_type)
    
    def get_function_statistics(self) -> Dict[str, Any]:
        """获取函数统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.graph_builder.get_function_statistics()
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._config_cache.clear()
        self._graph_cache.clear()
        logger.debug("缓存已清除")
    
    def _load_config_from_file(self, config_path: str) -> GraphConfig:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            GraphConfig: 图配置
        """
        # 检查缓存
        if config_path in self._config_cache:
            logger.debug(f"从缓存加载配置: {config_path}")
            return self._config_cache[config_path]
        
        try:
            if self.config_loader:
                # 委托给核心加载器
                config_data = self.config_loader.load(config_path)
            else:
                # 直接读取文件
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            
            config = GraphConfig.from_dict(config_data)
            
            # 处理函数注册配置
            self._process_function_registrations(config_data)
            
            # 缓存配置
            self._config_cache[config_path] = config
            
            return config
            
        except Exception as e:
            raise ConfigValidationError(f"加载配置文件失败: {e}") from e
    
    def _process_function_registrations(self, config_data: Dict[str, Any]) -> None:
        """处理函数注册配置
        
        Args:
            config_data: 配置数据
        """
        function_registrations = config_data.get("function_registrations", {})
        
        if not function_registrations:
            return
        
        # 注册节点函数
        node_functions = function_registrations.get("nodes", {})
        for name, module_path in node_functions.items():
            try:
                self._register_function_from_module(name, module_path, FunctionType.NODE_FUNCTION)
            except Exception as e:
                logger.warning(f"注册节点函数失败: {name} -> {module_path}, 错误: {e}")
        
        # 注册条件函数
        condition_functions = function_registrations.get("conditions", {})
        for name, module_path in condition_functions.items():
            try:
                self._register_function_from_module(name, module_path, FunctionType.CONDITION_FUNCTION)
            except Exception as e:
                logger.warning(f"注册条件函数失败: {name} -> {module_path}, 错误: {e}")
        
        # 处理自动发现配置
        auto_discovery = function_registrations.get("auto_discovery", {})
        if auto_discovery.get("enabled", False):
            module_paths = auto_discovery.get("module_paths", [])
            if module_paths:
                try:
                    discovered = self.function_registry.discover_functions(module_paths)
                    logger.info(f"自动发现函数: 节点函数 {len(discovered['nodes'])} 个, 条件函数 {len(discovered['conditions'])} 个")
                except Exception as e:
                    logger.warning(f"自动发现函数失败: {e}")
    
    def _register_function_from_module(self, name: str, module_path: str, function_type: FunctionType) -> None:
        """从模块注册函数
        
        Args:
            name: 函数名称
            module_path: 模块路径
            function_type: 函数类型
        """
        try:
            import importlib
            module = importlib.import_module(module_path)
            function = getattr(module, name)
            self.register_function(name, function, function_type)
        except Exception as e:
            raise FunctionRegistrationError(f"从模块注册函数失败: {e}") from e
    
    def _create_workflow_instance(
        self, 
        config: GraphConfig, 
        initial_state_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowInstance:
        """创建工作流实例
        
        Args:
            config: 图配置
            initial_state_data: 初始状态数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowInstance: 工作流实例
        """
        # 验证配置
        validation_result = self.validate_config(config)
        if not validation_result.is_valid:
            error_msg = f"配置验证失败: {'; '.join(validation_result.errors)}"
            raise ConfigValidationError(error_msg)
        
        # 检查缓存
        cache_key = str(hash(str(config.to_dict())))
        if cache_key in self._graph_cache:
            logger.debug(f"从缓存获取图: {config.name}")
            graph = self._graph_cache[cache_key]
        else:
            # 构建图
            try:
                state_manager = kwargs.get("state_manager")
                graph = self.graph_builder.build_graph_with_validation(config, state_manager)
                
                # 缓存图
                self._graph_cache[cache_key] = graph
                
            except Exception as e:
                raise ConfigValidationError(f"构建图失败: {e}") from e
        
        # 创建工作流实例
        return WorkflowInstance(graph, config, self)