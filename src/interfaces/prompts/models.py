"""
提示词相关数据模型

定义提示词系统的核心数据结构
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .types import PromptType


class PromptStatus(str, Enum):
    """提示词状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class PromptPriority(int, Enum):
    """提示词优先级枚举"""
    LOWEST = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    HIGHEST = 5


class PromptReference(BaseModel):
    """提示词引用"""
    ref_id: str = Field(..., description="引用ID")
    ref_type: str = Field(..., description="引用类型")
    ref_path: str = Field(..., description="引用路径")
    version: Optional[str] = Field(None, description="引用版本")
    alias: Optional[str] = Field(None, description="引用别名")
    
    model_config = ConfigDict(extra="forbid")


class PromptVariable(BaseModel):
    """提示词变量"""
    name: str = Field(..., description="变量名")
    type: str = Field(default="string", description="变量类型")
    default_value: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(default=True, description="是否必需")
    description: Optional[str] = Field(None, description="变量描述")
    
    model_config = ConfigDict(extra="forbid")


class PromptValidation(BaseModel):
    """提示词验证规则"""
    max_length: Optional[int] = Field(None, description="最大长度")
    min_length: Optional[int] = Field(None, description="最小长度")
    pattern: Optional[str] = Field(None, description="正则表达式模式")
    forbidden_words: Optional[List[str]] = Field(None, description="禁用词汇")
    required_keywords: Optional[List[str]] = Field(None, description="必需关键词")
    
    model_config = ConfigDict(extra="forbid")


class PromptMeta(BaseModel):
    """增强的提示词元数据"""
    
    # 基本信息
    id: str = Field(..., description="提示词唯一标识")
    name: str = Field(..., description="提示词名称")
    description: Optional[str] = Field(None, description="提示词描述")
    type: PromptType = Field(..., description="提示词类型")
    
    # 内容信息
    content: str = Field(..., description="提示词内容")
    template: Optional[str] = Field(None, description="模板内容")
    
    # 状态和优先级
    status: PromptStatus = Field(default=PromptStatus.ACTIVE, description="提示词状态")
    priority: PromptPriority = Field(default=PromptPriority.NORMAL, description="提示词优先级")
    
    # 版本信息
    version: str = Field(default="1.0.0", description="版本号")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")
    
    # 引用和依赖
    references: List[PromptReference] = Field(default_factory=list, description="引用列表")
    dependencies: List[str] = Field(default_factory=list, description="依赖列表")
    
    # 变量和验证
    variables: List[PromptVariable] = Field(default_factory=list, description="变量列表")
    validation: Optional[PromptValidation] = Field(None, description="验证规则")
    
    # 缓存配置
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    cache_ttl: Optional[int] = Field(None, description="缓存TTL（秒）")
    
    # 标签和分类
    tags: List[str] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(None, description="分类")
    
    # 扩展属性
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True
    )
    
    @field_validator('content')
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('提示词内容不能为空')
        return v
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('提示词ID不能为空')
        # 简单的ID格式验证
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('提示词ID只能包含字母、数字、下划线和连字符')
        return v
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    def add_reference(self, ref: PromptReference) -> None:
        """添加引用"""
        # 检查是否已存在
        for existing_ref in self.references:
            if existing_ref.ref_id == ref.ref_id and existing_ref.ref_path == ref.ref_path:
                return
        
        self.references.append(ref)
        self.update_timestamp()
    
    def remove_reference(self, ref_id: str, ref_path: str) -> None:
        """移除引用"""
        self.references = [
            ref for ref in self.references
            if not (ref.ref_id == ref_id and ref.ref_path == ref_path)
        ]
        self.update_timestamp()
    
    def add_variable(self, var: PromptVariable) -> None:
        """添加变量"""
        # 检查是否已存在
        for existing_var in self.variables:
            if existing_var.name == var.name:
                return
        
        self.variables.append(var)
        self.update_timestamp()
    
    def get_variable(self, name: str) -> Optional[PromptVariable]:
        """获取变量"""
        for var in self.variables:
            if var.name == name:
                return var
        return None
    
    def is_active(self) -> bool:
        """检查是否为活跃状态"""
        return self.status == PromptStatus.ACTIVE
    
    def can_cache(self) -> bool:
        """检查是否可以缓存"""
        return self.cache_enabled and self.is_active()


class PromptConfig(BaseModel):
    """提示词配置"""
    
    # 提示词选择
    system_prompt: Optional[str] = Field(None, description="系统提示词名称")
    rules: List[str] = Field(default_factory=list, description="规则提示词列表")
    user_command: Optional[str] = Field(None, description="用户指令名称")
    context: Optional[List[str]] = Field(None, description="上下文列表")
    examples: Optional[List[str]] = Field(None, description="示例列表")
    constraints: Optional[List[str]] = Field(None, description="约束列表")
    format: Optional[str] = Field(None, description="格式名称")
    
    # 缓存配置
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    default_cache_ttl: int = Field(default=3600, description="默认缓存TTL（秒）")
    max_cache_size: int = Field(default=1000, description="最大缓存大小")
    
    # 验证配置
    enable_validation: bool = Field(default=True, description="是否启用验证")
    
    # 加载配置
    load_timeout: int = Field(default=30, description="加载超时时间（秒）")
    max_content_length: int = Field(default=100000, description="最大内容长度")
    
    # 引用解析配置
    enable_reference_resolution: bool = Field(default=True, description="是否启用引用解析")
    max_reference_depth: int = Field(default=10, description="最大引用深度")
    
    # 错误处理配置
    enable_error_recovery: bool = Field(default=True, description="是否启用错误恢复")
    max_retry_attempts: int = Field(default=3, description="最大重试次数")
    
    model_config = ConfigDict(extra="forbid")


class PromptSearchCriteria(BaseModel):
    """提示词搜索条件"""
    
    # 基本搜索
    query: Optional[str] = Field(None, description="搜索查询")
    type: Optional[PromptType] = Field(None, description="提示词类型")
    status: Optional[PromptStatus] = Field(None, description="状态")
    category: Optional[str] = Field(None, description="分类")
    
    # 标签搜索
    tags: Optional[List[str]] = Field(None, description="标签列表")
    tags_match_all: bool = Field(default=False, description="是否匹配所有标签")
    
    # 时间范围
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    updated_after: Optional[datetime] = Field(None, description="更新时间之后")
    updated_before: Optional[datetime] = Field(None, description="更新时间之前")
    
    # 分页
    offset: int = Field(default=0, ge=0, description="偏移量")
    limit: int = Field(default=50, ge=1, le=1000, description="限制数量")
    
    # 排序
    sort_by: str = Field(default="updated_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序顺序")
    
    model_config = ConfigDict(extra="forbid")


class PromptSearchResult(BaseModel):
    """提示词搜索结果"""
    
    items: List[PromptMeta] = Field(default_factory=list, description="提示词列表")
    total: int = Field(default=0, description="总数")
    offset: int = Field(default=0, description="偏移量")
    limit: int = Field(default=50, description="限制数量")
    
    model_config = ConfigDict(extra="forbid")