"""历史管理核心接口

定义历史记录管理的所有核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .entities import (
    BaseHistoryRecord, LLMRequestRecord, LLMResponseRecord,
    TokenUsageRecord, CostRecord, WorkflowTokenStatistics,
    RecordType, TokenSource, MessageRecord, ToolCallRecord,
    HistoryQuery, HistoryResult
)


class IHistoryStorage(ABC):
    """历史存储接口
    
    定义历史记录存储的抽象接口，支持多种存储后端。
    """
    
    @abstractmethod
    async def save_record(self, record: BaseHistoryRecord) -> bool:
        """
        保存历史记录
        
        Args:
            record: 要保存的历史记录
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def save_records(self, records: List[BaseHistoryRecord]) -> List[bool]:
        """
        批量保存历史记录
        
        Args:
            records: 要保存的历史记录列表
            
        Returns:
            List[bool]: 每条记录的保存结果
        """
        pass
    
    @abstractmethod
    async def get_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        record_type: Optional[RecordType] = None,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseHistoryRecord]:
        """
        获取历史记录
        
        Args:
            session_id: 会话ID过滤
            workflow_id: 工作流ID过滤
            record_type: 记录类型过滤
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            List[BaseHistoryRecord]: 历史记录列表
        """
        pass
    
    @abstractmethod
    async def get_record_by_id(self, record_id: str) -> Optional[BaseHistoryRecord]:
        """
        根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            Optional[BaseHistoryRecord]: 历史记录，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_workflow_token_stats(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[WorkflowTokenStatistics]:
        """
        获取工作流Token统计
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            List[WorkflowTokenStatistics]: 统计信息列表
        """
        pass
    
    @abstractmethod
    async def update_workflow_token_stats(
        self,
        stats: WorkflowTokenStatistics
    ) -> bool:
        """
        更新工作流Token统计
        
        Args:
            stats: 统计信息
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional[datetime] = None
    ) -> int:
        """
        删除历史记录
        
        Args:
            session_id: 会话ID过滤
            workflow_id: 工作流ID过滤
            older_than: 删除早于此时间的记录
            
        Returns:
            int: 删除的记录数量
        """
        pass
    
    @abstractmethod
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        pass


class ITokenTracker(ABC):
    """Token追踪器接口
    
    定义Token使用追踪的抽象接口。
    """
    
    @abstractmethod
    async def track_workflow_token_usage(
        self,
        workflow_id: str,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        source: TokenSource = TokenSource.API,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        追踪工作流Token使用
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称
            provider: 提供商名称
            prompt_tokens: Prompt token数量
            completion_tokens: Completion token数量
            source: Token来源
            confidence: 置信度
            metadata: 额外元数据
        """
        pass
    
    @abstractmethod
    async def track_llm_request(
        self,
        workflow_id: str,
        session_id: str,
        model: str,
        provider: str,
        messages: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        estimated_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        追踪LLM请求
        
        Args:
            workflow_id: 工作流ID
            session_id: 会话ID
            model: 模型名称
            provider: 提供商名称
            messages: 消息列表
            parameters: 请求参数
            estimated_tokens: 估算的token数量
            metadata: 额外元数据
            
        Returns:
            str: 请求记录ID
        """
        pass
    
    @abstractmethod
    async def track_llm_response(
        self,
        request_id: str,
        content: str,
        finish_reason: str,
        token_usage: Dict[str, Any],
        response_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        追踪LLM响应
        
        Args:
            request_id: 请求ID
            content: 响应内容
            finish_reason: 完成原因
            token_usage: Token使用情况
            response_time: 响应时间
            metadata: 额外元数据
        """
        pass
    
    @abstractmethod
    async def get_workflow_statistics(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> WorkflowTokenStatistics:
        """
        获取工作流统计
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            WorkflowTokenStatistics: 统计信息
        """
        pass
    
    @abstractmethod
    async def get_multi_model_statistics(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, WorkflowTokenStatistics]:
        """
        获取工作流多模型统计
        
        Args:
            workflow_id: 工作流ID
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, WorkflowTokenStatistics]: 模型名称到统计信息的映射
        """
        pass
    
    @abstractmethod
    async def get_cross_workflow_statistics(
        self,
        workflow_ids: List[str],
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, WorkflowTokenStatistics]:
        """
        获取跨工作流统计
        
        Args:
            workflow_ids: 工作流ID列表
            model: 模型名称过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            Dict[str, WorkflowTokenStatistics]: 工作流ID到统计信息的映射
        """
        pass


class ICostCalculator(ABC):
    """成本计算器接口
    
    定义成本计算的抽象接口。
    """
    
    @abstractmethod
    def calculate_cost(self, token_usage: TokenUsageRecord) -> CostRecord:
        """
        计算Token使用的成本
        
        Args:
            token_usage: Token使用记录
            
        Returns:
            CostRecord: 成本记录
        """
        pass
    
    @abstractmethod
    def calculate_cost_from_tokens(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        currency: str = "USD"
    ) -> CostRecord:
        """
        根据Token数量计算成本
        
        Args:
            model: 模型名称
            provider: 提供商名称
            prompt_tokens: Prompt token数量
            completion_tokens: Completion token数量
            currency: 货币单位
            
        Returns:
            CostRecord: 成本记录
        """
        pass
    
    @abstractmethod
    def get_model_pricing(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型定价信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 定价信息
        """
        pass
    
    @abstractmethod
    def update_pricing(
        self,
        model_name: str,
        input_price: float,
        output_price: float,
        currency: str = "USD",
        provider: str = "custom"
    ) -> None:
        """
        更新模型定价
        
        Args:
            model_name: 模型名称
            input_price: 输入价格（每1K tokens）
            output_price: 输出价格（每1K tokens）
            currency: 货币单位
            provider: 提供商名称
        """
        pass
    
    @abstractmethod
    def list_supported_models(self) -> List[str]:
        """
        获取支持的模型列表
        
        Returns:
            List[str]: 模型名称列表
        """
        pass
    
    @abstractmethod
    def get_provider_models(self, provider: str) -> List[str]:
        """
        获取指定提供商的模型列表
        
        Args:
            provider: 提供商名称
            
        Returns:
            List[str]: 模型名称列表
        """
        pass


class IHistoryManager(ABC):
    """历史管理器接口
    
    定义历史记录管理的统一接口。
    """
    
    @abstractmethod
    async def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        pass
    
    @abstractmethod
    async def record_tool_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        pass
    
    @abstractmethod
    async def record_llm_request(self, record: LLMRequestRecord) -> None:
        """记录LLM请求"""
        pass
    
    @abstractmethod
    async def record_llm_response(self, record: LLMResponseRecord) -> None:
        """记录LLM响应"""
        pass
    
    @abstractmethod
    async def record_token_usage(self, record: TokenUsageRecord) -> None:
        """记录Token使用"""
        pass
    
    @abstractmethod
    async def record_cost(self, record: CostRecord) -> None:
        """记录成本"""
        pass
    
    @abstractmethod
    async def query_history(self, query: HistoryQuery) -> HistoryResult:
        """查询历史记录"""
        pass
    
    @abstractmethod
    async def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token统计"""
        pass
    
    @abstractmethod
    async def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        pass
    
    @abstractmethod
    async def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM统计"""
        pass