"""配置继承处理器

处理配置文件之间的继承关系，支持多重继承和环境变量解析。
"""

import os
import re
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.interfaces.config import ConfigError as ConfigurationError
from src.interfaces.config import IConfigLoader
from .base_processor import BaseConfigProcessor
import logging

logger = logging.getLogger(__name__)


class InheritanceProcessor(BaseConfigProcessor):
    """配置继承处理器实现
    
    实现 IConfigProcessor 接口，负责处理配置文件之间的继承关系和环境变量解析。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化配置继承处理器
        
        Args:
            config_loader: 配置加载器（可选）
        """
        super().__init__("inheritance")
        self.config_loader = config_loader
        self._env_var_pattern = re.compile(r"\$\{([^}]+)\}")
        self._loading_stack: List[str] = []
        logger.debug("继承处理器初始化完成")
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置继承
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        base_path = Path(config_path).parent
        return self.resolve_inheritance(config, base_path)
    
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
            # 对于非相对路径，尝试相对于基础路径的路径
            if base_path:
                full_path = base_path / config_path
            else:
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
        # 创建一个副本以避免修改原始数据
        result = parent.copy()
        
        # 深度合并字典
        for key, value in child.items():
            if key == "inherits_from":
                continue  # 跳过继承字段
                
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = self._merge_configs(result[key], value)
            else:
                # 子配置覆盖父配置
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
    
    def validate_config(self, config: Dict[str, Any], schema: Optional[object] = None) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 检查必要字段
        required_fields = config.get("_required_fields", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必要字段: {field}")
        
        return errors