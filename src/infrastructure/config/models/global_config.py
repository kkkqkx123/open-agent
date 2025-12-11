"""全局配置数据模型

提供全局配置所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LogOutputClientConfig(BaseModel):
    """日志输出配置数据模型"""

    type: str = Field(..., description="输出类型：console, file")
    level: str = Field("INFO", description="日志级别")
    format: str = Field("text", description="日志格式：text, json")
    path: Optional[str] = Field(None, description="文件路径（仅文件输出）")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "LogOutputClientConfig":
        """从字典创建配置"""
        return cls(**data)


class GlobalClientConfig(BaseModel):
    """全局配置数据模型
    
    包含全局配置所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """

    # 日志配置
    log_level: str = Field("INFO", description="全局日志级别")
    log_outputs: List[LogOutputClientConfig] = Field(
        default_factory=list, description="日志输出配置列表"
    )

    # 环境配置
    env: str = Field("development", description="运行环境")
    debug: bool = Field(False, description="调试模式")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "GlobalClientConfig":
        """从字典创建配置"""
        # 处理log_outputs字段
        if "log_outputs" in data:
            log_outputs = []
            for output_config in data["log_outputs"]:
                if isinstance(output_config, dict):
                    log_outputs.append(LogOutputClientConfig(**output_config))
                else:
                    log_outputs.append(output_config)
            data["log_outputs"] = log_outputs
        
        return cls(**data)


__all__ = [
    "LogOutputClientConfig",
    "GlobalClientConfig"
]