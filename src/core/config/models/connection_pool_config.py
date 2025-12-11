"""连接池配置模型"""

from pydantic import Field
from .base import BaseConfig


class ConnectionPoolConfig(BaseConfig):
    """连接池配置模型"""
    
    max_connections: int = Field(10, description="最大连接数")
    max_keepalive: int = Field(10, description="最大保活连接数")
    timeout: float = Field(30.0, description="连接超时时间（秒）")
    keepalive_expiry: float = Field(300.0, description="保活连接过期时间（秒）")
    enabled: bool = Field(True, description="是否启用连接池")
    
    def __hash__(self):
        """使配置对象可哈希，以便用作字典键"""
        return hash((
            self.max_connections,
            self.max_keepalive,
            self.timeout,
            self.keepalive_expiry,
            self.enabled
        ))