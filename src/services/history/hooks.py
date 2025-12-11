"""历史记录钩子实现

提供LLM调用的历史记录钩子，集成到LLM调用流程中。
"""

import asyncio
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, Sequence, List, TYPE_CHECKING
from datetime import datetime

from src.interfaces.llm import ILLMCallHook, LLMResponse
from src.infrastructure.messages.base import BaseMessage

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage
from src.interfaces.history import IHistoryManager, ICostCalculator
from src.core.history.entities import (
    LLMRequestRecord, LLMResponseRecord, 
    TokenUsageRecord, CostRecord
)
from src.services.llm.token_calculation_service import TokenCalculationService


logger = get_logger(__name__)


class HistoryRecordingHook(ILLMCallHook):
    """历史记录钩子 - 新架构版本
    
    实现ILLMCallHook接口，在LLM调用前后记录相关信息。
    """
    
    def __init__(
        self,
        history_manager: IHistoryManager,
        token_calculation_service: TokenCalculationService,
        cost_calculator: ICostCalculator,
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
        self._logger = get_logger(self.__class__.__name__)
    
    def before_call(
        self,
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        在LLM调用前记录请求
        
        Args:
            messages: 消息列表
            parameters: 调用参数
            **kwargs: 其他参数
        """
        try:
            # 获取工作流和模型信息
            workflow_id = self.workflow_context.get("workflow_id")
            session_id = kwargs.get("session_id") or self.workflow_context.get("session_id", "default")
            
            model_info = kwargs.get("model_info", {})
            model_name = model_info.get("name", "unknown")
            model_type = model_info.get("type", "openai")
            provider = model_info.get("provider", model_type)
            
            # 生成请求ID
            request_id = kwargs.get("request_id", self._generate_id())
            
            # 转换消息格式
            converted_messages = self._convert_messages(messages)
            
            # 使用LLM模块的精确token计算，不进行估算
            # 类型转换：IBaseMessage -> BaseMessage（运行时兼容）
            estimated_tokens = self.token_service.calculate_messages_tokens(
                messages,
                model_type, model_name
            )
            
            # 创建请求记录
            request_record = LLMRequestRecord(
                record_id=request_id,
                session_id=session_id,
                workflow_id=workflow_id,
                timestamp=datetime.now(),
                model=model_name,
                provider=provider,
                messages=converted_messages,
                parameters=parameters or {},
                estimated_tokens=estimated_tokens,
                metadata={
                    "workflow_context": self.workflow_context,
                    "model_info": model_info,
                    **kwargs.get("metadata", {})
                }
            )
            
            # 保存到待处理请求字典
            self.pending_requests[request_id] = request_record
            
            # 异步记录请求
            asyncio.create_task(self._record_llm_request(request_record))
            
            self._logger.debug(f"记录LLM请求: {request_id}, 模型: {model_name}, "
                             f"估算Token: {estimated_tokens}")
            
        except Exception as e:
            self._logger.error(f"记录LLM请求失败: {e}")
            # 不抛出异常，避免影响LLM调用
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        在LLM调用后记录响应和token使用
        
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
            if request_id not in self.pending_requests:
                self._logger.warning(f"未找到对应的请求记录: {request_id}")
                return
            
            request_record = self.pending_requests.pop(request_id)
            
            # 从响应中提取token使用信息
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
                record_type="token_usage",
                metadata={
                    "request_id": request_id,
                    "model_info": kwargs.get("model_info", {}),
                    "response_time": getattr(response, 'response_time', 0.0)
                },
                model=request_record.model,
                provider=request_record.provider,
                prompt_tokens=token_usage.get("prompt_tokens", 0),
                completion_tokens=token_usage.get("completion_tokens", 0),
                total_tokens=token_usage.get("total_tokens", 0),
                confidence=1.0
            )
            
            # 计算成本
            cost_record = self.cost_calculator.calculate_cost(token_record)
            
            # 异步记录所有数据
            asyncio.create_task(self._record_response_data(
                response_record, token_record, cost_record
            ))
            
            self._logger.debug(f"记录LLM响应: {request_id}, "
                             f"Token: {token_record.total_tokens}, "
                             f"成本: {cost_record.total_cost:.6f}")
            
        except Exception as e:
            self._logger.error(f"记录LLM响应失败: {e}")
            # 不抛出异常，避免影响LLM调用
    
    def on_error(
        self,
        error: Exception,
        messages: Sequence["IBaseMessage"],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Optional[LLMResponse]:
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
        try:
            request_id = kwargs.get("request_id", self._generate_id())
            workflow_id = self.workflow_context.get("workflow_id")
            session_id = kwargs.get("session_id") or self.workflow_context.get("session_id", "default")
            
            # 如果有对应的请求记录，记录错误信息
            if request_id in self.pending_requests:
                request_record = self.pending_requests.pop(request_id)
                
                # 创建错误响应记录
                error_response_record = LLMResponseRecord(
                    record_id=self._generate_id(),
                    session_id=session_id,
                    workflow_id=workflow_id,
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
                    model=request_record.model,
                    metadata={
                        "error": str(error),
                        "error_type": type(error).__name__,
                        **kwargs.get("metadata", {})
                    }
                )
                
                # 异步记录错误响应
                asyncio.create_task(self.history_manager.record_llm_response(error_response_record))
            
            self._logger.error(f"LLM调用错误: {error} - Request ID: {request_id}")
            
            # 不尝试恢复错误
            return None
            
        except Exception as e:
            self._logger.error(f"记录LLM错误失败: {e}")
            return None
    
    async def _record_llm_request(self, request_record: LLMRequestRecord) -> None:
        """异步记录LLM请求"""
        try:
            await self.history_manager.record_llm_request(request_record)
        except Exception as e:
            self._logger.error(f"异步记录LLM请求失败: {e}")
    
    async def _record_response_data(
        self,
        response_record: LLMResponseRecord,
        token_record: TokenUsageRecord,
        cost_record: CostRecord
    ) -> None:
        """异步记录响应数据"""
        try:
            await self.history_manager.record_llm_response(response_record)
            await self.history_manager.record_token_usage(token_record)
            await self.history_manager.record_cost(cost_record)
        except Exception as e:
            self._logger.error(f"异步记录响应数据失败: {e}")
    
    def _extract_token_usage(self, response: LLMResponse) -> Dict[str, Any]:
        """
        从响应中提取token使用信息
        
        Args:
            response: LLM响应
            
        Returns:
            Dict[str, Any]: token使用信息
        """
        # 优先使用元数据中的token信息
        if response.metadata and 'usage' in response.metadata:
            usage = response.metadata['usage']
            if isinstance(usage, dict):
                return usage
        
        # 使用响应中的tokens_used字段
        if response.tokens_used:
            return {
                "prompt_tokens": 0,  # 无法区分prompt和completion
                "completion_tokens": response.tokens_used,
                "total_tokens": response.tokens_used
            }
        
        # 默认返回空字典
        return {}
    
    def _convert_messages(self, messages: Sequence["IBaseMessage"]) -> List[Dict[str, Any]]:
        """
        将BaseMessage转换为字典格式
        
        Args:
            messages: 消息序列
            
        Returns:
            List[Dict[str, Any]]: 转换后的消息列表
        """
        converted = []
        for msg in messages:
            try:
                message_dict = {
                    "type": msg.type,
                    "content": str(getattr(msg, 'content', '')),
                    "additional_kwargs": getattr(msg, 'additional_kwargs', {})
                }
                
                # 添加其他可能的字段
                if hasattr(msg, 'name') and msg.name:
                    message_dict["name"] = msg.name
                
                if hasattr(msg, 'id') and msg.id:
                    message_dict["id"] = msg.id
                
                converted.append(message_dict)
                
            except Exception as e:
                self._logger.warning(f"转换消息失败: {e}")
                # 添加基本的消息信息
                converted.append({
                    "type": "unknown",
                    "content": str(msg),
                    "conversion_error": str(e)
                })
        
        return converted
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
    
    def update_workflow_context(self, context: Dict[str, Any]) -> None:
        """
        更新工作流上下文
        
        Args:
            context: 新的上下文信息
        """
        self.workflow_context.update(context)
        self._logger.debug(f"更新工作流上下文: {list(context.keys())}")
    
    def set_workflow_context(self, context: Dict[str, Any]) -> None:
        """
        设置工作流上下文
        
        Args:
            context: 新的上下文信息
        """
        self.workflow_context = context.copy()
        self._logger.debug(f"设置工作流上下文: {list(context.keys())}")
    
    def get_pending_request_count(self) -> int:
        """获取待处理请求数量"""
        return len(self.pending_requests)
    
    def clear_pending_requests(self) -> int:
        """清除所有待处理请求"""
        count = len(self.pending_requests)
        self.pending_requests.clear()
        self._logger.info(f"清除了 {count} 个待处理请求")
        return count