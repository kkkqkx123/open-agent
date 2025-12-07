"""插件系统接口定义

定义了所有插件必须实现的基础接口和类型。
已重构：将Hook相关方法从基础插件接口中分离。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..state.workflow import IWorkflowState
    from .graph import NodeExecutionResult


class PluginType(Enum):
    """插件类型枚举"""
    START = "start"
    END = "end"
    GENERIC = "generic"
    HOOK = "hook"  # Hook类型插件


class PluginStatus(Enum):
    """插件状态枚举"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class HookPoint(Enum):
    """Hook执行点枚举"""
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    ON_ERROR = "on_error"
    BEFORE_COMPILE = "before_compile"
    AFTER_COMPILE = "after_compile"


@dataclass
class PluginMetadata:
    """插件元数据

    包含插件的基本信息和配置模式。
    """
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: Optional[List[str]] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = field(default_factory=dict)
    supported_hook_points: Optional[List['HookPoint']] = field(default_factory=list)
        
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}
        if self.supported_hook_points is None:
            self.supported_hook_points = []


@dataclass
class PluginContext:
    """插件执行上下文

    提供插件执行时需要的上下文信息。
    """
    workflow_id: str
    thread_id: Optional[str] = None
    session_id: Optional[str] = None
    execution_start_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PluginExecutionResult:
    """插件执行结果"""
    plugin_id: str
    status: str
    success: bool
    error: Optional[str] = None
    execution_time: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class HookContext:
    """Hook执行上下文"""
    hook_point: HookPoint
    config: Dict[str, Any]
    node_type: Optional[str] = None
    state: Optional['IWorkflowState'] = None
    error: Optional[Exception] = None
    execution_result: Optional['NodeExecutionResult'] = None
    metadata: Optional[Dict[str, Any]] = None
    graph_id: Optional[str] = None


class HookExecutionResult:
    """Hook执行结果"""
    
    def __init__(
        self,
        should_continue: bool = True,
        modified_state: Optional['IWorkflowState'] = None,
        modified_result: Optional[Any] = None,
        force_next_node: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化Hook执行结果
        
        Args:
            should_continue: 是否继续执行后续Hook和节点逻辑
            modified_state: 修改后的状态
            modified_result: 修改后的节点执行结果
            force_next_node: 强制指定的下一个节点
            metadata: Hook执行元数据
        """
        self.should_continue = should_continue
        self.modified_state = modified_state
        self.modified_result = modified_result
        self.force_next_node = force_next_node
        self.metadata = metadata or {}
    
    def __bool__(self) -> bool:
        """布尔值转换，表示是否继续执行"""
        return self.should_continue


class IPlugin(ABC):
    """插件基础接口
    
    所有插件都必须实现此接口。
    这是一个纯插件接口，不包含任何Hook相关方法。
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """获取插件元数据
        
        Returns:
            PluginMetadata: 插件元数据
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证插件配置
        
        Args:
            config: 插件配置
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 基础验证
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return errors
        
        # 使用配置模式验证
        schema = self.metadata.config_schema
        if schema:
            errors.extend(self._validate_config_with_schema(config, schema))
        
        return errors
    
    def _validate_config_with_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """使用配置模式验证配置
        
        Args:
            config: 插件配置
            schema: 配置模式
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查必需字段
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        properties = schema.get("properties", {})
        for field_name, field_config in properties.items():
            if field_name in config:
                expected_type = field_config.get("type")
                actual_value = config[field_name]
                
                if expected_type == "string" and not isinstance(actual_value, str):
                    errors.append(f"字段 {field_name} 应为字符串类型")
                elif expected_type == "integer" and not isinstance(actual_value, int):
                    errors.append(f"字段 {field_name} 应为整数类型")
                elif expected_type == "boolean" and not isinstance(actual_value, bool):
                    errors.append(f"字段 {field_name} 应为布尔类型")
                elif expected_type == "array" and not isinstance(actual_value, list):
                    errors.append(f"字段 {field_name} 应为数组类型")
                elif expected_type == "object" and not isinstance(actual_value, dict):
                    errors.append(f"字段 {field_name} 应为对象类型")
        
        return errors
    
    def get_status(self) -> PluginStatus:
        """获取插件状态
        
        Returns:
            PluginStatus: 插件状态
        """
        return PluginStatus.ENABLED


class IHookPlugin(IPlugin):
    """Hook插件接口

    继承自IPlugin，专门用于Hook插件的接口定义。
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行前Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def set_execution_service(self, service: Any) -> None:
        """设置执行服务

        Args:
            service: 执行服务实例
        """
        pass

    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点

        Returns:
            List[HookPoint]: 支持的Hook执行点列表
        """
        # 默认支持所有Hook点，子类可以重写
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


class IStartPlugin(IPlugin):
    """START节点插件接口

    专门用于START节点的插件接口。
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass


class IEndPlugin(IPlugin):
    """END节点插件接口

    专门用于END节点的插件接口。
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass


class PluginError(Exception):
    """插件异常基类"""
    pass


class PluginInitializationError(PluginError):
    """插件初始化异常"""
    pass


class PluginExecutionError(PluginError):
    """插件执行异常"""
    pass


class PluginConfigurationError(PluginError):
    """插件配置异常"""
    pass