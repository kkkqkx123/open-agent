from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class IHistoryManager(ABC):
    @abstractmethod
    def record_message(self, record: 'MessageRecord') -> None: pass
    
    @abstractmethod
    def record_tool_call(self, record: 'ToolCallRecord') -> None: pass
    
    @abstractmethod
    def query_history(self, query: 'HistoryQuery') -> 'HistoryResult': pass