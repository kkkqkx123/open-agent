"""历史管理基础类

提供历史记录管理的基础实现和通用功能。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod

from .interfaces import ITokenTracker
from src.interfaces.repository.history import IHistoryRepository
from .entities import (
    BaseHistoryRecord, LLMRequestRecord, LLMResponseRecord,
    TokenUsageRecord, CostRecord, WorkflowTokenStatistics,
    RecordType, TokenSource
)
from src.interfaces.history.exceptions import (
     HistoryError, StatisticsError, RecordNotFoundError, TokenCalculationError, CostCalculationError
)
from src.interfaces.storage.exceptions import StorageError
from src.infrastructure.error_management import handle_error, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class BaseHistoryManager(ABC):
    """历史管理器基类
    
    提供历史记录管理的通用功能和默认实现。
    """
    
    def __init__(self, storage: IHistoryRepository):
        """
        初始化历史管理器
        
        Args:
            storage: 历史存储实例
        """
        self._storage = storage
        self._logger = get_logger(self.__class__.__name__)
    
    async def save_record(self, record: BaseHistoryRecord) -> bool:
        """
        保存历史记录
        
        Args:
            record: 历史记录
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            ValidationError: 记录验证失败
            StorageError: 存储操作失败
        """
        try:
            # 验证记录
            self._validate_record(record)
            
            # 保存到存储
            success = await self._storage.save_record(record)
            
            if success:
                self._logger.debug(f"成功保存历史记录: {record.record_id}")
            else:
                self._logger.error(f"保存历史记录失败: {record.record_id}")
                raise StorageError(f"保存历史记录失败: {record.record_id}")
            
            return success
            
        except Exception as e:
            if isinstance(e, (HistoryError, StorageError)):
                raise
            
            # 使用统一错误处理
            record_type = getattr(record, 'record_type', None)
            error_context = {
                "record_id": record.record_id if hasattr(record, 'record_id') else None,
                "record_type": getattr(record_type, 'value', str(record_type)) if record_type else None,
                "session_id": record.session_id if hasattr(record, 'session_id') else None,
                "operation": "save_record"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"保存历史记录时发生未知错误: {e}")
            raise HistoryError(f"保存历史记录失败: {e}") from e
    
    async def save_records(self, records: List[BaseHistoryRecord]) -> List[bool]:
        """
        批量保存历史记录
        
        Args:
            records: 历史记录列表
            
        Returns:
            List[bool]: 每条记录的保存结果
        """
        results = []
        for record in records:
            try:
                result = await self.save_record(record)
                results.append(result)
            except Exception as e:
                # 使用统一错误处理
                record_type = getattr(record, 'record_type', None)
                error_context = {
                    "record_id": record.record_id if hasattr(record, 'record_id') else None,
                    "record_type": getattr(record_type, 'value', str(record_type)) if record_type else None,
                    "operation": "save_records_batch"
                }
                handle_error(e, error_context)
                
                self._logger.error(f"批量保存中记录失败: {record.record_id}, 错误: {e}")
                results.append(False)
        
        return results
    
    async def get_record_by_id(self, record_id: str) -> Optional[BaseHistoryRecord]:
        """
        根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            Optional[BaseHistoryRecord]: 历史记录，如果不存在则返回None
        """
        try:
            record = await self._storage.get_record_by_id(record_id)
            return record
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "record_id": record_id,
                "operation": "get_record_by_id"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"获取记录失败: {record_id}, 错误: {e}")
            raise HistoryError(f"获取记录失败: {e}") from e
    
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
        try:
            records = await self._storage.get_records(
                session_id=session_id,
                workflow_id=workflow_id,
                record_type=record_type,
                model=model,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset
            )
            return records
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "session_id": session_id,
                "workflow_id": workflow_id,
                "record_type": record_type.value if record_type else None,
                "model": model,
                "limit": limit,
                "offset": offset,
                "operation": "get_records"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"获取历史记录失败: {e}")
            raise HistoryError(f"获取历史记录失败: {e}") from e
    
    def _validate_record(self, record: BaseHistoryRecord) -> None:
        """
        验证历史记录
        
        Args:
            record: 历史记录
            
        Raises:
            HistoryError: 验证失败
        """
        if not record:
            raise HistoryError("记录不能为空")
        
        if not record.record_id:
            raise HistoryError("记录ID不能为空")
        
        if not record.session_id:
            raise HistoryError("会话ID不能为空")
        
        if not isinstance(record.timestamp, datetime):
            raise HistoryError("时间戳格式无效")
        
        # 根据记录类型进行特定验证
        if isinstance(record, LLMRequestRecord):
            self._validate_llm_request_record(record)
        elif isinstance(record, LLMResponseRecord):
            self._validate_llm_response_record(record)
        elif isinstance(record, TokenUsageRecord):
            self._validate_token_usage_record(record)
        elif isinstance(record, CostRecord):
            self._validate_cost_record(record)
    
    def _validate_llm_request_record(self, record: LLMRequestRecord) -> None:
        """验证LLM请求记录"""
        if not record.model:
            raise HistoryError("模型名称不能为空")
        
        if not record.provider:
            raise HistoryError("提供商不能为空")
        
        if record.estimated_tokens < 0:
            raise HistoryError("估算Token数量不能为负数")
    
    def _validate_llm_response_record(self, record: LLMResponseRecord) -> None:
        """验证LLM响应记录"""
        if not record.request_id:
            raise HistoryError("请求ID不能为空")
        
        if record.response_time < 0:
            raise HistoryError("响应时间不能为负数")
    
    def _validate_token_usage_record(self, record: TokenUsageRecord) -> None:
        """验证Token使用记录"""
        if not record.model:
            raise HistoryError("模型名称不能为空")
        
        if not record.provider:
            raise HistoryError("提供商不能为空")
        
        if any(tokens < 0 for tokens in [
            record.prompt_tokens, record.completion_tokens, record.total_tokens
        ]):
            raise HistoryError("Token数量不能为负数")
        
        if not 0.0 <= record.confidence <= 1.0:
            raise HistoryError("置信度必须在0.0到1.0之间")
    
    def _validate_cost_record(self, record: CostRecord) -> None:
        """验证成本记录"""
        if not record.model:
            raise HistoryError("模型名称不能为空")
        
        if not record.provider:
            raise HistoryError("提供商不能为空")
        
        if any(cost < 0 for cost in [
            record.prompt_cost, record.completion_cost, record.total_cost
        ]):
            raise HistoryError("成本不能为负数")
        
        if any(tokens < 0 for tokens in [
            record.prompt_tokens, record.completion_tokens, record.total_tokens
        ]):
            raise HistoryError("Token数量不能为负数")


class BaseTokenTracker(ITokenTracker):
    """Token追踪器基类
    
    提供Token追踪的通用功能和默认实现。
    """
    
    def __init__(self, storage: IHistoryRepository):
        """
        初始化Token追踪器
        
        Args:
            storage: 历史存储实例
        """
        self._storage = storage
        self._logger = get_logger(self.__class__.__name__)
        self._pending_requests: Dict[str, LLMRequestRecord] = {}
    
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
        try:
            # 创建Token使用记录
            token_record = TokenUsageRecord(
                record_id=self._generate_id(),
                session_id=metadata.get("session_id", "default") if metadata else "default",
                workflow_id=workflow_id,
                timestamp=datetime.now(),
                model=model,
                provider=provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                source=source,
                confidence=confidence,
                metadata=metadata or {}
            )
            
            # 保存记录
            await self._storage.save_record(token_record)
            
            # 更新工作流统计
            await self._update_workflow_statistics(workflow_id, model, token_record)
            
            self._logger.debug(f"成功追踪Token使用: 工作流={workflow_id}, 模型={model}, "
                             f"Token={token_record.total_tokens}")
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "workflow_id": workflow_id,
                "model": model,
                "provider": provider,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "operation": "track_workflow_token_usage"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"追踪Token使用失败: {e}")
            raise StatisticsError(f"追踪Token使用失败: {e}", workflow_id=workflow_id) from e
    
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
        try:
            # 创建请求记录
            request_record = LLMRequestRecord(
                record_id=self._generate_id(),
                session_id=session_id,
                workflow_id=workflow_id,
                timestamp=datetime.now(),
                model=model,
                provider=provider,
                messages=messages,
                parameters=parameters,
                estimated_tokens=estimated_tokens,
                metadata=metadata or {}
            )
            
            # 保存到待处理请求
            self._pending_requests[request_record.record_id] = request_record
            
            # 保存到存储
            await self._storage.save_record(request_record)
            
            self._logger.debug(f"成功追踪LLM请求: {request_record.record_id}")
            
            return request_record.record_id
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "workflow_id": workflow_id,
                "session_id": session_id,
                "model": model,
                "provider": provider,
                "estimated_tokens": estimated_tokens,
                "operation": "track_llm_request"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"追踪LLM请求失败: {e}")
            raise StatisticsError(f"追踪LLM请求失败: {e}") from e
    
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
        try:
            # 获取对应的请求记录
            if request_id not in self._pending_requests:
                raise RecordNotFoundError(f"未找到请求记录: {request_id}")
            
            request_record = self._pending_requests.pop(request_id)
            
            # 创建响应记录
            response_record = LLMResponseRecord(
                record_id=self._generate_id(),
                session_id=request_record.session_id,
                workflow_id=request_record.workflow_id,
                timestamp=datetime.now(),
                request_id=request_id,
                content=content,
                finish_reason=finish_reason,
                token_usage=token_usage,
                response_time=response_time,
                model=request_record.model,
                metadata=metadata or {}
            )
            
            # 保存响应记录
            await self._storage.save_record(response_record)
            
            # 创建Token使用记录
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
                source=TokenSource.API,
                confidence=1.0,
                metadata={
                    "request_id": request_id,
                    **(metadata or {})
                }
            )
            
            # 保存Token使用记录
            await self._storage.save_record(token_record)
            
            # 更新工作流统计
            if request_record.workflow_id:
                await self._update_workflow_statistics(
                    request_record.workflow_id, 
                    request_record.model, 
                    token_record
                )
            
            self._logger.debug(f"成功追踪LLM响应: {request_id}")
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "request_id": request_id,
                "response_time": response_time,
                "operation": "track_llm_response"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"追踪LLM响应失败: {e}")
            raise StatisticsError(f"追踪LLM响应失败: {e}") from e
    
    async def _update_workflow_statistics(
        self,
        workflow_id: str,
        model: str,
        token_record: TokenUsageRecord
    ) -> None:
        """
        更新工作流统计信息
        
        Args:
            workflow_id: 工作流ID
            model: 模型名称
            token_record: Token使用记录
        """
        try:
            # 获取现有统计
            stats_list = await self._storage.get_workflow_token_stats(
                workflow_id, model
            )
            
            if stats_list:
                stats = stats_list[0]
                # 更新现有统计
                stats.update_from_record(token_record)
            else:
                # 创建新统计
                stats = WorkflowTokenStatistics(
                    workflow_id=workflow_id,
                    model=model
                )
                stats.update_from_record(token_record)
            
            # 保存更新后的统计
            await self._storage.update_workflow_token_stats(stats)
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "workflow_id": workflow_id,
                "model": model,
                "operation": "update_workflow_statistics"
            }
            handle_error(e, error_context)
            
            self._logger.error(f"更新工作流统计失败: {e}")
            # 不抛出异常，避免影响主要功能
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())