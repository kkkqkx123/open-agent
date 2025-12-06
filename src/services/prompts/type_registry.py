"""
提示词类型注册表

提供提示词类型的注册、发现和管理功能
"""

from typing import Dict, Type, List, Optional as OptionalType
from src.interfaces.prompts.types import IPromptType, PromptType
from src.interfaces.prompts import IPromptTypeRegistry
from src.interfaces.prompts.exceptions import PromptTypeNotFoundError, PromptTypeRegistrationError


class PromptTypeRegistry(IPromptTypeRegistry):
    """提示词类型注册表实现"""
    
    def __init__(self) -> None:
        self._types: Dict[str, IPromptType] = {}
        self._type_classes: Dict[str, Type[IPromptType]] = {}
    
    def register(self, prompt_type: IPromptType) -> None:
        """注册提示词类型"""
        type_name = prompt_type.type_name
        
        if type_name in self._types:
            raise PromptTypeRegistrationError(f"提示词类型 '{type_name}' 已注册")
        
        self._types[type_name] = prompt_type
        self._type_classes[type_name] = type(prompt_type)
    
    def register_class(self, type_class: Type[IPromptType]) -> None:
        """注册提示词类型类"""
        try:
            instance = type_class()
            self.register(instance)
        except Exception as e:
            raise PromptTypeRegistrationError(f"注册提示词类型类失败: {e}")
    
    def get_type(self, type_name: str) -> IPromptType:
        """获取提示词类型"""
        if type_name not in self._types:
            raise PromptTypeNotFoundError(f"提示词类型 '{type_name}' 未找到")
        
        return self._types[type_name]
    
    def get_type_by_enum(self, prompt_type: PromptType) -> IPromptType:
        """通过枚举获取提示词类型"""
        return self.get_type(prompt_type.value)
    
    def list_types(self) -> List[str]:
        """列出所有已注册的类型名称"""
        return list(self._types.keys())
    
    def is_registered(self, type_name: str) -> bool:
        """检查类型是否已注册"""
        return type_name in self._types
    
    def unregister(self, type_name: str) -> None:
        """注销提示词类型"""
        if type_name not in self._types:
            raise PromptTypeNotFoundError(f"提示词类型 '{type_name}' 未找到")
        
        del self._types[type_name]
        del self._type_classes[type_name]
    
    def clear(self) -> None:
        """清空所有注册的类型"""
        self._types.clear()
        self._type_classes.clear()
    
    def get_types_by_injection_order(self) -> List[IPromptType]:
        """按注入顺序获取所有类型"""
        return sorted(self._types.values(), key=lambda t: t.injection_order)
    
    def create_instance(self, type_name: str) -> IPromptType:
        """创建提示词类型的新实例"""
        if type_name not in self._type_classes:
            raise PromptTypeNotFoundError(f"提示词类型 '{type_name}' 未找到")
        
        type_class = self._type_classes[type_name]
        return type_class()
    
    def get(self, type_name: str) -> OptionalType[IPromptType]:
        """获取提示词类型（实现接口）"""
        return self._types.get(type_name)
    
    def get_all(self) -> List[IPromptType]:
        """获取所有提示词类型（实现接口）"""
        return list(self._types.values())
    
    def get_sorted_by_injection_order(self) -> List[IPromptType]:
        """按注入顺序排序获取所有类型（实现接口）"""
        return self.get_types_by_injection_order()
    
    def exists(self, type_name: str) -> bool:
        """检查类型是否存在（实现接口）"""
        return self.is_registered(type_name)


# 全局注册表实例
_global_registry: OptionalType[PromptTypeRegistry] = None


def get_global_registry() -> PromptTypeRegistry:
    """获取全局注册表实例"""
    global _global_registry
    if _global_registry is None:
        _global_registry = PromptTypeRegistry()
        _register_default_types(_global_registry)
    return _global_registry


def _register_default_types(registry: PromptTypeRegistry) -> None:
    """注册默认的提示词类型"""
    try:
        from ...core.prompts.types.system_prompt import SystemPromptType
        from ...core.prompts.types.rules_prompt import RulesPromptType
        from ...core.prompts.types.user_command_prompt import UserCommandPromptType
        
        # 注册核心提示词类型（使用默认的消息工厂）
        registry.register(SystemPromptType())
        registry.register(RulesPromptType())
        registry.register(UserCommandPromptType())
    except ImportError as e:
        # 如果导入失败，记录警告但不中断程序
        import warnings
        warnings.warn(f"无法导入提示词类型: {e}")