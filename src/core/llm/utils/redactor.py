"""敏感信息脱敏工具

提供通用的敏感信息脱敏功能，可被多个模块使用。
"""

import re
from typing import List, Pattern, Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Redactor:
    """敏感信息脱敏处理器"""

    def __init__(self, patterns: Optional[List[str]] = None, replacement: str = "***"):
        """初始化脱敏处理器

        Args:
            patterns: 敏感信息正则表达式模式列表
            replacement: 替换字符串
        """
        self.replacement = replacement
        self._patterns: List[Pattern] = []
        self._custom_patterns: Dict[str, Pattern] = {}

        # 默认敏感信息模式
        default_patterns = [
            # API密钥
            r"sk-[a-zA-Z0-9]{20,}",
            r"AIza[a-zA-Z0-9_-]{35}",
            r"xoxb-[0-9]{10}-[0-9]{10}-[a-zA-Z0-9]{24}",
            # 邮箱地址
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            # 手机号
            r"1[3-9]\d{9}",
            # 密码字段
            r'(?i)password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'(?i)passwd["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'(?i)pwd["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
            # 令牌
            r"Bearer\s+[a-zA-Z0-9_-]+",
            r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+',
            # 数据库连接字符串
            r"mysql://[^@]+:[^@]+@[^/]+",
            r"postgresql://[^@]+:[^@]+@[^/]+",
            r"mongodb://[^@]+:[^@]+@[^/]+",
            # URL中的用户名密码
            r"https?://[^:]+:[^@]+@[^/]+",
        ]

        # 使用提供的模式或默认模式
        patterns_to_use = patterns or default_patterns

        # 编译正则表达式
        for pattern in patterns_to_use:
            try:
                self._patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"警告: 无效的正则表达式模式 '{pattern}': {e}")

    def add_pattern(self, name: str, pattern: str) -> None:
        """添加自定义模式

        Args:
            name: 模式名称
            pattern: 正则表达式模式
        """
        try:
            self._custom_patterns[name] = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"无效的正则表达式模式 '{pattern}': {e}")

    def remove_pattern(self, name: str) -> bool:
        """移除自定义模式

        Args:
            name: 模式名称

        Returns:
            是否成功移除
        """
        if name in self._custom_patterns:
            del self._custom_patterns[name]
            return True
        return False

    def redact(self, text: str, level: LogLevel = LogLevel.INFO) -> str:
        """脱敏文本

        Args:
            text: 原始文本
            level: 日志级别

        Returns:
            脱敏后的文本
        """
        # DEBUG级别不脱敏
        if level == LogLevel.DEBUG:
            return text

        result = text

        # 应用默认模式
        for pattern in self._patterns:
            result = pattern.sub(self.replacement, result)

        # 应用自定义模式
        for pattern in self._custom_patterns.values():
            result = pattern.sub(self.replacement, result)

        return result

    def redact_dict(
        self,
        data: Dict[str, Any],
        level: LogLevel = LogLevel.INFO,
        recursive: bool = True,
    ) -> Any:
        """脱敏字典

        Args:
            data: 原始字典
            level: 日志级别
            recursive: 是否递归处理嵌套字典

        Returns:
            脱敏后的字典
        """
        if not isinstance(data, dict):
            return data

        result = {}

        for key, value in data.items():
            if isinstance(value, str):
                # 对字符串值进行脱敏
                result[key] = self.redact(value, level)
            elif isinstance(value, dict) and recursive:
                # 递归处理嵌套字典
                result[key] = self.redact_dict(value, level, recursive)
            elif isinstance(value, list) and recursive:
                # 递归处理列表
                result[key] = self.redact_list(value, level, recursive)
            else:
                # 其他类型直接复制
                result[key] = value

        return result

    def redact_list(
        self, data: List[Any], level: LogLevel = LogLevel.INFO, recursive: bool = True
    ) -> Any:
        """脱敏列表

        Args:
            data: 原始列表
            level: 日志级别
            recursive: 是否递归处理嵌套结构

        Returns:
            脱敏后的列表
        """
        if not isinstance(data, list):
            return data

        result = []

        for item in data:
            if isinstance(item, str):
                # 对字符串项进行脱敏
                result.append(self.redact(item, level))
            elif isinstance(item, dict) and recursive:
                # 递归处理嵌套字典
                result.append(self.redact_dict(item, level, recursive))
            elif isinstance(item, list) and recursive:
                # 递归处理嵌套列表
                result.append(self.redact_list(item, level, recursive))
            else:
                # 其他类型直接复制
                result.append(item)

        return result

    def redact_json(self, json_str: str, level: LogLevel = LogLevel.INFO) -> str:
        """脱敏JSON字符串

        Args:
            json_str: JSON字符串
            level: 日志级别

        Returns:
            脱敏后的JSON字符串
        """
        try:
            import json

            data = json.loads(json_str)
            redacted_data = self.redact_dict(data, level)
            return json.dumps(redacted_data, ensure_ascii=False)
        except Exception:
            # 如果解析失败，直接对字符串进行脱敏
            return self.redact(json_str, level)

    def is_sensitive(self, text: str) -> bool:
        """检查文本是否包含敏感信息

        Args:
            text: 文本

        Returns:
            是否包含敏感信息
        """
        # 检查默认模式
        for pattern in self._patterns:
            if pattern.search(text):
                return True

        # 检查自定义模式
        for pattern in self._custom_patterns.values():
            if pattern.search(text):
                return True

        return False

    def get_sensitive_parts(self, text: str) -> List[str]:
        """获取文本中的敏感信息部分

        Args:
            text: 文本

        Returns:
            敏感信息部分列表
        """
        sensitive_parts = []

        # 检查默认模式
        for pattern in self._patterns:
            matches = pattern.findall(text)
            sensitive_parts.extend(matches)

        # 检查自定义模式
        for pattern in self._custom_patterns.values():
            matches = pattern.findall(text)
            sensitive_parts.extend(matches)

        return sensitive_parts

    def get_pattern_names(self) -> List[str]:
        """获取所有自定义模式名称

        Returns:
            模式名称列表
        """
        return list(self._custom_patterns.keys())

    def set_replacement(self, replacement: str) -> None:
        """设置替换字符串

        Args:
            replacement: 替换字符串
        """
        self.replacement = replacement

    def clear_patterns(self) -> None:
        """清除所有自定义模式"""
        self._custom_patterns.clear()

    def reset_to_defaults(self, patterns: Optional[List[str]] = None) -> None:
        """重置为默认模式

        Args:
            patterns: 新的默认模式列表（可选）
        """
        self._patterns.clear()
        self._custom_patterns.clear()

        # 重新初始化默认模式
        default_patterns = [
            r"sk-[a-zA-Z0-9]{20,}",
            r"AIza[a-zA-Z0-9_-]{35}",
            r"xoxb-[0-9]{10}-[0-9]{10}-[a-zA-Z0-9]{24}",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"1[3-9]\d{9}",
            r'(?i)password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'(?i)passwd["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'(?i)pwd["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
            r"Bearer\s+[a-zA-Z0-9_-]+",
            r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+',
            r"mysql://[^@]+:[^@]+@[^/]+",
            r"postgresql://[^@]+:[^@]+@[^/]+",
            r"mongodb://[^@]+:[^@]+@[^/]+",
            r"https?://[^:]+:[^@]+@[^/]+",
        ]

        patterns_to_use = patterns or default_patterns

        for pattern in patterns_to_use:
            try:
                self._patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"警告: 无效的正则表达式模式 '{pattern}': {e}")