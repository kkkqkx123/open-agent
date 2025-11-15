"""回放数据源适配器"""

import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from src.domain.replay.interfaces import IReplaySource, ReplayEvent, ReplayFilter, EventType
from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import HistoryQuery, HistoryResult
from src.domain.checkpoint.interfaces import ICheckpointManager

logger = logging.getLogger(__name__)


class HistoryCheckpointReplaySource(IReplaySource):
    """基于History和Checkpoint的回放数据源适配器"""
    
    def __init__(
        self,
        history_manager: IHistoryManager,
        checkpoint_manager: ICheckpointManager
    ):
        """初始化适配器
        
        Args:
            history_manager: 历史管理器
            checkpoint_manager: 检查点管理器
        """
        self.history_manager = history_manager
        self.checkpoint_manager = checkpoint_manager
    
    async def get_events(
        self, 
        session_id: str, 
        filters: Optional[ReplayFilter] = None
    ) -> AsyncGenerator[ReplayEvent, None]:
        """获取事件流
        
        Args:
            session_id: 会话ID
            filters: 过滤器
            
        Yields:
            ReplayEvent: 事件对象
        """
        try:
            # 构建历史查询
            query = HistoryQuery(
                session_id=session_id,
                start_time=filters.start_time if filters else None,
                end_time=filters.end_time if filters else None,
                record_types=self._convert_event_types(filters.event_types) if filters else None,
                limit=filters.custom_filters.get("max_events") if filters and filters.custom_filters else None
            )
            
            # 查询历史记录
            result = self.history_manager.query_history(query)
            
            # 转换为ReplayEvent
            for record in result.records:
                event = self._convert_record_to_event(record, session_id)
                
                # 应用过滤器
                if self._should_include_event(event, filters):
                    yield event
                    
        except Exception as e:
            logger.error(f"获取事件流失败: {e}")
            raise
    
    async def get_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """获取检查点列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 检查点列表
        """
        try:
            # 假设session_id对应thread_id，实际可能需要映射
            checkpoints = await self.checkpoint_manager.list_checkpoints(session_id)
            return checkpoints
        except Exception as e:
            logger.error(f"获取检查点列表失败: {e}")
            return []
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话信息
        """
        try:
            # 从历史管理器获取基本统计信息
            token_stats = self.history_manager.get_token_statistics(session_id)
            cost_stats = self.history_manager.get_cost_statistics(session_id)
            llm_stats = self.history_manager.get_llm_statistics(session_id)
            
            # 获取检查点信息
            checkpoints = await self.get_checkpoints(session_id)
            
            return {
                "session_id": session_id,
                "token_statistics": token_stats,
                "cost_statistics": cost_stats,
                "llm_statistics": llm_stats,
                "checkpoint_count": len(checkpoints),
                "checkpoints": checkpoints[:5]  # 只返回前5个检查点
            }
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return None
    
    def _convert_event_types(self, event_types: Optional[List[EventType]]) -> Optional[List[str]]:
        """转换事件类型
        
        Args:
            event_types: 事件类型列表
            
        Returns:
            Optional[List[str]]: 转换后的记录类型列表
        """
        if not event_types:
            return None
        
        # 映射EventType到record_type
        type_mapping = {
            EventType.WORKFLOW_START: "workflow_event",
            EventType.WORKFLOW_END: "workflow_event",
            EventType.NODE_START: "workflow_event",
            EventType.NODE_END: "workflow_event",
            EventType.TOOL_CALL: "tool_call",
            EventType.TOOL_RESULT: "tool_call",
            EventType.LLM_CALL: "llm_request",
            EventType.LLM_RESPONSE: "llm_response",
            EventType.ERROR: "error",
            EventType.WARNING: "warning",
            EventType.INFO: "info",
            EventType.DEBUG: "debug",
            EventType.USER_MESSAGE: "message",
            EventType.SYSTEM_RESPONSE: "message"
        }
        
        record_types = set()
        for event_type in event_types:
            record_type = type_mapping.get(event_type)
            if record_type:
                record_types.add(record_type)
        
        return list(record_types) if record_types else None
    
    def _convert_record_to_event(self, record, session_id: str) -> ReplayEvent:
        """将历史记录转换为回放事件
        
        Args:
            record: 历史记录
            session_id: 会话ID
            
        Returns:
            ReplayEvent: 回放事件
        """
        # 根据记录类型确定事件类型
        event_type = self._map_record_type_to_event_type(record.record_type)
        
        # 构建事件数据
        event_data = {}
        if hasattr(record, 'content'):
            event_data['content'] = record.content
        if hasattr(record, 'tool_name'):
            event_data['tool_name'] = record.tool_name
        if hasattr(record, 'tool_input'):
            event_data['tool_input'] = record.tool_input
        if hasattr(record, 'tool_output'):
            event_data['tool_output'] = record.tool_output
        if hasattr(record, 'model'):
            event_data['model'] = record.model
        if hasattr(record, 'messages'):
            event_data['messages'] = record.messages
        if hasattr(record, 'response'):
            event_data['response'] = record.response
        if hasattr(record, 'token_usage'):
            event_data['token_usage'] = record.token_usage
        
        # 构建元数据
        metadata = {}
        if hasattr(record, 'metadata'):
            metadata.update(record.metadata)
        if hasattr(record, 'provider'):
            metadata['provider'] = record.provider
        if hasattr(record, 'message_type'):
            metadata['message_type'] = record.message_type.value
        
        return ReplayEvent(
            id=getattr(record, 'record_id', f"event_{id(record)}"),
            type=event_type,
            timestamp=getattr(record, 'timestamp', datetime.now()),
            data=event_data,
            metadata=metadata,
            session_id=session_id,
            thread_id=metadata.get('thread_id'),
            workflow_id=metadata.get('workflow_id')
        )
    
    def _map_record_type_to_event_type(self, record_type: str) -> EventType:
        """映射记录类型到事件类型
        
        Args:
            record_type: 记录类型
            
        Returns:
            EventType: 事件类型
        """
        mapping = {
            'message': EventType.USER_MESSAGE,
            'tool_call': EventType.TOOL_CALL,
            'llm_request': EventType.LLM_CALL,
            'llm_response': EventType.LLM_RESPONSE,
            'token_usage': EventType.INFO,
            'cost': EventType.INFO,
            'error': EventType.ERROR,
            'warning': EventType.WARNING,
            'info': EventType.INFO,
            'debug': EventType.DEBUG
        }
        
        return mapping.get(record_type, EventType.INFO)
    
    def _should_include_event(
        self, 
        event: ReplayEvent, 
        filters: Optional[ReplayFilter]
    ) -> bool:
        """判断是否应该包含事件
        
        Args:
            event: 事件对象
            filters: 过滤器
            
        Returns:
            bool: 是否应该包含
        """
        if not filters:
            return True
        
        # 检查事件类型
        if filters.event_types and event.type not in filters.event_types:
            return False
        
        # 检查时间范围
        if filters.start_time and event.timestamp < filters.start_time:
            return False
        if filters.end_time and event.timestamp > filters.end_time:
            return False
        
        # 检查线程ID
        if filters.thread_ids and event.thread_id not in filters.thread_ids:
            return False
        
        # 检查工作流ID
        if filters.workflow_ids and event.workflow_id not in filters.workflow_ids:
            return False
        
        # TODO: 实现自定义过滤器
        
        return True