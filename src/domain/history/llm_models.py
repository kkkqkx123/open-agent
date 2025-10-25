from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

@dataclass
class LLMRequestRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    model: str
    provider: str
    messages: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    record_type: str = "llm_request"
    estimated_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMResponseRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    request_id: str  # 关联请求记录
    content: str
    finish_reason: str
    token_usage: Dict[str, int]  # prompt, completion, total
    response_time: float
    model: str
    record_type: str = "llm_response"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TokenUsageRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    source: str  # "api", "local", "hybrid"
    record_type: str = "token_usage"
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CostRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: float
    completion_cost: float
    total_cost: float
    record_type: str = "cost"
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)