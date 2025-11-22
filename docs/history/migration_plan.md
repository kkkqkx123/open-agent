

# 历史管理模块深度迁移分析与方案

## 1. HistoryRecordingHook 迁移方案

### 1.1 当前架构分析

旧架构中的 [`HistoryRecordingHook`](src/infrastructure/history/history_hook.py:29) 实现了 [`ILLMCallHook`](src/interfaces/llm.py:169) 接口，在新架构中该接口已经存在并位于 [`src/interfaces/llm.py`](src/interfaces/llm.py:169)。

### 1.2 迁移策略

**目标位置**: `src/services/history/hooks.py`

```python
"""历史记录钩子实现"""

from typing import Dict, Any, Optional, Sequence
from datetime import datetime
from langchain_core.messages import BaseMessage

from src.interfaces.llm import ILLMCallHook, LLMResponse
from src.interfaces.history import IHistoryManager
from src.core.history.entities import (
    LLMRequestRecord, LLMResponseRecord, 
    TokenUsageRecord, CostRecord
)
from src.services.history.cost_calculator import CostCalculator
from src.services.llm.token_calculation_service import TokenCalculationService

class HistoryRecordingHook(ILLMCallHook):
    """历史记录钩子 - 新架构版本"""
    
    def __init__(
        self,
        history_manager: IHistoryManager,
        token_calculation_service: TokenCalculationService,
        cost_calculator: CostCalculator,
        workflow_context: Optional[Dict[str, Any]] = None
    ):
        """
        初始化历史记录钩子
        
        Args:
            history_manager: 历史管理器
            token_calculation_service: Token计算服务
            cost_calculator: 成本计算器
            workflow_context: 工作流上下文信息
        """
        self.history_manager = history_manager
        self.token_service = token_calculation_service
        self.cost_calculator = cost_calculator
        self.workflow_context = workflow_context or {}
        self.pending_requests: Dict[str, LLMRequestRecord] = {}
    
    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """在LLM调用前记录请求"""
        # 获取工作流和模型信息
        workflow_id = self.workflow_context.get("workflow_id")
        model_info = kwargs.get("model_info", {})
        model_name = model_info.get("name", "unknown")
        model_type = model_info.get("type", "openai")
        
        # 创建请求记录
        request_record = LLMRequestRecord(
            record_id=self._generate_id(),
            session_id=kwargs.get("session_id", "default"),
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            model=model_name,
            provider=model_type,
            messages=self._convert_messages(messages),
            parameters=parameters or {},
            # 使用LLM模块的精确token计算，不进行估算
            estimated_tokens=self.token_service.calculate_messages_tokens(
                messages, model_type, model_name
            ),
            metadata={
                "workflow_context": self.workflow_context,
                **kwargs.get("metadata", {})
            }
        )
        
        # 保存到待处理请求
        request_id = request_record.record_id
        self.pending_requests[request_id] = request_record
        
        # 异步记录请求
        import asyncio
        asyncio.create_task(self.history_manager.record_llm_request(request_record))
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """在LLM调用后记录响应和token使用"""
        if response is None:
            return
        
        request_id = kwargs.get("request_id")
        if request_id not in self.pending_requests:
            return
        
        request_record = self.pending_requests.pop(request_id)
        
        # 从响应中获取精确的token使用信息
        token_usage = self._extract_token_usage(response)
        
        # 创建响应记录
        response_record = LLMResponseRecord(
            record_id=self._generate_id(),
            session_id=request_record.session_id,
            workflow_id=request_record.workflow_id,
            timestamp=datetime.now(),
            request_id=request_id,
            content=response.content,
            finish_reason=response.finish_reason or "stop",
            token_usage=token_usage,
            response_time=getattr(response, 'response_time', 0.0),
            model=request_record.model,
            metadata=response.metadata or {}
        )
        
        # 创建token使用记录（基于API响应的精确数据）
        token_record = TokenUsageRecord(
            record_id=self._generate_id(),
            session_id=request_record.session_id,
            workflow_id=request_record.workflow_id,
            timestamp=datetime.now(),
            model=request_record.model,
            provider=request_record.provider,
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            total_tokens=token_usage.get("total_tokens", 0),
            source="api",  # 标记为API返回的精确数据
            confidence=1.0,
            metadata={
                "request_id": request_id,
                "model_info": kwargs.get("model_info", {})
            }
        )
        
        # 计算成本
        cost_record = self.cost_calculator.calculate_cost(token_record)
        
        # 异步记录所有数据
        import asyncio
        asyncio.create_task(self._record_response_data(
            response_record, token_record, cost_record
        ))
    
    def _extract_token_usage(self, response: LLMResponse) -> Dict[str, Any]:
        """从响应中提取token使用信息"""
        # 优先使用响应中的token信息
        if hasattr(response, 'token_usage') and response.token_usage:
            return response.token_usage
        
        # 如果响应中没有token信息，尝试从元数据中提取
        if response.metadata and 'usage' in response.metadata:
            return response.metadata['usage']
        
        # 默认返回空字典
        return {}
    
    async def _record_response_data(
        self,
        response_record: LLMResponseRecord,
        token_record: TokenUsageRecord,
        cost_record: CostRecord
    ) -> None:
        """异步记录响应数据"""
        await self.history_manager.record_llm_response(response_record)
        await self.history_manager.record_token_usage(token_record)
        await self.history_manager.record_cost(cost_record)
```

### 1.3 集成方案

在 [`src/services/llm/manager.py`](src/services/llm/manager.py) 中集成钩子：

```python
class LLMManager:
    def __init__(self, ...):
        # 现有初始化代码
        self._history_hook: Optional[HistoryRecordingHook] = None
    
    def set_history_hook(self, hook: HistoryRecordingHook) -> None:
        """设置历史记录钩子"""
        self._history_hook = hook
    
    async def generate_async(self, messages, parameters=None, **kwargs):
        # 执行前钩子
        if self._history_hook:
            self._history_hook.before_call(messages, parameters, **kwargs)
        
        try:
            # 执行LLM调用
            response = await self._client.generate_async(messages, parameters, **kwargs)
            
            # 执行后钩子
            if self._history_hook:
                self._history_hook.after_call(response, messages, parameters, **kwargs)
            
            return response
        except Exception as e:
            # 错误钩子
            if self._history_hook:
                self._history_hook.on_error(e, messages, parameters, **kwargs)
            raise
```

## 2. 成本计算器实现迁移方案

### 2.1 目标位置

`src/services/history/cost_calculator.py`

### 2.2 实现方案

```python
"""成本计算服务实现"""

from typing import Dict, Any
from datetime import datetime
from dataclasses import dataclass

from src.interfaces.history import ICostCalculator
from src.core.history.entities import TokenUsageRecord, CostRecord

@dataclass
class ModelPricing:
    """模型定价配置"""
    input_price: float  # 输入token价格（每1K tokens）
    output_price: float  # 输出token价格（每1K tokens）
    currency: str = "USD"
    provider: str = "openai"

class CostCalculator(ICostCalculator):
    """成本计算器实现"""
    
    def __init__(self, pricing_config: Dict[str, Any] = None):
        """
        初始化成本计算器
        
        Args:
            pricing_config: 定价配置字典
        """
        self.pricing_config = pricing_config or {}
        self._model_pricing: Dict[str, ModelPricing] = {}
        self._load_default_pricing()
    
    def _load_default_pricing(self) -> None:
        """加载默认定价配置"""
        # OpenAI模型定价
        self._model_pricing.update({
            "gpt-4": ModelPricing(0.03, 0.06, "USD", "openai"),
            "gpt-4-32k": ModelPricing(0.06, 0.12, "USD", "openai"),
            "gpt-3.5-turbo": ModelPricing(0.0015, 0.002, "USD", "openai"),
            "gpt-3.5-turbo-16k": ModelPricing(0.003, 0.004, "USD", "openai"),
        })
        
        # Gemini模型定价
        self._model_pricing.update({
            "gemini-pro": ModelPricing(0.0005, 0.0015, "USD", "google"),
            "gemini-pro-vision": ModelPricing(0.0025, 0.0075, "USD", "google"),
        })
        
        # Anthropic模型定价
        self._model_pricing.update({
            "claude-3-opus": ModelPricing(0.015, 0.075, "USD", "anthropic"),
            "claude-3-sonnet": ModelPricing(0.003, 0.015, "USD", "anthropic"),
            "claude-3-haiku": ModelPricing(0.00025, 0.00125, "USD", "anthropic"),
        })
    
    def calculate_cost(self, token_usage: TokenUsageRecord) -> CostRecord:
        """计算成本"""
        model_name = token_usage.model
        pricing = self._model_pricing.get(model_name)
        
        if not pricing:
            # 使用默认定价
            pricing = ModelPricing(0.001, 0.002, "USD", "unknown")
        
        # 计算成本（价格是每1K tokens）
        prompt_cost = (token_usage.prompt_tokens / 1000) * pricing.input_price
        completion_cost = (token_usage.completion_tokens / 1000) * pricing.output_price
        total_cost = prompt_cost + completion_cost
        
        return CostRecord(
            record_id=self._generate_id(),
            session_id=token_usage.session_id,
            workflow_id=token_usage.workflow_id,
            timestamp=datetime.now(),
            model=model_name,
            provider=pricing.provider,
            prompt_tokens=token_usage.prompt_tokens,
            completion_tokens=token_usage.completion_tokens,
            total_tokens=token_usage.total_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            currency=pricing.currency,
            metadata={
                "pricing_source": "calculator",
                "confidence": token_usage.confidence
            }
        )
    
    def get_model_pricing(self, model_name: str) -> Dict[str, float]:
        """获取模型定价"""
        pricing = self._model_pricing.get(model_name)
        if not pricing:
            return {}
        
        return {
            "input_price": pricing.input_price,
            "output_price": pricing.output_price,
            "currency": pricing.currency
        }
    
    def update_pricing(self, model_name: str, input_price: float, output_price: float) -> None:
        """更新定价"""
        existing = self._model_pricing.get(model_name)
        if existing:
            existing.input_price = input_price
            existing.output_price = output_price
        else:
            self._model_pricing[model_name] = ModelPricing(
                input_price, output_price, "USD", "custom"
            )
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
```

## 3. 核心历史模块迁移方案

### 3.1 目录结构

```
src/core/history/
├── __init__.py
├── interfaces.py      # 核心接口定义
├── entities.py        # 历史记录实体
├── exceptions.py      # 历史管理异常
└── base.py           # 基础历史管理类
```

### 3.2 核心实体定义

`src/core/history/entities.py`:

```python
"""历史记录核心实体"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class RecordType(Enum):
    """记录类型枚举"""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOKEN_USAGE = "token_usage"
    COST = "cost"

@dataclass
class BaseHistoryRecord:
    """历史记录基类"""
    record_id: str
    session_id: str
    workflow_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    record_type: RecordType = RecordType.MESSAGE
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMRequestRecord(BaseHistoryRecord):
    """LLM请求记录"""
    record_type: RecordType = RecordType.LLM_REQUEST
    model: str = ""
    provider: str = ""
    messages: list = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 0

@dataclass
class LLMResponseRecord(BaseHistoryRecord):
    """LLM响应记录"""
    record_type: RecordType = RecordType.LLM_RESPONSE
    request_id: str = ""
    content: str = ""
    finish_reason: str = ""
    token_usage: Dict[str, Any] = field(default_factory=dict)
    response_time: float = 0.0
    model: str = ""

@dataclass
class TokenUsageRecord(BaseHistoryRecord):
    """Token使用记录"""
    record_type: RecordType = RecordType.TOKEN_USAGE
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    source: str = ""  # "api" 或 "local"
    confidence: float = 1.0

@dataclass
class CostRecord(BaseHistoryRecord):
    """成本记录"""
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

@dataclass
class WorkflowTokenStatistics:
    """工作流Token统计"""
    workflow_id: str
    model: str
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
```

### 3.3 核心接口定义

`src/core/history/interfaces.py`:

```python
"""历史管理核心接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from .entities import (
    BaseHistoryRecord, LLMRequestRecord, LLMResponseRecord,
    TokenUsageRecord, CostRecord, WorkflowTokenStatistics
)

class IHistoryStorage(ABC):
    """历史存储接口"""
    
    @abstractmethod
    async def save_record(self, record: BaseHistoryRecord) -> bool:
        """保存记录"""
        pass
    
    @abstractmethod
    async def get_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        record_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[BaseHistoryRecord]:
        """获取记录"""
        pass
    
    @abstractmethod
    async def get_workflow_token_stats(
        self,
        workflow_id: str,
        model: Optional[str] = None
    ) -> List[WorkflowTokenStatistics]:
        """获取工作流Token统计"""
        pass

class ITokenTracker(ABC):
    """Token追踪器接口"""
    
    @abstractmethod
    async def track_workflow_token_usage(
        self,
        workflow_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """追踪工作流Token使用"""
        pass
    
    @abstractmethod
    async def get_workflow_statistics(
        self,
        workflow_id: str,
        model: Optional[str] = None
    ) -> WorkflowTokenStatistics:
        """获取工作流统计"""
        pass
```

## 4. 基于LLM模块的Token追踪改进方案

### 4.1 设计原则

1. **精确性**: 完全基于LLM模块的Token计算服务，不进行任何估算
2. **多维度**: 支持按工作流和模型维度分别统计
3. **实时性**: 在LLM调用完成后立即更新统计信息
4. **持久化**: 统计信息持久化存储，支持历史查询

### 4.2 实现方案

`src/services/history/token_tracker.py`:

```python
"""Token追踪服务实现"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import asdict

from src.core.history.interfaces import ITokenTracker, IHistoryStorage
from src.core.history.entities import TokenUsageRecord, WorkflowTokenStatistics
from src.services.llm.token_calculation_service import TokenCalculationService

class WorkflowTokenTracker(ITokenTracker):
    """工作流Token追踪器"""
    
    def __init__(
        self,
        storage: IHistoryStorage,
        token_calculation_service: TokenCalculationService
    ):
        """
        初始化Token追踪器
        
        Args:
            storage: 历史存储
            token_calculation_service: Token计算服务
        """
        self._storage = storage
        self._token_service = token_calculation_service
        self._workflow_stats_cache: Dict[str, Dict[str, WorkflowTokenStatistics]] = {}
    
    async def track_workflow_token_usage(
        self,
        workflow_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """追踪工作流Token使用"""
        # 创建Token使用记录
        token_record = TokenUsageRecord(
            record_id=self._generate_id(),
            session_id=metadata.get("session_id", "default") if metadata else "default",
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            model=model,
            provider=metadata.get("provider", "unknown") if metadata else "unknown",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            source="api",
            confidence=1.0,
            metadata=metadata or {}
        )
        
        # 保存记录
        await self._storage.save_record(token_record)
        
        # 更新工作流统计
        await self._update_workflow_statistics(workflow_id, model, token_record)
    
    async def _update_workflow_statistics(
        self,
        workflow_id: str,
        model: str,
        token_record: TokenUsageRecord
    ) -> None:
        """更新工作流统计信息"""
        # 获取现有统计
        stats_key = f"{workflow_id}:{model}"
        if workflow_id not in self._workflow_stats_cache:
            self._workflow_stats_cache[workflow_id] = {}
        
        if stats_key not in self._workflow_stats_cache[workflow_id]:
            # 从存储加载现有统计
            existing_stats = await self._storage.get_workflow_token_stats(
                workflow_id, model
            )
            if existing_stats:
                self._workflow_stats_cache[workflow_id][stats_key] = existing_stats[0]
            else:
                # 创建新统计
                self._workflow_stats_cache[workflow_id][stats_key] = WorkflowTokenStatistics(
                    workflow_id=workflow_id,
                    model=model
                )
        
        # 更新统计
        stats = self._workflow_stats_cache[workflow_id][stats_key]
        stats.total_prompt_tokens += token_record.prompt_tokens
        stats.total_completion_tokens += token_record.completion_tokens
        stats.total_tokens += token_record.total_tokens
        stats.request_count += 1
        stats.last_updated = datetime.now()
        
        # 计算成本（如果有成本计算器）
        if hasattr(self, '_cost_calculator'):
            cost_record = self._cost_calculator.calculate_cost(token_record)
            stats.total_cost += cost_record.total_cost
        
        # 持久化更新后的统计
        await self._storage.save_record(stats)
    
    async def get_workflow_statistics(
        self,
        workflow_id: str,
        model: Optional[str] = None
    ) -> WorkflowTokenStatistics:
        """获取工作流统计"""
        if model:
            stats_key = f"{workflow_id}:{model}"
            if (workflow_id in self._workflow_stats_cache and 
                stats_key in self._workflow_stats_cache[workflow_id]):
                return self._workflow_stats_cache[workflow_id][stats_key]
        
        # 从存储获取
        stats_list = await self._storage.get_workflow_token_stats(workflow_id, model)
        if stats_list:
            return stats_list[0]
        
        # 返回空统计
        return WorkflowTokenStatistics(
            workflow_id=workflow_id,
            model=model or "unknown"
        )
    
    async def get_multi_model_statistics(
        self,
        workflow_id: str
    ) -> Dict[str, WorkflowTokenStatistics]:
        """获取工作流多模型统计"""
        stats_list = await self._storage.get_workflow_token_stats(workflow_id)
        return {stats.model: stats for stats in stats_list}
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
```

## 5. Workflow和模型维度的Token统计方案

### 5.1 统计数据结构

```python
@dataclass
class WorkflowTokenSummary:
    """工作流Token汇总统计"""
    workflow_id: str
    total_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    model_breakdown: Dict[str, WorkflowTokenStatistics] = field(default_factory=dict)
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    def add_model_stats(self, stats: WorkflowTokenStatistics) -> None:
        """添加模型统计"""
        if stats.model not in self.model_breakdown:
            self.model_breakdown[stats.model] = stats
        
        self.total_tokens += stats.total_tokens
        self.total_cost += stats.total_cost
        self.total_requests += stats.request_count
        
        # 更新时间范围
        if stats.last_updated < self.period_start:
            self.period_start = stats.last_updated
        if stats.last_updated > self.period_end:
            self.period_end = stats.last_updated
```

### 5.2 统计查询服务

`src/services/history/statistics_service.py`:

```python
"""历史统计服务"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.core.history.interfaces import IHistoryStorage
from src.core.history.entities import WorkflowTokenStatistics, WorkflowTokenSummary

class HistoryStatisticsService:
    """历史统计服务"""
    
    def __init__(self, storage: IHistoryStorage):
        """
        初始化统计服务
        
        Args:
            storage: 历史存储
        """
        self._storage = storage
    
    async def get_workflow_token_summary(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> WorkflowTokenSummary:
        """获取工作流Token汇总统计"""
        # 获取指定时间范围内的所有模型统计
        model_stats = await self._storage.get_workflow_token_stats(
            workflow_id, start_time=start_time, end_time=end_time
        )
        
        # 创建汇总统计
        summary = WorkflowTokenSummary(workflow_id=workflow_id)
        for stats in model_stats:
            summary.add_model_stats(stats)
        
        return summary
    
    async def get_cross_workflow_comparison(
        self,
        workflow_ids: List[str],
        metric: str = "total_tokens"
    ) -> Dict[str, float]:
        """获取跨工作流对比统计"""
        comparison = {}
        
        for workflow_id in workflow_ids:
            summary = await self.get_workflow_token_summary(workflow_id)
            if metric == "total_tokens":
                comparison[workflow_id] = summary.total_tokens
            elif metric == "total_cost":
                comparison[workflow_id] = summary.total_cost
            elif metric == "total_requests":
                comparison[workflow_id] = summary.total_requests
        
        return comparison
    
    async def get_model_usage_trends(
        self,
        workflow_id: str,
        days: int = 7
    ) -> Dict[str, List[Dict[str, Any]]]:
        """获取模型使用趋势"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 按天分组获取统计
        daily_stats = {}
        current_date = start_time.date()
        
        while current_date <= end_time.date():
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            
            day_summary = await self.get_workflow_token_summary(
                workflow_id, day_start, day_end
            )
            
            daily_stats[current_date.isoformat()] = {
                "total_tokens": day_summary.total_tokens,
                "total_cost": day_summary.total_cost,
                "model_breakdown": {
                    model: {
                        "tokens": stats.total_tokens,
                        "cost": stats.total_cost,
                        "requests": stats.request_count
                    }
                    for model, stats in day_summary.model_breakdown.items()
                }
            }
            
            current_date += timedelta(days=1)
        
        return daily_stats
```

## 6. 集成和依赖注入配置

### 6.1 服务注册

`src/services/history/di_config.py`:

```python
"""历史管理服务依赖注入配置"""

from typing import Dict, Any
from pathlib import Path

from src.services.container import IDependencyContainer
from src.core.history.interfaces import IHistoryStorage, ITokenTracker
from src.services.history.manager import HistoryManager
from src.services.history.hooks import HistoryRecordingHook
from src.services.history.cost_calculator import CostCalculator
from src.services.history.token_tracker import WorkflowTokenTracker
from src.services.history.statistics_service import HistoryStatisticsService
from src.adapters.storage.adapters.file import FileStorageAdapter
from src.services.llm.token_calculation_service import TokenCalculationService

def register_history_services(
    container: IDependencyContainer,
    config: Dict[str, Any]
) -> None:
    """注册历史管理相关服务"""
    history_config = config.get("history", {})
    
    if not history_config.get("enabled", False):
        return
    
    # 注册存储适配器
    storage_path = Path(history_config.get("storage_path", "./history"))
    container.register_instance(
        IHistoryStorage,
        FileHistoryStorageAdapter(storage_path)
    )
    
    # 注册Token计算服务
    container.register_singleton(
        TokenCalculationService,
        TokenCalculationService()
    )
    
    # 注册成本计算器
    pricing_config = history_config.get("pricing", {})
    container.register_singleton(
        CostCalculator,
        CostCalculator(pricing_config)
    )
    
    # 注册Token追踪器
    container.register_singleton(
        ITokenTracker,
        WorkflowTokenTracker
    )
    
    # 注册历史管理器
    container.register_singleton(
        HistoryManager,
        HistoryManager
    )
    
    # 注册统计服务
    container.register_singleton(
        HistoryStatisticsService,
        HistoryStatisticsService
    )
    
    # 注册历史记录钩子
    container.register_factory(
        HistoryRecordingHook,
        lambda c: HistoryRecordingHook(
            history_manager=c.get(HistoryManager),
            token_calculation_service=c.get(TokenCalculationService),
            cost_calculator=c.get(CostCalculator)
        )
    )
```

## 7. 总结

通过以上迁移方案，我们实现了：

1. **HistoryRecordingHook**: 完全迁移到新架构，集成到LLM调用流程中
2. **成本计算器**: 提供完整的实现，支持多模型定价
3. **核心历史模块**: 创建了完整的实体和接口定义
4. **Token追踪改进**: 基于LLM模块的精确计算，支持工作流和模型维度统计
5. **统计服务**: 提供丰富的查询和分析功能

这个方案确保了：
- **精确性**: 完全基于LLM模块的Token计算，不进行估算
- **多维度**: 支持按工作流和模型分别统计
- **可扩展性**: 易于添加新的统计维度和功能
- **一致性**: 与新架构的扁平化设计保持一致