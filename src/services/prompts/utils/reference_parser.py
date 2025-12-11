"""引用解析器工具类

提供提示词引用解析的工具方法。
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


@dataclass
class ReferenceInfo:
    """引用信息"""
    ref_id: str
    version: Optional[str] = None
    alias: Optional[str] = None
    ref_type: str = "prompt"


class ReferenceParser:
    """引用解析器工具类
    
    支持解析各种引用格式：
    1. ref_id
    2. ref_id@version
    3. ref_id as alias
    4. ref_id@version as alias
    """
    
    # 编译正则表达式模式
    REFERENCE_PATTERN = re.compile(
        r'\{\{\s*ref\s*:\s*([^}]+)\s*\}\}',
        re.IGNORECASE
    )
    
    FILE_PATTERN = re.compile(
        r'\{\{\s*file\s*:\s*([^}]+)\s*\}\}',
        re.IGNORECASE
    )
    
    VARIABLE_PATTERN = re.compile(
        r'\{\{\s*var\s*:\s*([^}]+)\s*\}\}',
        re.IGNORECASE
    )
    
    ENV_PATTERN = re.compile(
        r'\{\{\s*env\s*:\s*([^}]+)\s*\}\}',
        re.IGNORECASE
    )
    
    CONFIG_PATTERN = re.compile(
        r'\{\{\s*config\s*:\s*([^}]+)\s*\}\}',
        re.IGNORECASE
    )
    
    CONDITIONAL_PATTERN = re.compile(
        r'\{\{\s*if\s+ref\s*:\s*([^}]+)\s*\}\}(.*?)\{\{\s*endif\s*\}\}',
        re.IGNORECASE | re.DOTALL
    )
    
    LOOP_PATTERN = re.compile(
        r'\{\{\s*for\s+(\w+)\s+in\s+(\w+)\s*\}\}(.*?)\{\{\s*endfor\s*\}\}',
        re.IGNORECASE | re.DOTALL
    )
    
    @classmethod
    def parse_reference_spec(cls, spec: str) -> ReferenceInfo:
        """解析引用规范
        
        Args:
            spec: 引用规范字符串
            
        Returns:
            引用信息对象
        """
        # 支持的格式：
        # 1. ref_id
        # 2. ref_id@version
        # 3. ref_id as alias
        # 4. ref_id@version as alias
        
        result = ReferenceInfo(ref_id=spec.strip())
        
        # 解析版本
        if "@" in spec:
            ref_part, version_part = spec.split("@", 1)
            result.ref_id = ref_part.strip()
            
            if " as " in version_part:
                version, alias = version_part.split(" as ", 1)
                result.version = version.strip()
                result.alias = alias.strip()
            else:
                result.version = version_part.strip()
        elif " as " in spec:
            ref_id, alias = spec.split(" as ", 1)
            result.ref_id = ref_id.strip()
            result.alias = alias.strip()
        
        return result
    
    @classmethod
    def extract_references(cls, content: str) -> List[Dict[str, Any]]:
        """从内容中提取所有引用
        
        Args:
            content: 内容字符串
            
        Returns:
            引用列表
        """
        references = []
        
        # 提取提示词引用
        for match in cls.REFERENCE_PATTERN.finditer(content):
            ref_spec = match.group(1).strip()
            ref_info = cls.parse_reference_spec(ref_spec)
            references.append({
                "type": "prompt",
                "ref_id": ref_info.ref_id,
                "version": ref_info.version,
                "alias": ref_info.alias,
                "match": match.group(0)
            })
        
        # 提取文件引用
        for match in cls.FILE_PATTERN.finditer(content):
            file_path = match.group(1).strip()
            references.append({
                "type": "file",
                "path": file_path,
                "match": match.group(0)
            })
        
        # 提取变量引用
        for match in cls.VARIABLE_PATTERN.finditer(content):
            var_name = match.group(1).strip()
            references.append({
                "type": "variable",
                "name": var_name,
                "match": match.group(0)
            })
        
        # 提取环境变量引用
        for match in cls.ENV_PATTERN.finditer(content):
            env_name = match.group(1).strip()
            references.append({
                "type": "env",
                "name": env_name,
                "match": match.group(0)
            })
        
        # 提取配置引用
        for match in cls.CONFIG_PATTERN.finditer(content):
            config_path = match.group(1).strip()
            references.append({
                "type": "config",
                "path": config_path,
                "match": match.group(0)
            })
        
        # 提取条件引用
        for match in cls.CONDITIONAL_PATTERN.finditer(content):
            ref_spec = match.group(1).strip()
            conditional_content = match.group(2)
            ref_info = cls.parse_reference_spec(ref_spec)
            references.append({
                "type": "conditional",
                "ref_id": ref_info.ref_id,
                "version": ref_info.version,
                "alias": ref_info.alias,
                "content": conditional_content,
                "match": match.group(0)
            })
        
        # 提取循环引用
        for match in cls.LOOP_PATTERN.finditer(content):
            var_name = match.group(1)
            collection_name = match.group(2)
            loop_content = match.group(3)
            references.append({
                "type": "loop",
                "variable": var_name,
                "collection": collection_name,
                "content": loop_content,
                "match": match.group(0)
            })
        
        return references
    
    @classmethod
    def find_reference_patterns(cls, content: str, pattern_type: str) -> List[re.Match]:
        """查找特定类型的引用模式
        
        Args:
            content: 内容字符串
            pattern_type: 模式类型 ("reference", "file", "variable", "env", "config", "conditional", "loop")
            
        Returns:
            匹配对象列表
        """
        pattern_map = {
            "reference": cls.REFERENCE_PATTERN,
            "file": cls.FILE_PATTERN,
            "variable": cls.VARIABLE_PATTERN,
            "env": cls.ENV_PATTERN,
            "config": cls.CONFIG_PATTERN,
            "conditional": cls.CONDITIONAL_PATTERN,
            "loop": cls.LOOP_PATTERN
        }
        
        pattern = pattern_map.get(pattern_type)
        if not pattern:
            logger.warning(f"未知的模式类型: {pattern_type}")
            return []
        
        return list(pattern.finditer(content))
    
    @classmethod
    def validate_reference_spec(cls, spec: str) -> List[str]:
        """验证引用规范
        
        Args:
            spec: 引用规范字符串
            
        Returns:
            验证错误列表
        """
        errors = []
        
        if not spec or not spec.strip():
            errors.append("引用规范不能为空")
            return errors
        
        spec = spec.strip()
        
        # 检查是否包含非法字符
        if re.search(r'[<>{}[\]\\]', spec):
            errors.append("引用规范包含非法字符")
        
        # 检查版本格式
        if "@" in spec:
            parts = spec.split("@", 1)
            if len(parts) != 2:
                errors.append("版本引用格式错误")
            else:
                ref_id, version_part = parts
                if not ref_id.strip():
                    errors.append("引用ID不能为空")
                
                if " as " in version_part:
                    version, alias = version_part.split(" as ", 1)
                    if not version.strip():
                        errors.append("版本号不能为空")
                    if not alias.strip():
                        errors.append("别名不能为空")
                elif not version_part.strip():
                    errors.append("版本号不能为空")
        
        # 检查别名格式
        elif " as " in spec:
            parts = spec.split(" as ", 1)
            if len(parts) != 2:
                errors.append("别名引用格式错误")
            else:
                ref_id, alias = parts
                if not ref_id.strip():
                    errors.append("引用ID不能为空")
                if not alias.strip():
                    errors.append("别名不能为空")
        
        return errors
    
    @classmethod
    def normalize_reference_spec(cls, spec: str) -> str:
        """标准化引用规范
        
        Args:
            spec: 原始引用规范
            
        Returns:
            标准化后的引用规范
        """
        spec = spec.strip()
        
        # 移除多余的空格
        spec = re.sub(r'\s+', ' ', spec)
        
        # 标准化 "as" 关键字周围的空格
        spec = re.sub(r'\s+as\s+', ' as ', spec)
        
        # 标准化 "@" 符号周围的空格
        spec = re.sub(r'\s*@\s*', '@', spec)
        
        return spec
    
    @classmethod
    def is_reference_string(cls, content: str) -> bool:
        """检查字符串是否包含引用
        
        Args:
            content: 内容字符串
            
        Returns:
            是否包含引用
        """
        patterns = [
            cls.REFERENCE_PATTERN,
            cls.FILE_PATTERN,
            cls.VARIABLE_PATTERN,
            cls.ENV_PATTERN,
            cls.CONFIG_PATTERN,
            cls.CONDITIONAL_PATTERN,
            cls.LOOP_PATTERN
        ]
        
        return any(pattern.search(content) for pattern in patterns)
    
    @classmethod
    def count_references(cls, content: str, reference_type: Optional[str] = None) -> int:
        """统计引用数量
        
        Args:
            content: 内容字符串
            reference_type: 引用类型，如果为None则统计所有类型
            
        Returns:
            引用数量
        """
        if reference_type:
            matches = cls.find_reference_patterns(content, reference_type)
            return len(matches)
        else:
            total = 0
            for pattern_type in ["reference", "file", "variable", "env", "config", "conditional", "loop"]:
                matches = cls.find_reference_patterns(content, pattern_type)
                total += len(matches)
            return total