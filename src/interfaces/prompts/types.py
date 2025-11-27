"""
提示词类型接口定义

提供插件化的提示词类型系统，支持动态扩展
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum


class PromptType(Enum):
    """提示词类型枚举"""
    SYSTEM = "system"
    RULES = "rules"
    USER_COMMAND = "user_commands"
    CONTEXT = "context"
    EXAMPLES = "examples"
    CONSTRAINTS = "constraints"
    FORMAT = "format"
    CUSTOM = "custom"


class IPromptType(ABC):
    """提示词类型接口"""
    
    @property
    @abstractmethod
    def type_name(self) -> str:
        """类型名称"""
        pass
    
    @property
    @abstractmethod
    def injection_order(self) -> int:
        """注入顺序（数字越小越先注入）"""
        pass
    
    @abstractmethod
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理提示词内容"""
        pass
    
    @abstractmethod
    def create_message(self, content: str) -> Any:
        """创建消息对象"""
        pass
    
    @abstractmethod
    def validate_content(self, content: str) -> List[str]:
        """验证提示词内容"""
        pass


class IPromptTypeRegistry(ABC):
    """提示词类型注册表接口"""
    
    @abstractmethod
    def register(self, prompt_type: IPromptType) -> None:
        """注册提示词类型"""
        pass
    
    @abstractmethod
    def get(self, type_name: str) -> Optional[IPromptType]:
        """获取提示词类型"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[IPromptType]:
        """获取所有提示词类型"""
        pass
    
    @abstractmethod
    def get_sorted_by_injection_order(self) -> List[IPromptType]:
        """按注入顺序排序获取所有类型"""
        pass
    
    @abstractmethod
    def exists(self, type_name: str) -> bool:
        """检查类型是否存在"""
        pass
    
    @abstractmethod
    def register_class(self, type_class: type) -> None:
        """注册提示词类型类"""
        pass
    
    @abstractmethod
    def get_type(self, type_name: str) -> IPromptType:
        """获取提示词类型（同义方法）"""
        pass
    
    @abstractmethod
    def get_type_by_enum(self, prompt_type: PromptType) -> IPromptType:
        """通过枚举获取提示词类型"""
        pass
    
    @abstractmethod
    def list_types(self) -> List[str]:
        """列出所有已注册的类型名称"""
        pass
    
    @abstractmethod
    def is_registered(self, type_name: str) -> bool:
        """检查类型是否已注册（同义方法）"""
        pass
    
    @abstractmethod
    def unregister(self, type_name: str) -> None:
        """注销提示词类型"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有注册的类型"""
        pass
    
    @abstractmethod
    def get_types_by_injection_order(self) -> List[IPromptType]:
        """按注入顺序获取所有类型"""
        pass
    
    @abstractmethod
    def create_instance(self, type_name: str) -> IPromptType:
        """创建提示词类型的新实例"""
        pass


class PromptTypeConfig:
    """提示词类型配置"""
    
    def __init__(
        self,
        type_name: str,
        injection_order: int,
        validation_rules: Optional[Dict[str, Any]] = None,
        default_content: Optional[str] = None,
        supported_formats: Optional[List[str]] = None
    ):
        self.type_name = type_name
        self.injection_order = injection_order
        self.validation_rules = validation_rules or {}
        self.default_content = default_content
        self.supported_formats = supported_formats or ["markdown", "text"]


def create_prompt_type_config(
    type_name: str,
    injection_order: int,
    **kwargs: Any
) -> PromptTypeConfig:
    """创建提示词类型配置"""
    return PromptTypeConfig(type_name, injection_order, **kwargs)


def get_default_prompt_type_configs() -> Dict[str, PromptTypeConfig]:
    """获取默认提示词类型配置"""
    return {
        "system": PromptTypeConfig("system", 10),
        "rules": PromptTypeConfig("rules", 20),
        "user_commands": PromptTypeConfig("user_commands", 30),
        "context": PromptTypeConfig("context", 40),
        "examples": PromptTypeConfig("examples", 50),
        "constraints": PromptTypeConfig("constraints", 60),
        "format": PromptTypeConfig("format", 70)
    }