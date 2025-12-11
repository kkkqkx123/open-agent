"""配置模式相关接口定义

提供配置验证模式的接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..common_domain import IValidationResult


class IConfigSchema(ABC):
    """配置模式接口
    
    定义配置验证模式的基本契约。
    """
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            IValidationResult: 验证结果
        """
        pass
    
    @abstractmethod
    def get_schema_type(self) -> str:
        """获取模式类型
        
        Returns:
            str: 模式类型
        """
        pass


class ISchemaRegistry(ABC):
    """模式注册表接口
    
    管理所有配置模式定义的接口。
    """
    
    @abstractmethod
    def register_schema(self, config_type: str, schema: IConfigSchema) -> None:
        """注册模式
        
        Args:
            config_type: 配置类型
            schema: 配置模式
        """
        pass
    
    @abstractmethod
    def get_schema(self, config_type: str) -> Optional[IConfigSchema]:
        """获取模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            Optional[IConfigSchema]: 配置模式，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def has_schema(self, config_type: str) -> bool:
        """检查是否存在模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            bool: 是否存在模式
        """
        pass
    
    @abstractmethod
    def get_registered_types(self) -> List[str]:
        """获取已注册的配置类型
        
        Returns:
            List[str]: 配置类型列表
        """
        pass
    
    @abstractmethod
    def unregister_schema(self, config_type: str) -> bool:
        """注销模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            bool: 是否成功注销
        """
        pass


class ISchemaGenerator(ABC):
    """Schema生成器接口
    
    定义从配置数据生成JSON Schema的基本契约。
    """
    
    @abstractmethod
    def generate_schema_from_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """从配置数据生成Schema
        
        Args:
            config_data: 配置数据
            
        Returns:
            Dict[str, Any]: JSON Schema
        """
        pass
    
    @abstractmethod
    def generate_schema_from_type(self, config_type: str) -> Dict[str, Any]:
        """从配置类型生成Schema
        
        Args:
            config_type: 配置类型
            
        Returns:
            Dict[str, Any]: JSON Schema
        """
        pass
    
    @abstractmethod
    def get_generator_type(self) -> str:
        """获取生成器类型
        
        Returns:
            str: 生成器类型
        """
        pass
