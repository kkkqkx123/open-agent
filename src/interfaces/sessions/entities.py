"""会话相关实体定义"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class UserRequest:
    """用户请求数据模型"""
    request_id: str
    user_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class UserInteraction:
    """用户交互数据模型"""
    interaction_id: str
    session_id: str
    thread_id: Optional[str]
    interaction_type: str  # "user_input", "system_response", "error", etc.
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: Optional[str]
    thread_ids: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]