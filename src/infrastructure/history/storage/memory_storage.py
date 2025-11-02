"""内存历史存储实现

提供基于内存的历史记录存储实现，主要用于测试和开发环境。
"""

import threading
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from src.domain.history.models import MessageRecord, ToolCallRecord
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord


class MemoryHistoryStorage:
    """内存历史存储实现
    
    将历史记录存储在内存中，主要用于测试和开发环境。
    """
    
    def __init__(self):
        self._records: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()
    
    def store_record(self, record: Union[MessageRecord, ToolCallRecord, LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord]) -> bool:
        """存储记录
        
        Args:
            record: 要存储的记录
            
        Returns:
            bool: 存储是否成功
        """
        try:
            with self._lock:
                session_id = record.session_id
                if session_id not in self._records:
                    self._records[session_id] = []
                
                # 自定义序列化函数来处理枚举类型和datetime
                def custom_serializer(obj):
                    if hasattr(obj, 'value'):  # 枚举类型
                        return obj.value
                    elif hasattr(obj, 'isoformat'):  # datetime类型
                        return obj.isoformat()
                    return str(obj)
                
                # 将记录转换为字典
                record_dict = record.__dict__.copy()
                
                # 处理特殊字段
                for key, value in record_dict.items():
                    if hasattr(value, 'value'):  # 枚举类型
                        record_dict[key] = value.value
                    elif hasattr(value, 'isoformat'):  # datetime类型
                        record_dict[key] = value.isoformat()
                
                self._records[session_id].append(record_dict)
            return True
        except Exception:
            return False
    
    def get_all_records(self, session_id: Optional[str]) -> List[Dict[str, Any]]:
        """获取会话的所有记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 记录列表
        """
        if session_id is None:
            return []
        
        with self._lock:
            return self._records.get(session_id, []).copy()
    
    def clear_session(self, session_id: str) -> bool:
        """清除会话的所有记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 清除是否成功
        """
        with self._lock:
            if session_id in self._records:
                del self._records[session_id]
                return True
            return False
    
    def get_all_sessions(self) -> List[str]:
        """获取所有会话ID
        
        Returns:
            List[str]: 会话ID列表
        """
        with self._lock:
            return list(self._records.keys())
    
    def get_session_count(self) -> int:
        """获取会话总数
        
        Returns:
            int: 会话总数
        """
        with self._lock:
            return len(self._records)
    
    def get_record_count(self, session_id: str) -> int:
        """获取会话的记录总数
        
        Args:
            session_id: 会话ID
            
        Returns:
            int: 记录总数
        """
        with self._lock:
            return len(self._records.get(session_id, []))
    
    def clear_all(self) -> bool:
        """清除所有记录
        
        Returns:
            bool: 清除是否成功
        """
        with self._lock:
            self._records.clear()
            return True