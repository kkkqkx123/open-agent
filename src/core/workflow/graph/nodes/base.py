"""节点基类

提供节点的基本实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.interfaces.workflow.graph import INode, NodeExecutionResult
from src.interfaces.state.interfaces import IState
from src.interfaces.state.workflow import IWorkflowState


class BaseNode(INode, ABC):
    """节点基类"""
    
    def __init__(self, node_id: str, name: str, node_type: str,
                 description: str = "", config: Optional[Dict[str, Any]] = None):
        """初始化节点
        
        Args:
            node_id: 节点ID
            name: 节点名称
            node_type: 节点类型
            description: 节点描述
            config: 节点配置
        """
        self._node_id = node_id
        self.name = name
        self._node_type = node_type
        self.description = description
        self.config = config or {}
    
    @property
    def node_id(self) -> str:
        """节点ID"""
        return self._node_id
    
    @property
    def node_type(self) -> str:
        """节点类型"""
        return self._node_type
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        self.config[key] = value
    
    def merge_configs(self, runtime_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和运行时配置
        
        Args:
            runtime_config: 运行时配置
            
        Returns:
            合并后的配置
        """
        from ...config.node_config_loader import get_node_config_loader
        
        # 获取节点配置加载器
        config_loader = get_node_config_loader()
        
        # 获取默认配置并合并
        return config_loader.merge_configs(self.node_type, runtime_config)
    
    @abstractmethod
    def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点
        
        Args:
            state: 当前状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def execute_async(self, state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点
        
        Args:
            state: 当前状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
        pass
    
    def validate(self) -> list:
        """验证节点配置
        
        Returns:
            list: 验证错误列表
        """
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "description": self.description,
            "config": self.config
        }