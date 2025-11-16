"""API配置"""
import os
from typing import Optional
from pydantic import BaseModel, Field


class APISettings(BaseModel):
    """API设置"""
    
    # 应用设置
    app_name: str = Field(default="Modular Agent API", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="环境")
    
    # 服务器设置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    reload: bool = Field(default=False, description="自动重载")
    
    # 数据库设置
    database_url: Optional[str] = Field(default=None, description="数据库URL")
    data_path: str = Field(default="data", description="数据存储路径")
    
    # 缓存设置
    cache_ttl: int = Field(default=300, description="缓存TTL（秒）")
    cache_max_size: int = Field(default=1000, description="缓存最大大小")
    cache_fallback_enabled: bool = Field(default=True, description="是否启用缓存降级机制")
    cache_invalidation_enabled: bool = Field(default=True, description="是否启用缓存失效机制")
    cache_enable_stats: bool = Field(default=True, description="是否启用缓存统计")
    
    # 日志设置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    
    # 安全设置
    secret_key: str = Field(default="your-secret-key-here", description="密钥")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间")
    
    # CORS设置
    cors_origins: list = Field(default=["*"], description="允许的CORS源")
    cors_methods: list = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="允许的CORS方法")
    cors_headers: list = Field(default=["*"], description="允许的CORS头")
    
    # 限流设置
    rate_limit_per_minute: int = Field(default=60, description="每分钟请求限制")
    
    # WebSocket设置
    websocket_ping_interval: int = Field(default=20, description="WebSocket心跳间隔（秒）")
    websocket_ping_timeout: int = Field(default=10, description="WebSocket心跳超时（秒）")


# 全局设置实例
settings = APISettings()


def get_settings() -> APISettings:
    """获取设置实例"""
    return settings


def update_settings(**kwargs):
    """更新设置"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)