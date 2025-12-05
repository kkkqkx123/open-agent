"""历史管理器实现

提供统一的历史记录管理服务。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.interfaces.history import IHistoryManager, DeleteResult
from src.core.history.entities import (
    BaseHistoryRecord, LLMRequestRecord, LLMResponseRecord,
    TokenUsageRecord, CostRecord, WorkflowTokenStatistics,
    MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult,
    RecordType
)
from src.interfaces.repository.history import IHistoryRepository
from src.interfaces.logger import ILogger
from src.core.history.base import BaseHistoryManager
from src.interfaces.history.exceptions import HistoryError
from src.interfaces.storage.exceptions import StorageError


class HistoryManager(BaseHistoryManager, IHistoryManager):
    """历史管理器实现
    
    继承BaseHistoryManager并实现IHistoryManager接口，
    提供完整的历史记录管理功能。
    """
    
    def __init__(
        self,
        storage: IHistoryRepository,
        enable_async_batching: bool = True,
        batch_size: int = 10,
        batch_timeout: float = 1.0,
        logger: Optional[ILogger] = None
    ):
        """
        初始化历史管理器
        
        Args:
            storage: 历史存储实例
            enable_async_batching: 是否启用异步批处理
            batch_size: 批处理大小
            batch_timeout: 批处理超时时间（秒）
            logger: 日志记录器
        """
        super().__init__(storage)
        self.enable_async_batching = enable_async_batching
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        # 批处理相关
        self._batch_queue: List[BaseHistoryRecord] = []
        self._last_batch_time = datetime.now()
        
        self._logger = logger
        if self._logger:
            self._logger.info(f"历史管理器初始化完成，批处理: {enable_async_batching}")
    
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        try:
            await self.save_record(record)
            if self._logger:
                self._logger.debug(f"记录消息: {record.record_id}")
        except Exception as e:
            if self._logger:
                self._logger.error(f"记录消息失败: {e}")
            raise HistoryError(f"记录消息失败: {e}")
    
    async def record_tool_call(self, record: 'ToolCallRecord') -> None:
        """记录工具调用"""
        try:
            await self.save_record(record)
            if self._logger:
                self._logger.debug(f"记录工具调用: {record.record_id}")
        except Exception as e:
            if self._logger:
                self._logger.error(f"记录工具调用失败: {e}")
            raise HistoryError(f"记录工具调用失败: {e}")
    
    async def record_llm_request(self, record: LLMRequestRecord) -> None:
        """记录LLM请求"""
        try:
            if self.enable_async_batching:
                await self._add_to_batch(record)
            else:
                await self.save_record(record)
            
            if self._logger:
                self._logger.debug(f"记录LLM请求: {record.record_id}")
        except Exception as e:
            if self._logger:
                self._logger.error(f"记录LLM请求失败: {e}")
            raise HistoryError(f"记录LLM请求失败: {e}")
    
    async def record_llm_response(self, record: LLMResponseRecord) -> None:
        """记录LLM响应"""
        try:
            if self.enable_async_batching:
                await self._add_to_batch(record)
            else:
                await self.save_record(record)
            
            if self._logger:
                self._logger.debug(f"记录LLM响应: {record.record_id}")
        except Exception as e:
            if self._logger:
                self._logger.error(f"记录LLM响应失败: {e}")
            raise HistoryError(f"记录LLM响应失败: {e}")
    
    async def record_token_usage(self, record: TokenUsageRecord) -> None:
        """记录Token使用"""
        try:
            if self.enable_async_batching:
                await self._add_to_batch(record)
            else:
                await self.save_record(record)
            
            if self._logger:
                self._logger.debug(f"记录Token使用: {record.record_id}")
        except Exception as e:
            if self._logger:
                self._logger.error(f"记录Token使用失败: {e}")
            raise HistoryError(f"记录Token使用失败: {e}")
    
    async def record_cost(self, record: CostRecord) -> None:
        """记录成本"""
        try:
            if self.enable_async_batching:
                await self._add_to_batch(record)
            else:
                await self.save_record(record)
            
            if self._logger:
                self._logger.debug(f"记录成本: {record.record_id}")
        except Exception as e:
            if self._logger:
                self._logger.error(f"记录成本失败: {e}")
            raise HistoryError(f"记录成本失败: {e}")
    
    async def query_history(self, query: 'HistoryQuery') -> 'HistoryResult':
        """查询历史记录"""
        try:
            # 转换查询参数
            records = await self.get_records(
                session_id=query.session_id,
                workflow_id=query.workflow_id,
                record_type=query.record_type,
                model=getattr(query, 'model', None),
                start_time=query.start_time,
                end_time=query.end_time,
                limit=query.limit,
                offset=query.offset
            )
            
            # 创建结果对象
            result = HistoryResult(records=records, total_count=len(records))
            
            if self._logger:
                self._logger.debug(f"查询历史记录: 返回 {len(records)} 条记录")
            
            return result
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"查询历史记录失败: {e}")
            raise HistoryError(f"查询历史记录失败: {e}")
    
    async def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token统计"""
        try:
            # 获取Token使用记录
            token_records = await self.get_records(
                session_id=session_id,
                record_type=RecordType.TOKEN_USAGE,
                limit=10000
            )
            
            if not token_records:
                return {
                    "session_id": session_id,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_requests": 0,
                    "model_breakdown": {}
                }
            
            # 统计Token使用
            total_tokens = 0
            prompt_tokens = 0
            completion_tokens = 0
            model_breakdown: Dict[str, Dict[str, Any]] = {}
            
            for record in token_records:
                if not isinstance(record, TokenUsageRecord):
                    continue
                
                total_tokens += record.total_tokens
                prompt_tokens += record.prompt_tokens
                completion_tokens += record.completion_tokens
                
                # 按模型分组
                if record.model not in model_breakdown:
                    model_breakdown[record.model] = {
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "request_count": 0
                    }
                
                model_breakdown[record.model]["total_tokens"] += record.total_tokens
                model_breakdown[record.model]["prompt_tokens"] += record.prompt_tokens
                model_breakdown[record.model]["completion_tokens"] += record.completion_tokens
                model_breakdown[record.model]["request_count"] += 1
            
            statistics = {
                "session_id": session_id,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_requests": len(token_records),
                "model_breakdown": model_breakdown,
                "avg_tokens_per_request": total_tokens / len(token_records) if token_records else 0
            }
            
            if self._logger:
                self._logger.debug(f"获取Token统计: 会话={session_id}, 总Token={total_tokens}")
            
            return statistics
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取Token统计失败: {e}")
            raise HistoryError(f"获取Token统计失败: {e}")
    
    async def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        try:
            # 获取成本记录
            cost_records = await self.get_records(
                session_id=session_id,
                record_type=RecordType.COST,
                limit=10000
            )
            
            if not cost_records:
                return {
                    "session_id": session_id,
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "model_breakdown": {},
                    "currency": "USD"
                }
            
            # 统计成本
            total_cost = 0.0
            model_breakdown: Dict[str, Dict[str, Any]] = {}
            currency = "USD"
            
            for record in cost_records:
                if not isinstance(record, CostRecord):
                    continue
                
                total_cost += record.total_cost
                currency = record.currency
                
                # 按模型分组
                if record.model not in model_breakdown:
                    model_breakdown[record.model] = {
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "request_count": 0,
                        "avg_cost_per_request": 0.0,
                        "avg_cost_per_token": 0.0
                    }
                
                model_breakdown[record.model]["total_cost"] += record.total_cost
                model_breakdown[record.model]["total_tokens"] += record.total_tokens
                model_breakdown[record.model]["request_count"] += 1
                model_breakdown[record.model]["avg_cost_per_request"] = (
                    model_breakdown[record.model]["total_cost"] / 
                    model_breakdown[record.model]["request_count"]
                )
                model_breakdown[record.model]["avg_cost_per_token"] = (
                    model_breakdown[record.model]["total_cost"] / 
                    model_breakdown[record.model]["total_tokens"]
                    if model_breakdown[record.model]["total_tokens"] > 0 else 0.0
                )
            
            statistics = {
                "session_id": session_id,
                "total_cost": total_cost,
                "total_requests": len(cost_records),
                "model_breakdown": model_breakdown,
                "currency": currency,
                "avg_cost_per_request": total_cost / len(cost_records) if cost_records else 0.0
            }
            
            if self._logger:
                self._logger.debug(f"获取成本统计: 会话={session_id}, 总成本={total_cost:.6f}")
            
            return statistics
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取成本统计失败: {e}")
            raise HistoryError(f"获取成本统计失败: {e}")
    
    async def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM统计"""
        try:
            # 获取LLM请求和响应记录
            request_records = await self.get_records(
                session_id=session_id,
                record_type=RecordType.LLM_REQUEST,
                limit=10000
            )
            
            response_records = await self.get_records(
                session_id=session_id,
                record_type=RecordType.LLM_RESPONSE,
                limit=10000
            )
            
            # 统计LLM调用
            model_stats: Dict[str, Dict[str, Any]] = {}
            total_response_time = 0.0
            finish_reason_counts: Dict[str, int] = {}
            
            for record in response_records:
                if not isinstance(record, LLMResponseRecord):
                    continue
                
                total_response_time += record.response_time
                
                # 按模型分组
                if record.model not in model_stats:
                    model_stats[record.model] = {
                        "request_count": 0,
                        "response_count": 0,
                        "total_response_time": 0.0,
                        "avg_response_time": 0.0,
                        "finish_reasons": {}
                    }
                
                model_stats[record.model]["response_count"] += 1
                model_stats[record.model]["total_response_time"] += record.response_time
                model_stats[record.model]["avg_response_time"] = (
                    model_stats[record.model]["total_response_time"] / 
                    model_stats[record.model]["response_count"]
                )
                
                # 统计完成原因
                finish_reason = record.finish_reason or "unknown"
                if finish_reason not in finish_reason_counts:
                    finish_reason_counts[finish_reason] = 0
                finish_reason_counts[finish_reason] += 1
                
                if finish_reason not in model_stats[record.model]["finish_reasons"]:
                    model_stats[record.model]["finish_reasons"][finish_reason] = 0
                model_stats[record.model]["finish_reasons"][finish_reason] += 1
            
            # 统计请求数量
            for record in request_records:
                if not isinstance(record, LLMRequestRecord):
                    continue
                
                if record.model in model_stats:
                    model_stats[record.model]["request_count"] += 1
                else:
                    model_stats[record.model] = {
                        "request_count": 1,
                        "response_count": 0,
                        "total_response_time": 0.0,
                        "avg_response_time": 0.0,
                        "finish_reasons": {}
                    }
            
            statistics = {
                "session_id": session_id,
                "total_requests": len(request_records),
                "total_responses": len(response_records),
                "avg_response_time": total_response_time / len(response_records) if response_records else 0.0,
                "model_breakdown": model_stats,
                "finish_reason_distribution": finish_reason_counts
            }
            
            if self._logger:
                self._logger.debug(f"获取LLM统计: 会话={session_id}, 请求数={len(request_records)}")
            
            return statistics
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取LLM统计失败: {e}")
            raise HistoryError(f"获取LLM统计失败: {e}")
    
    async def _add_to_batch(self, record: BaseHistoryRecord) -> None:
        """添加记录到批处理队列"""
        self._batch_queue.append(record)
        
        # 检查是否需要处理批次
        await self._process_batch_if_needed()
    
    async def _process_batch_if_needed(self) -> None:
        """根据需要处理批次"""
        now = datetime.now()
        time_since_last_batch = (now - self._last_batch_time).total_seconds()
        
        should_process = (
            len(self._batch_queue) >= self.batch_size or
            time_since_last_batch >= self.batch_timeout
        )
        
        if should_process and self._batch_queue:
            await self._process_batch()
    
    async def _process_batch(self) -> None:
        """处理批次"""
        if not self._batch_queue:
            return
        
        batch = self._batch_queue.copy()
        self._batch_queue.clear()
        self._last_batch_time = datetime.now()
        
        try:
            # 批量保存
            results = await self.save_records(batch)
            success_count = sum(results)
            
            if success_count == len(batch):
                if self._logger:
                    self._logger.debug(f"批处理成功: {success_count}/{len(batch)} 条记录")
            else:
                if self._logger:
                    self._logger.warning(f"批处理部分失败: {success_count}/{len(batch)} 条记录")
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"批处理失败: {e}")
            # 重新加入队列进行重试
            self._batch_queue.extend(batch)
    
    async def flush_batch(self) -> None:
        """强制处理当前批次"""
        if self._batch_queue:
            await self._process_batch()
            if self._logger:
                self._logger.info("强制处理批次完成")
    
    def get_batch_status(self) -> Dict[str, Any]:
        """获取批处理状态"""
        return {
            "enabled": self.enable_async_batching,
            "queue_size": len(self._batch_queue),
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "last_batch_time": self._last_batch_time.isoformat(),
            "time_since_last_batch": (datetime.now() - self._last_batch_time).total_seconds()
        }
    
    async def cleanup_old_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional[datetime] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """清理旧记录"""
        try:
            if dry_run:
                # 只统计不删除
                records = await self.get_records(
                    session_id=session_id,
                    workflow_id=workflow_id,
                    end_time=older_than,
                    limit=100000  # 获取大量记录进行统计
                )
                
                return {
                    "dry_run": True,
                    "records_to_delete": len(records),
                    "session_id": session_id,
                    "workflow_id": workflow_id,
                    "older_than": older_than.isoformat() if older_than else None
                }
            else:
                # 实际删除
                deleted_count = await self._storage.delete_records(
                    session_id=session_id,
                    workflow_id=workflow_id,
                    older_than=older_than
                )
                
                if self._logger:
                    self._logger.info(f"清理旧记录完成: 删除了 {deleted_count} 条记录")
                
                return {
                    "dry_run": False,
                    "deleted_count": deleted_count,
                    "session_id": session_id,
                    "workflow_id": workflow_id,
                    "older_than": older_than.isoformat() if older_than else None
                }
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"清理旧记录失败: {e}")
            raise HistoryError(f"清理旧记录失败: {e}")
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        try:
            storage_stats = await self._storage.get_storage_statistics()
            
            return {
                "storage_statistics": storage_stats,
                "batch_status": self.get_batch_status(),
                "manager_info": {
                    "enable_async_batching": self.enable_async_batching,
                    "batch_size": self.batch_size,
                    "batch_timeout": self.batch_timeout
                }
            }
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"获取存储信息失败: {e}")
            raise HistoryError(f"获取存储信息失败: {e}")
    
    async def query_history_by_thread(
        self,
        thread_id: str,
        limit: int = 10,
        offset: int = 0,
        record_type: Optional['RecordType'] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        model: Optional[str] = None
    ) -> 'HistoryResult':
        """按thread_id查询历史记录"""
        try:
            # 通过thread_id查询历史记录
            # 假设历史记录中包含thread_id字段，或者通过session_id关联
            records = await self.get_records(
                session_id=None,  # 不按session_id过滤
                workflow_id=None,  # 不按workflow_id过滤
                record_type=record_type,
                model=model,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset
            )
            
            # 过滤包含thread_id的记录
            # 这里假设记录的metadata中包含thread_id信息
            filtered_records = []
            for record in records:
                if hasattr(record, 'metadata') and record.metadata:
                    if record.metadata.get('thread_id') == thread_id:
                        filtered_records.append(record)
            
            # 创建结果对象
            result = HistoryResult(
                records=filtered_records,
                total_count=len(filtered_records),
                limit=limit,
                offset=offset
            )
            
            if self._logger:
                self._logger.debug(f"按thread_id查询历史记录: {thread_id}, 返回 {len(filtered_records)} 条记录")
            
            return result
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"按thread_id查询历史记录失败: {e}")
            raise HistoryError(f"按thread_id查询历史记录失败: {e}")
    
    async def delete_history(
        self,
        query: 'HistoryQuery'
    ) -> 'DeleteResult':
        """删除历史记录"""
        try:
            # 通过存储接口删除记录
            deleted_count = await self._storage.delete_records_by_query(query)
            
            result = DeleteResult(
                deleted_count=deleted_count,
                success=True
            )
            
            if self._logger:
                self._logger.debug(f"删除历史记录: {deleted_count} 条记录")
            return result
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"删除历史记录失败: {e}")
            raise HistoryError(f"删除历史记录失败: {e}")