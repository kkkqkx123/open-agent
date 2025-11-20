import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Sequence
from langchain_core.messages import BaseMessage

from src.interfaces.llm_core import ILLMCallHook
from src.core.llm.models import LLMResponse
from src.domain.history import (
    LLMRequestRecord,
    LLMResponseRecord,
    TokenUsageRecord,
    CostRecord,
    IHistoryManager
)
from src.domain.history.cost_interfaces import ICostCalculator
from infrastructure.history.token_tracker import TokenUsageTracker


def generate_id() -> str:
    """生成唯一ID的辅助函数"""
    import uuid
    return str(uuid.uuid4())


from infrastructure.history.session_context import get_current_session as get_current_session_id


class HistoryRecordingHook(ILLMCallHook):
    """历史记录钩子 - 用于记录LLM请求和响应、Token使用和成本"""
    
    def __init__(self, history_manager: IHistoryManager,
    token_tracker: TokenUsageTracker,
    cost_calculator: ICostCalculator):
        """
        初始化历史记录钩子
        
        Args:
            history_manager: 历史管理器
            token_tracker: Token使用追踪器
            cost_calculator: 成本计算器
        """
        self.history_manager = history_manager
        self.token_tracker = token_tracker
        self.cost_calculator = cost_calculator
        self.pending_requests: Dict[str, LLMRequestRecord] = {}
        self.logger = logging.getLogger(__name__)
    
    def before_call(self, messages: Sequence[BaseMessage],
                   parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """
        在LLM调用前记录请求
        
        Args:
            messages: 消息列表
            parameters: 调用参数
            **kwargs: 其他参数
        """
        try:
            # 生成请求ID
            request_id = kwargs.get("request_id", generate_id())
            
            # 创建LLM请求记录
            request_record = LLMRequestRecord(
                record_id=request_id,
                session_id=kwargs.get("session_id", get_current_session_id()) or "default_session",
                timestamp=datetime.now(),
                model=kwargs.get("model", "unknown"),
                provider=kwargs.get("provider", "unknown"),
                messages=self._convert_messages(messages),
                parameters=parameters or {},
                estimated_tokens=self.token_tracker.estimate_tokens(list(messages)),
                metadata=kwargs.get("metadata", {})
            )
            
            # 保存到待处理请求字典
            self.pending_requests[request_record.record_id] = request_record
            
            # 记录到历史（异步执行）
            asyncio.create_task(self.history_manager.record_llm_request(request_record))
            
            self.logger.debug(f"记录LLM请求: {request_record.record_id}")
            
        except Exception as e:
            self.logger.error(f"记录LLM请求失败: {e}")
    
    def after_call(self, response: Optional[LLMResponse],
                  messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """
        在LLM调用后记录响应、Token使用和成本
        
        Args:
            response: LLM响应
            messages: 原始消息列表
            parameters: 调用参数
            **kwargs: 其他参数
        """
        if response is None:
            return
        
        try:
            request_id = kwargs.get("request_id")
            if request_id in self.pending_requests:
                request_record = self.pending_requests.pop(request_id)
                
                # 记录LLM响应
                response_record = LLMResponseRecord(
                    record_id=generate_id(),
                    session_id=request_record.session_id,
                    timestamp=datetime.now(),
                    request_id=request_id,
                    content=response.content,
                    finish_reason=response.finish_reason or "stop",
                    token_usage={
                        "prompt_tokens": response.token_usage.prompt_tokens,
                        "completion_tokens": response.token_usage.completion_tokens,
                        "total_tokens": response.token_usage.total_tokens
                    },
                    response_time=response.response_time or 0.0,
                    model=response.model,
                    metadata=response.metadata
                )
                
                # 记录Token使用
                token_record = TokenUsageRecord(
                    record_id=generate_id(),
                    session_id=request_record.session_id,
                    timestamp=datetime.now(),
                    model=response.model,
                    provider=request_record.provider,
                    prompt_tokens=response.token_usage.prompt_tokens,
                    completion_tokens=response.token_usage.completion_tokens,
                    total_tokens=response.token_usage.total_tokens,
                    source="api",
                    confidence=1.0,
                    metadata=response.metadata
                )
                
                # 记录成本
                cost_record = self.cost_calculator.calculate_cost(token_record)
                
                # 异步记录所有数据
                asyncio.create_task(self._record_response_data(response_record, token_record, cost_record))
                
                self.logger.debug(f"记录LLM响应和相关数据: {request_id}")
            
        except Exception as e:
            self.logger.error(f"记录LLM响应失败: {e}")
    
    async def _record_response_data(self, response_record: LLMResponseRecord, 
                                  token_record: TokenUsageRecord, 
                                  cost_record: CostRecord) -> None:
        """异步记录响应数据"""
        try:
            await self.history_manager.record_llm_response(response_record)
            await self.history_manager.record_token_usage(token_record)
            await self.history_manager.record_cost(cost_record)
        except Exception as e:
            self.logger.error(f"异步记录响应数据失败: {e}")
    
    def on_error(self, error: Exception, messages: Sequence[BaseMessage],
                 parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Optional[LLMResponse]:
        """
        记录错误（可选实现）
        
        Args:
            error: 发生的错误
            messages: 消息列表
            parameters: 调用参数
            **kwargs: 其他参数
            
        Returns:
            Optional[LLMResponse]: 如果可以恢复，返回替代响应；否则返回None
        """
        # 记录错误，但不尝试恢复
        request_id = kwargs.get("request_id", generate_id())
        session_id = kwargs.get("session_id", get_current_session_id()) or "default_session"
        
        # 如果有对应的请求记录，记录错误信息
        if request_id in self.pending_requests:
            request_record = self.pending_requests.pop(request_id)
            
            # 创建错误响应记录
            error_response_record = LLMResponseRecord(
                record_id=generate_id(),
                session_id=session_id,
                timestamp=datetime.now(),
                request_id=request_id,
                content=f"Error: {str(error)}",
                finish_reason="error",
                token_usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                response_time=0.0,
                model=kwargs.get("model", "unknown"),
                metadata={"error": str(error), **kwargs.get("metadata", {})}
            )
            
            # 异步记录错误响应
            asyncio.create_task(self.history_manager.record_llm_response(error_response_record))
        
        self.logger.error(f"LLM调用错误: {error} - Request ID: {request_id}")
        
        # 不尝试恢复错误
        return None
    
    def _convert_messages(self, messages: Sequence[BaseMessage]) -> List[Dict[str, Any]]:
        """
        将BaseMessage转换为字典格式
        
        Args:
            messages: 消息序列
            
        Returns:
            List[Dict[str, Any]]: 转换后的消息列表
        """
        converted = []
        for msg in messages:
            converted.append({
                "type": msg.type,
                "content": str(getattr(msg, 'content', '')),
                "additional_kwargs": getattr(msg, 'additional_kwargs', {})
            })
        return converted