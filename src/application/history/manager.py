from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult
from src.infrastructure.history.storage.file_storage import FileHistoryStorage


class HistoryManager(IHistoryManager):
    def __init__(self, storage: FileHistoryStorage):
        self.storage = storage
    
    def record_message(self, record: MessageRecord) -> None:
        self.storage.store_record(record)
    
    def record_tool_call(self, record: ToolCallRecord) -> None:
        self.storage.store_record(record)
    
    def query_history(self, query: HistoryQuery) -> HistoryResult:
        # 简单实现，后续优化
        return HistoryResult(records=[])