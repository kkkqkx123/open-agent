"""节点注册表

管理节点类型和节点实例的注册、获取和管理功能。
"""

from abc import abstractmethod
from typing import Dict, Any, List, Type, Optional
from src.interfaces.state.base import IState
from src.interfaces.workflow.graph import NodeExecutionResult
from .base_registry import BaseRegistry


class BaseNode:
    """节点基类"""
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """节点类型标识"""
        pass
    
    @abstractmethod
    def execute(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑
        
        Args:
            state: 当前工作流状态
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
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置
        
        Args:
            config: 节点配置
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        schema = self.get_config_schema()
        
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
                if expected_type == "string" and not isinstance(config[field_name], str):
                    errors.append(f"字段 {field_name} 应为字符串类型")
                elif expected_type == "integer" and not isinstance(config[field_name], int):
                    errors.append(f"字段 {field_name} 应为整数类型")
                elif expected_type == "boolean" and not isinstance(config[field_name], bool):
                    errors.append(f"字段 {field_name} 应为布尔类型")
                elif expected_type == "array" and not isinstance(config[field_name], list):
                    errors.append(f"字段 {field_name} 应为数组类型")
                elif expected_type == "object" and not isinstance(config[field_name], dict):
                    errors.append(f"字段 {field_name} 应为对象类型")
        
        return errors
    
    def merge_configs(self, runtime_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和运行时配置
        
        Args:
            runtime_config: 运行时配置
            
        Returns:
            合并后的配置
        """
        # TODO: 修复 node_config_loader 模块缺失问题
        # from src.core.workflow.config.node_config_loader import get_node_config_loader
        
        # 获取节点配置加载器
        # config_loader = get_node_config_loader()
        
        # 如果配置加载器不可用，直接返回运行时配置
        # if config_loader is None:
        return runtime_config
        
        # 获取默认配置并合并
        # return config_loader.merge_configs(self.node_type, runtime_config)


class NodeRegistry(BaseRegistry):
    """节点注册表
    
    管理节点类型和节点实例的注册、获取和管理。
    """
    
    def __init__(self):
        """初始化节点注册表"""
        super().__init__("node")
        self._node_classes: Dict[str, Type[BaseNode]] = {}
        self._node_instances: Dict[str, BaseNode] = {}
    
    def register_node_class(self, node_class: Type[BaseNode]) -> None:
        """注册节点类型
        
        Args:
            node_class: 节点类
            
        Raises:
            ValueError: 节点类无效或节点类型已存在
        """
        if node_class is None:
            raise ValueError("节点类不能为None")
        
        # 获取节点类型
        node_type = self._extract_node_type(node_class)
        
        if node_type in self._node_classes:
            self._logger.warning(f"节点类型 '{node_type}' 已存在，将被覆盖")
        
        self._node_classes[node_type] = node_class
        self._logger.debug(f"注册节点类型: {node_type} -> {node_class.__name__}")
    
    def register_node_instance(self, node: BaseNode) -> None:
        """注册节点实例
        
        Args:
            node: 节点实例
            
        Raises:
            ValueError: 节点实例无效或节点类型已存在
        """
        if node is None:
            raise ValueError("节点实例不能为None")
        
        node_type = node.node_type
        
        if node_type in self._node_instances:
            self._logger.warning(f"节点实例 '{node_type}' 已存在，将被覆盖")
        
        self._node_instances[node_type] = node
        self._logger.debug(f"注册节点实例: {node_type}")
    
    def get_node_class(self, node_type: str) -> Optional[Type[BaseNode]]:
        """获取节点类型
        
        Args:
            node_type: 节点类型
            
        Returns:
            Optional[Type[BaseNode]]: 节点类，如果不存在返回None
        """
        return self._node_classes.get(node_type)
    
    def get_node_instance(self, node_type: str) -> Optional[BaseNode]:
        """获取节点实例
        
        Args:
            node_type: 节点类型
            
        Returns:
            Optional[BaseNode]: 节点实例，如果不存在返回None
        """
        # 优先返回已注册的实例
        if node_type in self._node_instances:
            return self._node_instances[node_type]
        
        # 如果没有实例，尝试创建新实例
        node_class = self.get_node_class(node_type)
        if node_class is None:
            return None
        
        try:
            return node_class()
        except Exception as e:
            self._logger.error(f"创建节点实例失败 '{node_type}': {e}")
            return None
    
    def list_node_types(self) -> List[str]:
        """列出所有注册的节点类型
        
        Returns:
            List[str]: 节点类型列表
        """
        # 合并节点类和节点实例的类型
        all_types = set(self._node_classes.keys())
        all_types.update(self._node_instances.keys())
        return list(all_types)
    
    def get_node_schema(self, node_type: str) -> Optional[Dict[str, Any]]:
        """获取节点配置Schema
        
        Args:
            node_type: 节点类型
            
        Returns:
            Optional[Dict[str, Any]]: 配置Schema，如果不存在返回None
        """
        node = self.get_node_instance(node_type)
        if node is None:
            return None
        return node.get_config_schema()
    
    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """验证节点配置
        
        Args:
            node_type: 节点类型
            config: 节点配置
            
        Returns:
            List[str]: 验证错误列表
        """
        try:
            node = self.get_node_instance(node_type)
            if node is None:
                return [f"节点类型不存在: {node_type}"]
            return node.validate_config(config)
        except Exception as e:
            return [f"验证节点配置失败: {e}"]
    
    def unregister_node_class(self, node_type: str) -> bool:
        """注销节点类型
        
        Args:
            node_type: 节点类型
            
        Returns:
            bool: 是否成功注销
        """
        if node_type in self._node_classes:
            del self._node_classes[node_type]
            self._logger.debug(f"注销节点类型: {node_type}")
            return True
        return False
    
    def unregister_node_instance(self, node_type: str) -> bool:
        """注销节点实例
        
        Args:
            node_type: 节点类型
            
        Returns:
            bool: 是否成功注销
        """
        if node_type in self._node_instances:
            del self._node_instances[node_type]
            self._logger.debug(f"注销节点实例: {node_type}")
            return True
        return False
    
    def clear(self) -> None:
        """清除所有注册的节点"""
        self._node_classes.clear()
        self._node_instances.clear()
        super().clear()
        self._logger.debug("清除所有节点注册")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = super().get_stats()
        stats.update({
            "node_classes": len(self._node_classes),
            "node_instances": len(self._node_instances),
            "registered_types": self.list_node_types()
        })
        return stats
    
    def validate_item(self, name: str, item: Any) -> None:
        """验证项目
        
        Args:
            name: 项目名称
            item: 项目对象
            
        Raises:
            ValueError: 项目验证失败
        """
        super().validate_item(name, item)
        
        if not (isinstance(item, type) and issubclass(item, BaseNode)) and not isinstance(item, BaseNode):
            raise ValueError(f"项目必须是节点类或节点实例: {type(item)}")
    
    def _extract_node_type(self, node_class: Type[BaseNode]) -> str:
        """提取节点类型
        
        Args:
            node_class: 节点类
            
        Returns:
            str: 节点类型
            
        Raises:
            ValueError: 无法提取节点类型
        """
        try:
            # 尝试创建临时实例来获取 node_type 属性值
            temp_instance = node_class()
            return temp_instance.node_type
        except TypeError as e:
            # 如果是因为缺少必需参数而失败，尝试从类属性获取
            if "missing" in str(e) and "required positional argument" in str(e):
                # 检查是否有装饰器设置的节点类型
                if hasattr(node_class, '_decorator_node_type'):
                    return getattr(node_class, '_decorator_node_type')
                # 检查是否有 node_type 属性
                elif hasattr(node_class, 'node_type'):
                    return getattr(node_class, 'node_type')
                else:
                    raise ValueError(f"节点类 {node_class.__name__} 需要依赖项，但无法确定节点类型")
            else:
                raise ValueError(f"获取节点类型失败: {e}")
        except AttributeError as e:
            raise ValueError(f"节点类缺少 node_type 属性: {e}")
        except Exception as e:
            raise ValueError(f"获取节点类型失败: {e}")


# 装饰器版本，用于自动注册节点
def node(node_type: str):
    """节点注册装饰器
    
    Args:
        node_type: 节点类型
        
    Returns:
        装饰器函数
    """
    def decorator(node_class: Type[BaseNode]) -> Type[BaseNode]:
        # 创建一个新的类，覆盖 node_type 属性
        class WrappedNode(node_class):
            @property
            def node_type(self) -> str:
                return node_type
            
            # 传递所有构造函数参数到原始类
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        
        # 保持原始类的名称和文档
        WrappedNode.__name__ = node_class.__name__
        WrappedNode.__qualname__ = node_class.__qualname__
        if hasattr(node_class, '__doc__'):
            WrappedNode.__doc__ = node_class.__doc__
        
        # 为包装类添加 node_type 属性，以便注册系统能够获取
        setattr(WrappedNode, '_decorator_node_type', node_type)
        
        return WrappedNode
    
    return decorator