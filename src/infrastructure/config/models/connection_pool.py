"""连接池配置数据模型

提供连接池所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from pydantic import BaseModel, Field


class ConnectionPoolClientConfig(BaseModel):
    """连接池配置数据模型
    
    包含连接池所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """
    
    max_connections: int = Field(10, description="最大连接数")
    max_keepalive: int = Field(10, description="最大保活连接数")
    timeout: float = Field(30.0, description="连接超时时间（秒）")
    keepalive_expiry: float = Field(300.0, description="保活连接过期时间（秒）")
    enabled: bool = Field(True, description="是否启用连接池")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionPoolClientConfig":
        """从字典创建配置"""
        return cls(**data)


__all__ = [
    "ConnectionPoolClientConfig"
]