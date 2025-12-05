"""配置继承处理工具

专门用于配置系统的继承处理功能。
"""

import os
import re
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
import yaml
from pydantic import ValidationError
from abc import abstractmethod

from src.interfaces.configuration import ConfigError as ConfigurationError
from src.interfaces.config.interfaces import IConfigLoader, IConfigInheritanceHandler


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
            # 直接使用文件路径加载，避免使用配置加载器，以正确处理相对路径
            loaded_config = self._load_config_from_file(parent_path, base_path)
            parent_config = self._merge_configs(parent_config, loaded_config)
        
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
            # 对于非相对路径，尝试不同的解析策略
            if base_path:
                # 策略1: 尝试相对于configs/llms的路径（如果base_path包含llms部分）
                llms_path = None
                base_str = str(base_path)
                if "configs/llms" in base_str or "configs\\llms" in base_str:
                    # 找到configs/llms部分并构建路径
                    parts = base_path.parts
                    llms_index = -1
                    for i, part in enumerate(parts):
                        if part == "llms":
                            llms_index = i
                            break
                    if llms_index != -1:
                        # 构建 configs/llms/.../config_path 路径
                        llms_base = Path(*parts[:llms_index+1])  # 包含"llms"的部分
                        llms_relative_path = llms_base / config_path
                        if llms_relative_path.with_suffix(".yaml").exists():
                            full_path = llms_relative_path
                        else:
                            # 如果configs/llms路径不存在，尝试相对于基础路径的路径
                            relative_to_base = base_path / config_path
                            if relative_to_base.with_suffix(".yaml").exists():
                                full_path = relative_to_base
                            else:
                                full_path = Path("configs") / config_path
                    else:
                        # 如果没有找到llms部分，尝试相对于基础路径的路径
                        relative_to_base = base_path / config_path
                        if relative_to_base.with_suffix(".yaml").exists():
                            full_path = relative_to_base
                        else:
                            full_path = Path("configs") / config_path
                else:
                    # 如果base_path不包含llms，尝试相对于基础路径的路径
                    relative_to_base = base_path / config_path
                    if relative_to_base.with_suffix(".yaml").exists():
                        full_path = relative_to_base
                    else:
                        full_path = Path("configs") / config_path
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
        from src.infrastructure.common.utils.dict_merger import DictMerger
        merger = DictMerger()
        
        # 创建一个副本以避免修改原始数据
        result = merger.deep_merge(parent.copy(), child)
        
        # 移除inherits_from字段，因为它已在上层处理
        if "inherits_from" in result:
            del result["inherits_from"]
        
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
        
        result = _resolve_recursive(config)
        assert isinstance(result, dict)
        return result
    
    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量"""
        def replace_env_var(match: Any) -> str:
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
        
        result = _resolve_recursive(config, config)
        assert isinstance(result, dict)
        return result
    
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
    
    def validate_config(self, config: Dict[str, Any], schema: Optional[object] = None) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 如果提供了Pydantic模式，使用它验证
        if schema and hasattr(schema, 'model_validate'):
            try:
                # 使用getattr来动态调用方法，避免类型检查错误
                getattr(schema, 'model_validate')(config)
            except ValidationError as e:
                errors.extend([str(err) for err in e.errors()])
        
        # 使用通用验证器进行结构和类型验证
        from src.infrastructure.common.utils.validator import Validator
        validator = Validator()
        
        # 执行结构验证
        structure_result = validator.validate_structure(config, [])
        if not structure_result.is_valid:
            errors.extend(structure_result.errors)
        
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


class InheritanceConfigLoader(IConfigLoader):
    """继承配置加载器装饰器
    
    为配置加载器添加继承处理功能。
    """
    
    def __init__(self, base_loader: IConfigLoader):
        """初始化继承配置加载器
        
        Args:
            base_loader: 基础配置加载器
        """
        self.base_loader = base_loader
        self.inheritance_handler = ConfigInheritanceHandler(base_loader)
    
    @property
    def base_path(self) -> Path:
        """获取配置基础路径"""
        return self.base_loader.base_path
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        return self.load_config(config_path)
    
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置并处理继承关系
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Returns:
            处理后的配置数据
        """
        # 使用基础加载器加载配置
        config = self.base_loader.load_config(config_path, config_type)
        
        # 处理继承关系
        if config:
            base_path = Path(config_path).parent
            config = self.inheritance_handler.resolve_inheritance(config, base_path)
        
        return config
    
    def reload(self) -> None:
        """重新加载所有配置"""
        self.base_loader.reload()
    
    def watch_for_changes(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """监听配置变化"""
        self.base_loader.watch_for_changes(callback)
    
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""
        return self.base_loader.resolve_env_vars(config)
    
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        self.base_loader.stop_watching()
    
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置，如果不存在则返回None"""
        return self.base_loader.get_config(config_path)
    
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件"""
        if hasattr(self.base_loader, '_handle_file_change'):
            self.base_loader._handle_file_change(file_path)  # type: ignore[attr-defined]
    
    def save_config(self, config: Dict[str, Any], config_path: str, config_type: Optional[str] = None) -> None:
        """保存配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            config_type: 配置类型（可选）
        """
        self.base_loader.save_config(config, config_path, config_type)
    
    def list_configs(self, config_type: Optional[str] = None) -> List[str]:
        """列出配置文件
        
        Args:
            config_type: 配置类型（可选）
            
        Returns:
            配置文件路径列表
        """
        return self.base_loader.list_configs(config_type)
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            路径是否有效
        """
        return self.base_loader.validate_config_path(config_path)