"""
配置模型定义
使用Pydantic进行类型验证和序列化
"""

from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from pathlib import Path
from pydantic import BaseModel, Field, validator
from enum import Enum


class ConfigType(str, Enum):
    """配置类型枚举"""
    LLM = "llm"
    TOOL = "tool"
    TOOL_SET = "tool_set"
    GLOBAL = "global"
    WORKFLOW = "workflow"


class BaseConfig(BaseModel):
    """基础配置模型"""
    
    class Config:
        """Pydantic配置"""
        extra = "allow"  # 允许额外字段
        validate_assignment = True  # 赋值时验证
        use_enum_values = True  # 使用枚举值
    
    def merge_with(self, other: "BaseConfig") -> "BaseConfig":
        """与另一个配置合并"""
        # 获取两个字典
        self_dict = self.dict()
        other_dict = other.dict()
        
        # 合并配置
        merged = {**other_dict, **self_dict}
        
        # 创建新的配置实例
        return self.__class__(**merged)
    
    def validate_config(self) -> None:
        """验证配置"""
        # Pydantic会自动验证，这里可以添加自定义验证逻辑
        pass


class LLMConfig(BaseConfig):
    """LLM配置模型"""
    
    # 基础配置
    name: str = Field(description="LLM名称")
    provider: str = Field(description="提供商")
    model: str = Field(description="模型名称")
    
    # 连接配置
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="基础URL")
    timeout: Optional[int] = Field(default=30, description="超时时间(秒)")
    max_retries: Optional[int] = Field(default=3, description="最大重试次数")
    
    # 模型参数
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=2048, ge=1, description="最大token数")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="top_p参数")
    
    # 功能配置
    supports_function_calling: Optional[bool] = Field(default=False, description="是否支持函数调用")
    supports_streaming: Optional[bool] = Field(default=True, description="是否支持流式输出")
    
    # 池配置
    pool_size: Optional[int] = Field(default=5, ge=1, description="连接池大小")
    pool_timeout: Optional[int] = Field(default=10, description="连接池超时时间")
    
    # 继承配置
    inherits_from: Optional[Union[str, List[str]]] = Field(default=None, description="继承的配置")
    
    @validator('provider')
    def validate_provider(cls, v):
        """验证提供商"""
        valid_providers = ['openai', 'anthropic', 'gemini', 'mock', 'human_relay']
        if v not in valid_providers:
            raise ValueError(f'不支持的提供商: {v}，支持的提供商: {valid_providers}')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """验证温度参数"""
        if v is not None and (v < 0.0 or v > 2.0):
            raise ValueError('温度参数必须在0.0到2.0之间')
        return v
    
    @validator('top_p')
    def validate_top_p(cls, v):
        """验证top_p参数"""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('top_p参数必须在0.0到1.0之间')
        return v


class ToolConfig(BaseConfig):
    """工具配置模型"""
    
    # 基础配置
    name: str = Field(description="工具名称")
    type: str = Field(description="工具类型")
    description: Optional[str] = Field(default=None, description="工具描述")
    
    # 功能配置
    enabled: Optional[bool] = Field(default=True, description="是否启用")
    timeout: Optional[int] = Field(default=30, description="超时时间(秒)")
    max_retries: Optional[int] = Field(default=3, description="最大重试次数")
    
    # 参数配置
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="工具参数")
    required_params: Optional[List[str]] = Field(default_factory=list, description="必需参数")
    
    # 权限配置
    requires_auth: Optional[bool] = Field(default=False, description="是否需要认证")
    auth_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="认证配置")
    
    # 缓存配置
    cache_enabled: Optional[bool] = Field(default=False, description="是否启用缓存")
    cache_ttl: Optional[int] = Field(default=300, description="缓存过期时间(秒)")
    
    # 继承配置
    inherits_from: Optional[Union[str, List[str]]] = Field(default=None, description="继承的配置")
    
    @validator('type')
    def validate_tool_type(cls, v):
        """验证工具类型"""
        valid_types = ['rest', 'mcp', 'rest', 'external']
        if v not in valid_types:
            raise ValueError(f'不支持的工具类型: {v}，支持的类型: {valid_types}')
        return v


class ToolSetConfig(BaseConfig):
    """工具集配置模型"""
    
    # 基础配置
    name: str = Field(description="工具集名称")
    description: Optional[str] = Field(default=None, description="工具集描述")
    
    # 工具配置
    tools: Optional[List[str]] = Field(default_factory=list, description="包含的工具")
    tool_configs: Optional[Dict[str, ToolConfig]] = Field(default_factory=dict, description="工具配置")
    
    # 分类配置
    category: Optional[str] = Field(default="general", description="工具集分类")
    tags: Optional[List[str]] = Field(default_factory=list, description="工具集标签")
    
    # 权限配置
    requires_auth: Optional[bool] = Field(default=False, description="工具集是否需要认证")
    allowed_roles: Optional[List[str]] = Field(default_factory=list, description="允许的角色")
    
    # 执行配置
    parallel_execution: Optional[bool] = Field(default=False, description="是否并行执行")
    execution_order: Optional[List[str]] = Field(default_factory=list, description="执行顺序")
    
    # 继承配置
    inherits_from: Optional[Union[str, List[str]]] = Field(default=None, description="继承的配置")
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    
    @validator('category')
    def validate_category(cls, v):
        """验证分类"""
        valid_categories = ['general', 'development', 'analysis', 'automation', 'integration']
        if v not in valid_categories:
            raise ValueError(f'不支持的工具集分类: {v}，支持的分类: {valid_categories}')
        return v


class GlobalConfig(BaseConfig):
    """全局配置模型"""
    
    # 应用配置
    app_name: Optional[str] = Field(default="Modular Agent Framework", description="应用名称")
    app_version: Optional[str] = Field(default="1.0.0", description="应用版本")
    environment: Optional[str] = Field(default="development", description="运行环境")
    
    # 日志配置
    log_level: Optional[str] = Field(default="INFO", description="日志级别")
    log_format: Optional[str] = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    
    # 性能配置
    max_workers: Optional[int] = Field(default=4, ge=1, description="最大工作线程数")
    task_timeout: Optional[int] = Field(default=300, ge=1, description="任务超时时间")
    
    # 存储配置
    data_dir: Optional[str] = Field(default="./data", description="数据目录")
    cache_dir: Optional[str] = Field(default="./cache", description="缓存目录")
    
    # 安全配置
    encryption_key: Optional[str] = Field(default=None, description="加密密钥")
    allowed_hosts: Optional[List[str]] = Field(default_factory=list, description="允许的主机")
    
    # 功能开关
    features: Optional[Dict[str, bool]] = Field(default_factory=dict, description="功能开关")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            raise ValueError(f'不支持的日志级别: {v}，支持的级别: {valid_levels}')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """验证运行环境"""
        valid_environments = ['development', 'testing', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'不支持的环境: {v}，支持的环境: {valid_environments}')
        return v


# 配置类型映射
CONFIG_TYPE_MAP = {
    ConfigType.LLM: LLMConfig,
    ConfigType.TOOL: ToolConfig,
    ConfigType.TOOL_SET: ToolSetConfig,
    ConfigType.GLOBAL: GlobalConfig,
}


def get_config_model(config_type: ConfigType) -> type:
    """获取配置模型类"""
    return CONFIG_TYPE_MAP.get(config_type, BaseConfig)


T = TypeVar('T', bound=BaseConfig)


class ConfigRegistry:
    """配置注册表"""
    
    def __init__(self):
        self._configs: Dict[str, BaseConfig] = {}
        self._types: Dict[str, ConfigType] = {}
    
    def register(self, name: str, config: BaseConfig, config_type: ConfigType) -> None:
        """注册配置"""
        self._configs[name] = config
        self._types[name] = config_type
    
    def get(self, name: str) -> Optional[BaseConfig]:
        """获取配置"""
        return self._configs.get(name)
    
    def get_type(self, name: str) -> Optional[ConfigType]:
        """获取配置类型"""
        return self._types.get(name)
    
    def list_configs(self) -> List[str]:
        """列出所有配置名称"""
        return list(self._configs.keys())
    
    def list_configs_by_type(self, config_type: ConfigType) -> List[str]:
        """按类型列出配置"""
        return [name for name, ctype in self._types.items() if ctype == config_type]