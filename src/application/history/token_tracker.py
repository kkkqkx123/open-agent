from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage

from src.domain.history import TokenUsageRecord, LLMRequestRecord, LLMResponseRecord
from src.infrastructure.llm.token_calculators.base import ITokenCalculator
from src.domain.history.interfaces import IHistoryManager


def generate_id() -> str:
    """生成唯一ID的辅助函数"""
    import uuid
    return str(uuid.uuid4())


def get_current_session() -> str:
    """获取当前会话ID的辅助函数"""
    # 这里应该从上下文获取当前会话ID
    # 为了简化，暂时返回一个默认值，实际实现中应该从上下文获取
    return "default_session"


class TokenUsageTracker:
    """Token使用追踪器"""
    
    def __init__(self, token_counter: ITokenCalculator, history_manager: IHistoryManager):
        self.token_counter = token_counter
        self.history_manager = history_manager
        self.usage_history: List[TokenUsageRecord] = []
    
    def track_request(self, messages: List[BaseMessage], 
                     model: str, provider: str, session_id: Optional[str] = None) -> TokenUsageRecord:
        """
        追踪LLM请求的Token使用情况
        
        Args:
            messages: 消息列表
            model: 模型名称
            provider: 提供商名称
            session_id: 会话ID
            
        Returns:
            TokenUsageRecord: Token使用记录
        """
        # 计算token使用量
        total_tokens = self.token_counter.count_messages_tokens(messages) or 0
        
        # 创建使用记录
        record = TokenUsageRecord(
            record_id=generate_id(),
            session_id=session_id or get_current_session(),
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            prompt_tokens=total_tokens,  # 初步估算，后续会被API响应更新
            completion_tokens=0,
            total_tokens=total_tokens,
            source="local",  # 或从API获取
            confidence=0.7  # 本地估算的置信度较低
        )
        
        # 保存到历史记录
        self.history_manager.record_token_usage(record)
        self.usage_history.append(record)
        
        return record
    
    def update_from_response(self, record: TokenUsageRecord, 
                           api_response: Dict[str, Any]) -> TokenUsageRecord:
        """
        从API响应更新Token使用记录
        
        Args:
            record: 原始Token使用记录
            api_response: API响应数据
            
        Returns:
            TokenUsageRecord: 更新后的Token使用记录
        """
        # 从API响应更新准确的token数
        if "usage" in api_response:
            usage = api_response["usage"]
            record.prompt_tokens = usage.get("prompt_tokens", record.prompt_tokens)
            record.completion_tokens = usage.get("completion_tokens", record.completion_tokens)
            record.total_tokens = usage.get("total_tokens", record.total_tokens)
            record.source = "api"
            record.confidence = 1.0  # API数据的置信度最高
        elif "usageMetadata" in api_response:
            # Gemini API格式
            usage = api_response["usageMetadata"]
            record.prompt_tokens = usage.get("promptTokenCount", record.prompt_tokens)
            record.completion_tokens = usage.get("candidatesTokenCount", record.completion_tokens)
            record.total_tokens = usage.get("totalTokenCount", record.total_tokens)
            record.source = "api"
            record.confidence = 1.0
        elif "usage" in api_response and "input_tokens" in api_response["usage"]:
            # Anthropic API格式
            usage = api_response["usage"]
            record.prompt_tokens = usage.get("input_tokens", record.prompt_tokens)
            record.completion_tokens = usage.get("output_tokens", record.completion_tokens)
            record.total_tokens = record.prompt_tokens + record.completion_tokens
            record.source = "api"
            record.confidence = 1.0
        
        # 更新历史记录
        self.history_manager.record_token_usage(record)
        
        return record
    
    def estimate_tokens(self, messages: List[BaseMessage]) -> int:
        """
        估算Token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: 估算的Token数量
        """
        return self.token_counter.count_messages_tokens(messages) or 0
    
    def get_session_token_usage(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的Token使用统计
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: Token使用统计信息
        """
        # 这里需要查询历史记录以获取统计信息
        # 由于IHistoryManager接口还没有实现，这里返回模拟数据
        return {
            "session_id": session_id,
            "total_tokens": sum(record.total_tokens for record in self.usage_history 
                              if record.session_id == session_id),
            "prompt_tokens": sum(record.prompt_tokens for record in self.usage_history 
                               if record.session_id == session_id),
            "completion_tokens": sum(record.completion_tokens for record in self.usage_history 
                                    if record.session_id == session_id),
        }