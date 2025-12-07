"""统一元素构建接口

定义图元素（节点、边）构建的统一接口，确保构建行为的一致性。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .config import INodeConfig, IEdgeConfig


class BuildResult(Enum):
    """构建结果状态"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class BuildContext:
    """构建上下文
    
    包含构建过程中需要的所有上下文信息。
    """
    
    def __init__(
        self,
        graph_config: Any,
        state_manager: Optional[Any] = None,
        function_resolver: Optional[Any] = None,
        logger: Optional[Any] = None,
        cache: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        node_function_manager: Optional[Any] = None,
        flexible_edge_factory: Optional[Any] = None
    ):
        self.graph_config = graph_config
        self.state_manager = state_manager
        self.function_resolver = function_resolver
        self.logger = logger
        self.cache = cache or {}
        self.metadata = metadata or {}
        self.node_function_manager = node_function_manager
        self.flexible_edge_factory = flexible_edge_factory
        self.build_stats = {
            "total_elements": 0,
            "successful_builds": 0,
            "failed_builds": 0,
            "warnings": 0
        }
    
    def get_cache_key(self, element_type: str, element_name: str) -> str:
        """生成缓存键"""
        return f"{element_type}:{element_name}"
    
    def get_cached_result(self, element_type: str, element_name: str) -> Optional[Any]:
        """获取缓存结果"""
        cache_key = self.get_cache_key(element_type, element_name)
        return self.cache.get(cache_key)
    
    def cache_result(self, element_type: str, element_name: str, result: Any) -> None:
        """缓存结果"""
        cache_key = self.get_cache_key(element_type, element_name)
        self.cache[cache_key] = result
    
    def record_build_result(self, result: BuildResult, message: str = "") -> None:
        """记录构建结果"""
        self.build_stats["total_elements"] += 1
        
        if result == BuildResult.SUCCESS:
            self.build_stats["successful_builds"] += 1
        elif result == BuildResult.ERROR:
            self.build_stats["failed_builds"] += 1
        elif result == BuildResult.WARNING:
            self.build_stats["warnings"] += 1
        
        if self.logger and message:
            if result == BuildResult.ERROR:
                self.logger.error(message)
            elif result == BuildResult.WARNING:
                self.logger.warning(message)
            else:
                self.logger.debug(message)


class IElementBuilder(ABC):
    """统一元素构建接口
    
    定义所有图元素构建器必须实现的基础接口。
    """
    
    @abstractmethod
    def get_element_type(self) -> str:
        """获取元素类型
        
        Returns:
            str: 元素类型标识符
        """
        pass
    
    @abstractmethod
    def can_build(self, config: Any) -> bool:
        """检查是否可以构建指定配置的元素
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            
        Returns:
            bool: 是否可以构建
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Any, context: BuildContext) -> List[str]:
        """验证元素配置
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        pass
    
    @abstractmethod
    def build_element(
        self, 
        config: Any, 
        context: BuildContext
    ) -> Any:
        """构建元素
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            context: 构建上下文
            
        Returns:
            Any: 构建的元素实例
            
        Raises:
            ValueError: 配置验证失败或构建过程中出现错误
        """
        pass
    
    @abstractmethod
    def add_to_graph(
        self, 
        element: Any, 
        builder: Any, 
        config: Any,
        context: BuildContext
    ) -> None:
        """将元素添加到图中
        
        Args:
            element: 构建的元素实例
            builder: 图构建器
            config: 元素配置 (INodeConfig | IEdgeConfig)
            context: 构建上下文
        """
        pass
    
    def get_supported_config_types(self) -> List[type]:
        """获取支持的配置类型
        
        Returns:
            List[type]: 支持的配置类型列表
        """
        return [object]
    
    def get_build_priority(self) -> int:
        """获取构建优先级
        
        数值越小优先级越高，用于确定构建顺序。
        
        Returns:
            int: 构建优先级
        """
        return 100
    
    def should_cache(self, config: Any) -> bool:
        """检查是否应该缓存构建结果
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            
        Returns:
            bool: 是否应该缓存
        """
        return True


class INodeBuilder(IElementBuilder):
    """节点构建器接口"""
    
    @abstractmethod
    def get_node_function(
        self, 
        config: Any, 
        context: BuildContext
    ) -> Optional[Callable]:
        """获取节点函数
        
        Args:
            config: 节点配置 (INodeConfig)
            context: 构建上下文
            
        Returns:
            Optional[Callable]: 节点函数，如果无法获取返回None
        """
        pass
    
    def wrap_node_function(
        self, 
        function: Callable, 
        config: Any,
        context: BuildContext
    ) -> Callable:
        """包装节点函数
        
        为节点函数添加额外的功能，如状态管理、迭代管理等。
        
        Args:
            function: 原始节点函数
            config: 节点配置 (INodeConfig)
            context: 构建上下文
            
        Returns:
            Callable: 包装后的函数
        """
        return function


class IEdgeBuilder(IElementBuilder):
    """边构建器接口"""
    
    @abstractmethod
    def get_edge_function(
        self, 
        config: Any, 
        context: BuildContext
    ) -> Optional[Callable]:
        """获取边函数（主要用于条件边）
        
        Args:
            config: 边配置 (IEdgeConfig)
            context: 构建上下文
            
        Returns:
            Optional[Callable]: 边函数，如果无法获取返回None
        """
        pass
    
    def get_path_map(self, config: Any, context: BuildContext) -> Optional[Dict[str, Any]]:
        """获取路径映射（主要用于条件边）
        
        Args:
            config: 边配置 (IEdgeConfig)
            context: 构建上下文
            
        Returns:
            Optional[Dict[str, Any]]: 路径映射，如果没有返回None
        """
        return getattr(config, 'path_map', None)


class IElementBuilderFactory(ABC):
    """元素构建器工厂接口"""
    
    @abstractmethod
    def create_builder(self, element_type: str, context: BuildContext) -> IElementBuilder:
        """创建元素构建器
        
        Args:
            element_type: 元素类型
            context: 构建上下文
            
        Returns:
            IElementBuilder: 元素构建器实例
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的元素类型
        
        Returns:
            List[str]: 支持的元素类型列表
        """
        pass
    
    @abstractmethod
    def register_builder(self, element_type: str, builder_class: type) -> None:
        """注册元素构建器
        
        Args:
            element_type: 元素类型
            builder_class: 构建器类
        """
        pass


class IBuildStrategy(ABC):
    """构建策略接口"""
    
    @abstractmethod
    def can_handle(self, config: Any, context: BuildContext) -> bool:
        """检查是否可以处理指定配置
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            context: 构建上下文
            
        Returns:
            bool: 是否可以处理
        """
        pass
    
    @abstractmethod
    def execute(
        self, 
        config: Any, 
        context: BuildContext,
        builder: IElementBuilder
    ) -> Any:
        """执行构建策略
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            context: 构建上下文
            builder: 元素构建器
            
        Returns:
            Any: 构建结果
        """
        pass
    
    def get_strategy_name(self) -> str:
        """获取策略名称
        
        Returns:
            str: 策略名称
        """
        return self.__class__.__name__


class IValidationRule(ABC):
    """验证规则接口"""
    
    @abstractmethod
    def validate(
        self, 
        config: Any, 
        context: BuildContext
    ) -> List[str]:
        """执行验证
        
        Args:
            config: 元素配置 (INodeConfig | IEdgeConfig)
            context: 构建上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """获取规则名称
        
        Returns:
            str: 规则名称
        """
        pass
    
    def get_priority(self) -> int:
        """获取验证优先级
        
        数值越小优先级越高。
        
        Returns:
            int: 验证优先级
        """
        return 100