"""配置继承系统

实现配置继承和验证机制，支持配置文件的继承和覆盖功能。
"""

import os
import re
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError
from abc import ABC, abstractmethod

from .exceptions import ConfigurationError
from .config_interfaces import IConfigLoader, IConfigInheritanceHandler


class IConfigInheritanceHandler(ABC):
    """配置继承处理器接口"""
    
    @abstractmethod
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """解析配置继承关系
        
        Args:
            config: 原始配置
            base_path: 基础路径
            
        Returns:
            解析后的配置
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any], schema: Optional[BaseModel] = None) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        pass


class ConfigInheritanceHandler(IConfigInheritanceHandler):
    """配置继承处理器实现"""
    
    def __init__(self, config_loader: Optional['IConfigLoader'] = None):
        """初始化配置继承处理器
        
        Args:
            config_loader: 配置加载器（可选）
        """
        self.config_loader = config_loader
        self._env_var_pattern = re.compile(r"\$\{([^}]+)\}")
    
    def resolve_inheritance(self, config: Dict[str, Any], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """解析配置继承关系
        
        Args:
            config: 原始配置
            base_path: 基础路径
            
        Returns:
            解析后的配置
        """
        # 检查是否有继承配置
        inherits_from = config.get("inherits_from")
        if inherits_from:
            # 加载父配置
            parent_config = self._load_parent_config(inherits_from, base_path)
            
            # 合并配置（子配置覆盖父配置）
            merged_config = self._merge_configs(parent_config, config)
            
            # 递归处理继承链
            return self.resolve_inheritance(merged_config, base_path)
        
        # 处理配置中的环境变量
        config = self._resolve_env_vars(config)
        
        # 处理配置中的引用
        config = self._resolve_references(config)
        
        return config
    
    def _load_parent_config(self, inherits_from: Union[str, List[str]], base_path: Optional[Path] = None) -> Dict[str, Any]:
        """加载父配置
        
        Args:
            inherits_from: 继承的配置路径或路径列表
            base_path: 基础路径
            
        Returns:
            父配置
        """
        if isinstance(inherits_from, str):
            inherits_from = [inherits_from]
        
        parent_config = {}
        
        for parent_path in inherits_from:
            # 如果提供了配置加载器，使用它加载配置
            if self.config_loader and not parent_path.startswith("./") and not parent_path.startswith("../"):
                try:
                    parent_config = self.config_loader.load(parent_path)
                except ConfigurationError:
                    # 如果配置加载器无法加载，尝试作为文件路径
                    parent_config = self._load_config_from_file(parent_path, base_path)
            else:
                parent_config = self._merge_configs(
                    parent_config,
                    self._load_config_from_file(parent_path, base_path)
                )
        
        return parent_config
    
    def _load_config_from_file(self, config_path: str, base_path: Optional[Path] = None) -> Dict[str, Any]:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            base_path: 基础路径
            
        Returns:
            配置数据
        """
        # 构建完整路径
        if config_path.startswith("./") or config_path.startswith("../"):
            # 相对路径，相对于当前基础路径
            if base_path:
                full_path = base_path / config_path
            else:
                full_path = Path(config_path)
        else:
            # 绝对路径或相对于configs目录的路径
            full_path = Path("configs") / config_path
        
        if not full_path.suffix:
            full_path = full_path.with_suffix(".yaml")
        
        if not full_path.exists():
            raise ConfigurationError(f"继承配置文件不存在: {full_path}")
        
        with open(full_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        
        # 递归解析继承关系
        return self.resolve_inheritance(config, full_path.parent)
    
    def _merge_configs(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（子配置覆盖父配置）
        
        Args:
            parent: 父配置
            child: 子配置
            
        Returns:
            合并后的配置
        """
        result = parent.copy()
        
        for key, value in child.items():
            if key == "inherits_from":
                # 跳过inherits_from字段，因为它已在上层处理
                continue
            
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 如果两个值都是字典，递归合并
                result[key] = self._merge_configs(result[key], value)
            else:
                # 否则直接覆盖
                result[key] = value
        
        return result
    
    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量
        
        Args:
            config: 配置数据
            
        Returns:
            解析后的配置
        """
        def _resolve_recursive(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: _resolve_recursive(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_resolve_recursive(item) for item in value]
            elif isinstance(value, str):
                return self._resolve_env_var_string(value)
            else:
                return value
        
        return _resolve_recursive(config)
    
    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量"""
        def replace_env_var(match):
            var_expr = match.group(1)
            
            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                # 普通环境变量
                var_name = var_expr.strip()
                value = os.getenv(var_name)
                if value is None:
                    raise ConfigurationError(f"环境变量未定义: {var_name}")
                return value
        
        # 使用正则表达式替换所有环境变量
        return self._env_var_pattern.sub(replace_env_var, text)
    
    def _resolve_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的引用（如 $ref: path.to.value）
        
        Args:
            config: 配置数据
            
        Returns:
            解析后的配置
        """
        def _resolve_recursive(obj: Any, root: Dict[str, Any], path: str = "") -> Any:
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if isinstance(v, str) and v.startswith("$ref:"):
                        # 解析引用
                        ref_path = v[5:].strip()  # 移除 "$ref:"
                        ref_value = self._get_nested_value(root, ref_path)
                        result[k] = _resolve_recursive(ref_value, root, current_path)
                    else:
                        result[k] = _resolve_recursive(v, root, current_path)
                return result
            elif isinstance(obj, list):
                return [_resolve_recursive(item, root, path) for item in obj]
            else:
                return obj
        
        return _resolve_recursive(config, config)
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值
        
        Args:
            obj: 字典对象
            path: 路径（点分隔）
            
        Returns:
            对应的值
        """
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise ConfigurationError(f"引用路径不存在: {path}")
        
        return current
    
    def validate_config(self, config: Dict[str, Any], schema: Optional[BaseModel] = None) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 如果提供了Pydantic模式，使用它验证
        if schema:
            try:
                schema.model_validate(config)
            except ValidationError as e:
                errors.extend([str(err) for err in e.errors()])
        
        # 执行自定义验证规则
        errors.extend(self._custom_validation(config))
        
        return errors
    
    def _custom_validation(self, config: Dict[str, Any]) -> List[str]:
        """自定义验证规则
        
        Args:
            config: 配置数据
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 检查必要字段
        required_fields = config.get("_required_fields", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必要字段: {field}")
        
        # 检查字段类型
        field_types = config.get("_field_types", {})
        for field, expected_type in field_types.items():
            if field in config:
                actual_value = config[field]
                if not self._check_type(actual_value, expected_type):
                    errors.append(f"字段 '{field}' 类型错误，期望 {expected_type}，实际 {type(actual_value)}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值的类型
        
        Args:
            value: 要检查的值
            expected_type: 期望的类型字符串
            
        Returns:
            类型是否匹配
        """
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": object  # 任何类型
        }
        
        expected_python_type = type_mapping.get(expected_type.lower())
        if expected_python_type is None:
            return True  # 未知类型，跳过检查
        
        return isinstance(value, expected_python_type)


class InheritanceConfigLoader:
    """支持继承的配置加载器装饰器"""
    
    def __init__(self, base_config_loader: 'IConfigLoader'):
        """初始化继承配置加载器
        
        Args:
            base_config_loader: 基础配置加载器
        """
        self.base_config_loader = base_config_loader
        self.inheritance_handler = ConfigInheritanceHandler(self.base_config_loader)
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件（处理继承）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            解析后的配置
        """
        # 使用基础加载器加载配置
        config = self.base_config_loader.load(config_path)
        
        # 解析继承关系
        config_path_obj = Path(config_path)
        base_path = config_path_obj.parent if config_path_obj.parent != Path(".") else None
        
        resolved_config = self.inheritance_handler.resolve_inheritance(config, base_path)
        
        return resolved_config
    
    def validate_with_schema(self, config: Dict[str, Any], schema: Optional[BaseModel] = None) -> List[str]:
        """使用模式验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        return self.inheritance_handler.validate_config(config, schema)
    
    def get_inheritance_handler(self) -> ConfigInheritanceHandler:
        """获取继承处理器
        
        Returns:
            继承处理器
        """
        return self.inheritance_handler