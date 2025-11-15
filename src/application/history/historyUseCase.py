"""历史管理服务集成模块

提供历史管理服务的纯业务逻辑功能，不依赖表现层。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, MessageType, ToolCallRecord, HistoryQuery, HistoryResult
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
from infrastructure.history.session_context import session_context


class HistoryUseCase:
    """历史管理服务集成类
    
    提供历史管理服务的纯业务逻辑功能，不依赖表现层。
    """
    
    def __init__(self, history_manager: IHistoryManager):
        self.history_manager = history_manager
    
    def record_session_start(self, session_id: str, workflow_config: str, agent_config: Optional[str] = None) -> None:
        """记录会话开始
        
        Args:
            session_id: 会话ID
            workflow_config: 工作流配置
            agent_config: 代理配置
        """
        with session_context(session_id):
            # 记录系统消息
            system_message = MessageRecord(
                record_id=self._generate_id(),
                session_id=session_id,
                timestamp=datetime.now(),
                message_type=MessageType.SYSTEM,
                content=f"会话开始 - 工作流: {workflow_config}" + (f", 代理: {agent_config}" if agent_config else ""),
                metadata={
                    "workflow_config": workflow_config,
                    "agent_config": agent_config,
                    "event_type": "session_start"
                }
            )
            self.history_manager.record_message(system_message)
    
    def record_session_end(self, session_id: str, reason: str = "normal") -> None:
        """记录会话结束
        
        Args:
            session_id: 会话ID
            reason: 结束原因
        """
        with session_context(session_id):
            # 记录系统消息
            system_message = MessageRecord(
                record_id=self._generate_id(),
                session_id=session_id,
                timestamp=datetime.now(),
                message_type=MessageType.SYSTEM,
                content=f"会话结束 - 原因: {reason}",
                metadata={
                    "reason": reason,
                    "event_type": "session_end"
                }
            )
            self.history_manager.record_message(system_message)
    
    def record_error(self, session_id: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """记录错误
        
        Args:
            session_id: 会话ID
            error: 错误对象
            context: 错误上下文
        """
        with session_context(session_id):
            # 记录系统消息
            system_message = MessageRecord(
                record_id=self._generate_id(),
                session_id=session_id,
                timestamp=datetime.now(),
                message_type=MessageType.SYSTEM,
                content=f"错误: {str(error)}",
                metadata={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "context": context or {},
                    "event_type": "error"
                }
            )
            self.history_manager.record_message(system_message)
    
    def record_message(self, session_id: str, message_type: MessageType, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录消息
        
        Args:
            session_id: 会话ID
            message_type: 消息类型
            content: 消息内容
            metadata: 元数据
        """
        with session_context(session_id):
            message = MessageRecord(
                record_id=self._generate_id(),
                session_id=session_id,
                timestamp=datetime.now(),
                message_type=message_type,
                content=content,
                metadata=metadata or {}
            )
            self.history_manager.record_message(message)
    
    def record_tool_call(self, session_id: str, tool_name: str, tool_input: Dict[str, Any], tool_output: Optional[Dict[str, Any]] = None) -> None:
        """记录工具调用
        
        Args:
            session_id: 会话ID
            tool_name: 工具名称
            tool_input: 工具输入
            tool_output: 工具输出
        """
        with session_context(session_id):
            tool_call = ToolCallRecord(
                record_id=self._generate_id(),
                session_id=session_id,
                timestamp=datetime.now(),
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output
            )
            self.history_manager.record_tool_call(tool_call)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话摘要
        """
        # 查询会话的所有记录
        query = HistoryQuery(session_id=session_id)
        result = self.history_manager.query_history(query)
        
        # 统计各类记录数量
        message_count = 0
        tool_call_count = 0
        llm_request_count = 0
        llm_response_count = 0
        token_usage_count = 0
        cost_count = 0
        
        user_message_count = 0
        assistant_message_count = 0
        system_message_count = 0
        
        for record in result.records:
            record_type = getattr(record, 'record_type', '')
            
            if record_type == 'message':
                message_count += 1
                message_type = getattr(record, 'message_type', None)
                if message_type == MessageType.USER:
                    user_message_count += 1
                elif message_type == MessageType.ASSISTANT:
                    assistant_message_count += 1
                elif message_type == MessageType.SYSTEM:
                    system_message_count += 1
            elif record_type == 'tool_call':
                tool_call_count += 1
            elif record_type == 'llm_request':
                llm_request_count += 1
            elif record_type == 'llm_response':
                llm_response_count += 1
            elif record_type == 'token_usage':
                token_usage_count += 1
            elif record_type == 'cost':
                cost_count += 1
        
        # 获取Token和成本统计
        token_stats = self.history_manager.get_token_statistics(session_id)
        cost_stats = self.history_manager.get_cost_statistics(session_id)
        llm_stats = self.history_manager.get_llm_statistics(session_id)
        
        # 获取时间范围
        timestamps = [getattr(record, 'timestamp') for record in result.records if hasattr(record, 'timestamp') and getattr(record, 'timestamp') is not None]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None
        
        return {
            "session_id": session_id,
            "total_records": result.total,
            "message_count": message_count,
            "user_message_count": user_message_count,
            "assistant_message_count": assistant_message_count,
            "system_message_count": system_message_count,
            "tool_call_count": tool_call_count,
            "llm_request_count": llm_request_count,
            "llm_response_count": llm_response_count,
            "token_usage_count": token_usage_count,
            "cost_count": cost_count,
            "token_statistics": token_stats,
            "cost_statistics": cost_stats,
            "llm_statistics": llm_stats,
            "start_time": start_time,
            "end_time": end_time,
            "duration": (end_time - start_time).total_seconds() if start_time and end_time else None
        }
    
    def export_session_data(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """导出会话数据
        
        Args:
            session_id: 会话ID
            format: 导出格式 ("json", "csv", "txt")
            
        Returns:
            Dict[str, Any]: 导出的数据
        """
        # 获取会话摘要
        summary = self.get_session_summary(session_id)
        
        # 获取所有记录
        query = HistoryQuery(session_id=session_id)
        result = self.history_manager.query_history(query)
        
        # 转换记录为可序列化格式
        records_data = []
        for record in result.records:
            record_dict = record.__dict__.copy()
            
            # 处理特殊字段
            for key, value in record_dict.items():
                if hasattr(value, 'value'):  # 枚举类型
                    record_dict[key] = value.value
                elif hasattr(value, 'isoformat'):  # datetime类型
                    record_dict[key] = value.isoformat()
            
            records_data.append(record_dict)
        
        return {
            "summary": summary,
            "records": records_data,
            "export_format": format,
            "exported_at": datetime.now().isoformat()
        }
    
    def _generate_id(self) -> str:
        """生成唯一ID
        
        Returns:
            str: 唯一ID
        """
        import uuid
        return str(uuid.uuid4())