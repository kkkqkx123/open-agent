"""基础配置模型"""

from abc import ABC
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class BaseConfig(BaseModel, ABC):
    """基础配置模型"""

    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段
        validate_assignment=True,  # 赋值时验证
        use_enum_values=True,  # 使用枚举值
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseConfig":
        """从字典创建配置"""
        return cls(**data)

    def merge_with(self, other: "BaseConfig") -> "BaseConfig":
        """与另一个配置合并"""
        current_dict = self.to_dict()
        other_dict = other.to_dict()

        # 深度合并字典
        merged = _deep_merge(current_dict, other_dict)
        return self.__class__.from_dict(merged)

    def update(self, **kwargs: Any) -> "BaseConfig":
        """更新配置"""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return self.__class__.from_dict(current_dict)


def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result