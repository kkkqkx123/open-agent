"""增强图构建器

扩展现有的图构建器，集成函数注册表，支持动态函数解析。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING
import logging

from .builder import GraphBuilder
from .config import NodeConfig, EdgeConfig
from .registry import NodeRegistry
from .function_registry import FunctionRegistry, FunctionType, get_global_function_registry
from .state import WorkflowState

if TYPE_CHECKING:
    from src.domain.state.interfaces import IStateCollaborationManager

logger = logging.getLogger(__name__)


class EnhancedGraphBuilder(GraphBuilder):
    """增强图构建器
    
    扩展现有的 GraphBuilder，集成函数注册表，支持动态函数解析。
    优先级：函数注册表 -> 节点注册表 -> 内置函数 -> 父类方法
    """
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistry] = None,
        enable_function_fallback: bool = True
    ):
        """初始化增强图构建器
        
        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退机制
        """
        super().__init__(node_registry)
        self.function_registry = function_registry or get_global_function_registry()
        self.enable_function_fallback = enable_function_fallback
        
        logger.debug(f"增强图构建器初始化完成，函数回退: {enable_function_fallback}")
    
    def _get_node_function(self, node_config: NodeConfig, state_manager: Optional["IStateCollaborationManager"] = None) -> Optional[Callable]:
        """获取节点函数（重写父类方法）
        
        优先级：函数注册表 -> 节点注册表 -> 内置函数 -> 父类方法
        
        Args:
            node_config: 节点配置
            state_manager: 状态管理器
            
        Returns:
            Optional[Callable]: 节点函数
        """
        function_name = node_config.function_name
        
        # 1. 优先从函数注册表获取
        if self.function_registry:
            node_function = self.function_registry.get_node_function(function_name)
            if node_function:
                logger.debug(f"从函数注册表获取节点函数: {function_name}")
                return self._wrap_node_function(node_function, state_manager)
        
        # 2. 如果启用回退，尝试父类方法
        if self.enable_function_fallback:
            parent_function = super()._get_node_function(node_config, state_manager)
            if parent_function:
                logger.debug(f"从父类方法获取节点函数: {function_name}")
                return parent_function
        
        # 3. 尝试从内置函数获取
        from .builtin_functions import get_builtin_node_function
        builtin_function = get_builtin_node_function(function_name)
        if builtin_function:
            logger.debug(f"从内置函数获取节点函数: {function_name}")
            return self._wrap_node_function(builtin_function, state_manager)
        
        # 4. 尝试从节点注册表获取
        if self.node_registry:
            try:
                node_class = self.node_registry.get_node_class(function_name)
                if node_class:
                    node_instance = node_class()
                    logger.debug(f"从节点注册表获取节点函数: {function_name}")
                    return self._wrap_node_function(node_instance.execute, state_manager)
            except ValueError:
                # 节点类型不存在，继续尝试其他方法
                pass
        
        logger.warning(f"无法找到节点函数: {function_name}")
        return None
    
    def _get_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取条件函数（重写父类方法）
        
        优先级：函数注册表 -> 内置条件 -> 父类方法
        
        Args:
            condition_name: 条件函数名称
            
        Returns:
            Optional[Callable]: 条件函数
        """
        # 1. 优先从函数注册表获取
        if self.function_registry:
            condition_function = self.function_registry.get_condition_function(condition_name)
            if condition_function:
                logger.debug(f"从函数注册表获取条件函数: {condition_name}")
                return condition_function
        
        # 2. 如果启用回退，尝试父类方法
        if self.enable_function_fallback:
            parent_function = super()._get_condition_function(condition_name)
            if parent_function:
                logger.debug(f"从父类方法获取条件函数: {condition_name}")
                return parent_function
        
        # 3. 尝试从内置函数获取
        from .builtin_functions import get_builtin_condition_function
        builtin_function = get_builtin_condition_function(condition_name)
        if builtin_function:
            logger.debug(f"从内置函数获取条件函数: {condition_name}")
            return builtin_function
        
        logger.warning(f"无法找到条件函数: {condition_name}")
        return None
    
    def _wrap_node_function(self, function: Callable, state_manager: Optional["IStateCollaborationManager"] = None) -> Callable:
        """包装节点函数以支持状态管理
        
        Args:
            function: 原始节点函数
            state_manager: 状态管理器
            
        Returns:
            Callable: 包装后的函数
        """
        if state_manager is None:
            # 如果没有状态管理器，直接返回原函数
            return function
        
        # 如果有状态管理器，使用增强的执行器包装
        from .builder import EnhancedNodeWithAdapterExecutor
        from .registry import BaseNode
        
        # 检查函数是否是节点类的execute方法
        if hasattr(function, '__self__') and hasattr(function, '__func__') and isinstance(getattr(function, '__self__', None), BaseNode):
            node_instance = getattr(function, '__self__')
            adapter_wrapper = EnhancedNodeWithAdapterExecutor(node_instance, state_manager)
            return adapter_wrapper.execute
        
        # 对于普通函数，创建一个简单的包装器
        def wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
            """包装的节点函数"""
            try:
                # 使用协作适配器执行
                from .adapters.collaboration_adapter import CollaborationStateAdapter
                collaboration_adapter = CollaborationStateAdapter(state_manager)
                
                def node_executor(domain_state: Any) -> Any:
                    """节点执行函数"""
                    # 将域状态转换为图状态
                    temp_graph_state = collaboration_adapter.state_adapter.to_graph_state(domain_state)
                    # 执行原始函数
                    result = function(temp_graph_state)
                    # 将结果转换回域状态
                    return collaboration_adapter.state_adapter.from_graph_state(result)
                
                # 使用协作适配器执行
                return collaboration_adapter.execute_with_collaboration(state, node_executor)
            except Exception as e:
                logger.error(f"包装函数执行失败: {e}")
                # 回退到直接执行
                return function(state)
        
        return wrapped_function
    
    def register_function(self, name: str, function: Callable, function_type: FunctionType) -> None:
        """注册函数到函数注册表
        
        Args:
            name: 函数名称
            function: 函数对象
            function_type: 函数类型
        """
        if self.function_registry:
            self.function_registry.register(name, function, function_type)
            logger.debug(f"注册函数: {name} ({function_type.value})")
        else:
            logger.warning("函数注册表未初始化，无法注册函数")
    
    def unregister_function(self, name: str, function_type: FunctionType) -> bool:
        """从函数注册表注销函数
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            bool: 是否成功注销
        """
        if self.function_registry:
            result = self.function_registry.unregister(name, function_type)
            if result:
                logger.debug(f"注销函数: {name} ({function_type.value})")
            return result
        else:
            logger.warning("函数注册表未初始化，无法注销函数")
            return False
    
    def list_registered_functions(self, function_type: Optional[FunctionType] = None) -> Dict[str, List[str]]:
        """列出已注册的函数
        
        Args:
            function_type: 函数类型过滤器
            
        Returns:
            Dict[str, List[str]]: 函数分类列表
        """
        if self.function_registry:
            return self.function_registry.list_functions(function_type)
        else:
            logger.warning("函数注册表未初始化")
            return {"nodes": [], "conditions": []}
    
    def validate_function_exists(self, name: str, function_type: FunctionType) -> bool:
        """验证函数是否存在
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            bool: 函数是否存在
        """
        if self.function_registry:
            return self.function_registry.validate_function_exists(name, function_type)
        else:
            logger.warning("函数注册表未初始化")
            return False
    
    def get_function_info(self, name: str, function_type: FunctionType) -> Optional[Dict[str, Any]]:
        """获取函数信息
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息
        """
        if self.function_registry:
            return self.function_registry.get_function_info(name, function_type)
        else:
            logger.warning("函数注册表未初始化")
            return None
    
    def discover_functions(self, module_paths: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """自动发现并注册函数
        
        Args:
            module_paths: 要扫描的模块路径列表
            
        Returns:
            Dict[str, List[str]]: 发现的函数统计信息
        """
        if self.function_registry:
            return self.function_registry.discover_functions(module_paths)
        else:
            logger.warning("函数注册表未初始化，无法进行函数发现")
            return {"nodes": [], "conditions": []}
    
    def validate_config_functions(self, config: Any) -> List[str]:
        """验证配置中的函数是否存在
        
        Args:
            config: 图配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not self.function_registry:
            errors.append("函数注册表未初始化")
            return errors
        
        # 验证节点函数
        for node_name, node_config in config.nodes.items():
            function_name = node_config.function_name
            if not self.function_registry.validate_function_exists(function_name, FunctionType.NODE_FUNCTION):
                errors.append(f"节点 '{node_name}' 引用的函数 '{function_name}' 不存在")
        
        # 验证条件函数
        for edge in config.edges:
            if edge.condition and not self.function_registry.validate_function_exists(edge.condition, FunctionType.CONDITION_FUNCTION):
                errors.append(f"边 '{edge.from_node}' -> '{edge.to_node}' 引用的条件函数 '{edge.condition}' 不存在")
        
        return errors
    
    def build_graph_with_validation(self, config: Any, state_manager: Optional["IStateCollaborationManager"] = None) -> Any:
        """构建图并进行验证
        
        Args:
            config: 图配置
            state_manager: 状态管理器
            
        Returns:
            构建的图
            
        Raises:
            ValueError: 配置验证失败
        """
        # 验证配置中的函数
        function_errors = self.validate_config_functions(config)
        if function_errors:
            raise ValueError(f"配置验证失败: {'; '.join(function_errors)}")
        
        # 构建图
        return self.build_graph(config, state_manager)
    
    def get_function_statistics(self) -> Dict[str, Any]:
        """获取函数统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.function_registry:
            return {"error": "函数注册表未初始化"}
        
        functions = self.function_registry.list_functions()
        
        return {
            "total_node_functions": len(functions.get("nodes", [])),
            "total_condition_functions": len(functions.get("conditions", [])),
            "node_functions": functions.get("nodes", []),
            "condition_functions": functions.get("conditions", []),
            "function_fallback_enabled": self.enable_function_fallback
        }