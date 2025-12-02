"""对话跟踪器

跟踪和管理对话历史，提供详细的token使用统计。
"""

from src.services.logger import get_logger
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import BaseMessage

from .token_types import TokenUsage
from ..utils.encoding_protocol import extract_content_as_string

logger = get_logger(__name__)


class ConversationTracker:
    """对话跟踪器
    
    跟踪对话历史，提供详细的token使用统计和分析。
    """
    
    def __init__(self, max_history: int = 1000):
        """
        初始化对话跟踪器
        
        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self._messages: List[Dict[str, Any]] = []
        self._sessions: List[Dict[str, Any]] = []
        self._current_session: Optional[Dict[str, Any]] = None
        
        # 统计信息
        self._stats: Dict[str, Any] = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "sessions_count": 0,
            "average_tokens_per_message": 0,
            "average_tokens_per_session": 0
        }
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        开始新的对话会话
        
        Args:
            session_id: 会话ID，如果不提供则自动生成
            
        Returns:
            str: 会话ID
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 结束当前会话
        if self._current_session:
            self.end_session()
        
        # 开始新会话
        self._current_session = {
            "session_id": session_id,
            "start_time": datetime.now(),
            "messages": [],
            "token_usage": TokenUsage(),
            "message_count": 0
        }
        
        logger.debug(f"开始新会话: {session_id}")
        return session_id
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """
        结束当前会话
        
        Returns:
            Optional[Dict[str, Any]]: 会话统计信息，如果没有当前会话则返回None
        """
        if not self._current_session:
            return None
        
        # 更新会话信息
        self._current_session["end_time"] = datetime.now()
        self._current_session["duration"] = (
            self._current_session["end_time"] - self._current_session["start_time"]
        ).total_seconds()
        
        # 添加到会话历史
        self._sessions.append(self._current_session)
        
        # 更新统计信息
        self._update_session_stats()
        
        session_info = self._get_session_summary(self._current_session)
        self._current_session = None
        
        if session_info:
            logger.debug(f"结束会话: {session_info['session_id']}")
        return session_info
    
    def add_message(self, message: BaseMessage, token_count: Optional[int] = None, 
                   api_usage: Optional[TokenUsage] = None) -> None:
        """
        添加消息到当前会话
        
        Args:
            message: 消息对象
            token_count: token数量（可选）
            api_usage: API使用信息（可选）
        """
        if not self._current_session:
            self.start_session()
        
        # 提取消息内容
        content = extract_content_as_string(message.content)
        
        # 创建消息记录
        message_record = {
            "timestamp": datetime.now(),
            "message_type": message.type,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "content_length": len(content),
            "token_count": token_count,
            "api_usage": api_usage
        }
        
        # 确保内容预览是字符串类型
        content_preview = message_record["content_preview"]
        if not isinstance(content_preview, str):
            content_preview = str(content_preview)
            message_record["content_preview"] = content_preview
        
        # 确保内容预览不超过103个字符（100个字符 + "..."）
        if len(content_preview) > 103:
            message_record["content_preview"] = content_preview[:100] + "..."
        # 如果内容超过100个字符，确保预览以"..."结尾
        elif len(content) > 100 and not content_preview.endswith("..."):
            message_record["content_preview"] = content[:100] + "..."
        
        # 添加到当前会话
        if self._current_session:
            self._current_session["messages"].append(message_record)
            self._current_session["message_count"] += 1
            
            # 确保当前会话存在
            if "token_usage" in self._current_session:
                # 如果提供了api_usage，使用api_usage，否则使用token_count
                if api_usage:
                    # 使用api_usage更新会话token使用
                    self._current_session["token_usage"] = self._current_session["token_usage"].add(api_usage)
                elif token_count is not None:
                    # 使用token_count更新会话token使用
                    self._current_session["token_usage"].total_tokens += token_count
                    if message.type == "human":
                        self._current_session["token_usage"].prompt_tokens += token_count
                    elif message.type == "ai":
                        self._current_session["token_usage"].completion_tokens += token_count
                # 如果两者都提供，优先使用api_usage，因为它是更准确的API返回值
        
        # 添加到全局消息历史
        self._messages.append(message_record)
        
        # 限制历史记录数量
        if len(self._messages) > self.max_history:
            self._messages.pop(0)
        
        # 更新统计信息
        self._update_message_stats()
    
    def add_messages(self, messages: List[BaseMessage], token_count: Optional[int] = None,
                    api_usage: Optional[TokenUsage] = None) -> None:
        """
        批量添加消息到当前会话
        
        Args:
            messages: 消息列表
            token_count: 总token数量（可选）
            api_usage: API使用信息（可选）
        """
        for message in messages:
            # 为单个消息分配token数量
            single_token_count = None
            if token_count and len(messages) > 0:
                # 简单平均分配
                single_token_count = token_count // len(messages)
            
            self.add_message(message, single_token_count, None)
        
        # 如果有总的API使用信息，更新最后一条消息
        if api_usage and self._current_session and self._current_session["messages"]:
            self._current_session["messages"][-1]["api_usage"] = api_usage
    
    def get_conversation_tokens(self) -> int:
        """
        获取当前对话的总token数量
        
        Returns:
            int: 总token数量
        """
        if self._current_session:
            token_usage: TokenUsage = self._current_session["token_usage"]
            return token_usage.total_tokens
        return 0
    
    def get_session_tokens(self, session_id: str) -> Optional[int]:
        """
        获取指定会话的token数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[int]: token数量，如果会话不存在则返回None
        """
        for session in self._sessions:
            if session["session_id"] == session_id:
                token_usage: TokenUsage = session["token_usage"]
                return token_usage.total_tokens
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取详细的统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        
        # 添加当前会话信息
        if self._current_session:
            duration_seconds = (datetime.now() - self._current_session["start_time"]).total_seconds()
            stats["current_session"] = {
                "session_id": self._current_session["session_id"],
                "message_count": self._current_session["message_count"],
                "token_usage": self._current_session["token_usage"].to_dict(),
                "duration_seconds": int(duration_seconds)  # 确保转换为整数
            }
        
        # 添加消息类型统计
        stats["message_types"] = self._get_message_type_stats()
        
        # 添加会话统计
        stats["session_stats"] = self._get_session_stats()
        
        return stats
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的消息
        
        Args:
            count: 消息数量
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        return self._messages[-count:] if self._messages else []
    
    def get_session_history(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID，如果不提供则返回所有会话
            
        Returns:
            List[Dict[str, Any]]: 会话历史
        """
        if session_id:
            for session in self._sessions:
                if session["session_id"] == session_id:
                    return [session]
            return []
        
        return self._sessions.copy()
    
    def clear_history(self) -> None:
        """清空所有历史记录"""
        self._messages.clear()
        self._sessions.clear()
        self._current_session = None
        self._reset_stats()
        logger.debug("已清空所有历史记录")
    
    def clear_session_history(self, session_id: Optional[str] = None) -> None:
        """
        清空指定会话的历史记录
        
        Args:
            session_id: 会话ID，如果不提供则清空当前会话
        """
        if session_id:
            # 清空指定会话
            self._sessions = [s for s in self._sessions if s["session_id"] != session_id]
            logger.debug(f"已清空会话: {session_id}")
        elif self._current_session:
            # 清空当前会话
            session_id = self._current_session["session_id"]
            # 结束当前会话，这会将其添加到历史记录中
            self.end_session()
            # 然后从历史记录中删除它
            self._sessions = [s for s in self._sessions if s["session_id"] != session_id]
            logger.debug(f"已清空当前会话: {session_id}")
        
        # 重新计算统计信息
        self._recalculate_stats()
    
    def export_conversation(self, format_type: str = "json") -> str:
        """
        导出对话历史
        
        Args:
            format_type: 导出格式 ("json", "txt", "csv")
            
        Returns:
            str: 导出的对话内容
        """
        if format_type == "json":
            import json
            return json.dumps({
                "sessions": [self._get_session_summary(s) for s in self._sessions],
                "current_session": self._get_session_summary(self._current_session) if self._current_session else None,
                "stats": self.get_stats()
            }, indent=2, default=str)
        
        elif format_type == "txt":
            lines = []
            for session in self._sessions:
                lines.append(f"=== Session: {session['session_id']} ===")
                lines.append(f"Start: {session['start_time']}")
                lines.append(f"Messages: {session['message_count']}")
                lines.append(f"Tokens: {session['token_usage'].total_tokens}")
                lines.append("")
                
                for msg in session["messages"]:
                    lines.append(f"[{msg['message_type']}] {msg['content_preview']}")
                    if msg['token_count']:
                        lines.append(f"Tokens: {msg['token_count']}")
                lines.append("")
            
            return "\n".join(lines)
        
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题
            writer.writerow(["Session ID", "Timestamp", "Message Type", "Content Preview", "Token Count"])
            
            # 写入数据
            for session in self._sessions:
                for msg in session["messages"]:
                    writer.writerow([
                        session["session_id"],
                        msg["timestamp"],
                        msg["message_type"],
                        msg["content_preview"],
                        msg["token_count"]
                    ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def _update_message_stats(self) -> None:
        """更新消息统计信息"""
        self._stats["total_messages"] = len(self._messages)
        
        if self._messages:
            total_tokens = sum(msg.get("token_count", 0) for msg in self._messages)
            self._stats["total_tokens"] = total_tokens
            # 确保平均值是整数
            self._stats["average_tokens_per_message"] = int(total_tokens / len(self._messages)) if self._messages else 0
    
    def _update_session_stats(self) -> None:
        """更新会话统计信息"""
        self._stats["sessions_count"] = len(self._sessions)
        
        if self._sessions:
            total_tokens = sum(session["token_usage"].total_tokens for session in self._sessions)
            self._stats["total_tokens"] = total_tokens
            self._stats["total_prompt_tokens"] = sum(session["token_usage"].prompt_tokens for session in self._sessions)
            self._stats["total_completion_tokens"] = sum(session["token_usage"].completion_tokens for session in self._sessions)
            # 确保平均值是整数
            self._stats["average_tokens_per_session"] = int(total_tokens / len(self._sessions)) if self._sessions else 0
    
    def _get_message_type_stats(self) -> Dict[str, int]:
        """获取消息类型统计"""
        type_stats: Dict[str, int] = {}
        for msg in self._messages:
            msg_type = msg.get("message_type", "unknown")
            type_stats[msg_type] = type_stats.get(msg_type, 0) + 1
        return type_stats
    
    def _get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        if not self._sessions:
            return {}
        
        durations = [s.get("duration", 0) for s in self._sessions]
        token_counts = [s["token_usage"].total_tokens for s in self._sessions]
        message_counts = [s["message_count"] for s in self._sessions]
        
        return {
            "total_sessions": len(self._sessions),
            "average_duration_seconds": int(sum(durations) / len(durations)) if durations else 0,
            "average_tokens_per_session": int(sum(token_counts) / len(token_counts)) if token_counts else 0,
            "average_messages_per_session": int(sum(message_counts) / len(message_counts)) if message_counts else 0,
            "max_tokens_per_session": max(token_counts) if token_counts else 0,
            "min_tokens_per_session": min(token_counts) if token_counts else 0
        }
    
    def _get_session_summary(self, session: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        if not session:
            return None
        
        return {
            "session_id": session["session_id"],
            "start_time": session["start_time"],
            "end_time": session.get("end_time"),
            "duration": session.get("duration"),
            "message_count": session["message_count"],
            "token_usage": session["token_usage"]
        }
    
    def _reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "sessions_count": 0,
            "average_tokens_per_message": 0,
            "average_tokens_per_session": 0
        }
    
    def _recalculate_stats(self) -> None:
        """重新计算统计信息"""
        self._reset_stats()
        self._update_message_stats()
        self._update_session_stats()