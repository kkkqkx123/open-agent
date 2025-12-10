"""配置实现基类

定义配置实现的基础接口和抽象类，提供配置加载、处理和转换的通用框架。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from src.interfaces.config import IConfigLoader, IConfigProcessor, ValidationResult
from src.interfaces.common_domain import ValidationResult as CommonValidationResult

logger = logging.getLogger(__name__)


class IConfigImpl(ABC):
    """配置实现接口"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> CommonValidationResult:
        """验证配置数据
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换配置为模块特定格式
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        pass


class IConfigSchema(ABC):
    """配置模式接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> CommonValidationResult:
        """验证配置"""
        pass


class IConfigProcessorChain(ABC):
    """配置处理器链接口"""
    
    @abstractmethod
    def add_processor(self, processor: IConfigProcessor) -> None:
        """添加处理器"""
        pass
    
    @abstractmethod
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """应用处理器链"""
        pass
    
    @abstractmethod
    def get_processors(self) -> list[IConfigProcessor]:
        """获取处理器列表"""
        pass


class BaseConfigImpl(IConfigImpl):
    """配置实现基类
    
    提供配置加载、处理和转换的通用流程。
    """
    
    def __init__(self,
                 module_type: str,
                 config_loader: IConfigLoader,
                 processor_chain: 'IConfigProcessorChain',
                 schema: 'IConfigSchema'):
        """初始化配置实现
        
        Args:
            module_type: 模块类型
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        self.module_type = module_type
        self.config_loader = config_loader
        self.processor_chain = processor_chain
        self.schema = schema
        self._base_path = Path("configs")
        
        logger.debug(f"初始化{module_type}模块配置实现")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置的通用流程
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        logger.debug(f"开始加载{self.module_type}模块配置: {config_path}")
        
        try:
            # 1. 加载原始配置
            logger.debug(f"加载原始配置文件: {config_path}")
            raw_config = self.config_loader.load(config_path)
            
            # 2. 应用处理器链
            logger.debug(f"应用处理器链处理配置")
            processed_config = self.processor_chain.process(raw_config, config_path)
            
            # 3. 验证配置
            logger.debug(f"验证配置数据")
            validation_result = self.validate_config(processed_config)
            
            if not validation_result.is_valid:
                error_msg = f"{self.module_type}模块配置验证失败: " + "; ".join(validation_result.errors)
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 4. 转换为模块特定格式
            logger.debug(f"转换为{self.module_type}模块特定格式")
            final_config = self.transform_config(processed_config)
            
            logger.info(f"{self.module_type}模块配置加载成功: {config_path}")
            return final_config
            
        except Exception as e:
            logger.error(f"加载{self.module_type}模块配置失败: {e}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> CommonValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        if self.schema:
            return self.schema.validate(config)
        
        # 如果没有模式，返回成功
        return CommonValidationResult(is_valid=True, errors=[], warnings=[])
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为模块特定格式
        
        子类应该重写此方法以实现模块特定的转换逻辑。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        # 默认实现：不做转换
        return config
    
    def set_base_path(self, base_path: Path) -> None:
        """设置配置基础路径
        
        Args:
            base_path: 基础路径
        """
        self._base_path = base_path
        # Note: base_path is a read-only property on IConfigLoader, cannot be set directly
        # The config_loader must handle base_path internally or through initialization
    
    def get_config_path(self, config_name: str) -> str:
        """获取配置文件完整路径
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置文件路径
        """
        # 构建模块特定的配置路径
        module_path = self._base_path / self.module_type / config_name
        
        # 如果没有扩展名，添加.yaml
        if not module_path.suffix:
            module_path = module_path.with_suffix('.yaml')
        
        return str(module_path)
    
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            重新加载的配置数据
        """
        logger.info(f"重新加载{self.module_type}模块配置: {config_path}")
        return self.load_config(config_path)
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            当前配置数据
        """
        # 获取默认配置路径
        config_name = f"{self.module_type}"
        config_path = self.get_config_path(config_name)
        return self.load_config(config_path)


class ConfigProcessorChain(IConfigProcessorChain):
    """配置处理器链实现"""
    
    def __init__(self):
        self._processors: list[IConfigProcessor] = []
    
    def add_processor(self, processor: IConfigProcessor) -> None:
        """添加处理器
        
        Args:
            processor: 配置处理器
        """
        self._processors.append(processor)
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """应用处理器链
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        result = config
        
        for i, processor in enumerate(self._processors):
            logger.debug(f"应用处理器 {i+1}/{len(self._processors)}: {processor.__class__.__name__}")
            result = processor.process(result, config_path)
        
        return result
    
    def get_processors(self) -> list[IConfigProcessor]:
        """获取处理器列表
        
        Returns:
            处理器列表
        """
        return self._processors.copy()


class ConfigSchema(IConfigSchema):
    """配置模式基类实现"""
    
    def __init__(self, schema_definition: Optional[Dict[str, Any]] = None):
        """初始化配置模式
        
        Args:
            schema_definition: 模式定义
        """
        self.schema_definition = schema_definition or {}
    
    def validate(self, config: Dict[str, Any]) -> CommonValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        # 基础验证逻辑
        errors = []
        
        # 检查必需字段
        required_fields = self.schema_definition.get("required", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        properties = self.schema_definition.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in config:
                field_value = config[field_name]
                expected_type = field_schema.get("type")
                
                if expected_type and not self._check_type(field_value, expected_type):
                    errors.append(f"字段 {field_name} 类型错误，期望 {expected_type}")
        
        return CommonValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值类型
        
        Args:
            value: 值
            expected_type: 期望类型
            
        Returns:
            类型是否匹配
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # 未知类型，默认通过