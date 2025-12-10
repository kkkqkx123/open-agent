"""环境变量处理器

处理配置中的环境变量替换。
"""

import os
import re
from typing import Dict, Any

from .base_processor import BaseConfigProcessor
import logging

logger = logging.getLogger(__name__)


class EnvironmentProcessor(BaseConfigProcessor):
    """环境变量处理器
    
    处理配置中的环境变量替换。
    """
    
    def __init__(self):
        """初始化环境变量处理器"""
        super().__init__("environment")
        self._env_var_pattern = re.compile(r"\$\{([^}]+)\}")
        logger.debug("环境变量处理器初始化完成")
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理环境变量替换
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        return self._resolve_env_vars_recursive(config)
    
    def _resolve_env_vars_recursive(self, obj: Any) -> Any:
        """递归解析环境变量
        
        Args:
            obj: 要处理的对象
            
        Returns:
            处理后的对象
        """
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._resolve_env_var_string(obj)
        else:
            return obj
    
    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量
        
        Args:
            text: 包含环境变量的字符串
            
        Returns:
            解析后的字符串
        """
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
                    logger.warning(f"环境变量未定义: {var_name}")
                    return f"${{{var_name}}}"
                return value
        
        # 使用正则表达式替换所有环境变量
        return self._env_var_pattern.sub(replace_env_var, text)