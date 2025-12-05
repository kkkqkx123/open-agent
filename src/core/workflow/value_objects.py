"""工作流值对象

定义工作流相关的值对象，包括步骤、转换、规则等。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union, TYPE_CHECKING
from enum import Enum
import uuid
import re

# Type alias for custom validation function to simplify complex type annotation
CustomValidationFunction = Callable[[Any, Optional[Dict[str, Any]]], bool]

if TYPE_CHECKING:
    from .entities import Workflow as BusinessWorkflow
from src.interfaces.workflow.exceptions import WorkflowValidationError


class StepType(Enum):
    """步骤类型"""
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    DECISION = "decision"
    WAITING = "waiting"
    NOTIFICATION = "notification"
    START = "start"
    END = "end"
    PARALLEL = "parallel"
    CONTROL = "control"


class TransitionType(Enum):
    """转换类型"""
    SIMPLE = "simple"
    CONDITIONAL = "conditional"
    TIMEOUT = "timeout"
    ERROR = "error"


class RuleType(Enum):
    """规则类型"""
    VALIDATION = "validation"
    BUSINESS = "business"
    SECURITY = "security"
    PERFORMANCE = "performance"


class RuleOperator(Enum):
    """规则操作符"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"


@dataclass
class WorkflowStep:
    """工作流步骤值对象"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: StepType = StepType.ANALYSIS
    description: str = ""
    
    # 配置信息
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 执行配置
    timeout: Optional[int] = None  # 超时时间（秒）
    retry_count: int = 0  # 重试次数
    retry_delay: int = 1  # 重试延迟（秒）
    
    # 条件配置
    pre_conditions: List[str] = field(default_factory=list)
    post_conditions: List[str] = field(default_factory=list)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.name:
            raise WorkflowValidationError("步骤名称不能为空")
        
        # 验证步骤名称格式
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.name):
            raise WorkflowValidationError("步骤名称只能包含字母、数字和下划线，且必须以字母开头")
    
    def add_config(self, key: str, value: Any) -> None:
        """添加配置"""
        self.config[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.config.get(key, default)
    
    def add_pre_condition(self, condition: str) -> None:
        """添加前置条件"""
        if condition not in self.pre_conditions:
            self.pre_conditions.append(condition)
    
    def add_post_condition(self, condition: str) -> None:
        """添加后置条件"""
        if condition not in self.post_conditions:
            self.post_conditions.append(condition)
    
    def validate(self) -> List[str]:
        """验证步骤定义"""
        errors = []
        
        if not self.name:
            errors.append("步骤名称不能为空")
        
        if self.timeout is not None and self.timeout <= 0:
            errors.append("超时时间必须大于0")
        
        if self.retry_count < 0:
            errors.append("重试次数不能为负数")
        
        if self.retry_delay < 0:
            errors.append("重试延迟不能为负数")
        
        return errors


@dataclass
class WorkflowTransition:
    """工作流转换值对象"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_step: str = ""
    to_step: str = ""
    type: TransitionType = TransitionType.SIMPLE
    
    # 条件配置
    condition: Optional[str] = None  # 条件表达式
    condition_config: Dict[str, Any] = field(default_factory=dict)
    
    # 转换配置
    priority: int = 0  # 优先级，数字越大优先级越高
    enabled: bool = True  # 是否启用
    
    # 超时配置
    timeout: Optional[int] = None  # 超时时间（秒）
    
    # 元数据
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.from_step:
            raise WorkflowValidationError("起始步骤不能为空")
        
        if not self.to_step:
            raise WorkflowValidationError("目标步骤不能为空")
        
        if self.from_step == self.to_step:
            raise WorkflowValidationError("起始步骤和目标步骤不能相同")
        
        # 条件转换必须有条件表达式
        if self.type == TransitionType.CONDITIONAL and not self.condition:
            raise WorkflowValidationError("条件转换必须有条件表达式")
    
    def evaluate_condition(self, context: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            context: 评估上下文
            
        Returns:
            条件是否满足
        """
        if not self.condition:
            return True
        
        try:
            # 简单的条件评估实现
            # 在实际项目中，可能需要更复杂的表达式引擎
            return self._evaluate_simple_condition(context)
        except Exception as e:
            raise WorkflowValidationError(f"条件评估失败: {e}")
    
    def _evaluate_simple_condition(self, context: Dict[str, Any]) -> bool:
        """评估简单条件"""
        # 这是一个简化的实现，实际项目中可能需要使用更强大的表达式引擎
        condition = self.condition.strip() if self.condition else ""
        
        # 替换变量
        for key, value in context.items():
            condition = condition.replace(f"${key}", str(value))
        
        # 简单的安全评估（仅支持基本操作）
        try:
            # 注意：在生产环境中，应该使用更安全的表达式评估器
            return eval(condition, {"__rests__": {}}, context)
        except:
            return False
    
    def validate(self) -> List[str]:
        """验证转换定义"""
        errors = []
        
        if not self.from_step:
            errors.append("起始步骤不能为空")
        
        if not self.to_step:
            errors.append("目标步骤不能为空")
        
        if self.from_step == self.to_step:
            errors.append("起始步骤和目标步骤不能相同")
        
        if self.type == TransitionType.CONDITIONAL and not self.condition:
            errors.append("条件转换必须有条件表达式")
        
        if self.timeout is not None and self.timeout <= 0:
            errors.append("超时时间必须大于0")
        
        return errors


@dataclass
class WorkflowRule:
    """工作流规则值对象"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: RuleType = RuleType.VALIDATION
    description: str = ""
    
    # 规则定义
    target_field: str = ""  # 规则作用的字段
    operator: RuleOperator = RuleOperator.EQUALS
    value: Any = None  # 比较值
    
    # 规则配置
    enabled: bool = True
    required: bool = True  # 是否必需
    error_message: str = ""  # 错误消息
    
    # 高级配置
    custom_function: Optional[CustomValidationFunction] = None  # 自定义验证函数
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.name:
            raise WorkflowValidationError("规则名称不能为空")
        
        if not self.target_field:
            raise WorkflowValidationError("规则字段不能为空")
        
        if not self.error_message:
            self.error_message = f"字段 '{self.target_field}' 验证失败"
    
    def validate_value(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """验证值
        
        Args:
            value: 要验证的值
            context: 验证上下文
            
        Returns:
            验证是否通过
        """
        if not self.enabled:
            return True
        
        # 如果有自定义函数，使用自定义函数
        if self.custom_function:
            return self._validate_with_custom_function(value, context or {})
        
        # 使用内置操作符验证
        return self._validate_with_operator(value)
    
    def _validate_with_operator(self, value: Any) -> bool:
        """使用操作符验证"""
        if self.operator == RuleOperator.EQUALS:
            return value == self.value
        elif self.operator == RuleOperator.NOT_EQUALS:
            return value != self.value
        elif self.operator == RuleOperator.GREATER_THAN:
            try:
                return float(value) > float(self.value)
            except (ValueError, TypeError):
                return False
        elif self.operator == RuleOperator.LESS_THAN:
            try:
                return float(value) < float(self.value)
            except (ValueError, TypeError):
                return False
        elif self.operator == RuleOperator.CONTAINS:
            return str(self.value) in str(value)
        elif self.operator == RuleOperator.REGEX:
            try:
                return bool(re.search(str(self.value), str(value)))
            except re.error:
                return False
        elif self.operator == RuleOperator.IN:
            return value in self.value if isinstance(self.value, (list, tuple, set)) else False
        elif self.operator == RuleOperator.NOT_IN:
            return value not in self.value if isinstance(self.value, (list, tuple, set)) else True
        
        return False
    
    def _validate_with_custom_function(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """使用自定义函数验证"""
        if self.custom_function is not None and callable(self.custom_function):
            return self.custom_function(value, context)
        return True
    
    def validate(self) -> List[str]:
        """验证规则定义"""
        errors = []
        
        if not self.name:
            errors.append("规则名称不能为空")
        
        if not self.target_field:
            errors.append("规则字段不能为空")
        
        if self.operator == RuleOperator.IN and not isinstance(self.value, (list, tuple, set)):
            errors.append("IN操作符的值必须是列表、元组或集合")
        
        if self.operator == RuleOperator.REGEX:
            try:
                re.compile(str(self.value))
            except re.error:
                errors.append("正则表达式无效")
        
        return errors


@dataclass
class WorkflowTemplate:
    """工作流模板值对象"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = ""
    
    # 模板内容
    steps: List[WorkflowStep] = field(default_factory=list)
    transitions: List[WorkflowTransition] = field(default_factory=list)
    rules: List[WorkflowRule] = field(default_factory=list)
    
    # 模板配置
    parameters: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    author: str = ""
    created_at: str = ""
    
    def create_workflow(self, name: str, description: str, **kwargs) -> "BusinessWorkflow":
        """从模板创建工作流

        Args:
            name: 工作流名称
            description: 工作流描述
            **kwargs: 参数覆盖

        Returns:
            创建的工作流实例
        """
        # Import here to avoid circular imports
        from .entities import Workflow as BusinessWorkflow
        
        # 合并参数
        config = {**self.default_config, **kwargs}
        
        # 创建工作流
        workflow = BusinessWorkflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            metadata=config
        )
        
        return workflow
    
    def _customize_step(self, step: WorkflowStep, config: Dict[str, Any]) -> WorkflowStep:
        """自定义步骤"""
        import copy
        
        customized = copy.deepcopy(step)
        customized.id = str(uuid.uuid4())  # 生成新的ID
        
        # 应用参数替换
        for key, value in customized.config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                param_name = value[2:-1]
                if param_name in config:
                    customized.config[key] = config[param_name]
        
        return customized
    
    def _customize_transition(self, transition: WorkflowTransition, config: Dict[str, Any]) -> WorkflowTransition:
        """自定义转换"""
        import copy
        
        customized = copy.deepcopy(transition)
        customized.id = str(uuid.uuid4())  # 生成新的ID
        
        # 应用参数替换
        if transition.condition:
            for key, value in config.items():
                transition.condition = transition.condition.replace(f"${key}", str(value))
        
        return customized
    
    def _customize_rule(self, rule: WorkflowRule, config: Dict[str, Any]) -> WorkflowRule:
        """自定义规则"""
        import copy
        
        customized = copy.deepcopy(rule)
        customized.id = str(uuid.uuid4())  # 生成新的ID
        
        # 应用参数替换
        if isinstance(customized.value, str) and customized.value.startswith("${") and customized.value.endswith("}"):
            param_name = customized.value[2:-1]
            if param_name in config:
                customized.value = config[param_name]
        
        return customized