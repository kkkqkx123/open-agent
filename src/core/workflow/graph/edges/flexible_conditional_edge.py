"""灵活条件边实现

提供基于路由函数的条件边核心层实现，支持条件逻辑与路由目标的解耦。
"""

from typing import Dict, Any, List, Optional, Callable, Union, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.graph import IEdge
from src.interfaces.state.base import IState
from .base import BaseEdge

if TYPE_CHECKING:
    from src.core.workflow.registry import FunctionRegistry

logger = get_logger(__name__)


class FlexibleConditionalEdge(BaseEdge, IEdge):
    """灵活条件边实现
    
    核心层的灵活条件边实现，提供基于路由函数的条件边。
    支持条件逻辑与路由目标的解耦，使路由逻辑可以复用。
    
    特点：
    - 基于路由函数进行条件判断
    - 支持路由函数参数化
    - 支持路由函数注册和管理
    - 提供路由函数缓存
    - 支持动态路由目标
    """
    
    def __init__(self, edge_id: str = "", from_node: str = "", 
                 route_function: str = "", route_parameters: Optional[Dict[str, Any]] = None,
                 description: str = "", metadata: Optional[Dict[str, Any]] = None):
        """初始化灵活条件边
        
        Args:
            edge_id: 边ID
            from_node: 起始节点ID
            route_function: 路由函数名称
            route_parameters: 路由函数参数
            description: 边描述
            metadata: 边元数据
        """
        super().__init__(edge_id, from_node, "")
        self.route_function = route_function
        self.route_parameters = route_parameters or {}
        self.description = description
        self._metadata = metadata or {}
        self._function_registry: Optional["FunctionRegistry"] = None
        self._cached_route_function: Optional[Any] = None
        
        logger.debug(f"创建灵活条件边: {from_node} -> [路由函数: {route_function}]")
    
    @property
    def edge_type(self) -> str:
        """边类型"""
        return "flexible_conditional"
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取边元数据"""
        return self._metadata.copy()
    
    def set_function_registry(self, registry: "FunctionRegistry") -> None:
        """设置函数注册表
        
        Args:
            registry: 函数注册表实例
        """
        self._function_registry = registry
        self._cached_route_function = None  # 清除缓存
        logger.debug(f"设置灵活条件边 {self._edge_id} 的函数注册表")
    
    def can_traverse(self, state: IState) -> bool:
        """判断是否可以遍历此边
        
        Args:
            state: 当前工作流状态
            
        Returns:
            bool: 路由函数是否返回有效目标
        """
        target_node = self._get_target_node(state, {})
        return target_node is not None and target_node != ""
    
    def can_traverse_with_config(self, state: IState, config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边（带配置）
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            bool: 路由函数是否返回有效目标
        """
        merged_config = self._merge_configs(config)
        
        # 检查是否禁用
        if merged_config.get("disabled", False):
            logger.debug(f"灵活条件边 {self._edge_id} 已禁用")
            return False
        
        target_node = self._get_target_node(state, merged_config)
        return target_node is not None and target_node != ""
    
    def get_next_nodes(self, state: IState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            List[str]: 路由函数返回的目标节点列表
        """
        target_node = self._get_target_node(state, config)
        
        if target_node:
            logger.debug(f"灵活条件边 {self._edge_id} 路由到: {target_node}")
            return [target_node]
        
        logger.debug(f"灵活条件边 {self._edge_id} 无有效目标节点")
        return []
    
    def _get_target_node(self, state: IState, config: Dict[str, Any]) -> Optional[str]:
        """获取目标节点
        
        Args:
            state: 当前工作流状态
            config: 配置
            
        Returns:
            Optional[str]: 目标节点ID，如果没有有效目标则返回None
        """
        try:
            route_func = self._get_route_function()
            if route_func is None:
                logger.error(f"灵活条件边 {self._edge_id} 路由函数不存在: {self.route_function}")
                return None
            
            # 合并路由参数
            merged_config = self._merge_configs(config)
            route_parameters = self.route_parameters.copy()
            route_parameters.update(merged_config.get("route_parameters", {}))
            
            # 准备路由函数参数
            route_state = self._prepare_route_state(state, route_parameters)
            
            # 调用路由函数
            if hasattr(route_func, 'route'):
                # 新的IFunction接口
                target_node = route_func.route(route_state, route_parameters)
            else:
                # 旧的Callable接口
                target_node = route_func(route_state)
            
            # 验证返回值
            if not isinstance(target_node, str):
                logger.warning(f"灵活条件边 {self._edge_id} 路由函数返回非字符串: {target_node}")
                return None
            
            return target_node
            
        except Exception as e:
            logger.error(f"灵活条件边 {self._edge_id} 路由函数执行失败: {e}")
            merged_config = self._merge_configs(config)
            if merged_config.get("fail_on_error", False):
                return None
            return merged_config.get("fallback_target")
    
    def _get_route_function(self) -> Optional[Any]:
        """获取路由函数
        
        Returns:
            Optional[Any]: 路由函数，如果不存在则返回None
        """
        # 使用缓存的函数
        if self._cached_route_function:
            return self._cached_route_function
        
        # 从函数注册表获取
        if self._function_registry:
            route_func = self._function_registry.get_route_function(self.route_function)
            if route_func:
                self._cached_route_function = route_func
                return route_func
        
        return None
    
    def _prepare_route_state(self, state: IState, route_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """准备路由函数状态
        
        Args:
            state: 当前工作流状态
            route_parameters: 路由参数
            
        Returns:
            Dict[str, Any]: 路由状态
        """
        # 基础状态数据
        route_state = {
            "state": state,
            "data": state.get_data("data", {}),
            "messages": state.get_data("messages", []),
            "context": state.get_data("context", {}),
            "_route_parameters": route_parameters,
            "_edge_id": self._edge_id,
            "_from_node": self._from_node
        }
        
        return route_state
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取边配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
        return {
            "type": "object",
            "properties": {
                "route_function": {
                    "type": "string",
                    "description": "路由函数名称",
                    "default": ""
                },
                "route_parameters": {
                    "type": "object",
                    "description": "路由函数参数",
                    "default": {}
                },
                "disabled": {
                    "type": "boolean",
                    "description": "是否禁用此边",
                    "default": False
                },
                "fallback_target": {
                    "type": "string",
                    "description": "路由失败时的备用目标节点",
                    "default": ""
                },
                "fail_on_error": {
                    "type": "boolean",
                    "description": "路由失败时是否返回None",
                    "default": False
                },
                "cache_route_function": {
                    "type": "boolean",
                    "description": "是否缓存路由函数",
                    "default": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "路由函数执行超时时间（秒）",
                    "default": 10
                },
                "metadata": {
                    "type": "object",
                    "description": "边元数据",
                    "default": {}
                }
            },
            "required": ["route_function"]
        }
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            config: 边配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证路由函数名称
        route_function = config.get("route_function", self.route_function)
        if not route_function:
            errors.append("路由函数名称不能为空")
        
        # 验证路由参数
        route_parameters = config.get("route_parameters", {})
        if not isinstance(route_parameters, dict):
            errors.append("路由参数必须是字典类型")
        
        # 验证超时时间
        timeout = config.get("timeout", 10)
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append("timeout 必须是正整数")
        
        # 验证备用目标节点
        fallback_target = config.get("fallback_target")
        if fallback_target is not None and not isinstance(fallback_target, str):
            errors.append("fallback_target 必须是字符串类型")
        
        return errors
    
    def validate(self) -> List[str]:
        """验证边配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = super().validate()
        
        # 验证路由函数名称
        if not self.route_function:
            errors.append("路由函数名称不能为空")
        
        # 验证路由参数
        if not isinstance(self.route_parameters, dict):
            errors.append("路由参数必须是字典类型")
        
        # 验证元数据
        if not isinstance(self._metadata, dict):
            errors.append("元数据必须是字典类型")
        
        # 验证函数注册表
        if self._function_registry is None:
            errors.append("函数注册表未设置")
        elif not self._function_registry.get_route_function(self.route_function):
            errors.append(f"路由函数不存在: {self.route_function}")
        
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
            "route_function": self.route_function,
            "route_parameters": self.route_parameters.copy(),
            "disabled": False,
            "fallback_target": "",
            "fail_on_error": False,
            "cache_route_function": True,
            "timeout": 10
        }
        
        # 合并元数据配置
        if self._metadata:
            base_config.update(self._metadata)
        
        # 合并传入的配置
        base_config.update(config)
        
        return base_config
    
    def update_route_function(self, route_function: str, route_parameters: Optional[Dict[str, Any]] = None) -> None:
        """更新路由函数配置
        
        Args:
            route_function: 新的路由函数名称
            route_parameters: 新的路由函数参数
        """
        self.route_function = route_function
        if route_parameters is not None:
            self.route_parameters = route_parameters
        
        # 清除缓存
        self._cached_route_function = None
        
        logger.debug(f"更新灵活条件边 {self._edge_id} 路由函数: {route_function}")
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新边元数据
        
        Args:
            metadata: 新的元数据
        """
        if not isinstance(metadata, dict):
            raise ValueError("元数据必须是字典类型")
        
        self._metadata.update(metadata)
        logger.debug(f"更新灵活条件边 {self._edge_id} 元数据: {metadata}")
    
    def get_route_function_info(self) -> Optional[Dict[str, Any]]:
        """获取路由函数信息
        
        Returns:
            Optional[Dict[str, Any]]: 路由函数信息
        """
        if self._function_registry is None:
            return None
        
        try:
            return self._function_registry.get_function_schema("route_function", self.route_function)
        except Exception as e:
            logger.error(f"获取路由函数信息失败: {e}")
            return None
    
    def list_available_route_functions(self) -> List[str]:
        """列出所有可用的路由函数
        
        Returns:
            List[str]: 路由函数名称列表
        """
        if self._function_registry is None:
            return []
        
        return self._function_registry.list_route_functions()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 边的字典表示
        """
        return {
            "edge_id": self._edge_id,
            "edge_type": self.edge_type,
            "from_node": self._from_node,
            "route_function": self.route_function,
            "route_parameters": self.route_parameters,
            "description": self.description,
            "metadata": self._metadata
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"FlexibleConditionalEdge({self._from_node} -> [{self.route_function}])"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        params = f" params={self.route_parameters}" if self.route_parameters else ""
        meta = f" metadata={self._metadata}" if self._metadata else ""
        return f"FlexibleConditionalEdge(edge_id='{self._edge_id}', from_node='{self._from_node}', route_function='{self.route_function}'{params}{desc}{meta})"