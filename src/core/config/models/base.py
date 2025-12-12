"""基础配置模型"""

from abc import ABC
from typing import Any, Dict, TypeVar, Type, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, PrivateAttr


T = TypeVar("T", bound="BaseConfig")


class BaseConfig(BaseModel, ABC):
    """基础配置模型
    
    提供所有配置类的统一接口，包括验证、合并、更新和锁定等功能。
    """

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段
        validate_assignment=True,  # 赋值时验证
        use_enum_values=True,  # 使用枚举值
    )
    
    # 元数据（不参与序列化）
    _metadata: dict = PrivateAttr(default_factory=dict)
    _locked: bool = PrivateAttr(default=False)
    _created_at: datetime = PrivateAttr(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（排除 None 值）"""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """从字典创建配置"""
        return cls(**data)

    def copy(self: T, deep: bool = True, **update: Any) -> T:
        """创建配置副本
        
        Args:
            deep: 是否深复制
            **update: 需要更新的字段
            
        Returns:
            新的配置实例
        """
        data = self.model_dump(exclude_none=False)
        if update:
            data.update(update)
        return self.__class__(**data)

    def merge_with(self: T, other: T) -> T:
        """与另一个相同类型的配置合并（深度合并）
        
        Args:
            other: 另一个配置实例，必须与 self 类型相同
            
        Returns:
            合并后的新配置实例
            
        Raises:
            TypeError: 如果 other 不是相同类型
        """
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Cannot merge {self.__class__.__name__} with {other.__class__.__name__}"
            )
        current_dict = self.to_dict()
        other_dict = other.to_dict()
        merged = _deep_merge(current_dict, other_dict)
        return self.__class__.from_dict(merged)

    def update(self: T, **kwargs: Any) -> T:
        """更新配置并返回新实例（不修改当前实例）
        
        Args:
            **kwargs: 需要更新的字段和值
            
        Returns:
            更新后的新配置实例
        """
        if self._locked:
            raise RuntimeError(
                f"Configuration {self.__class__.__name__} is locked and cannot be modified"
            )
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return self.__class__.from_dict(current_dict)
    
    # === 验证相关方法 ===
    
    def validate_business_rules(self) -> List[str]:
        """验证业务规则，返回错误列表（子类可覆盖）
        
        Returns:
            错误消息列表，为空表示验证通过
        """
        return []

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate_business_rules()) == 0
    
    # === 锁定机制 ===
    
    def lock(self) -> None:
        """锁定配置，防止修改（用于生产环境）"""
        self._locked = True

    def unlock(self) -> None:
        """解锁配置"""
        self._locked = False

    def is_locked(self) -> bool:
        """检查配置是否被锁定"""
        return self._locked
    
    # === 元数据方法 ===
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值或默认值
        """
        return self._metadata.get(key, default)
    
    def get_created_at(self) -> datetime:
        """获取配置创建时间"""
        return self._created_at


def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result