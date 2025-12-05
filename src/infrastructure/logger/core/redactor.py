"""日志脱敏器"""

import re
import hashlib
from typing import List, Optional, Pattern, Dict, Any, TYPE_CHECKING

from .log_level import LogLevel

from ....interfaces.logger import ILogRedactor


class LogRedactor(ILogRedactor):
    """日志脱敏器"""

    # 默认敏感信息模式
    DEFAULT_PATTERNS = [
        # OpenAI API Key
        (r"sk-[a-zA-Z0-9]{20,}", "sk-***"),
        # 邮箱地址
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "***@***.***"),
        # 手机号（中国）
        (r"1[3-9]\d{9}", "1*********"),
        # 身份证号
        (
            r"\b[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
            "***************",
        ),
        # 密码字段
        (r'(["\']?password["\']?\s*[:=]\s*["\']?)[^"\',\s}]+', r"\1***PASSWORD***"),
        # Token
        (r'(["\']?token["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_-]{20,}', r"\1***TOKEN***"),
        # API Key通用模式
        (
            r'(["\']?api[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_-]{16,}',
            r"\1***APIKEY***",
        ),
        # Secret Key
        (
            r'(["\']?secret[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_-]{16,}',
            r"\1***SECRET***",
        ),
        # Access Token
        (
            r'(["\']?access[_-]?token["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9._-]{20,}',
            r"\1***ACCESSTOKEN***",
        ),
        # Bearer Token
        (r"Bearer\s+[a-zA-Z0-9._-]{20,}", "Bearer ***"),
        # JWT Token
        (r"eyJ[a-zA-Z0-9._-]*\.eyJ[a-zA-Z0-9._-]*\.[a-zA-Z0-9._-]*", "JWT.***.***"),
    ]

    def __init__(
        self,
        patterns: Optional[List[tuple[Pattern, str]]] = None,
        hash_sensitive: bool = False,
    ):
        """初始化日志脱敏器

        Args:
            patterns: 自定义正则表达式模式列表
            hash_sensitive: 是否对敏感信息进行哈希处理
        """
        self.patterns = patterns or self._compile_default_patterns()
        self.hash_sensitive = hash_sensitive
        self._cache: Dict[str, str] = {}

    def _compile_default_patterns(self) -> List[tuple[Pattern, str]]:
        """编译默认模式

        Returns:
            编译后的正则表达式模式列表
        """
        compiled_patterns = []
        for pattern, replacement in self.DEFAULT_PATTERNS:
            compiled_patterns.append((re.compile(pattern), replacement))
        return compiled_patterns

    def redact(self, text: str, level: LogLevel | str = LogLevel.INFO) -> str:
        """脱敏文本

        Args:
            text: 原始文本
            level: 日志级别

        Returns:
            脱敏后的文本
        """
        # 将字符串级别转换为LogLevel
        if isinstance(level, str):
            level = LogLevel[level]
        
        # DEBUG级别不脱敏
        if level.value == LogLevel.DEBUG.value:
            return text

        # 检查缓存（DEBUG级别不缓存）
        cache_key = f"{text}_{level.value}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        redacted_text = text

        # 应用所有模式
        for pattern, replacement in self.patterns:
            if self.hash_sensitive and replacement == "***":
                # 使用哈希替换
                redacted_text = pattern.sub(self._hash_replace, redacted_text)
            else:
                # 使用固定替换
                redacted_text = pattern.sub(replacement, redacted_text)

        # 缓存结果
        self._cache[cache_key] = redacted_text
        return redacted_text

    def _hash_replace(self, match: re.Match) -> str:
        """使用哈希替换匹配的文本

        Args:
            match: 正则匹配对象

        Returns:
            哈希替换文本
        """
        original = match.group()

        # 使用缓存避免重复计算
        if original in self._cache:
            return self._cache[original]

        # 计算哈希值
        hash_obj = hashlib.sha256(original.encode("utf-8"))
        hash_hex = hash_obj.hexdigest()[:8]  # 只取前8位

        # 构建替换文本
        if len(original) <= 10:
            replacement = "*" * len(original)
        else:
            replacement = f"{original[:3]}{hash_hex}{original[-3:]}"

        # 缓存结果
        self._cache[original] = replacement

        return replacement

    def add_pattern(self, pattern: str, replacement: str = "***") -> None:
        """添加自定义模式

        Args:
            pattern: 正则表达式模式
            replacement: 替换文本
        """
        compiled_pattern = re.compile(pattern)
        self.patterns.append((compiled_pattern, replacement))

    def remove_pattern(self, pattern: str) -> bool:
        """移除模式

        Args:
            pattern: 要移除的正则表达式模式

        Returns:
            是否成功移除
        """
        for i, (compiled_pattern, _) in enumerate(self.patterns):
            if compiled_pattern.pattern == pattern:
                del self.patterns[i]
                return True
        return False

    def clear_patterns(self) -> None:
        """清除所有模式"""
        self.patterns.clear()

    def reset_to_default(self) -> None:
        """重置为默认模式"""
        self.patterns = self._compile_default_patterns()

    def set_hash_sensitive(self, hash_sensitive: bool) -> None:
        """设置是否对敏感信息进行哈希处理

        Args:
            hash_sensitive: 是否进行哈希处理
        """
        self.hash_sensitive = hash_sensitive
        if not hash_sensitive:
            self._cache.clear()

    def get_patterns_count(self) -> int:
        """获取模式数量

        Returns:
            模式数量
        """
        return len(self.patterns)

    def test_redaction(self, text: str) -> Dict[str, Any]:
        """测试脱敏效果

        Args:
            text: 测试文本

        Returns:
            测试结果字典
        """
        original_text = text
        redacted_text = self.redact(text)

        # 检查是否有变化
        has_changes = original_text != redacted_text

        # 统计匹配的模式
        matched_patterns = []
        for pattern, replacement in self.patterns:
            if pattern.search(text):
                matched_patterns.append(
                    {
                        "pattern": pattern.pattern,
                        "replacement": replacement,
                        "matches": len(pattern.findall(text)),
                    }
                )

        return {
            "original": original_text,
            "redacted": redacted_text,
            "has_changes": has_changes,
            "matched_patterns": matched_patterns,
        }


class CustomLogRedactor(LogRedactor):
    """自定义日志脱敏器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化自定义日志脱敏器

        Args:
            config: 脱敏配置
        """
        self.config = config or {}

        # 从配置中获取模式
        patterns = self._load_patterns_from_config()

        # 获取哈希设置
        hash_sensitive = self.config.get("hash_sensitive", False)

        super().__init__(patterns, hash_sensitive)

    def _load_patterns_from_config(self) -> Optional[List[tuple[Pattern, str]]]:
        """从配置加载模式

        Returns:
            编译后的正则表达式模式列表
        """
        patterns_config = self.config.get("patterns")
        if not patterns_config:
            return None

        compiled_patterns = []
        for pattern_config in patterns_config:
            pattern_str = pattern_config.get("pattern")
            replacement = pattern_config.get("replacement", "***")

            if pattern_str:
                compiled_pattern = re.compile(pattern_str)
                compiled_patterns.append((compiled_pattern, replacement))

        return compiled_patterns if compiled_patterns else None

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新配置

        Args:
            config: 新的脱敏配置
        """
        self.config = config

        # 重新加载模式
        patterns = self._load_patterns_from_config()
        if patterns:
            self.patterns = patterns
        else:
            self.reset_to_default()

        # 更新哈希设置
        self.hash_sensitive = config.get("hash_sensitive", False)
        if not self.hash_sensitive:
            self._cache.clear()