"""工作流配置接口定义

定义工作流图配置的接口，用于支持infrastructure层的配置使用。
遵循分层架构原则，interface层只定义接口，不依赖其他层。
"""

from typing import Dict, Any, Optional, List, Mapping, Sequence
from abc import ABC, abstractmethod
from enum import Enum

from ..common_domain import ISerializable


class EdgeType(Enum):
    """边类型枚举"""
    SIMPLE = "simple"
    CONDITIONAL = "conditional"


class INodeConfig(ISerializable, ABC):
    """节点配置接口
    
    定义工作流节点配置的基本契约。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """节点名称"""
        pass
    
    @property
    @abstractmethod
    def function_name(self) -> str:
        """函数名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """节点描述"""
        pass
    
    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        """节点配置字典"""
        pass
    
    @property
    @abstractmethod
    def composition_name(self) -> Optional[str]:
        """节点内部函数组合名称"""
        pass
    
    @property
    @abstractmethod
    def function_sequence(self) -> List[str]:
        """函数执行序列"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "INodeConfig":
        """从字典创建节点配置
        
        Args:
            data: 配置字典
            
        Returns:
            INodeConfig: 节点配置实例
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass


class IEdgeConfig(ISerializable, ABC):
    """边配置接口
    定义工作流边配置的基本契约
    """
    
    @property
    @abstractmethod
    def from_node(self) -> str:
        """起始节点"""
        pass
    
    @property
    @abstractmethod
    def to_node(self) -> str:
        """目标节点"""
        pass
    
    @property
    @abstractmethod
    def type(self) -> EdgeType:
        """边类型"""
        pass
    
    @property
    @abstractmethod
    def condition(self) -> Optional[str]:
        """条件函数名（兼容旧格式）"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """边描述"""
        pass
    
    @property
    @abstractmethod
    def path_map(self) -> Optional[Dict[str, Any]]:
        """条件边的路径映射"""
        pass
    
    @property
    @abstractmethod
    def route_function(self) -> Optional[str]:
        """路由函数名称"""
        pass
    
    @property
    @abstractmethod
    def route_parameters(self) -> Optional[Dict[str, Any]]:
        """路由函数参数"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IEdgeConfig":
        """从字典创建边配置
        
        Args:
            data: 配置字典
            
        Returns:
            IEdgeConfig: 边配置实例
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @abstractmethod
    def is_flexible_conditional(self) -> bool:
        """检查是否为灵活条件边
        
        Returns:
            bool: 是否为灵活条件边
        """
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """验证边配置
        
        Returns:
            List[str]: 验证错误列表
        """
        pass


class IStateFieldConfig(ISerializable, ABC):
    """状态字段配置接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """字段名称"""
        pass
    
    @property
    @abstractmethod
    def type(self) -> str:
        """字段类型"""
        pass
    
    @property
    @abstractmethod
    def default(self) -> Any:
        """默认值"""
        pass
    
    @property
    @abstractmethod
    def reducer(self) -> Optional[str]:
        """Reducer函数"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """字段描述"""
        pass


class IGraphStateConfig(ISerializable, ABC):
    """图状态配置接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """状态名称"""
        pass
    
    @property
    @abstractmethod
    def fields(self) -> Mapping[str, "IStateFieldConfig"]:
        """状态字段"""
        pass


class IGraphConfig(ISerializable, ABC):
    """图配置接口
    定义工作流图配置的基本契约
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """图名称"""
        pass
    
    @property
    @abstractmethod
    def id(self) -> str:
        """图ID"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """图描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """版本"""
        pass
    
    @property
    @abstractmethod
    def state_schema(self) -> IGraphStateConfig:
        """状态模式"""
        pass
    
    @property
    @abstractmethod
    def nodes(self) -> Mapping[str, INodeConfig]:
        """节点字典"""
        pass
    
    @property
    @abstractmethod
    def edges(self) -> Sequence[IEdgeConfig]:
        """边列表"""
        pass
    
    @property
    @abstractmethod
    def entry_point(self) -> Optional[str]:
        """入口点"""
        pass
    
    @property
    @abstractmethod
    def checkpointer(self) -> Optional[str]:
        """检查点配置"""
        pass
    
    @property
    @abstractmethod
    def interrupt_before(self) -> Optional[List[str]]:
        """中断配置（前置）"""
        pass
    
    @property
    @abstractmethod
    def interrupt_after(self) -> Optional[List[str]]:
        """中断配置（后置）"""
        pass
    
    @property
    @abstractmethod
    def state_overrides(self) -> Dict[str, Any]:
        """状态覆盖"""
        pass
    
    @property
    @abstractmethod
    def additional_config(self) -> Dict[str, Any]:
        """额外配置"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IGraphConfig":
        """从字典创建图配置
        
        Args:
            data: 配置字典
            
        Returns:
            IGraphConfig: 图配置实例
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """验证图配置
        
        Returns:
            List[str]: 验证错误列表
        """
        pass
