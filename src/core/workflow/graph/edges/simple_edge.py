"""简单边实现

提供节点之间的直接连接，无条件判断的核心层实现。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.graph import IEdge
from src.interfaces.state.base import IState
from .base import BaseEdge

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class SimpleEdge(BaseEdge, IEdge):
    """简单边实现
    
    核心层的简单边实现，提供节点之间的直接连接，无条件判断。
    适用于工作流中的顺序执行场景。
    
    特点：
    - 无条件判断，总是可以遍历
    - 支持配置合并和验证
    - 提供详细的执行日志
    - 支持元数据传递
    """
    
    def __init__(self, edge_id: str = "", from_node: str = "", to_node: str = "", 
                description: str = "", metadata: Optional[Dict[str, Any]] = None):
        """初始化简单边
        
        Args:
            edge_id: 边ID
            from_node: 起始节点ID
            to_node: 目标节点ID
            description: 边描述
            metadata: 边元数据
        """
        super().__init__(edge_id, from_node, to_node)
        self.description = description
        self._metadata = metadata or {}
        
        logger.debug(f"创建简单边: {from_node} -> {to_node} (ID: {edge_id})")
    
    @property
    def edge_type(self) -> str:
        """边类型"""
        return "simple"
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取边元数据"""
        return self._metadata.copy()
    
    def can_traverse(self, state: IState) -> bool:
        """判断是否可以遍历此边
        
        Args:
            state: 当前工作流状态
            
        Returns:
            bool: 总是返回True，简单边无条件限制
        """
        logger.debug(f"简单边 {self._edge_id} 遍历检查: {self._from_node} -> {self._to_node}")
        return True
    
    def can_traverse_with_config(self, state: IState, config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边（带配置）
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            bool: 总是返回True，简单边无条件限制
        """
        merged_config = self._merge_configs(config)
        logger.debug(f"简单边 {self._edge_id} 带配置遍历检查: {self._from_node} -> {self._to_node}")
        
        # 检查是否有禁用标志
        if merged_config.get("disabled", False):
            logger.debug(f"简单边 {self._edge_id} 已禁用")
            return False
        
        return True
    
    def get_next_nodes(self, state: IState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            List[str]: 返回目标节点
        """
        merged_config = self._merge_configs(config)
        
        # 检查是否有动态目标节点
        dynamic_target = merged_config.get("dynamic_target")
        if dynamic_target:
            logger.debug(f"简单边 {self._edge_id} 使用动态目标: {dynamic_target}")
            return [dynamic_target]
        
        logger.debug(f"简单边 {self._edge_id} 返回目标节点: {self._to_node}")
        return [self._to_node]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取边配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
        return {
            "type": "object",
            "properties": {
                "disabled": {
                    "type": "boolean",
                    "description": "是否禁用此边",
                    "default": False
                },
                "dynamic_target": {
                    "type": "string",
                    "description": "动态目标节点ID（可选）",
                    "default": ""
                },
                "timeout": {
                    "type": "integer",
                    "description": "遍历超时时间（秒）",
                    "default": 30
                },
                "retry_count": {
                    "type": "integer",
                    "description": "重试次数",
                    "default": 0
                },
                "metadata": {
                    "type": "object",
                    "description": "边元数据",
                    "default": {}
                }
            },
            "required": []
        }
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            config: 边配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证超时时间
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append("timeout 必须是正整数")
        
        # 验证重试次数
        retry_count = config.get("retry_count", 0)
        if not isinstance(retry_count, int) or retry_count < 0:
            errors.append("retry_count 必须是非负整数")
        
        # 验证动态目标节点
        dynamic_target = config.get("dynamic_target")
        if dynamic_target is not None and not isinstance(dynamic_target, str):
            errors.append("dynamic_target 必须是字符串类型")
        
        return errors
    
    def validate(self) -> List[str]:
        """验证边配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = super().validate()
        
        # 检查是否自循环
        if self._from_node == self._to_node:
            errors.append("不允许节点自循环")
        
        # 验证元数据
        if not isinstance(self._metadata, dict):
            errors.append("元数据必须是字典类型")
        
        return errors
    
    def _merge_configs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            config: 边配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        # 基础配置
        base_config = {
            "disabled": False,
            "timeout": 30,
            "retry_count": 0
        }
        
        # 合并元数据配置
        if self._metadata:
            base_config.update(self._metadata)
        
        # 合并传入的配置
        base_config.update(config)
        
        return base_config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 边的字典表示
        """
        return {
            "edge_id": self._edge_id,
            "edge_type": self.edge_type,
            "from_node": self._from_node,
            "to_node": self._to_node,
            "description": self.description,
            "metadata": self._metadata
        }
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新边元数据
        
        Args:
            metadata: 新的元数据
        """
        if not isinstance(metadata, dict):
            raise ValueError("元数据必须是字典类型")
        
        self._metadata.update(metadata)
        logger.debug(f"更新简单边 {self._edge_id} 元数据: {metadata}")
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SimpleEdge({self._from_node} -> {self._to_node})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        meta = f" metadata={self._metadata}" if self._metadata else ""
        return f"SimpleEdge(edge_id='{self._edge_id}', from_node='{self._from_node}', to_node='{self._to_node}'{desc}{meta})"