"""配置验证处理器

提供统一的配置验证功能，支持基于模式的验证和自定义验证规则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
import logging
from pathlib import Path

from .base_processor import BaseConfigProcessor
from src.interfaces.config import ValidationResult, IConfigSchema, ISchemaRegistry
from src.interfaces.config.schema import ISchemaGenerator

if TYPE_CHECKING:
    from src.interfaces.config import IConfigSchema, ISchemaRegistry

logger = logging.getLogger(__name__)


class ValidationProcessor(BaseConfigProcessor):
    """配置验证处理器
    
    提供基于模式的配置验证功能。
    """
    
    def __init__(self, schema_registry: Optional[ISchemaRegistry] = None):
        """初始化验证处理器
        
        Args:
            schema_registry: 模式注册表
        """
        super().__init__("validation")
        self.schema_registry = schema_registry
        self.custom_validators: Dict[str, List[Callable]] = {}
    
    def register_validator(self, config_type: str, validator: Callable[[Dict[str, Any]], List[str]]) -> None:
        """注册自定义验证器
        
        Args:
            config_type: 配置类型
            validator: 验证函数
        """
        if config_type not in self.custom_validators:
            self.custom_validators[config_type] = []
        self.custom_validators[config_type].append(validator)
        logger.debug(f"注册{config_type}配置的自定义验证器")
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """内部验证逻辑
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            验证后的配置数据
        """
        errors = []
        warnings = []
        
        # 1. 基于模式的验证
        if self.schema_registry:
            schema_errors, schema_warnings = self._validate_with_schema(config, config_path)
            errors.extend(schema_errors)
            warnings.extend(schema_warnings)
        
        # 2. 自定义验证
        custom_errors, custom_warnings = self._validate_with_custom_rules(config, config_path)
        errors.extend(custom_errors)
        warnings.extend(custom_warnings)
        
        # 3. 基础验证
        basic_errors, basic_warnings = self._validate_basic(config, config_path)
        errors.extend(basic_errors)
        warnings.extend(basic_warnings)
        
        # 记录警告
        for warning in warnings:
            logger.warning(f"配置验证警告 ({config_path}): {warning}")
        
        # 如果有错误，抛出异常
        if errors:
            error_msg = f"配置验证失败 ({config_path}): " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"配置验证通过: {config_path}")
        return config
    
    def _validate_with_schema(self, config: Dict[str, Any], config_path: str) -> tuple[List[str], List[str]]:
        """基于模式验证
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        try:
            # 根据配置路径确定配置类型
            config_type = self._determine_config_type(config_path)
            
            # 获取相应的模式
            if self.schema_registry:
                schema = self.schema_registry.get_schema(config_type)
            else:
                schema = None
            
            if schema:
                result = schema.validate(config)
                if not result.is_valid:
                    errors.extend(result.errors)
            else:
                warnings.append(f"未找到{config_type}配置的模式定义")
                
        except Exception as e:
            errors.append(f"模式验证失败: {e}")
        
        return errors, warnings
    
    def _validate_with_custom_rules(self, config: Dict[str, Any], config_path: str) -> tuple[List[str], List[str]]:
        """自定义验证规则验证
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            错误列表和警告列表
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        try:
            # 根据配置路径确定配置类型
            config_type = self._determine_config_type(config_path)
            
            # 获取自定义验证器
            validators = self.custom_validators.get(config_type, [])
            
            # 执行自定义验证
            for validator in validators:
                try:
                    validator_errors = validator(config)
                    errors.extend(validator_errors)
                except Exception as e:
                    errors.append(f"自定义验证器执行失败: {e}")
                    
        except Exception as e:
            errors.append(f"自定义验证失败: {e}")
        
        return errors, warnings
    
    def _validate_basic(self, config: Dict[str, Any], config_path: str) -> tuple[List[str], List[str]]:
        """基础验证
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            错误列表和警告列表
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # 检查配置是否为字典
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return errors, warnings
        
        # 检查空配置
        if not config:
            warnings.append("配置为空")
        
        # 检查配置文件路径
        try:
            path = Path(config_path)
            if not path.exists():
                warnings.append(f"配置文件不存在: {config_path}")
        except Exception as e:
            warnings.append(f"配置文件路径检查失败: {e}")
        
        return errors, warnings
    
    def _determine_config_type(self, config_path: str) -> str:
        """确定配置类型
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置类型
        """
        path = Path(config_path)
        
        # 根据路径确定配置类型
        parts = path.parts
        
        if "llm" in parts or "llms" in parts:
            return "llm"
        elif "workflow" in parts or "workflows" in parts:
            return "workflow"
        elif "tool" in parts or "tools" in parts:
            return "tools"
        elif "state" in parts:
            return "state"
        elif "session" in parts or "sessions" in parts:
            return "session"
        else:
            return "general"


class SchemaRegistry(ISchemaRegistry):
    """模式注册表实现
    
    管理所有配置模式定义的具体实现，支持Schema生成器。
    """
    
    def __init__(self) -> None:
        """初始化模式注册表"""
        self._schemas: Dict[str, IConfigSchema] = {}
        self._schema_generators: Dict[str, 'ISchemaGenerator'] = {}
        logger.debug("初始化模式注册表")
    
    def register_schema(self, config_type: str, schema: IConfigSchema) -> None:
        """注册模式
        
        Args:
            config_type: 配置类型
            schema: 配置模式
        """
        self._schemas[config_type] = schema
        logger.debug(f"注册{config_type}配置模式")
    
    def get_schema(self, config_type: str) -> Optional[IConfigSchema]:
        """获取模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            配置模式
        """
        return self._schemas.get(config_type)
    
    def has_schema(self, config_type: str) -> bool:
        """检查是否存在模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            是否存在模式
        """
        return config_type in self._schemas
    
    def get_registered_types(self) -> List[str]:
        """获取已注册的配置类型
        
        Returns:
            配置类型列表
        """
        return list(self._schemas.keys())
    
    def unregister_schema(self, config_type: str) -> bool:
        """注销模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            是否成功注销
        """
        if config_type in self._schemas:
            del self._schemas[config_type]
            logger.debug(f"注销{config_type}配置模式")
            return True
        return False
    
    def register_schema_generator(self, generator_type: str, generator: ISchemaGenerator) -> None:
        """注册Schema生成器
        
        Args:
            generator_type: 生成器类型
            generator: Schema生成器实例
        """
        self._schema_generators[generator_type] = generator
        logger.debug(f"注册{generator_type} Schema生成器")
    
    def get_schema_generator(self, generator_type: str) -> Optional[ISchemaGenerator]:
        """获取Schema生成器
        
        Args:
            generator_type: 生成器类型
            
        Returns:
            Optional[ISchemaGenerator]: Schema生成器实例，如果不存在则返回None
        """
        return self._schema_generators.get(generator_type)
    
    def has_schema_generator(self, generator_type: str) -> bool:
        """检查是否存在Schema生成器
        
        Args:
            generator_type: 生成器类型
            
        Returns:
            bool: 是否存在
        """
        return generator_type in self._schema_generators
    
    def get_registered_generator_types(self) -> List[str]:
        """获取已注册的生成器类型
        
        Returns:
            List[str]: 生成器类型列表
        """
        return list(self._schema_generators.keys())
    
    def unregister_schema_generator(self, generator_type: str) -> bool:
        """注销Schema生成器
        
        Args:
            generator_type: 生成器类型
            
        Returns:
            bool: 是否成功注销
        """
        if generator_type in self._schema_generators:
            del self._schema_generators[generator_type]
            logger.debug(f"注销{generator_type} Schema生成器")
            return True
        return False
    
    def generate_schema(self, generator_type: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用指定的生成器生成Schema
        
        Args:
            generator_type: 生成器类型
            config_data: 配置数据
            
        Returns:
            Dict[str, Any]: 生成的JSON Schema
            
        Raises:
            ValueError: 如果找不到指定的生成器
        """
        generator = self.get_schema_generator(generator_type)
        if not generator:
            raise ValueError(f"未找到{generator_type}类型的Schema生成器")
        
        return generator.generate_schema_from_config(config_data)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "schema_count": len(self._schemas),
            "generator_count": len(self._schema_generators),
            "registered_schemas": list(self._schemas.keys()),
            "registered_generators": list(self._schema_generators.keys())
        }