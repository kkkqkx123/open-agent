"""简单边定义

表示节点之间的直接连接，无条件判断。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.core.workflow.config import EdgeConfig


@dataclass
class SimpleEdge:
    """简单边
    
    表示从一个节点到另一个节点的直接连接，没有条件判断。
    """
    
    from_node: str
    to_node: str
    description: Optional[str] = None
    
    @classmethod
    def from_config(cls, config: EdgeConfig) -> "SimpleEdge":
        """从配置创建简单边
        
        Args:
            config: 边配置
            
        Returns:
            SimpleEdge: 简单边实例
        """
        if config.type.value != "simple":
            raise ValueError(f"配置类型不匹配，期望 simple，实际 {config.type.value}")
        
        return cls(
            from_node=config.from_node,
            to_node=config.to_node,
            description=config.description
        )
    
    def to_config(self) -> EdgeConfig:
        """转换为配置
        
        Returns:
            EdgeConfig: 边配置
        """
        from src.core.workflow.config import EdgeType
        return EdgeConfig(
            from_node=self.from_node,
            to_node=self.to_node,
            type=EdgeType.SIMPLE,
            description=self.description
        )
    
    def validate(self, node_names: set) -> list[str]:
        """验证边的有效性
        
        Args:
            node_names: 可用节点名称集合
            
        Returns:
            list[str]: 验证错误列表
        """
        errors = []
        
        if self.from_node not in node_names:
            errors.append(f"起始节点 '{self.from_node}' 不存在")
        
        if self.to_node not in node_names:
            errors.append(f"目标节点 '{self.to_node}' 不存在")
        
        if self.from_node == self.to_node:
            errors.append("不允许节点自循环")
        
        return errors
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SimpleEdge({self.from_node} -> {self.to_node})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        return f"SimpleEdge(from_node='{self.from_node}', to_node='{self.to_node}'{desc})"