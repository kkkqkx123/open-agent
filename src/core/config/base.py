"""基础配置模型"""

from abc import ABC
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ConfigType(str, Enum):
    """配置类型枚举"""
    WORKFLOW = "workflow"
    TOOL = "tool"
    TOOL_SET = "tool_set"
    LLM = "llm"
    GRAPH = "graph"
    GLOBAL = "global"


class ValidationRule(BaseModel):
    """验证规则模型"""
    field: str = Field(..., description="要验证的字段")
    rule_type: str = Field(..., description="验证规则类型")
    value: Any = Field(None, description="验证值")
    message: Optional[str] = Field(None, description="验证失败时的错误消息")


class ConfigInheritance(BaseModel):
    """配置继承模型"""
    from_config: Union[str, List[str]] = Field(..., description="继承的配置路径")
    override_fields: List[str] = Field(default_factory=list, description="要覆盖的字段列表")
    merge_strategy: str = Field("deep", description="合并策略：deep, shallow, replace")


class ConfigMetadata(BaseModel):
    """配置元数据模型"""
    name: str = Field(..., description="配置名称")
    version: str = Field("1.0.0", description="配置版本")
    description: str = Field("", description="配置描述")
    author: str = Field("", description="配置作者")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    tags: List[str] = Field(default_factory=list, description="配置标签")


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