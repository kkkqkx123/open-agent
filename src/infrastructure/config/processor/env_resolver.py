"""环境变量解析器"""

import os
import re
from typing import Any, Dict, Union, Optional


class EnvResolver:
    """环境变量解析器"""

    def __init__(self, prefix: str = ""):
        """初始化环境变量解析器

        Args:
            prefix: 环境变量前缀
        """
        self.prefix = prefix
        self.env_var_pattern = re.compile(r"\$\{([^}]+)\}")
        self.env_var_default_pattern = re.compile(r"\$\{([^:]+):([^}]*)\}")

    def resolve(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量

        Args:
            config: 配置字典

        Returns:
            解析后的配置字典
        """

        def _resolve_recursive(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: _resolve_recursive(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_resolve_recursive(item) for item in value]
            elif isinstance(value, str):
                return self._resolve_string(value)
            else:
                return value

        result = _resolve_recursive(config)
        # 确保返回类型是 Dict[str, Any]
        assert isinstance(result, dict)
        return result

    def _resolve_string(self, text: str) -> str:
        """解析字符串中的环境变量

        Args:
            text: 包含环境变量的字符串

        Returns:
            解析后的字符串
        """

        def replace_env_var(match: re.Match) -> str:
            var_expr = match.group(1)

            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                # 添加前缀
                full_var_name = f"{self.prefix}{var_name}" if self.prefix else var_name
                return os.getenv(full_var_name, default_value)
            else:
                # 普通环境变量
                full_var_name = f"{self.prefix}{var_expr}" if self.prefix else var_expr
                value = os.getenv(full_var_name)
                if value is None:
                    raise ValueError(f"环境变量未找到: {full_var_name}")
                return value

        # 使用正则表达式替换所有环境变量
        return self.env_var_pattern.sub(replace_env_var, text)

    def get_env_var(self, name: str, default: Optional[str] = None) -> str:
        """获取环境变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            环境变量值或默认值
        """
        full_name = f"{self.prefix}{name}" if self.prefix else name
        result = os.getenv(full_name, default)
        return result if result is not None else ""

    def set_env_var(self, name: str, value: str) -> None:
        """设置环境变量

        Args:
            name: 变量名
            value: 变量值
        """
        full_name = f"{self.prefix}{name}" if self.prefix else name
        os.environ[full_name] = value

    def has_env_var(self, name: str) -> bool:
        """检查环境变量是否存在

        Args:
            name: 变量名

        Returns:
            是否存在
        """
        full_name = f"{self.prefix}{name}" if self.prefix else name
        return full_name in os.environ

    def list_env_vars(self, pattern: Optional[str] = None) -> Dict[str, str]:
        """列出环境变量

        Args:
            pattern: 匹配模式（可选）

        Returns:
            环境变量字典
        """
        result = {}
        prefix_pattern = f"^{self.prefix}" if self.prefix else "^"

        for key, value in os.environ.items():
            # 检查是否匹配前缀
            if not re.match(prefix_pattern, key):
                continue

            # 检查是否匹配模式
            if pattern and not re.search(pattern, key):
                continue

            # 移除前缀
            display_key = key[len(self.prefix) :] if self.prefix else key
            result[display_key] = value

        return result

    def clear_env_vars(self, pattern: Optional[str] = None) -> None:
        """清除环境变量

        Args:
            pattern: 匹配模式（可选）
        """
        prefix_pattern = f"^{self.prefix}" if self.prefix else "^"
        keys_to_remove = []

        for key in os.environ:
            # 检查是否匹配前缀
            if not re.match(prefix_pattern, key):
                continue

            # 检查是否匹配模式
            if pattern and not re.search(pattern, key):
                continue

            keys_to_remove.append(key)

        for key in keys_to_remove:
            del os.environ[key]
