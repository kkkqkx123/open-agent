"""
工具配置模型

定义各种工具类型的配置数据结构。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ToolType(Enum):
    """工具类型枚举"""
    BUILTIN = "builtin"      # 无状态内置工具
    NATIVE = "native"        # 有状态原生工具
    REST = "rest"           # 有状态REST工具
    MCP = "mcp"            # 有状态MCP工具


@dataclass(kw_only=True)
class StateManagerConfig:
    """状态管理器配置"""
    
    # 基础配置
    manager_type: str = "memory"  # "memory", "persistent", "session", "distributed"
    ttl: Optional[int] = None  # 状态生存时间（秒）
    auto_cleanup: bool = True  # 自动清理过期状态
    cleanup_interval: int = 300  # 清理间隔（秒）
    
    # 持久化配置
    persistence_path: Optional[str] = None  # 持久化路径
    persistence_format: str = "json"  # "json", "pickle", "sqlite"
    compression: bool = False  # 是否压缩存储
    
    # 分布式配置
    redis_url: Optional[str] = None  # Redis连接URL
    redis_prefix: str = "tool_state"  # Redis键前缀
    redis_db: int = 0  # Redis数据库编号
    
    # 会话配置
    session_isolation: bool = True  # 会话隔离
    max_states_per_session: int = 10  # 每会话最大状态数
    session_timeout: int = 3600  # 会话超时时间（秒）


@dataclass(kw_only=True)
class ConnectionStateConfig:
    """连接状态配置"""
    
    # 连接池配置
    pool_size: int = 10  # 连接池大小
    max_overflow: int = 20  # 最大溢出连接数
    pool_timeout: int = 30  # 连接池超时
    pool_recycle: int = 3600  # 连接回收时间（秒）
    
    # 连接配置
    timeout: int = 30  # 连接超时
    read_timeout: int = 60  # 读取超时
    write_timeout: int = 60  # 写入超时
    connect_timeout: int = 10  # 连接建立超时
    
    # Keep-alive配置
    keep_alive: bool = True  # 保持连接
    keep_alive_timeout: int = 30  # Keep-alive超时
    keep_alive_interval: int = 60  # Keep-alive间隔
    
    # 重试配置
    retry_attempts: int = 3  # 重试次数
    retry_delay: float = 1.0  # 重试延迟
    retry_backoff: float = 2.0  # 重试退避因子
    retry_jitter: bool = True  # 重试抖动


@dataclass(kw_only=True)
class BusinessStateConfig:
    """业务状态配置"""
    
    # 状态存储配置
    max_history_size: int = 1000  # 最大历史记录数
    max_state_size: int = 1024 * 1024  # 最大状态大小（字节）
    state_compression: bool = False  # 状态压缩
    
    # 版本控制配置
    versioning: bool = True  # 启用版本控制
    max_versions: int = 10  # 最大版本数
    auto_save: bool = True  # 自动保存
    
    # 同步配置
    sync_interval: int = 60  # 同步间隔（秒）
    sync_on_change: bool = True  # 变化时同步
    conflict_resolution: str = "last_write_wins"  # 冲突解决策略
    
    # 备份配置
    backup_enabled: bool = False  # 启用备份
    backup_interval: int = 3600  # 备份间隔（秒）
    backup_retention: int = 7  # 备份保留天数


@dataclass(kw_only=True)
class ToolConfig:
    """基础工具配置"""
    name: str
    tool_type: str
    description: str
    parameters_schema: Dict[str, Any]
    enabled: bool = True
    timeout: int = 30
    metadata: Optional[Dict[str, Any]] = None


@dataclass(kw_only=True)
class BuiltinToolConfig(ToolConfig):
    """无状态内置工具配置"""
    function_path: str  # 函数路径
    tool_type: str = "builtin"  # 无状态内置工具
    # 无状态配置


@dataclass(kw_only=True)
class NativeToolConfig(ToolConfig):
    """有状态原生工具配置"""
    function_path: str
    tool_type: str = "native"
    state_config: StateManagerConfig = field(default_factory=StateManagerConfig)
    business_config: BusinessStateConfig = field(default_factory=BusinessStateConfig)
    state_injection: bool = True  # 是否注入状态参数
    state_parameter_name: str = "state"  # 状态参数名称


@dataclass(kw_only=True)
class RestToolConfig(ToolConfig):
    """有状态REST工具配置"""
    api_url: str  # API端点URL
    tool_type: str = "rest"
    method: str = "GET"  # HTTP方法
    headers: Dict[str, str] = field(default_factory=dict)  # 请求头
    auth_method: Optional[str] = None  # 认证方法
    api_key: Optional[str] = None  # API密钥
    state_config: StateManagerConfig = field(default_factory=StateManagerConfig)


@dataclass(kw_only=True)
class MCPToolConfig(ToolConfig):
    """有状态MCP工具配置"""
    mcp_server_url: str  # MCP服务器URL
    tool_type: str = "mcp"
    dynamic_schema: bool = False # 是否动态获取Schema
    state_config: StateManagerConfig = field(default_factory=StateManagerConfig)