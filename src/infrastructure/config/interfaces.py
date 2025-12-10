"""Infrastructure层配置接口定义

定义Infrastructure层内部各组件间的接口，实现依赖倒置。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IConfigSchema(ABC):
    """配置模式接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> 'ValidationResult':
        """验证配置"""
        pass


class ISchemaRegistry(ABC):
    """模式注册表接口"""
    
    @abstractmethod
    def register_schema(self, config_type: str, schema: IConfigSchema) -> None:
        """注册模式"""
        pass
    
    @abstractmethod
    def get_schema(self, config_type: str) -> Optional[IConfigSchema]:
        """获取模式"""
        pass
    
    @abstractmethod
    def has_schema(self, config_type: str) -> bool:
        """检查是否存在模式"""
        pass


class IConfigProcessorChain(ABC):
    """配置处理器链接口"""
    
    @abstractmethod
    def add_processor(self, processor: 'IConfigProcessor') -> None:
        """添加处理器"""
        pass
    
    @abstractmethod
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """应用处理器链"""
        pass
    
    @abstractmethod
    def get_processors(self) -> List['IConfigProcessor']:
        """获取处理器列表"""
        pass


class ITypeConverter(ABC):
    """类型转换器接口"""
    
    @abstractmethod
    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换配置数据类型"""
        pass
    
    @abstractmethod
    def convert_to_type(self, value: Any, target_type: str) -> Any:
        """转换到指定类型"""
        pass


class ValidationResult:
    """验证结果"""
    
    def __init__(self, is_valid: bool, errors: List[str]):
        self.is_valid = is_valid
        self.errors = errors