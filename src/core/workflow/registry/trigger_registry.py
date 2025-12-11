"""触发器注册表

管理触发器的注册、获取和查询功能。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from src.interfaces.dependency_injection import get_logger
from .base_registry import BaseRegistry, TypedRegistry

logger = get_logger(__name__)


@dataclass
class TriggerConfig:
    """触发器配置"""
    name: str
    trigger_type: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_async: bool = False
    category: Optional[str] = None


@dataclass
class RegisteredTrigger:
    """已注册的触发器"""
    name: str
    trigger: Callable
    config: TriggerConfig
    is_builtin: bool = False


class TriggerRegistry(TypedRegistry):
    """触发器注册表
    
    管理触发器的注册、获取和查询。
    """
    
    def __init__(self) -> None:
        """初始化触发器注册表"""
        super().__init__(
            "trigger",
            ["time", "state", "event", "condition", "custom"]
        )
        self._compositions: Dict[str, Dict[str, Any]] = {}
    
    def register_trigger(
        self, 
        name: str, 
        trigger: Callable, 
        config: TriggerConfig,
        is_builtin: bool = False
    ) -> None:
        """注册触发器
        
        Args:
            name: 触发器名称
            trigger: 触发器对象
            config: 触发器配置
            is_builtin: 是否为内置触发器
        """
        registered_trigger = RegisteredTrigger(
            name=name,
            trigger=trigger,
            config=config,
            is_builtin=is_builtin
        )
        
        self.register(name, registered_trigger)
        
        # 按类别分类
        trigger_type = config.trigger_type
        if trigger_type in self._items_by_type:
            self._items_by_type[trigger_type].append(name)
        else:
            self._items_by_type["custom"].append(name)
        
        self._logger.debug(f"注册触发器: {name} (类型: {trigger_type})")
    
    def get_trigger(self, name: str) -> Optional[Callable]:
        """获取触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            Optional[Callable]: 触发器对象，如果不存在返回None
        """
        registered_trigger = self.get(name)
        return registered_trigger.trigger if registered_trigger else None
    
    def get_trigger_config(self, name: str) -> Optional[TriggerConfig]:
        """获取触发器配置
        
        Args:
            name: 触发器名称
            
        Returns:
            Optional[TriggerConfig]: 触发器配置，如果不存在返回None
        """
        registered_trigger = self.get(name)
        return registered_trigger.config if registered_trigger else None
    
    def register_composition(self, name: str, composition_config: Dict[str, Any]) -> None:
        """注册触发器组合配置
        
        Args:
            name: 组合名称
            composition_config: 触发器组合配置
        """
        self._compositions[name] = composition_config
        self._logger.debug(f"注册触发器组合: {name}")
    
    def get_composition(self, name: str) -> Optional[Dict[str, Any]]:
        """获取触发器组合配置
        
        Args:
            name: 组合名称
            
        Returns:
            Optional[Dict[str, Any]]: 触发器组合配置，如果不存在返回None
        """
        return self._compositions.get(name)
    
    def list_triggers(self) -> List[str]:
        """列出所有触发器名称
        
        Returns:
            List[str]: 触发器名称列表
        """
        return self.list_items()
    
    def list_triggers_by_type(self, trigger_type: str) -> List[str]:
        """按类型列出触发器
        
        Args:
            trigger_type: 触发器类型
            
        Returns:
            List[str]: 触发器名称列表
        """
        return self.list_items_by_type(trigger_type)
    
    def list_compositions(self) -> List[str]:
        """列出所有触发器组合
        
        Returns:
            List[str]: 触发器组合名称列表
        """
        return list(self._compositions.keys())
    
    def has_trigger(self, name: str) -> bool:
        """检查是否存在指定名称的触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            bool: 是否存在
        """
        return self.has_item(name)
    
    def has_composition(self, name: str) -> bool:
        """检查是否存在指定名称的触发器组合
        
        Args:
            name: 组合名称
            
        Returns:
            bool: 是否存在
        """
        return name in self._compositions
    
    def unregister_trigger(self, name: str) -> bool:
        """注销触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            bool: 是否成功注销
        """
        registered_trigger = self.get(name)
        if not registered_trigger:
            return False
        
        trigger_type = registered_trigger.config.trigger_type
        
        # 从分类中移除
        if trigger_type in self._items_by_type and name in self._items_by_type[trigger_type]:
            self._items_by_type[trigger_type].remove(name)
        
        # 从主注册表中移除
        self.unregister(name)
        self._logger.debug(f"注销触发器: {name}")
        return True
    
    def unregister_composition(self, name: str) -> bool:
        """注销触发器组合
        
        Args:
            name: 组合名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._compositions:
            del self._compositions[name]
            self._logger.debug(f"注销触发器组合: {name}")
            return True
        return False
    
    def get_trigger_types(self) -> List[str]:
        """获取所有触发器类型
        
        Returns:
            List[str]: 触发器类型列表
        """
        return self.get_type_categories()
    
    def get_builtin_triggers(self) -> List[str]:
        """获取所有内置触发器
        
        Returns:
            List[str]: 内置触发器名称列表
        """
        builtin_triggers = []
        for name in self.list_items():
            registered_trigger = self.get(name)
            if registered_trigger and registered_trigger.is_builtin:
                builtin_triggers.append(name)
        return builtin_triggers
    
    def get_custom_triggers(self) -> List[str]:
        """获取所有自定义触发器
        
        Returns:
            List[str]: 自定义触发器名称列表
        """
        custom_triggers = []
        for name in self.list_items():
            registered_trigger = self.get(name)
            if registered_trigger and not registered_trigger.is_builtin:
                custom_triggers.append(name)
        return custom_triggers
    
    def validate_trigger_config(self, name: str, config: Dict[str, Any]) -> List[str]:
        """验证触发器配置
        
        Args:
            name: 触发器名称
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        registered_trigger = self.get(name)
        
        if not registered_trigger:
            errors.append(f"触发器不存在: {name}")
            return errors
        
        trigger_config = registered_trigger.config
        
        # 验证必需参数
        if trigger_config.parameters:
            required_params = [
                param_name for param_name, param_config in trigger_config.parameters.items()
                if param_config.get("required", False)
            ]
            
            for param in required_params:
                if param not in config:
                    errors.append(f"缺少必需参数: {param}")
        
        # 验证参数类型
        if trigger_config.parameters:
            for param_name, param_value in config.items():
                if param_name in trigger_config.parameters:
                    param_config = trigger_config.parameters[param_name]
                    expected_type = param_config.get("type")
                    
                    if expected_type == "string" and not isinstance(param_value, str):
                        errors.append(f"参数 {param_name} 应为字符串类型")
                    elif expected_type == "integer" and not isinstance(param_value, int):
                        errors.append(f"参数 {param_name} 应为整数类型")
                    elif expected_type == "boolean" and not isinstance(param_value, bool):
                        errors.append(f"参数 {param_name} 应为布尔类型")
                    elif expected_type == "array" and not isinstance(param_value, list):
                        errors.append(f"参数 {param_name} 应为数组类型")
                    elif expected_type == "object" and not isinstance(param_value, dict):
                        errors.append(f"参数 {param_name} 应为对象类型")
        
        return errors
    
    def get_trigger_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取触发器信息
        
        Args:
            name: 触发器名称
            
        Returns:
            Optional[Dict[str, Any]]: 触发器信息，如果不存在返回None
        """
        registered_trigger = self.get(name)
        if not registered_trigger:
            return None
        
        config = registered_trigger.config
        
        return {
            "name": name,
            "type": config.trigger_type,
            "description": config.description,
            "is_builtin": registered_trigger.is_builtin,
            "is_async": config.is_async,
            "category": config.category,
            "parameters": config.parameters,
            "callable": registered_trigger.trigger.__name__ if hasattr(registered_trigger.trigger, '__name__') else str(registered_trigger.trigger)
        }
    
    def clear(self, trigger_type: Optional[str] = None) -> None:
        """清除触发器
        
        Args:
            trigger_type: 要清除的触发器类型，如果为None则清除所有
        """
        if trigger_type is None:
            # 清除所有触发器
            super().clear()
            self._compositions.clear()
            self._logger.debug("清除所有触发器和组合")
        else:
            # 清除指定类型的触发器
            trigger_names = self.list_items_by_type(trigger_type).copy()
            for name in trigger_names:
                self.unregister_trigger(name)
            self._logger.debug(f"清除所有 {trigger_type} 类型的触发器")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = super().get_stats()
        stats.update({
            "total_triggers": len(self._items),
            "total_compositions": len(self._compositions),
            "builtin_triggers": len(self.get_builtin_triggers()),
            "custom_triggers": len(self.get_custom_triggers()),
            "trigger_types": self.get_trigger_types()
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
        
        if not isinstance(item, RegisteredTrigger):
            raise ValueError("项目必须是 RegisteredTrigger 实例")
        
        if not callable(item.trigger):
            raise ValueError("触发器必须是可调用对象")
        
        if not isinstance(item.config, TriggerConfig):
            raise ValueError("触发器必须具有有效的 TriggerConfig")
        
        if not item.config.name or not isinstance(item.config.name, str):
            raise ValueError("触发器配置必须具有有效的名称")
        
        if not item.config.trigger_type or not isinstance(item.config.trigger_type, str):
            raise ValueError("触发器配置必须具有有效的类型")