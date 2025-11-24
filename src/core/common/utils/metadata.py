"""统一元数据管理器"""

from typing import Any, Dict, Optional, Union
import json


class MetadataManager:
    """统一元数据管理器"""
    
    @staticmethod
    def normalize_metadata(metadata: Any) -> Dict[str, Any]:
        """标准化元数据为字典格式
        
        Args:
            metadata: 原始元数据
            
        Returns:
            标准化的元数据字典
        """
        if metadata is None:
            return {}
        
        if isinstance(metadata, dict):
            return dict(metadata)
        elif isinstance(metadata, (list, tuple, str, bytes)):
            # 对于内置类型如列表、元组、字符串、字节等，直接返回空字典
            return {}
        elif hasattr(metadata, '__getitem__') and hasattr(metadata, '__iter__'):
            # 检查是否为类映射对象（具有__getitem__和__iter__）
            try:
                # 尝试构建字典
                result = {}
                # 优先使用keys方法
                if hasattr(metadata, 'keys'):
                    for key in metadata.keys():
                        try:
                            result[key] = metadata[key]
                        except (TypeError, KeyError, IndexError):
                            continue
                else:
                    # 使用迭代器
                    for key in metadata:
                        try:
                            result[key] = metadata[key]
                        except (TypeError, KeyError, IndexError):
                            continue
                return result
            except (TypeError, KeyError):
                return {}
        elif hasattr(metadata, '__dict__'):
            # 如果不是类映射对象，则检查是否具有__dict__属性
            return dict(metadata.__dict__)
        else:
            # 对于其他类型，如字符串、数字等，返回空字典
            return {}
    
    @staticmethod
    def merge_metadata(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并元数据
        
        Args:
            base: 基础元数据
            override: 覆盖元数据
            
        Returns:
            合并后的元数据
        """
        result = base.copy()
        result.update(override)
        return result
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """验证元数据
        
        Args:
            metadata: 元数据字典
            schema: 验证模式
            
        Returns:
            是否验证通过
        """
        # 简化的验证逻辑，实际可以使用jsonschema等库
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in metadata:
                return False
        
        return True
    
    @staticmethod
    def extract_field(metadata: Dict[str, Any], field: str, default: Any = None) -> Any:
        """提取字段值
        
        Args:
            metadata: 元数据字典
            field: 字段名
            default: 默认值
            
        Returns:
            字段值
        """
        return metadata.get(field, default)
    
    @staticmethod
    def set_field(metadata: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """设置字段值
        
        Args:
            metadata: 元数据字典
            field: 字段名
            value: 字段值
            
        Returns:
            更新后的元数据
        """
        result = metadata.copy()
        result[field] = value
        return result
    
    @staticmethod
    def remove_field(metadata: Dict[str, Any], field: str) -> Dict[str, Any]:
        """移除字段
        
        Args:
            metadata: 元数据字典
            field: 字段名
            
        Returns:
            更新后的元数据
        """
        result = metadata.copy()
        result.pop(field, None)
        return result
    
    @staticmethod
    def to_json(metadata: Dict[str, Any], indent: int = 2) -> str:
        """转换为JSON字符串
        
        Args:
            metadata: 元数据字典
            indent: 缩进空格数
            
        Returns:
            JSON字符串
        """
        return json.dumps(metadata, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def from_json(json_str: str) -> Dict[str, Any]:
        """从JSON字符串解析
        
        Args:
            json_str: JSON字符串
            
        Returns:
            元数据字典
        """
        result: Dict[str, Any] = json.loads(json_str)
        return result