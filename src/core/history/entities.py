"""历史记录核心实体

定义所有历史记录相关的数据结构和枚举类型。
"""

from src.interfaces.dependency_injection import get_logger
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from src.interfaces.history.exceptions import (
    HistoryError, TokenCalculationError, CostCalculationError
)
from src.interfaces.history.entities import (
    IBaseHistoryRecord, ILLMRequestRecord, ILLMResponseRecord,
    ITokenUsageRecord, ICostRecord, IMessageRecord, IToolCallRecord
)

logger = get_logger(__name__)


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


class BaseHistoryRecord(IBaseHistoryRecord):
    """历史记录基类
    
    所有历史记录的通用基类，包含基本字段和通用方法。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        record_type: str = "message",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化历史记录基类"""
        self._record_id = record_id
        self._session_id = session_id
        self._workflow_id = workflow_id
        self._timestamp = timestamp or datetime.now()
        self._record_type = record_type
        self._metadata = metadata or {}

    # 实现IBaseHistoryRecord接口的属性
    @property
    def record_id(self) -> str:
        """记录ID"""
        return self._record_id

    @property
    def session_id(self) -> str:
        """会话ID"""
        return self._session_id

    @property
    def workflow_id(self) -> Optional[str]:
        """工作流ID"""
        return self._workflow_id

    @property
    def timestamp(self) -> datetime:
        """时间戳"""
        return self._timestamp

    @property
    def record_type(self) -> str:
        """记录类型"""
        return self._record_type

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.record_id:
            raise HistoryError("record_id 不能为空")
        if not self.session_id:
            raise HistoryError("session_id 不能为空")
    
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
        """从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            历史记录实例
            
        Raises:
            HistoryError: 创建失败
        """
        try:
            # 输入验证
            if data is None:
                raise HistoryError("数据不能为None")
            
            if not isinstance(data, dict):
                raise HistoryError(f"数据必须是字典类型，实际类型: {type(data).__name__}")
            
            # 处理特殊字段
            if 'timestamp' in data:
                if isinstance(data['timestamp'], str):
                    try:
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    except ValueError as e:
                        raise HistoryError(f"时间戳格式无效: {e}") from e
                elif not isinstance(data['timestamp'], datetime):
                    raise HistoryError(f"时间戳必须是字符串或datetime类型，实际类型: {type(data['timestamp']).__name__}")
            
            if 'record_type' in data:
                if isinstance(data['record_type'], str):
                    try:
                        data['record_type'] = RecordType(data['record_type'])
                    except ValueError as e:
                        raise HistoryError(f"记录类型无效: {e}") from e
                elif not isinstance(data['record_type'], RecordType):
                    raise HistoryError(f"记录类型必须是字符串或RecordType枚举，实际类型: {type(data['record_type']).__name__}")
            
            return cls(**data)
            
        except HistoryError:
            # 重新抛出已知异常
            raise
        except Exception as e:
            # 包装其他异常
            raise HistoryError(f"从字典创建历史记录失败: {e}") from e


class LLMRequestRecord(BaseHistoryRecord, ILLMRequestRecord):
    """LLM请求记录
    
    记录每次LLM调用的请求信息。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "",
        provider: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        estimated_tokens: int = 0
    ):
        """初始化LLM请求记录"""
        super().__init__(
            record_id=record_id,
            session_id=session_id,
            workflow_id=workflow_id,
            timestamp=timestamp,
            record_type="llm_request",
            metadata=metadata
        )
        self._model = model
        self._provider = provider
        self._messages = messages or []
        self._parameters = parameters or {}
        self._estimated_tokens = estimated_tokens

    # 实现ILLMRequestRecord接口的属性
    @property
    def model(self) -> str:
        """模型名称"""
        return self._model

    @property
    def provider(self) -> str:
        """提供商"""
        return self._provider

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """消息列表"""
        return self._messages

    @property
    def parameters(self) -> Dict[str, Any]:
        """请求参数"""
        return self._parameters

    @property
    def estimated_tokens(self) -> int:
        """估算的token数量"""
        return self._estimated_tokens
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        if self.estimated_tokens < 0:
            raise HistoryError("estimated_tokens 不能为负数")


class LLMResponseRecord(BaseHistoryRecord, ILLMResponseRecord):
    """LLM响应记录
    
    记录每次LLM调用的响应信息。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: str = "",
        content: str = "",
        finish_reason: str = "",
        token_usage: Optional[Dict[str, Any]] = None,
        response_time: float = 0.0,
        model: str = ""
    ):
        """初始化LLM响应记录"""
        super().__init__(
            record_id=record_id,
            session_id=session_id,
            workflow_id=workflow_id,
            timestamp=timestamp,
            record_type="llm_response",
            metadata=metadata
        )
        self._request_id = request_id
        self._content = content
        self._finish_reason = finish_reason
        self._token_usage = token_usage or {}
        self._response_time = response_time
        self._model = model

    # 实现ILLMResponseRecord接口的属性
    @property
    def request_id(self) -> str:
        """关联的请求ID"""
        return self._request_id

    @property
    def content(self) -> str:
        """响应内容"""
        return self._content

    @property
    def finish_reason(self) -> str:
        """完成原因"""
        return self._finish_reason

    @property
    def token_usage(self) -> Dict[str, Any]:
        """Token使用情况"""
        return self._token_usage

    @property
    def response_time(self) -> float:
        """响应时间（秒）"""
        return self._response_time

    @property
    def model(self) -> str:
        """使用的模型"""
        return self._model

    @property
    def prompt_tokens(self) -> int:
        """获取prompt token数量"""
        return int(self.token_usage.get("prompt_tokens", 0))

    @property
    def completion_tokens(self) -> int:
        """获取completion token数量"""
        return int(self.token_usage.get("completion_tokens", 0))

    @property
    def total_tokens(self) -> int:
        """获取总token数量"""
        return int(self.token_usage.get("total_tokens", 0))
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        if self.response_time < 0:
            raise HistoryError("response_time 不能为负数")


class TokenUsageRecord(BaseHistoryRecord, ITokenUsageRecord):
    """Token使用记录
    
    记录详细的Token使用情况，支持多维度统计。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        record_type: str = "token_usage",
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "",
        provider: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        source: TokenSource = TokenSource.API,
        confidence: float = 1.0
    ):
        """初始化Token使用记录"""
        super().__init__(
            record_id=record_id,
            session_id=session_id,
            workflow_id=workflow_id,
            timestamp=timestamp,
            record_type=record_type,
            metadata=metadata
        )
        self._model = model
        self._provider = provider
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._total_tokens = total_tokens
        self._source = source
        self._confidence = confidence
    
    @property
    def model(self) -> str:
        """模型名称"""
        return self._model
    
    @property
    def provider(self) -> str:
        """提供商"""
        return self._provider
    
    @property
    def prompt_tokens(self) -> int:
        """Prompt token数量"""
        return self._prompt_tokens
    
    @property
    def completion_tokens(self) -> int:
        """Completion token数量"""
        return self._completion_tokens
    
    @property
    def total_tokens(self) -> int:
        """总token数量"""
        return self._total_tokens
    
    @property
    def source(self) -> str:
        """Token来源"""
        return self._source.value
    
    @property
    def source_enum(self) -> TokenSource:
        """Token来源枚举值"""
        return self._source
    
    @property
    def confidence(self) -> float:
        """置信度"""
        return self._confidence
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        
        # 验证Token数量
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise TokenCalculationError("Token数量不能为负数")
        
        # 验证置信度
        if not 0.0 <= self.confidence <= 1.0:
            raise TokenCalculationError("confidence 必须在0.0到1.0之间")
        
        # 确保total_tokens等于prompt_tokens + completion_tokens
        calculated_total = self.prompt_tokens + self.completion_tokens
        if self.total_tokens != calculated_total:
            logger.warning(f"Token总数不一致，自动修正: {self.total_tokens} -> {calculated_total}")
            self._total_tokens = calculated_total
    
    @property
    def prompt_cost_per_1m(self) -> Optional[float]:
        """获取每1M prompt tokens的成本"""
        return self.metadata.get("prompt_cost_per_1m")
    
    @property
    def completion_cost_per_1m(self) -> Optional[float]:
        """获取每1M completion tokens的成本"""
        return self.metadata.get("completion_cost_per_1m")


class CostRecord(BaseHistoryRecord, ICostRecord):
    """成本记录
    
    记录LLM调用的成本信息。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        record_type: str = "cost",
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "",
        provider: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        prompt_cost: float = 0.0,
        completion_cost: float = 0.0,
        total_cost: float = 0.0,
        currency: str = "USD"
    ):
        """初始化成本记录"""
        super().__init__(
            record_id=record_id,
            session_id=session_id,
            workflow_id=workflow_id,
            timestamp=timestamp,
            record_type=record_type,
            metadata=metadata
        )
        self._model = model
        self._provider = provider
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._total_tokens = total_tokens
        self._prompt_cost = prompt_cost
        self._completion_cost = completion_cost
        self._total_cost = total_cost
        self._currency = currency
    
    @property
    def model(self) -> str:
        """模型名称"""
        return self._model
    
    @property
    def provider(self) -> str:
        """提供商"""
        return self._provider
    
    @property
    def prompt_tokens(self) -> int:
        """Prompt token数量"""
        return self._prompt_tokens
    
    @property
    def completion_tokens(self) -> int:
        """Completion token数量"""
        return self._completion_tokens
    
    @property
    def total_tokens(self) -> int:
        """总token数量"""
        return self._total_tokens
    
    @property
    def prompt_cost(self) -> float:
        """Prompt成本"""
        return self._prompt_cost
    
    @property
    def completion_cost(self) -> float:
        """Completion成本"""
        return self._completion_cost
    
    @property
    def total_cost(self) -> float:
        """总成本"""
        return self._total_cost
    
    @property
    def currency(self) -> str:
        """货币单位"""
        return self._currency
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        
        # 验证成本
        if any(cost < 0 for cost in [self.prompt_cost, self.completion_cost, self.total_cost]):
            raise CostCalculationError("成本不能为负数")
        
        # 验证Token数量
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise CostCalculationError("Token数量不能为负数")
        
        # 确保total_cost等于prompt_cost + completion_cost
        calculated_total = self.prompt_cost + self.completion_cost
        if abs(self.total_cost - calculated_total) > 0.0001:  # 允许小的浮点误差
            logger.warning(f"总成本不一致，自动修正: {self.total_cost} -> {calculated_total}")
            self._total_cost = calculated_total
    
    @property
    def avg_cost_per_token(self) -> float:
        """获取平均每个token的成本"""
        if self.total_tokens <= 0:
            logger.warning("Token数量为0或负数，返回0.0")
            return 0.0
        return self.total_cost / self.total_tokens
    
    @property
    def prompt_cost_per_1m(self) -> float:
        """获取每1M prompt tokens的成本"""
        if self.prompt_tokens <= 0:
            logger.warning("Prompt token数量为0或负数，返回0.0")
            return 0.0
        return (self.prompt_cost / self.prompt_tokens * 1000000)
    
    @property
    def completion_cost_per_1m(self) -> float:
        """获取每1M completion tokens的成本"""
        if self.completion_tokens <= 0:
            logger.warning("Completion token数量为0或负数，返回0.0")
            return 0.0
        return (self.completion_cost / self.completion_tokens * 1000000)
    


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
    
    def __post_init__(self) -> None:
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


class MessageRecord(BaseHistoryRecord, IMessageRecord):
    """消息记录
    
    记录对话中的消息。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        role: str = "",
        content: str = ""
    ):
        """初始化消息记录"""
        super().__init__(
            record_id=record_id,
            session_id=session_id,
            workflow_id=workflow_id,
            timestamp=timestamp,
            record_type="message",
            metadata=metadata
        )
        self._role = role
        self._content = content

    # 实现IMessageRecord接口的属性
    @property
    def role(self) -> str:
        """消息角色"""
        return self._role

    @property
    def content(self) -> str:
        """消息内容"""
        return self._content


class ToolCallRecord(BaseHistoryRecord, IToolCallRecord):
    """工具调用记录
    
    记录工具的调用和执行情况。
    """
    
    def __init__(
        self,
        record_id: str,
        session_id: str,
        workflow_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tool_name: str = "",
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """初始化工具调用记录"""
        super().__init__(
            record_id=record_id,
            session_id=session_id,
            workflow_id=workflow_id,
            timestamp=timestamp,
            record_type="tool_call",
            metadata=metadata
        )
        self._tool_name = tool_name
        self._tool_input = tool_input or {}
        self._tool_output = tool_output or {}
        self._status = status

    # 实现IToolCallRecord接口的属性
    @property
    def tool_name(self) -> str:
        """工具名称"""
        return self._tool_name

    @property
    def tool_input(self) -> Dict[str, Any]:
        """工具输入"""
        return self._tool_input

    @property
    def tool_output(self) -> Dict[str, Any]:
        """工具输出"""
        return self._tool_output

    @property
    def status(self) -> str:
        """调用状态"""
        return self._status


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