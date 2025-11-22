"""历史记录核心实体

定义所有历史记录相关的数据结构和枚举类型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class RecordType(Enum):
    """记录类型枚举"""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOKEN_USAGE = "token_usage"
    COST = "cost"


class TokenSource(Enum):
    """Token来源枚举"""
    API = "api"           # 来自API响应的精确数据
    LOCAL = "local"       # 本地估算数据
    HYBRID = "hybrid"     # 混合来源


@dataclass
class BaseHistoryRecord:
    """历史记录基类
    
    所有历史记录的通用基类，包含基本字段和通用方法。
    """
    record_id: str
    session_id: str
    workflow_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    record_type: RecordType = RecordType.MESSAGE
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.record_id:
            raise ValueError("record_id 不能为空")
        if not self.session_id:
            raise ValueError("session_id 不能为空")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseHistoryRecord':
        """从字典创建实例"""
        # 处理特殊字段
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        if 'record_type' in data and isinstance(data['record_type'], str):
            data['record_type'] = RecordType(data['record_type'])
        
        return cls(**data)


@dataclass
class LLMRequestRecord(BaseHistoryRecord):
    """LLM请求记录
    
    记录每次LLM调用的请求信息。
    """
    record_type: RecordType = RecordType.LLM_REQUEST
    model: str = ""
    provider: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 0
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if self.estimated_tokens < 0:
            raise ValueError("estimated_tokens 不能为负数")


@dataclass
class LLMResponseRecord(BaseHistoryRecord):
    """LLM响应记录
    
    记录每次LLM调用的响应信息。
    """
    record_type: RecordType = RecordType.LLM_RESPONSE
    request_id: str = ""
    content: str = ""
    finish_reason: str = ""
    token_usage: Dict[str, Any] = field(default_factory=dict)
    response_time: float = 0.0
    model: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if self.response_time < 0:
            raise ValueError("response_time 不能为负数")
    
    @property
    def prompt_tokens(self) -> int:
        """获取prompt token数量"""
        return self.token_usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        """获取completion token数量"""
        return self.token_usage.get("completion_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        """获取总token数量"""
        return self.token_usage.get("total_tokens", 0)


@dataclass
class TokenUsageRecord(BaseHistoryRecord):
    """Token使用记录
    
    记录详细的Token使用情况，支持多维度统计。
    """
    record_type: RecordType = RecordType.TOKEN_USAGE
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    source: TokenSource = TokenSource.API
    confidence: float = 1.0
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise ValueError("Token数量不能为负数")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence 必须在0.0到1.0之间")
        
        # 确保total_tokens等于prompt_tokens + completion_tokens
        calculated_total = self.prompt_tokens + self.completion_tokens
        if self.total_tokens != calculated_total:
            self.total_tokens = calculated_total
    
    @property
    def prompt_cost_per_1k(self) -> Optional[float]:
        """获取每1K prompt tokens的成本"""
        return self.metadata.get("prompt_cost_per_1k")
    
    @property
    def completion_cost_per_1k(self) -> Optional[float]:
        """获取每1K completion tokens的成本"""
        return self.metadata.get("completion_cost_per_1k")


@dataclass
class CostRecord(BaseHistoryRecord):
    """成本记录
    
    记录LLM调用的成本信息。
    """
    record_type: RecordType = RecordType.COST
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_cost: float = 0.0
    completion_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if any(cost < 0 for cost in [self.prompt_cost, self.completion_cost, self.total_cost]):
            raise ValueError("成本不能为负数")
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise ValueError("Token数量不能为负数")
        
        # 确保total_cost等于prompt_cost + completion_cost
        calculated_total = self.prompt_cost + self.completion_cost
        if abs(self.total_cost - calculated_total) > 0.0001:  # 允许小的浮点误差
            self.total_cost = calculated_total
    
    @property
    def avg_cost_per_token(self) -> float:
        """获取平均每个token的成本"""
        return self.total_cost / self.total_tokens if self.total_tokens > 0 else 0.0
    
    @property
    def prompt_cost_per_1k(self) -> float:
        """获取每1K prompt tokens的成本"""
        return (self.prompt_cost / self.prompt_tokens * 1000) if self.prompt_tokens > 0 else 0.0
    
    @property
    def completion_cost_per_1k(self) -> float:
        """获取每1K completion tokens的成本"""
        return (self.completion_cost / self.completion_tokens * 1000) if self.completion_tokens > 0 else 0.0


@dataclass
class WorkflowTokenStatistics:
    """工作流Token统计
    
    聚合统计特定工作流和模型的Token使用情况。
    """
    workflow_id: str
    model: str
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.workflow_id:
            raise ValueError("workflow_id 不能为空")
        if not self.model:
            raise ValueError("model 不能为空")
        if any(value < 0 for value in [
            self.total_prompt_tokens, self.total_completion_tokens, 
            self.total_tokens, self.total_cost, self.request_count
        ]):
            raise ValueError("统计值不能为负数")
    
    def update_from_record(self, record: TokenUsageRecord) -> None:
        """从Token使用记录更新统计"""
        if record.workflow_id != self.workflow_id or record.model != self.model:
            raise ValueError("记录与统计不匹配")
        
        self.total_prompt_tokens += record.prompt_tokens
        self.total_completion_tokens += record.completion_tokens
        self.total_tokens += record.total_tokens
        self.request_count += 1
        self.last_updated = record.timestamp
        
        # 更新时间范围
        if self.period_start is None or record.timestamp < self.period_start:
            self.period_start = record.timestamp
        if self.period_end is None or record.timestamp > self.period_end:
            self.period_end = record.timestamp
    
    def update_from_cost_record(self, record: CostRecord) -> None:
        """从成本记录更新成本统计"""
        if record.workflow_id != self.workflow_id or record.model != self.model:
            raise ValueError("记录与统计不匹配")
        
        self.total_cost += record.total_cost
        self.last_updated = record.timestamp
    
    @property
    def avg_tokens_per_request(self) -> float:
        """获取每个请求的平均token数量"""
        return self.total_tokens / self.request_count if self.request_count > 0 else 0.0
    
    @property
    def avg_cost_per_request(self) -> float:
        """获取每个请求的平均成本"""
        return self.total_cost / self.request_count if self.request_count > 0 else 0.0
    
    @property
    def avg_cost_per_token(self) -> float:
        """获取每个token的平均成本"""
        return self.total_cost / self.total_tokens if self.total_tokens > 0 else 0.0


@dataclass
class WorkflowTokenSummary:
    """工作流Token汇总统计
    
    汇总特定工作流所有模型的Token使用情况。
    """
    workflow_id: str
    total_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    model_breakdown: Dict[str, WorkflowTokenStatistics] = field(default_factory=dict)
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    def add_model_stats(self, stats: WorkflowTokenStatistics) -> None:
        """添加模型统计"""
        if stats.workflow_id != self.workflow_id:
            raise ValueError("统计与汇总不匹配")
        
        if stats.model not in self.model_breakdown:
            self.model_breakdown[stats.model] = stats
        
        self.total_tokens += stats.total_tokens
        self.total_cost += stats.total_cost
        self.total_requests += stats.request_count
        
        # 更新时间范围
        if stats.period_start and stats.period_start < self.period_start:
            self.period_start = stats.period_start
        if stats.period_end and stats.period_end > self.period_end:
            self.period_end = stats.period_end
    
    @property
    def models_used(self) -> List[str]:
        """获取使用的模型列表"""
        return list(self.model_breakdown.keys())
    
    @property
    def most_used_model(self) -> Optional[str]:
        """获取使用最多的模型"""
        if not self.model_breakdown:
            return None
        return max(self.model_breakdown.items(), key=lambda x: x[1].total_tokens)[0]
    
    @property
    def most_expensive_model(self) -> Optional[str]:
        """获取成本最高的模型"""
        if not self.model_breakdown:
            return None
        return max(self.model_breakdown.items(), key=lambda x: x[1].total_cost)[0]


@dataclass
class MessageRecord(BaseHistoryRecord):
    """消息记录
    
    记录对话中的消息。
    """
    record_type: RecordType = RecordType.MESSAGE
    role: str = ""
    content: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if not self.role:
            raise ValueError("role 不能为空")


@dataclass
class ToolCallRecord(BaseHistoryRecord):
    """工具调用记录
    
    记录工具的调用和执行情况。
    """
    record_type: RecordType = RecordType.TOOL_CALL
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"  # success, error, pending
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if not self.tool_name:
            raise ValueError("tool_name 不能为空")


@dataclass
class HistoryQuery:
    """历史查询条件
    
    用于查询历史记录的条件对象。
    """
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    record_type: Optional[RecordType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    model: Optional[str] = None
    
    def validate(self) -> None:
        """验证查询条件"""
        if self.limit < 1:
            raise ValueError("limit 必须大于0")
        if self.offset < 0:
            raise ValueError("offset 不能为负数")
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time 不能晚于 end_time")


@dataclass
class HistoryResult:
    """历史查询结果
    
    包含查询得到的历史记录和元数据。
    """
    records: List[BaseHistoryRecord] = field(default_factory=list)
    total_count: int = 0
    offset: int = 0
    limit: int = 100
    query: Optional[HistoryQuery] = None
    
    def has_more(self) -> bool:
        """检查是否还有更多记录"""
        return self.offset + self.limit < self.total_count
    
    def next_offset(self) -> int:
        """获取下一页的偏移量"""
        return self.offset + self.limit