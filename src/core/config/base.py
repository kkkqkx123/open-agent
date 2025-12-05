"""基础配置模型"""

from src.services.logger.injection import get_logger
from abc import ABC
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from ..common.exceptions.config import ConfigError, ConfigValidationError
from ..common.error_management import handle_error, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


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
        try:
            # 输入验证
            if other is None:
                raise ConfigValidationError("合并的配置对象不能为None")
            
            if not isinstance(other, BaseConfig):
                raise ConfigValidationError(
                    f"合并对象必须是BaseConfig类型，实际类型: {type(other).__name__}"
                )

            current_dict = self.to_dict()
            other_dict = other.to_dict()

            # 深度合并字典
            merged = _deep_merge(current_dict, other_dict)
            return self.__class__.from_dict(merged)
            
        except ConfigValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "config_class": self.__class__.__name__,
                "other_config_class": other.__class__.__name__ if other else "None",
                "operation": "merge_with"
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise ConfigError(
                f"配置合并失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e

    def update(self, **kwargs: Any) -> "BaseConfig":
        """更新配置"""
        try:
            # 输入验证
            if not kwargs:
                logger.warning("更新配置时没有提供任何参数")
                return self

            current_dict = self.to_dict()
            
            # 验证更新参数
            for key, value in kwargs.items():
                if value is None:
                    logger.warning(f"更新配置时参数 {key} 的值为None")
            
            current_dict.update(kwargs)
            return self.__class__.from_dict(current_dict)
            
        except ConfigValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "config_class": self.__class__.__name__,
                "update_keys": list(kwargs.keys()),
                "operation": "update"
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise ConfigError(
                f"配置更新失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e


def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any], max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
    """安全的深度合并两个字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        max_depth: 最大递归深度
        current_depth: 当前递归深度
        
    Returns:
        合并后的字典
        
    Raises:
        ConfigValidationError: 输入验证失败
        ConfigError: 合并操作失败
    """
    try:
        # 输入验证
        if not isinstance(dict1, dict):
            raise ConfigValidationError(
                f"第一个参数必须是字典类型，实际类型: {type(dict1).__name__}"
            )
        
        if not isinstance(dict2, dict):
            raise ConfigValidationError(
                f"第二个参数必须是字典类型，实际类型: {type(dict2).__name__}"
            )
        
        # 递归深度检查
        if current_depth >= max_depth:
            raise ConfigError(f"配置合并深度超过限制: {max_depth}")
        
        result = dict1.copy()

        for key, value in dict2.items():
            try:
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    result[key] = _deep_merge(
                        result[key],
                        value,
                        max_depth,
                        current_depth + 1
                    )
                else:
                    # 直接赋值
                    result[key] = value
                    
            except Exception as e:
                # 记录字段级别的错误，但继续处理其他字段
                logger.warning(f"合并配置字段 {key} 失败: {e}")
                raise ConfigError(
                    f"无法合并配置字段 {key}: {e}",
                    details={
                        "field": key,
                        "field_type": type(value).__name__,
                        "existing_type": type(result.get(key)).__name__ if key in result else None,
                        "original_error": str(e)
                    }
                ) from e

        return result
        
    except ConfigValidationError:
        # 重新抛出验证错误
        raise
    except Exception as e:
        # 包装其他异常
        error_context = {
            "dict1_keys": list(dict1.keys()) if isinstance(dict1, dict) else None,
            "dict2_keys": list(dict2.keys()) if isinstance(dict2, dict) else None,
            "current_depth": current_depth,
            "max_depth": max_depth,
            "operation": "_deep_merge"
        }
        
        # 使用统一错误处理
        handle_error(e, error_context)
        
        raise ConfigError(
            f"深度合并失败: {e}",
            details={"original_error": str(e), **error_context}
        ) from e