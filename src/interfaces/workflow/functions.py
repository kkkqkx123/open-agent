"""统一的Function接口定义

为graph模块的所有function类型（NodeFunction、ConditionFunction、RouteFunction、TriggerFunction）
提供统一的接口规范，参考Hook系统的设计模式。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .graph import IWorkflowState


class FunctionType(Enum):
    """Function类型枚举"""
    NODE = "node_function"
    CONDITION = "condition_function"
    ROUTE = "route_function"
    TRIGGER = "trigger_function"


class FunctionMetadata:
    """Function元数据容器"""
    
    def __init__(
        self,
        function_id: str,
        name: str,
        function_type: FunctionType,
        description: str = "",
        version: str = "1.0.0",
        category: str = "",
        is_async: bool = False,
        parameters: Optional[Dict[str, Any]] = None,
        return_type: str = "Any",
        tags: Optional[List[str]] = None
    ):
        """初始化Function元数据
        
        Args:
            function_id: Function唯一标识
            name: Function名称
            function_type: Function类型
            description: Function描述
            version: Function版本
            category: Function分类（如 "builtin"、"custom"等）
            is_async: 是否异步函数
            parameters: 参数说明字典
            return_type: 返回类型说明
            tags: Function标签列表
        """
        self.function_id = function_id
        self.name = name
        self.function_type = function_type
        self.description = description
        self.version = version
        self.category = category
        self.is_async = is_async
        self.parameters = parameters or {}
        self.return_type = return_type
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "function_id": self.function_id,
            "name": self.name,
            "function_type": self.function_type.value,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "is_async": self.is_async,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "tags": self.tags
        }


class IFunction(ABC):
    """统一的Function基接口
    
    所有function类型都应实现此接口，提供统一的元数据、生命周期管理和验证能力。
    
    参考Hook系统的IHook接口设计，保持架构一致性。
    """
    
    # ======== 元数据属性 ========
    
    @property
    @abstractmethod
    def function_id(self) -> str:
        """获取Function唯一标识
        
        Returns:
            str: Function的唯一标识符，通常是 function_type:name 的形式
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """获取Function名称
        
        Returns:
            str: Function名称
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """获取Function描述
        
        Returns:
            str: Function的详细描述
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """获取Function版本
        
        Returns:
            str: Function版本号（如 "1.0.0"）
        """
        pass
    
    @property
    @abstractmethod
    def function_type(self) -> FunctionType:
        """获取Function类型
        
        Returns:
            FunctionType: Function类型枚举值
        """
        pass
    
    @property
    @abstractmethod
    def is_async(self) -> bool:
        """是否异步函数
        
        Returns:
            bool: True为异步，False为同步
        """
        pass
    
    # ======== 参数信息 ========
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取Function参数说明
        
        用于获取function的输入参数信息，支持工具调用、验证等场景。
        
        Returns:
            Dict[str, Any]: 参数说明字典，结构示例：
            {
                "state": {
                    "type": "IWorkflowState",
                    "required": True,
                    "description": "当前工作流状态"
                },
                "config": {
                    "type": "Dict[str, Any]",
                    "required": False,
                    "description": "Function配置",
                    "default": {}
                }
            }
        """
        pass
    
    @abstractmethod
    def get_return_type(self) -> str:
        """获取Function返回类型
        
        Returns:
            str: 返回类型说明，如 "str"、"Dict[str, Any]"、"bool" 等
        """
        pass
    
    # ======== 生命周期管理 ========
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化Function
        
        在Function首次使用前调用，用于执行初始化逻辑。
        
        Args:
            config: Function配置字典
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理Function资源
        
        在Function不再使用时调用，用于释放资源。
        
        Returns:
            bool: 清理是否成功
        """
        pass
    
    # ======== 配置验证 ========
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Function配置
        
        验证传入的配置是否符合Function的要求。
        
        Args:
            config: Function配置字典
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """验证Function调用参数
        
        验证调用Function时传入的参数是否正确。
        
        Args:
            params: 调用参数字典
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        pass
    
    # ======== 元信息 ========
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """获取Function完整元数据
        
        返回Function的所有元信息，用于序列化、调试、文档生成等。
        
        Returns:
            Dict[str, Any]: 元数据字典，应包含至少以下键：
            - function_id: str
            - name: str
            - function_type: str
            - description: str
            - version: str
            - is_async: bool
            - parameters: Dict
            - return_type: str
        """
        pass


# ========== 具体Function类型接口 ==========

class INodeFunction(IFunction, ABC):
    """节点执行函数接口
    
    用于执行工作流节点的具体逻辑。
    """
    
    @abstractmethod
    async def execute(
        self,
        state: 'IWorkflowState',
        config: Dict[str, Any]
    ) -> Any:
        """执行节点函数
        
        Args:
            state: 当前工作流状态
            config: 节点配置
            
        Returns:
            Any: 执行结果
            
        Raises:
            Exception: 执行失败时抛出异常
        """
        pass


class IConditionFunction(IFunction, ABC):
    """条件判断函数接口
    
    用于在条件边中进行条件判断和路由决策。
    """
    
    @abstractmethod
    def evaluate(
        self,
        state: 'IWorkflowState',
        condition: Dict[str, Any]
    ) -> bool:
        """评估条件
        
        Args:
            state: 当前工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        pass


class IRouteFunction(IFunction, ABC):
    """路由函数接口
    
    用于在灵活条件边中进行动态路由决策，根据状态决定下一个节点。
    """
    
    @abstractmethod
    def route(
        self,
        state: 'IWorkflowState',
        params: Dict[str, Any]
    ) -> Optional[str]:
        """执行路由决策
        
        Args:
            state: 当前工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID，None表示无有效目标
        """
        pass


class ITriggerFunction(IFunction, ABC):
    """触发器函数接口
    
    用于判断是否应该触发工作流或某些特定操作。
    """
    
    @abstractmethod
    def should_trigger(
        self,
        state: 'IWorkflowState',
        config: Dict[str, Any]
    ) -> bool:
        """判断是否应该触发
        
        Args:
            state: 当前工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
        """
        pass


# ========== 注册表接口 ==========

class IFunctionRegistry(ABC):
    """统一Function注册表接口
    
    管理所有类型的function（Node、Condition、Route、Trigger），
    提供统一的注册、查询、验证和生命周期管理接口。
    
    替代现有分散的NodeFunctionRegistry、RouteFunctionRegistry等，
    统一function的管理方式。
    """
    
    # ======== 注册 ========
    
    @abstractmethod
    def register_function(
        self,
        func: IFunction,
        overwrite: bool = False
    ) -> None:
        """注册Function
        
        Args:
            func: Function实例
            overwrite: 是否覆盖已存在的同名Function
            
        Raises:
            ValueError: 如果Function ID已存在且overwrite=False
        """
        pass
    
    @abstractmethod
    def unregister_function(self, function_id: str) -> bool:
        """注销Function
        
        Args:
            function_id: Function ID (格式: function_type:name)
            
        Returns:
            bool: 是否成功注销
        """
        pass
    
    # ======== 查询 ========
    
    @abstractmethod
    def get_function(self, function_id: str) -> Optional[IFunction]:
        """获取Function
        
        Args:
            function_id: Function ID (格式: function_type:name)
            
        Returns:
            Optional[IFunction]: Function实例，不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_function_by_name(self, name: str) -> Optional[IFunction]:
        """按名称获取Function（仅在名称唯一时使用）
        
        如果存在多个同名但不同类型的Function，返回第一个。
        
        Args:
            name: Function名称
            
        Returns:
            Optional[IFunction]: Function实例，不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_functions(
        self,
        function_type: Optional[FunctionType] = None,
        category: Optional[str] = None
    ) -> List[IFunction]:
        """列出Functions
        
        Args:
            function_type: Function类型过滤，None表示返回所有类型
            category: 分类过滤（如 "builtin"、"custom"），None表示返回所有
            
        Returns:
            List[IFunction]: Function列表
        """
        pass
    
    # ======== 类型特定查询 ========
    
    @abstractmethod
    def get_node_functions(self) -> List[INodeFunction]:
        """获取所有Node Functions
        
        Returns:
            List[INodeFunction]: Node Function列表
        """
        pass
    
    @abstractmethod
    def get_condition_functions(self) -> List[IConditionFunction]:
        """获取所有Condition Functions
        
        Returns:
            List[IConditionFunction]: Condition Function列表
        """
        pass
    
    @abstractmethod
    def get_route_functions(self) -> List[IRouteFunction]:
        """获取所有Route Functions
        
        Returns:
            List[IRouteFunction]: Route Function列表
        """
        pass
    
    @abstractmethod
    def get_trigger_functions(self) -> List[ITriggerFunction]:
        """获取所有Trigger Functions
        
        Returns:
            List[ITriggerFunction]: Trigger Function列表
        """
        pass
    
    # ======== 统计 ========
    
    @abstractmethod
    def get_function_count(
        self,
        function_type: Optional[FunctionType] = None
    ) -> int:
        """获取Function数量
        
        Args:
            function_type: Function类型，None表示统计所有
            
        Returns:
            int: Function数量
        """
        pass
    
    @abstractmethod
    def has_function(self, function_id: str) -> bool:
        """检查Function是否存在
        
        Args:
            function_id: Function ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    # ======== 清理 ========
    
    @abstractmethod
    def clear(self, function_type: Optional[FunctionType] = None) -> None:
        """清除Functions
        
        Args:
            function_type: 要清除的Function类型，None表示清除所有
        """
        pass
    
    @abstractmethod
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息，包含各类型Function数量等
        """
        pass


__all__ = [
    "FunctionType",
    "FunctionMetadata",
    "IFunction",
    "INodeFunction",
    "IConditionFunction",
    "IRouteFunction",
    "ITriggerFunction",
    "IFunctionRegistry",
]
