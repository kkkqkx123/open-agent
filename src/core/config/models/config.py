"""配置模型定义

使用Pydantic定义配置模型，支持配置验证和序列化。
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict
from pathlib import Path
from enum import Enum
import yaml


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


class BaseConfigModel(BaseModel):
    """基础配置模型"""
    
    # 基础字段
    config_type: ConfigType = Field(..., description="配置类型")
    metadata: ConfigMetadata = Field(..., description="配置元数据")
    
    # 继承配置
    inherits_from: Optional[Union[str, List[str]]] = Field(None, description="继承的配置路径")
    inheritance_config: Optional[ConfigInheritance] = Field(None, description="继承配置")
    
    # 验证规则
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="验证规则")
    
    # 环境变量
    env_vars: Dict[str, str] = Field(default_factory=dict, description="环境变量映射")
    
    # 自定义字段
    additional_config: Dict[str, Any] = Field(default_factory=dict, description="额外配置")
    
    model_config = ConfigDict(
        extra="allow",  # 允许额外字段
        validate_assignment=True,  # 赋值时验证
        use_enum_values=True  # 使用枚举值
    )
    
    @field_validator('metadata', mode='before')
    def validate_metadata(cls, v: Any) -> Any:
        """验证元数据"""
        if isinstance(v, dict):
            return ConfigMetadata(**v)
        return v
    
    def validate_config(self) -> List[str]:
        """验证配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if not self.metadata.name:
            errors.append("配置名称不能为空")
        
        # 验证继承配置
        if self.inherits_from and self.inheritance_config:
            if self.inheritance_config.from_config != self.inherits_from:
                errors.append("继承配置不一致")
        
        # 验证自定义规则
        for rule in self.validation_rules:
            if not self._validate_rule(rule):
                errors.append(rule.message or f"字段 '{rule.field}' 验证失败")
        
        return errors
    
    def _validate_rule(self, rule: ValidationRule) -> bool:
        """验证单个规则
        
        Args:
            rule: 验证规则
            
        Returns:
            是否通过验证
        """
        field_value = self._get_nested_value(self.dict(), rule.field)
        
        if rule.rule_type == "required":
            return field_value is not None
        elif rule.rule_type == "type":
            return isinstance(field_value, rule.value)
        elif rule.rule_type == "range":
            if isinstance(field_value, (int, float)) and isinstance(rule.value, (list, tuple)) and len(rule.value) == 2:
                min_val, max_val = rule.value
                return bool(min_val <= field_value <= max_val)
            return False
        elif rule.rule_type == "in":
            return field_value in rule.value
        elif rule.rule_type == "regex":
            import re
            return bool(re.match(rule.value, str(field_value)))
        
        return True
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值
        
        Args:
            obj: 字典对象
            path: 路径（点分隔）
            
        Returns:
            对应的值
        """
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """转换为字典
        
        Args:
            exclude_none: 是否排除None值
            
        Returns:
            字典表示
        """
        return self.dict(exclude_none=exclude_none, by_alias=True)
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """保存到文件
        
        Args:
            filepath: 文件路径
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        # 确保目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为YAML格式
        config_dict = self.to_dict()
        
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'BaseConfigModel':
        """从文件加载配置
        
        Args:
            filepath: 文件路径
            
        Returns:
            配置模型实例
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
        
        return cls(**config_dict)


class WorkflowConfigModel(BaseConfigModel):
    """工作流配置模型"""
    
    config_type: ConfigType = Field(ConfigType.WORKFLOW, description="配置类型")
    
    # 工作流特定字段
    workflow_name: str = Field(..., description="工作流名称")
    description: str = Field("", description="工作流描述")
    entry_point: str = Field(..., description="入口节点")
    max_iterations: int = Field(10, description="最大迭代次数")
    timeout: int = Field(300, description="超时时间（秒）")
    
    # 节点配置
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="节点配置")
    
    # 边配置
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边配置")
    
    # 状态模式
    state_schema: Dict[str, Any] = Field(default_factory=dict, description="状态模式")
    
    # 检查点配置
    checkpointer: Optional[str] = Field(None, description="检查点配置")
    interrupt_before: List[str] = Field(default_factory=list, description="中断前节点")
    interrupt_after: List[str] = Field(default_factory=list, description="中断后节点")
    
    @field_validator('max_iterations')
    def validate_max_iterations(cls, v: Any) -> Any:
        """验证最大迭代次数"""
        if v <= 0:
            raise ValueError("最大迭代次数必须大于0")
        return v
    
    @field_validator('timeout')
    def validate_timeout(cls, v: Any) -> Any:
        """验证超时时间"""
        if v <= 0:
            raise ValueError("超时时间必须大于0")
        return v

class ToolConfigModel(BaseConfigModel):
    """工具配置模型"""
    
    config_type: ConfigType = Field(ConfigType.TOOL, description="配置类型")
    
    # 工具特定字段
    tool_name: str = Field(..., description="工具名称")
    tool_type: str = Field("function", description="工具类型")
    description: str = Field("", description="工具描述")
    
    # 工具参数
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    required_parameters: List[str] = Field(default_factory=list, description="必需参数")
    
    # 执行配置
    timeout: int = Field(30, description="执行超时时间")
    retry_count: int = Field(3, description="重试次数")
    retry_delay: float = Field(1.0, description="重试延迟")


class LLMConfigModel(BaseConfigModel):
    """LLM配置模型"""
    
    config_type: ConfigType = Field(ConfigType.LLM, description="配置类型")
    
    # LLM特定字段
    model_name: str = Field(..., description="模型名称")
    provider: str = Field("openai", description="模型提供商")
    description: str = Field("", description="模型描述")
    
    # 模型参数
    temperature: float = Field(0.7, description="温度参数")
    max_tokens: int = Field(1000, description="最大令牌数")
    top_p: float = Field(1.0, description="Top P参数")
    frequency_penalty: float = Field(0.0, description="频率惩罚")
    presence_penalty: float = Field(0.0, description="存在惩罚")
    
    # API配置
    api_key: str = Field("", description="API密钥")
    base_url: str = Field("", description="基础URL")
    timeout: int = Field(30, description="超时时间")
    
    # 高级配置
    streaming: bool = Field(False, description="是否启用流式")
    batch_size: int = Field(1, description="批处理大小")


class ToolSetConfigModel(BaseConfigModel):
    """工具集配置模型"""
    
    config_type: ConfigType = Field(ConfigType.TOOL_SET, description="配置类型")
    
    # 工具集特定字段
    toolset_name: str = Field(..., description="工具集名称")
    description: str = Field("", description="工具集描述")
    
    # 工具集成员
    tools: List[str] = Field(default_factory=list, description="工具列表")
    category: str = Field("general", description="工具集分类")


class GraphConfigModel(BaseConfigModel):
    """图配置模型"""
    
    config_type: ConfigType = Field(ConfigType.GRAPH, description="配置类型")
    
    # 图特定字段
    graph_name: str = Field(..., description="图名称")
    description: str = Field("", description="图描述")
    version: str = Field("1.0.0", description="图版本")
    
    # 状态模式
    state_schema: Dict[str, Any] = Field(default_factory=dict, description="状态模式")
    
    # 节点配置
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="节点配置")
    
    # 边配置
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边配置")
    
    # 入口点
    entry_point: str = Field(..., description="入口节点")
    
    # 检查点配置
    checkpointer: Optional[str] = Field(None, description="检查点配置")
    interrupt_before: List[str] = Field(default_factory=list, description="中断前节点")
    interrupt_after: List[str] = Field(default_factory=list, description="中断后节点")


class GlobalConfigModel(BaseConfigModel):
    """全局配置模型"""
    
    config_type: ConfigType = Field(ConfigType.GLOBAL, description="配置类型")
    
    # 全局特定字段
    app_name: str = Field("Modular Agent Framework", description="应用名称")
    log_level: str = Field("INFO", description="日志级别")
    environment: str = Field("development", description="环境类型")


# 配置模型映射
CONFIG_MODEL_MAPPING = {
    ConfigType.WORKFLOW: WorkflowConfigModel,
    ConfigType.TOOL: ToolConfigModel,
    ConfigType.TOOL_SET: ToolSetConfigModel,
    ConfigType.LLM: LLMConfigModel,
    ConfigType.GRAPH: GraphConfigModel,
    ConfigType.GLOBAL: GlobalConfigModel,
}


def create_config_model(config_type: ConfigType, **kwargs: Any) -> BaseConfigModel:
    """创建配置模型实例
    
    Args:
        config_type: 配置类型
        **kwargs: 配置参数
        
    Returns:
        配置模型实例
    """
    model_class = CONFIG_MODEL_MAPPING.get(config_type)
    if not model_class:
        raise ValueError(f"不支持的配置类型: {config_type}")
    
    return model_class(**kwargs)  # type: ignore


def validate_config_with_model(config_dict: Dict[str, Any], config_type: ConfigType) -> List[str]:
    """使用配置模型验证配置
    
    Args:
        config_dict: 配置字典
        config_type: 配置类型
        
    Returns:
        验证错误列表
    """
    try:
        model = create_config_model(config_type, **config_dict)
        return model.validate_config()
    except Exception as e:
        return [str(e)]


def get_config_model(config_type: ConfigType) -> type[BaseConfigModel]:
    """获取配置类型对应的模型类
    
    Args:
        config_type: 配置类型
        
    Returns:
        配置模型类
        
    Raises:
        ValueError: 如果配置类型不支持
    """
    model_class = CONFIG_MODEL_MAPPING.get(config_type)
    if not model_class:
        raise ValueError(f"不支持的配置类型: {config_type}")
    return model_class


class ConfigRegistry:
    """配置注册表"""
    
    def __init__(self) -> None:
        """初始化配置注册表"""
        self._configs: Dict[str, BaseConfigModel] = {}
        self._config_types: Dict[str, ConfigType] = {}
    
    def register(self, name: str, config: BaseConfigModel, config_type: ConfigType) -> None:
        """注册配置
        
        Args:
            name: 配置名称
            config: 配置实例
            config_type: 配置类型
        """
        self._configs[name] = config
        self._config_types[name] = config_type
    
    def get(self, name: str) -> Optional[BaseConfigModel]:
        """获取已注册的配置
        
        Args:
            name: 配置名称
            
        Returns:
            配置实例或None
        """
        return self._configs.get(name)
    
    def list_configs_by_type(self, config_type: ConfigType) -> List[str]:
        """按类型获取已注册的配置列表
        
        Args:
            config_type: 配置类型
            
        Returns:
            配置名称列表
        """
        return [name for name, ctype in self._config_types.items() if ctype == config_type]
    
    def unregister(self, name: str) -> bool:
        """注销配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否成功注销
        """
        if name in self._configs:
            del self._configs[name]
            del self._config_types[name]
            return True
        return False
    
    def list_all_configs(self) -> List[str]:
        """列出所有已注册的配置
        
        Returns:
            配置名称列表
        """
        return list(self._configs.keys())