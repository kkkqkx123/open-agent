"""历史记录实体接口定义

定义历史记录管理中使用的实体接口，遵循分层架构原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from ..common_domain import ISerializable


class IBaseHistoryRecord(ISerializable, ABC):
    """历史记录基类接口
    
    定义所有历史记录的通用契约。
    """
    
    @property
    @abstractmethod
    def record_id(self) -> str:
        """记录ID"""
        pass
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """会话ID"""
        pass
    
    @property
    @abstractmethod
    def workflow_id(self) -> Optional[str]:
        """工作流ID"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """时间戳"""
        pass
    
    @property
    @abstractmethod
    def record_type(self) -> str:
        """记录类型"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass


class ILLMRequestRecord(IBaseHistoryRecord, ABC):
    """LLM请求记录接口
    
    定义LLM请求记录的基本契约。
    """
    
    @property
    @abstractmethod
    def model(self) -> str:
        """模型名称"""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """提供商"""
        pass
    
    @property
    @abstractmethod
    def messages(self) -> list:
        """消息列表"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """请求参数"""
        pass
    
    @property
    @abstractmethod
    def estimated_tokens(self) -> int:
        """估算的token数量"""
        pass


class ILLMResponseRecord(IBaseHistoryRecord, ABC):
    """LLM响应记录接口
    
    定义LLM响应记录的基本契约。
    """
    
    @property
    @abstractmethod
    def request_id(self) -> str:
        """关联的请求ID"""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """响应内容"""
        pass
    
    @property
    @abstractmethod
    def finish_reason(self) -> str:
        """完成原因"""
        pass
    
    @property
    @abstractmethod
    def token_usage(self) -> Dict[str, Any]:
        """Token使用情况"""
        pass
    
    @property
    @abstractmethod
    def response_time(self) -> float:
        """响应时间（秒）"""
        pass
    
    @property
    @abstractmethod
    def model(self) -> str:
        """使用的模型"""
        pass
    
    @property
    @abstractmethod
    def prompt_tokens(self) -> int:
        """Prompt token数量"""
        pass
    
    @property
    @abstractmethod
    def completion_tokens(self) -> int:
        """Completion token数量"""
        pass
    
    @property
    @abstractmethod
    def total_tokens(self) -> int:
        """总token数量"""
        pass


class ITokenUsageRecord(IBaseHistoryRecord, ABC):
    """Token使用记录接口
    
    定义Token使用记录的基本契约。
    """
    
    @property
    @abstractmethod
    def model(self) -> str:
        """模型名称"""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """提供商"""
        pass
    
    @property
    @abstractmethod
    def prompt_tokens(self) -> int:
        """Prompt token数量"""
        pass
    
    @property
    @abstractmethod
    def completion_tokens(self) -> int:
        """Completion token数量"""
        pass
    
    @property
    @abstractmethod
    def total_tokens(self) -> int:
        """总token数量"""
        pass
    
    @property
    @abstractmethod
    def source(self) -> str:
        """Token来源"""
        pass
    
    @property
    @abstractmethod
    def confidence(self) -> float:
        """置信度"""
        pass
    
    @property
    @abstractmethod
    def prompt_cost_per_1m(self) -> Optional[float]:
        """每1M prompt tokens的成本"""
        pass
    
    @property
    @abstractmethod
    def completion_cost_per_1m(self) -> Optional[float]:
        """每1M completion tokens的成本"""
        pass


class ICostRecord(IBaseHistoryRecord, ABC):
    """成本记录接口
    
    定义成本记录的基本契约。
    """
    
    @property
    @abstractmethod
    def model(self) -> str:
        """模型名称"""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """提供商"""
        pass
    
    @property
    @abstractmethod
    def prompt_tokens(self) -> int:
        """Prompt token数量"""
        pass
    
    @property
    @abstractmethod
    def completion_tokens(self) -> int:
        """Completion token数量"""
        pass
    
    @property
    @abstractmethod
    def total_tokens(self) -> int:
        """总token数量"""
        pass
    
    @property
    @abstractmethod
    def prompt_cost(self) -> float:
        """Prompt成本"""
        pass
    
    @property
    @abstractmethod
    def completion_cost(self) -> float:
        """Completion成本"""
        pass
    
    @property
    @abstractmethod
    def total_cost(self) -> float:
        """总成本"""
        pass
    
    @property
    @abstractmethod
    def currency(self) -> str:
        """货币单位"""
        pass
    
    @property
    @abstractmethod
    def avg_cost_per_token(self) -> float:
        """平均每个token的成本"""
        pass
    
    @property
    @abstractmethod
    def prompt_cost_per_1m(self) -> float:
        """每1M prompt tokens的成本"""
        pass
    
    @property
    @abstractmethod
    def completion_cost_per_1m(self) -> float:
        """每1M completion tokens的成本"""
        pass


class IMessageRecord(IBaseHistoryRecord, ABC):
    """消息记录接口
    
    定义消息记录的基本契约。
    """
    
    @property
    @abstractmethod
    def role(self) -> str:
        """消息角色"""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """消息内容"""
        pass


class IToolCallRecord(IBaseHistoryRecord, ABC):
    """工具调用记录接口
    
    定义工具调用记录的基本契约。
    """
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def tool_input(self) -> Dict[str, Any]:
        """工具输入"""
        pass
    
    @property
    @abstractmethod
    def tool_output(self) -> Dict[str, Any]:
        """工具输出"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """调用状态"""
        pass