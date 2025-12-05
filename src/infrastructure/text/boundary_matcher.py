"""边界匹配工具 - 提供精确的Unicode边界匹配功能"""

import re
from typing import Any, Pattern, Dict, Set, Optional, Union
from enum import Enum


class BoundaryType(Enum):
    """边界类型枚举"""
    WORD = "word"                    # 单词边界
    SENTENCE = "sentence"            # 句子边界
    UNICODE_CATEGORY = "unicode"     # Unicode分类边界
    CUSTOM = "custom"                # 自定义边界


class UnicodeCategory(Enum):
    """Unicode字符分类"""
    LETTER = "letter"                # 字母
    NUMBER = "number"                # 数字
    PUNCTUATION = "punctuation"      # 标点
    SYMBOL = "symbol"                # 符号
    SPACE = "space"                  # 空格
    CJK = "cjk"                      # 中日韩字符
    LATIN = "latin"                  # 拉丁字符
    OTHER = "other"                  # 其他


class BoundaryMatcher:
    """边界匹配器 - 提供精确的边界匹配功能"""

    def __init__(self):
        """初始化边界匹配器"""
        self._unicode_patterns = self._build_unicode_patterns()
        self._boundary_cache: Dict[str, Pattern] = {}

    def _build_unicode_patterns(self) -> Dict[UnicodeCategory, str]:
        """构建Unicode字符分类模式"""
        return {
            UnicodeCategory.LETTER: r"[A-Za-z\u00c0-\u00ff\u0100-\u017f\u0180-\u024f]",
            UnicodeCategory.NUMBER: r"[0-9\u0660-\u0669\u06f0-\u06f9]",
            UnicodeCategory.PUNCTUATION: r"[.,;:!?\"'()\\[\\]{}@#%&*+-=<>/\\\\]",
            UnicodeCategory.SYMBOL: r"[~`^|]",
            UnicodeCategory.SPACE: r"[ \t\r\n\f\v]",
            UnicodeCategory.CJK: r"[\u4e00-\u9fff\u3400-\u4dbf]",
            UnicodeCategory.LATIN: r"[A-Za-zÀ-ÖØ-öø-ÿ]",
            UnicodeCategory.OTHER: r"[^A-Za-z0-9\u00c0-\u00ff\u0100-\u017f\u0180-\u024f\u0660-\u0669\u06f0-\u06f9.,;:!?\"'()\\[\\]{}@#%&*+-=<>/\\\\~`^| \t\r\n\f\v]"
        }

    def get_unicode_category(self, char: str) -> UnicodeCategory:
        """获取字符的Unicode分类

        Args:
            char: 单个字符

        Returns:
            Unicode分类
        """
        if not char:
            return UnicodeCategory.OTHER

        code_point = ord(char)
        
        # 检查CJK字符
        if (('\u4e00' <= char <= '\u9fff') or  # CJK统一汉字
            ('\u3400' <= char <= '\u4dbf') or  # CJK扩展A
            (code_point >= 0x20000 and code_point <= 0x2a6df)):  # CJK扩展B
            return UnicodeCategory.CJK
        
        # 检查拉丁字符
        if (('\u0041' <= char <= '\u005a') or  # A-Z
            ('\u0061' <= char <= '\u007a') or  # a-z
            ('\u00c0' <= char <= '\u00ff')):    # 拉丁扩展A
            return UnicodeCategory.LATIN
        
        # 使用unicodedata模块检查其他分类
        import unicodedata
        category = unicodedata.category(char)
        
        if category.startswith('L'):  # Letter
            return UnicodeCategory.LETTER
        elif category.startswith('N'):  # Number
            return UnicodeCategory.NUMBER
        elif category.startswith('P'):  # Punctuation
            return UnicodeCategory.PUNCTUATION
        elif category.startswith('S'):  # Symbol
            return UnicodeCategory.SYMBOL
        elif category.startswith('Z'):  # Separator
            return UnicodeCategory.SPACE
        else:
            return UnicodeCategory.OTHER

    def create_boundary_pattern(self, 
                               pattern: str,
                               left_boundary: Optional[Union[BoundaryType, Set[UnicodeCategory]]] = None,
                               right_boundary: Optional[Union[BoundaryType, Set[UnicodeCategory]]] = None,
                               flags: int = 0) -> Pattern:
        """创建带边界匹配的模式

        Args:
            pattern: 核心匹配模式
            left_boundary: 左边界类型或字符分类集合
            right_boundary: 右边界类型或字符分类集合
            flags: 正则表达式标志

        Returns:
            编译后的正则表达式模式
        """
        cache_key = f"{pattern}_{left_boundary}_{right_boundary}_{flags}"
        if cache_key in self._boundary_cache:
            return self._boundary_cache[cache_key]

        # 构建左边界
        left_pattern = ""
        if left_boundary:
            if isinstance(left_boundary, BoundaryType):
                left_pattern = self._get_boundary_pattern(left_boundary, "left")
            elif isinstance(left_boundary, set):
                left_pattern = self._get_category_boundary_pattern(left_boundary, "left")

        # 构建右边界
        right_pattern = ""
        if right_boundary:
            if isinstance(right_boundary, BoundaryType):
                right_pattern = self._get_boundary_pattern(right_boundary, "right")
            elif isinstance(right_boundary, set):
                right_pattern = self._get_category_boundary_pattern(right_boundary, "right")

        # 组合完整模式
        full_pattern = f"{left_pattern}({pattern}){right_pattern}"
        
        # 添加Unicode标志
        flags |= re.UNICODE
        
        compiled_pattern = re.compile(full_pattern, flags)
        self._boundary_cache[cache_key] = compiled_pattern
        return compiled_pattern

    def _get_boundary_pattern(self, boundary_type: BoundaryType, side: str) -> str:
        """获取边界类型对应的模式

        Args:
            boundary_type: 边界类型
            side: 边界方向 ("left" 或 "right")

        Returns:
            边界模式字符串
        """
        if boundary_type == BoundaryType.WORD:
            return r"\b" if side == "left" else r"\b"
        elif boundary_type == BoundaryType.SENTENCE:
            return r"(?<=^|[.!?]\s+)" if side == "left" else r"(?=[.!?]|$)"
        elif boundary_type == BoundaryType.UNICODE_CATEGORY:
            # 使用默认的字母数字边界
            return r"(?<![A-Za-z0-9\u4e00-\u9fff])" if side == "left" else r"(?![A-Za-z0-9\u4e00-\u9fff])"
        else:
            return ""

    def _get_category_boundary_pattern(self, categories: Set[UnicodeCategory], side: str) -> str:
        """获取字符分类边界模式

        Args:
            categories: 字符分类集合
            side: 边界方向

        Returns:
            边界模式字符串
        """
        # 构建字符类
        char_classes = []
        for category in categories:
            if category in self._unicode_patterns:
                char_classes.append(self._unicode_patterns[category])
        
        if not char_classes:
            return ""
        
        char_class = f"[{'|'.join(char_classes)}]"
        
        if side == "left":
            return f"(?<!{char_class})"
        else:
            return f"(?!{char_class})"

    def create_email_pattern(self, flags: int = re.IGNORECASE) -> Pattern:
        """创建精确的邮箱匹配模式

        Args:
            flags: 正则表达式标志

        Returns:
            邮箱匹配模式
        """
        email_core = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        
        # 使用简单的边界匹配，避免look-behind的固定宽度限制
        pattern = f"(?<![a-zA-Z0-9._%+-])({email_core})(?![a-zA-Z0-9.-])"
        return re.compile(pattern, flags | re.UNICODE)

    def create_phone_pattern(self, country: str = "china", flags: int = 0) -> Pattern:
        """创建精确的电话号码匹配模式

        Args:
            country: 国家代码
            flags: 正则表达式标志

        Returns:
            电话号码匹配模式
        """
        if country == "china":
            phone_core = r"1[3-9]\d{9}"
        elif country == "international":
            phone_core = r"\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
        else:
            phone_core = r"\d{7,15}"
        
        # 电话号码边界：前后不能是数字，使用自定义边界以支持中文环境
        return self.create_boundary_pattern(
            phone_core,
            left_boundary={UnicodeCategory.NUMBER},
            right_boundary={UnicodeCategory.NUMBER},
            flags=flags
        )

    def create_id_card_pattern(self, country: str = "china", flags: int = 0) -> Pattern:
        """创建精确的身份证号匹配模式

        Args:
            country: 国家代码
            flags: 正则表达式标志

        Returns:
            身份证号匹配模式
        """
        if country == "china":
            # 18位身份证：6位地区码 + 8位出生日期 + 3位顺序码 + 1位校验码
            id_core = r"[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]"
        else:
            id_core = r"\d{8,20}"
        
        # 身份证号边界：前后不能是数字
        return self.create_boundary_pattern(
            id_core,
            left_boundary=BoundaryType.WORD,
            right_boundary=BoundaryType.WORD,
            flags=flags
        )

    def create_chinese_name_pattern(self, flags: int = 0) -> Pattern:
        """创建精确的中文姓名匹配模式

        Args:
            flags: 正则表达式标志

        Returns:
            中文姓名匹配模式
        """
        # 中文姓名：2-4个中文字符
        name_core = r"[\u4e00-\u9fff]{2,4}"
        
        # 中文姓名边界：前后不能是中文字符，使用正向和负向查找
        pattern = f"(?<![\u4e00-\u9fff])({name_core})(?![\u4e00-\u9fff])"
        return re.compile(pattern, flags | re.UNICODE)

    def create_credit_card_pattern(self, flags: int = 0) -> Pattern:
        """创建精确的信用卡号匹配模式

        Args:
            flags: 正则表达式标志

        Returns:
            信用卡号匹配模式
        """
        # 常见信用卡号模式
        card_core = r"(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})"
        
        # 信用卡号边界：前后不能是数字
        return self.create_boundary_pattern(
            card_core,
            left_boundary=BoundaryType.WORD,
            right_boundary=BoundaryType.WORD,
            flags=flags
        )

    def create_api_key_pattern(self, provider: str = "openai", flags: int = 0) -> Pattern:
        """创建精确的API密钥匹配模式

        Args:
            provider: 提供商名称
            flags: 正则表达式标志

        Returns:
            API密钥匹配模式
        """
        if provider == "openai":
            key_core = r"sk-[a-zA-Z0-9]{20,}"
        elif provider == "anthropic":
            key_core = r"sk-ant-api03-[a-zA-Z0-9_-]{95}"
        elif provider == "google":
            key_core = r"AIza[a-zA-Z0-9_-]{35}"
        else:
            key_core = r"[a-zA-Z0-9_-]{20,}"
        
        # API密钥边界：前后不能是字母数字字符
        return self.create_boundary_pattern(
            key_core,
            left_boundary={UnicodeCategory.LETTER, UnicodeCategory.NUMBER},
            right_boundary={UnicodeCategory.LETTER, UnicodeCategory.NUMBER},
            flags=flags
        )

    def test_boundary_matching(self, pattern: Pattern, test_text: str) -> Dict[str, Any]:
        """测试边界匹配效果

        Args:
            pattern: 正则表达式模式
            test_text: 测试文本

        Returns:
            测试结果字典
        """
        matches = list(pattern.finditer(test_text))
        
        result = {
            'pattern': pattern.pattern,
            'test_text': test_text,
            'matches': [],
            'total_matches': len(matches)
        }
        
        for match in matches:
            result['matches'].append({
                'matched_text': match.group(),
                'start': match.start(),
                'end': match.end(),
                'context_before': test_text[max(0, match.start()-10):match.start()],
                'context_after': test_text[match.end():min(len(test_text), match.end()+10)]
            })
        
        return result

    def analyze_text_boundaries(self, text: str) -> Dict[str, Any]:
        """分析文本的边界特性

        Args:
            text: 要分析的文本

        Returns:
            边界分析结果
        """
        result = {
            'length': len(text),
            'character_boundaries': [],
            'unicode_categories': {},
            'potential_boundaries': []
        }
        
        # 分析每个字符的边界特性
        for i, char in enumerate(text):
            category = self.get_unicode_category(char)
            
            if category not in result['unicode_categories']:
                result['unicode_categories'][category] = []
            
            result['unicode_categories'][category].append({
                'char': char,
                'position': i,
                'code_point': ord(char)
            })
            
            # 检查边界变化
            if i > 0:
                prev_char = text[i-1]
                prev_category = self.get_unicode_category(prev_char)
                
                if category != prev_category:
                    result['potential_boundaries'].append({
                        'position': i,
                        'before': prev_char,
                        'after': char,
                        'before_category': prev_category.value,
                        'after_category': category.value
                    })
        
        return result


# 全局边界匹配器实例
boundary_matcher = BoundaryMatcher()