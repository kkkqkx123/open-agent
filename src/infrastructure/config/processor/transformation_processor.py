"""配置转换处理器

提供配置数据的类型转换和格式转换功能。
"""

from typing import Dict, Any, Optional, List, Callable
import logging
from pathlib import Path

from .base_processor import BaseConfigProcessor

logger = logging.getLogger(__name__)


class TransformationProcessor(BaseConfigProcessor):
    """配置转换处理器
    
    提供配置数据的类型转换和格式转换功能。
    """
    
    def __init__(self, type_converter: Optional['TypeConverter'] = None):
        """初始化转换处理器
        
        Args:
            type_converter: 类型转换器
        """
        super().__init__("transformation")
        self.type_converter = type_converter or TypeConverter()
        self.transformers: Dict[str, List[Callable]] = {}
    
    def register_transformer(self, config_type: str, transformer: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """注册转换器
        
        Args:
            config_type: 配置类型
            transformer: 转换函数
        """
        if config_type not in self.transformers:
            self.transformers[config_type] = []
        self.transformers[config_type].append(transformer)
        logger.debug(f"注册{config_type}配置的转换器")
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """内部转换逻辑
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            转换后的配置数据
        """
        # 1. 类型转换
        config = self._convert_types(config)
        
        # 2. 自定义转换
        config = self._apply_custom_transformers(config, config_path)
        
        # 3. 标准化转换
        config = self._normalize_config(config)
        
        logger.debug(f"配置转换完成: {config_path}")
        return config
    
    def _convert_types(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """类型转换
        
        Args:
            config: 配置数据
            
        Returns:
            类型转换后的配置数据
        """
        return self.type_converter.convert(config)
    
    def _apply_custom_transformers(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """应用自定义转换器
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            转换后的配置数据
        """
        # 根据配置路径确定配置类型
        config_type = self._determine_config_type(config_path)
        
        # 获取自定义转换器
        transformers = self.transformers.get(config_type, [])
        
        # 应用转换器
        for transformer in transformers:
            try:
                config = transformer(config)
            except Exception as e:
                logger.warning(f"转换器执行失败: {e}")
        
        return config
    
    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化配置
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 移除空值
        config = self._remove_empty_values(config)
        
        # 标准化键名
        config = self._normalize_keys(config)
        
        # 标准化值
        config = self._normalize_values(config)
        
        return config
    
    def _remove_empty_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """移除空值
        
        Args:
            config: 配置数据
            
        Returns:
            移除空值后的配置数据
        """
        result = {}
        
        for key, value in config.items():
            if isinstance(value, dict):
                nested = self._remove_empty_values(value)
                if nested:  # 只保留非空字典
                    result[key] = nested
            elif isinstance(value, list):
                filtered = [item for item in value if item is not None and item != ""]
                if filtered:  # 只保留非空列表
                    result[key] = filtered
            elif value is not None and value != "":
                result[key] = value
        
        return result
    
    def _normalize_keys(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化键名
        
        Args:
            config: 配置数据
            
        Returns:
            标准化键名后的配置数据
        """
        result = {}
        
        for key, value in config.items():
            # 转换为下划线命名
            normalized_key = self._to_snake_case(key)
            
            if isinstance(value, dict):
                result[normalized_key] = self._normalize_keys(value)
            else:
                result[normalized_key] = value
        
        return result
    
    def _normalize_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化值
        
        Args:
            config: 配置数据
            
        Returns:
            标准化值后的配置数据
        """
        result = {}
        
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._normalize_values(value)
            elif isinstance(value, list):
                result[key] = [self._normalize_value(item) for item in value]
            else:
                result[key] = self._normalize_value(value)
        
        return result
    
    def _normalize_value(self, value: Any) -> Any:
        """标准化单个值
        
        Args:
            value: 值
            
        Returns:
            标准化后的值
        """
        if isinstance(value, str):
            # 去除首尾空白
            value = value.strip()
            
            # 转换布尔值字符串
            if value.lower() in ("true", "yes", "1"):
                return True
            elif value.lower() in ("false", "no", "0"):
                return False
        
        return value
    
    def _to_snake_case(self, name: str) -> str:
        """转换为下划线命名
        
        Args:
            name: 原始名称
            
        Returns:
            下划线命名
        """
        # 将驼峰命名转换为下划线命名
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
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


class TypeConverter:
    """类型转换器
    
    提供配置数据的类型转换功能。
    """
    
    def __init__(self):
        """初始化类型转换器"""
        self.type_mappings = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "object": dict,
            "array": list
        }
        
        # 自定义转换器
        self.custom_converters: Dict[str, Callable] = {}
    
    def register_converter(self, type_name: str, converter: Callable) -> None:
        """注册自定义转换器
        
        Args:
            type_name: 类型名称
            converter: 转换函数
        """
        self.custom_converters[type_name] = converter
        logger.debug(f"注册自定义转换器: {type_name}")
    
    def convert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换配置数据类型
        
        Args:
            config: 配置数据
            
        Returns:
            转换后的配置数据
        """
        return self._convert_recursive(config)
    
    def _convert_recursive(self, data: Any) -> Any:
        """递归转换数据
        
        Args:
            data: 数据
            
        Returns:
            转换后的数据
        """
        if isinstance(data, dict):
            return {key: self._convert_recursive(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_recursive(item) for item in data]
        else:
            return self._convert_value(data)
    
    def _convert_value(self, value: Any) -> Any:
        """转换单个值
        
        Args:
            value: 值
            
        Returns:
            转换后的值
        """
        # 如果已经是基本类型，直接返回
        if isinstance(value, (str, int, float, bool, type(None))):
            return self._convert_basic_type(value)
        
        # 其他类型保持不变
        return value
    
    def _convert_basic_type(self, value: Any) -> Any:
        """转换基本类型
        
        Args:
            value: 值
            
        Returns:
            转换后的值
        """
        if isinstance(value, str):
            # 尝试转换字符串为其他类型
            return self._convert_string(value)
        
        return value
    
    def _convert_string(self, value: str) -> Any:
        """转换字符串
        
        Args:
            value: 字符串值
            
        Returns:
            转换后的值
        """
        # 布尔值转换
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False
        
        # 数字转换
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 保持字符串
        return value
    
    def convert_to_type(self, value: Any, target_type: str) -> Any:
        """转换到指定类型
        
        Args:
            value: 值
            target_type: 目标类型
            
        Returns:
            转换后的值
        """
        # 检查自定义转换器
        if target_type in self.custom_converters:
            return self.custom_converters[target_type](value)
        
        # 检查内置类型映射
        if target_type in self.type_mappings:
            python_type = self.type_mappings[target_type]
            try:
                return python_type(value)
            except (ValueError, TypeError):
                logger.warning(f"无法转换值 {value} 到类型 {target_type}")
                return value
        
        # 未知类型，保持原值
        logger.warning(f"未知的目标类型: {target_type}")
        return value