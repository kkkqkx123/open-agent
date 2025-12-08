"""改进的敏感信息脱敏处理器 - 支持Unicode和中文字符"""

import re
from typing import List, Pattern, Dict, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
from ...text.boundary_matcher import boundary_matcher, BoundaryType, UnicodeCategory


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class PatternCategory(Enum):
    """模式分类枚举"""
    CREDENTIALS = "credentials"  # 凭证类
    CONTACT = "contact"         # 联系方式
    IDENTITY = "identity"       # 身份标识
    FINANCIAL = "financial"     # 金融信息
    TECHNICAL = "technical"     # 技术信息
    CHINESE = "chinese"         # 中文信息


@dataclass
class RedactorPattern:
    """脱敏模式数据类"""
    name: str
    pattern: str
    category: PatternCategory
    description: str
    priority: int = 0
    flags: int = re.IGNORECASE
    replacement: Optional[str] = None


class Redactor:
    """支持Unicode和中文字符的敏感信息脱敏处理器"""

    def __init__(self, patterns: Optional[List[RedactorPattern]] = None, replacement: str = "***"):
        """初始化脱敏处理器

        Args:
            patterns: 自定义脱敏模式列表
            replacement: 默认替换字符串
        """
        self.replacement = replacement
        self._patterns: List[Tuple[Pattern, RedactorPattern]] = []
        self._custom_patterns: Dict[str, Tuple[Pattern, RedactorPattern]] = {}
        
        # 初始化默认模式
        default_patterns = self._get_default_patterns()
        patterns_to_use = patterns or default_patterns
        
        # 按优先级排序
        patterns_to_use.sort(key=lambda p: p.priority, reverse=True)
        
        # 编译正则表达式
        for redactor_pattern in patterns_to_use:
            self._compile_pattern(redactor_pattern)

    def _get_default_patterns(self) -> List[RedactorPattern]:
        """获取默认脱敏模式"""
        return [
            # 凭证类模式
            RedactorPattern(
                name="openai_api_key",
                pattern=r"sk-[a-zA-Z0-9]{20,}",
                category=PatternCategory.CREDENTIALS,
                description="OpenAI API密钥",
                priority=100
            ),
            RedactorPattern(
                name="anthropic_api_key",
                pattern=r"sk-ant-api03-[a-zA-Z0-9_-]{95}",
                category=PatternCategory.CREDENTIALS,
                description="Anthropic API密钥",
                priority=100
            ),
            RedactorPattern(
                name="google_api_key",
                pattern=r"AIza[a-zA-Z0-9_-]{35}",
                category=PatternCategory.CREDENTIALS,
                description="Google API密钥",
                priority=100
            ),
            RedactorPattern(
                name="slack_token",
                pattern=r"xox[baprs]-[0-9]{10}-[0-9]{10}-[a-zA-Z0-9]{24}",
                category=PatternCategory.CREDENTIALS,
                description="Slack令牌",
                priority=100
            ),
            
            # 联系方式模式 - 改进的Unicode支持
            RedactorPattern(
                name="email_unicode",
                pattern=r"(?<![a-zA-Z0-9._%+-\u4e00-\u9fff])[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?![a-zA-Z0-9.-\u4e00-\u9fff])",
                category=PatternCategory.CONTACT,
                description="邮箱地址（Unicode边界）",
                priority=90
            ),
            RedactorPattern(
                name="phone_china",
                pattern=r"(?<!\d)1[3-9]\d{9}(?!\d)",
                category=PatternCategory.CONTACT,
                description="中国手机号",
                priority=90
            ),
            RedactorPattern(
                name="phone_international",
                pattern=r"(?<!\d)(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?!\d)",
                category=PatternCategory.CONTACT,
                description="国际电话号码",
                priority=85
            ),
            
            # 身份标识模式
            RedactorPattern(
                name="id_card_china",
                pattern=r"(?<!\d)[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
                category=PatternCategory.IDENTITY,
                description="中国身份证号",
                priority=95
            ),
            RedactorPattern(
                name="ssn_us",
                pattern=r"(?<!\d)\d{3}[-.\s]?\d{2}[-.\s]?\d{4}(?!\d)",
                category=PatternCategory.IDENTITY,
                description="美国社会保障号",
                priority=90
            ),
            
            # 金融信息模式
            RedactorPattern(
                name="credit_card",
                pattern=r"(?<!\d)(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})(?!\d)",
                category=PatternCategory.FINANCIAL,
                description="信用卡号",
                priority=95
            ),
            RedactorPattern(
                name="bank_card_china",
                pattern=r"(?<!\d)[0-9]{16,19}(?!\d)",
                category=PatternCategory.FINANCIAL,
                description="中国银行卡号",
                priority=90
            ),
            
            # 技术信息模式
            RedactorPattern(
                name="password_field",
                pattern=r'(?i)((password|passwd|pwd)["\']?\s*[:=]\s*["\']?[^"\'\s,}]+)',
                category=PatternCategory.TECHNICAL,
                description="密码字段",
                priority=100,
                replacement="***"  # 完全替换密码字段
            ),
            RedactorPattern(
                name="bearer_token",
                pattern=r"(?i)Bearer\s+[a-zA-Z0-9._-]+",
                category=PatternCategory.TECHNICAL,
                description="Bearer令牌",
                priority=95
            ),
            RedactorPattern(
                name="token_field",
                pattern=r'(?i)(token|access_token|refresh_token)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9._-]+',
                category=PatternCategory.TECHNICAL,
                description="令牌字段",
                priority=95
            ),
            RedactorPattern(
                name="database_url",
                pattern=r"(?i)(mysql|postgresql|mongodb)://[^@]+:[^@]+@[^/]+",
                category=PatternCategory.TECHNICAL,
                description="数据库连接字符串",
                priority=90
            ),
            RedactorPattern(
                name="url_credentials",
                pattern=r"https?://[^:]+:[^@]+@[^/]+",
                category=PatternCategory.TECHNICAL,
                description="URL中的用户名密码",
                priority=90
            ),
            RedactorPattern(
                name="ip_address",
                pattern=r"(?<!\d)(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}(?!\d)",
                category=PatternCategory.TECHNICAL,
                description="IP地址",
                priority=80
            ),
            
            RedactorPattern(
                name="chinese_address",
                pattern=r"[\u4e00-\u9fff]{2,}(?:省|市|区|县|镇|街道|路|号|室|栋|楼|层|单元)",
                category=PatternCategory.CHINESE,
                description="中文地址",
                priority=60
            ),
        ]

    def _compile_pattern(self, redactor_pattern: RedactorPattern) -> None:
        """编译正则表达式模式"""
        try:
            # 添加Unicode标志以确保正确处理Unicode字符
            flags = redactor_pattern.flags | re.UNICODE
            compiled_pattern = re.compile(redactor_pattern.pattern, flags)
            self._patterns.append((compiled_pattern, redactor_pattern))
        except re.error as e:
            print(f"警告: 无效的正则表达式模式 '{redactor_pattern.name}': {e}")

    def add_pattern(self, redactor_pattern: RedactorPattern) -> None:
        """添加自定义模式

        Args:
            redactor_pattern: 脱敏模式对象
        """
        try:
            flags = redactor_pattern.flags | re.UNICODE
            compiled_pattern = re.compile(redactor_pattern.pattern, flags)
            self._custom_patterns[redactor_pattern.name] = (compiled_pattern, redactor_pattern)
            
            # 重新排序所有模式
            self._reorder_patterns()
        except re.error as e:
            raise ValueError(f"无效的正则表达式模式 '{redactor_pattern.name}': {e}")

    def _reorder_patterns(self) -> None:
        """重新排序所有模式（按优先级）"""
        all_patterns = []
        
        # 添加默认模式
        for pattern, redactor_pattern in self._patterns:
            all_patterns.append((pattern, redactor_pattern))
        
        # 添加自定义模式
        for pattern, redactor_pattern in self._custom_patterns.values():
            all_patterns.append((pattern, redactor_pattern))
        
        # 按优先级排序
        all_patterns.sort(key=lambda x: x[1].priority, reverse=True)
        
        # 更新模式列表
        self._patterns = all_patterns

    def remove_pattern(self, name: str) -> bool:
        """移除自定义模式

        Args:
            name: 模式名称

        Returns:
            是否成功移除
        """
        if name in self._custom_patterns:
            del self._custom_patterns[name]
            self._reorder_patterns()
            return True
        return False

    def redact(self, text: str, level: LogLevel = LogLevel.INFO, 
               categories: Optional[List[PatternCategory]] = None) -> str:
        """脱敏文本

        Args:
            text: 原始文本
            level: 日志级别
            categories: 指定要处理的模式分类，None表示处理所有

        Returns:
            脱敏后的文本
        """
        # DEBUG级别不脱敏
        if level == LogLevel.DEBUG:
            return text

        result = text

        # 应用模式
        for pattern, redactor_pattern in self._patterns:
            # 检查分类过滤
            if categories and redactor_pattern.category not in categories:
                continue
                
            # 使用模式特定的替换字符串或默认替换字符串
            replacement = redactor_pattern.replacement or self.replacement
            result = pattern.sub(replacement, result)

        return result

    def redact_dict(
        self,
        data: Dict[str, Any],
        level: LogLevel = LogLevel.INFO,
        recursive: bool = True,
        categories: Optional[List[PatternCategory]] = None,
    ) -> Any:
        """脱敏字典

        Args:
            data: 原始字典
            level: 日志级别
            recursive: 是否递归处理嵌套字典
            categories: 指定要处理的模式分类

        Returns:
            脱敏后的字典
        """
        if not isinstance(data, dict):
            return data

        result = {}

        for key, value in data.items():
            if isinstance(value, str):
                # 对字符串值进行脱敏
                result[key] = self.redact(value, level, categories)
            elif isinstance(value, dict) and recursive:
                # 递归处理嵌套字典
                result[key] = self.redact_dict(value, level, recursive, categories)
            elif isinstance(value, list) and recursive:
                # 递归处理列表
                result[key] = self.redact_list(value, level, recursive, categories)
            else:
                # 其他类型直接复制
                result[key] = value

        return result

    def redact_list(
        self, 
        data: List[Any], 
        level: LogLevel = LogLevel.INFO, 
        recursive: bool = True,
        categories: Optional[List[PatternCategory]] = None,
    ) -> Any:
        """脱敏列表

        Args:
            data: 原始列表
            level: 日志级别
            recursive: 是否递归处理嵌套结构
            categories: 指定要处理的模式分类

        Returns:
            脱敏后的列表
        """
        if not isinstance(data, list):
            return data

        result = []

        for item in data:
            if isinstance(item, str):
                # 对字符串项进行脱敏
                result.append(self.redact(item, level, categories))
            elif isinstance(item, dict) and recursive:
                # 递归处理嵌套字典
                result.append(self.redact_dict(item, level, recursive, categories))
            elif isinstance(item, list) and recursive:
                # 递归处理嵌套列表
                result.append(self.redact_list(item, level, recursive, categories))
            else:
                # 其他类型直接复制
                result.append(item)

        return result

    def redact_json(self, json_str: str, level: LogLevel = LogLevel.INFO,
                   categories: Optional[List[PatternCategory]] = None) -> str:
        """脱敏JSON字符串

        Args:
            json_str: JSON字符串
            level: 日志级别
            categories: 指定要处理的模式分类

        Returns:
            脱敏后的JSON字符串
        """
        try:
            import json

            data = json.loads(json_str)
            redacted_data = self.redact_dict(data, level, categories=categories)
            return json.dumps(redacted_data, ensure_ascii=False, indent=2)
        except Exception:
            # 如果解析失败，直接对字符串进行脱敏
            return self.redact(json_str, level, categories)

    def is_sensitive(self, text: str, 
                    categories: Optional[List[PatternCategory]] = None) -> bool:
        """检查文本是否包含敏感信息

        Args:
            text: 文本
            categories: 指定要检查的模式分类

        Returns:
            是否包含敏感信息
        """
        for pattern, redactor_pattern in self._patterns:
            # 检查分类过滤
            if categories and redactor_pattern.category not in categories:
                continue
                
            if pattern.search(text):
                return True

        return False

    def get_sensitive_parts(self, text: str,
                           categories: Optional[List[PatternCategory]] = None) -> List[Dict[str, Any]]:
        """获取文本中的敏感信息部分

        Args:
            text: 文本
            categories: 指定要处理的模式分类

        Returns:
            敏感信息部分列表，包含匹配内容和模式信息
        """
        sensitive_parts = []

        for pattern, redactor_pattern in self._patterns:
            # 检查分类过滤
            if categories and redactor_pattern.category not in categories:
                continue
                
            matches = pattern.finditer(text)
            for match in matches:
                sensitive_parts.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'pattern_name': redactor_pattern.name,
                    'category': redactor_pattern.category.value,
                    'description': redactor_pattern.description
                })

        return sensitive_parts

    def get_pattern_names(self) -> List[str]:
        """获取所有自定义模式名称

        Returns:
            模式名称列表
        """
        return list(self._custom_patterns.keys())

    def get_patterns_by_category(self, category: PatternCategory) -> List[RedactorPattern]:
        """根据分类获取模式

        Args:
            category: 模式分类

        Returns:
            该分类下的模式列表
        """
        patterns = []
        for _, redactor_pattern in self._patterns:
            if redactor_pattern.category == category:
                patterns.append(redactor_pattern)
        return patterns

    def set_replacement(self, replacement: str) -> None:
        """设置默认替换字符串

        Args:
            replacement: 替换字符串
        """
        self.replacement = replacement

    def clear_patterns(self) -> None:
        """清除所有自定义模式"""
        self._custom_patterns.clear()
        self._reorder_patterns()

    def reset_to_defaults(self, patterns: Optional[List[RedactorPattern]] = None) -> None:
        """重置为默认模式

        Args:
            patterns: 新的默认模式列表（可选）
        """
        self._patterns.clear()
        self._custom_patterns.clear()

        # 重新初始化默认模式
        default_patterns = patterns or self._get_default_patterns()
        default_patterns.sort(key=lambda p: p.priority, reverse=True)

        for redactor_pattern in default_patterns:
            self._compile_pattern(redactor_pattern)

    def validate_unicode_text(self, text: str) -> Dict[str, Any]:
        """验证文本的Unicode特性

        Args:
            text: 要验证的文本

        Returns:
            包含Unicode信息的字典
        """
        result = {
            'length': len(text),
            'has_chinese': False,
            'has_cjk': False,
            'has_non_ascii': False,
            'chinese_chars': [],
            'unicode_ranges': set()
        }

        for char in text:
            code_point = ord(char)
            
            # 检查中文字符
            if '\u4e00' <= char <= '\u9fff':
                result['has_chinese'] = True
                result['chinese_chars'].append(char)
            
            # 检查CJK字符
            if (('\u4e00' <= char <= '\u9fff') or  # CJK统一汉字
                ('\u3400' <= char <= '\u4dbf') or  # CJK扩展A
                ('\u20000' <= char <= '\u2a6df') or  # CJK扩展B
                ('\u2a700' <= char <= '\u2ebef')):  # CJK扩展C-F
                result['has_cjk'] = True
            
            # 检查非ASCII字符
            if code_point > 127:
                result['has_non_ascii'] = True
            
            # 记录Unicode范围
            if code_point <= 0x7F:
                result['unicode_ranges'].add('ASCII')
            elif code_point <= 0xFF:
                result['unicode_ranges'].add('Latin-1')
            elif code_point <= 0xFFFF:
                result['unicode_ranges'].add('BMP')
            else:
                result['unicode_ranges'].add('Supplementary')

        result['unicode_ranges'] = list(result['unicode_ranges'])
        return result


# 向后兼容的别名
Redactor = Redactor