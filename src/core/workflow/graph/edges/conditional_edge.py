"""条件边实现

提供基于条件判断的节点连接的核心层实现，支持多种条件类型。
"""

from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.graph import IEdge
from src.interfaces.state.base import IState
from .base import BaseEdge
from src.infrastructure.graph.conditions import ConditionType, ConditionEvaluator

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class ConditionalEdge(BaseEdge, IEdge):
    """条件边实现
    
    核心层的条件边实现，提供基于条件判断的节点连接。
    支持多种内置条件类型和自定义条件函数。
    
    特点：
    - 支持多种条件类型（工具调用、错误、消息内容等）
    - 支持自定义条件函数
    - 提供条件评估缓存
    - 支持条件组合和优先级
    - 详细的条件评估日志
    """
    
    def __init__(self, edge_id: str = "", from_node: str = "", to_node: str = "",
                 condition_type: str = "has_tool_calls", condition_parameters: Optional[Dict[str, Any]] = None,
                 description: str = "", metadata: Optional[Dict[str, Any]] = None):
        """初始化条件边
        
        Args:
            edge_id: 边ID
            from_node: 起始节点ID
            to_node: 目标节点ID
            condition_type: 条件类型
            condition_parameters: 条件参数
            description: 边描述
            metadata: 边元数据
        """
        super().__init__(edge_id, from_node, to_node)
        self.condition_type = condition_type
        self.condition_parameters = condition_parameters or {}
        self.description = description
        self._metadata = metadata or {}
        self._evaluator = ConditionEvaluator()
        self._custom_conditions: Dict[str, Callable] = {}
        
        logger.debug(f"创建条件边: {from_node} -> {to_node} (条件: {condition_type})")
    
    @property
    def edge_type(self) -> str:
        """边类型"""
        return "conditional"
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取边元数据"""
        return self._metadata.copy()
    
    def can_traverse(self, state: IState) -> bool:
        """判断是否可以遍历此边
        
        Args:
            state: 当前工作流状态
            
        Returns:
            bool: 条件是否满足
        """
        return self._evaluate_condition(state, {})
    
    def can_traverse_with_config(self, state: IState, config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边（带配置）
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            bool: 条件是否满足
        """
        merged_config = self._merge_configs(config)
        
        # 检查是否禁用
        if merged_config.get("disabled", False):
            logger.debug(f"条件边 {self._edge_id} 已禁用")
            return False
        
        return self._evaluate_condition(state, merged_config)
    
    def get_next_nodes(self, state: IState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            List[str]: 如果条件满足返回目标节点，否则返回空列表
        """
        if self.can_traverse_with_config(state, config):
            merged_config = self._merge_configs(config)
            
            # 检查是否有动态目标节点
            dynamic_target = merged_config.get("dynamic_target")
            if dynamic_target:
                logger.debug(f"条件边 {self._edge_id} 条件满足，使用动态目标: {dynamic_target}")
                return [dynamic_target]
            
            logger.debug(f"条件边 {self._edge_id} 条件满足，返回目标节点: {self._to_node}")
            return [self._to_node]
        
        logger.debug(f"条件边 {self._edge_id} 条件不满足，无目标节点")
        return []
    
    def _evaluate_condition(self, state: IState, config: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            state: 当前工作流状态
            config: 配置
            
        Returns:
            bool: 条件是否满足
        """
        try:
            # 解析条件类型
            condition_enum = self._parse_condition_type(self.condition_type)
            
            # 合并条件参数
            merged_parameters = self.condition_parameters.copy()
            merged_parameters.update(config.get("condition_parameters", {}))
            
            # 评估条件
            result = self._evaluator.evaluate(condition_enum, state, merged_parameters, config)
            
            logger.debug(f"条件边 {self._edge_id} 评估结果: {result} (条件: {self.condition_type})")
            return result
            
        except Exception as e:
            logger.error(f"条件边 {self._edge_id} 条件评估失败: {e}")
            # 根据配置决定失败时的行为
            return bool(config.get("fail_on_error", False))
    
    def _parse_condition_type(self, condition_type: str) -> ConditionType:
        """解析条件类型
        
        Args:
            condition_type: 条件类型字符串
            
        Returns:
            ConditionType: 条件类型枚举
            
        Raises:
            ValueError: 未知的条件类型
        """
        try:
            return ConditionType(condition_type)
        except ValueError:
            # 检查是否是自定义条件
            if condition_type in self._custom_conditions:
                return ConditionType.CUSTOM
            
            raise ValueError(f"未知的条件类型: {condition_type}")
    
    def register_custom_condition(self, name: str, condition_func: Callable) -> None:
        """注册自定义条件函数
        
        Args:
            name: 条件名称
            condition_func: 条件函数，签名为 (state, parameters, config) -> bool
        """
        self._custom_conditions[name] = condition_func
        logger.debug(f"注册自定义条件: {name}")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取边配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
        return {
            "type": "object",
            "properties": {
                "condition_type": {
                    "type": "string",
                    "description": "条件类型",
                    "enum": [ct.value for ct in ConditionType] + list(self._custom_conditions.keys()),
                    "default": "has_tool_calls"
                },
                "condition_parameters": {
                    "type": "object",
                    "description": "条件参数",
                    "default": {}
                },
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
                "fail_on_error": {
                    "type": "boolean",
                    "description": "条件评估失败时是否返回False",
                    "default": False
                },
                "cache_result": {
                    "type": "boolean",
                    "description": "是否缓存条件评估结果",
                    "default": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "条件评估超时时间（秒）",
                    "default": 10
                },
                "metadata": {
                    "type": "object",
                    "description": "边元数据",
                    "default": {}
                }
            },
            "required": ["condition_type"]
        }
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            config: 边配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证条件类型
        condition_type = config.get("condition_type", self.condition_type)
        try:
            self._parse_condition_type(condition_type)
        except ValueError as e:
            errors.append(str(e))
        
        # 验证条件参数
        condition_parameters = config.get("condition_parameters", {})
        if not isinstance(condition_parameters, dict):
            errors.append("condition_parameters 必须是字典类型")
        
        # 验证超时时间
        timeout = config.get("timeout", 10)
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append("timeout 必须是正整数")
        
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
        
        # 验证条件类型
        try:
            self._parse_condition_type(self.condition_type)
        except ValueError as e:
            errors.append(str(e))
        
        # 验证条件参数
        if not isinstance(self.condition_parameters, dict):
            errors.append("条件参数必须是字典类型")
        
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
            "condition_type": self.condition_type,
            "condition_parameters": self.condition_parameters.copy(),
            "disabled": False,
            "fail_on_error": False,
            "cache_result": True,
            "timeout": 10
        }
        
        # 合并元数据配置
        if self._metadata:
            base_config.update(self._metadata)
        
        # 合并传入的配置
        base_config.update(config)
        
        return base_config
    
    def update_condition(self, condition_type: str, condition_parameters: Optional[Dict[str, Any]] = None) -> None:
        """更新条件配置
        
        Args:
            condition_type: 新的条件类型
            condition_parameters: 新的条件参数
        """
        self.condition_type = condition_type
        if condition_parameters is not None:
            self.condition_parameters = condition_parameters
        
        logger.debug(f"更新条件边 {self._edge_id} 条件: {condition_type}")
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新边元数据
        
        Args:
            metadata: 新的元数据
        """
        if not isinstance(metadata, dict):
            raise ValueError("元数据必须是字典类型")
        
        self._metadata.update(metadata)
        logger.debug(f"更新条件边 {self._edge_id} 元数据: {metadata}")
    
    def list_available_conditions(self) -> List[str]:
        """列出所有可用的条件类型
        
        Returns:
            List[str]: 条件类型列表
        """
        builtin_conditions = [ct.value for ct in ConditionType]
        custom_conditions = list(self._custom_conditions.keys())
        return builtin_conditions + custom_conditions
    
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
            "condition_type": self.condition_type,
            "condition_parameters": self.condition_parameters,
            "description": self.description,
            "metadata": self._metadata
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"ConditionalEdge({self._from_node} -> {self._to_node} [{self.condition_type}])"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        params = f" params={self.condition_parameters}" if self.condition_parameters else ""
        meta = f" metadata={self._metadata}" if self._metadata else ""
        return f"ConditionalEdge(edge_id='{self._edge_id}', from_node='{self._from_node}', to_node='{self._to_node}', condition='{self.condition_type}'{params}{desc}{meta})"