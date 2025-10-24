from src.domain.history.models import MessageRecord, MessageType, ToolCallRecord
from src.domain.history.interfaces import IHistoryManager
from src.presentation.tui.state_manager import StateManager
import uuid
from datetime import datetime
from typing import Optional


class TUIHistoryAdapter:
    def __init__(self, history_manager: IHistoryManager, state_manager: StateManager):
        self.history_manager = history_manager
        self.state_manager = state_manager
    
    def on_user_message(self, content: str) -> None:
        if not self.state_manager.session_id:
            return
        
        record = MessageRecord(
            record_id=str(uuid.uuid4()),
            session_id=self.state_manager.session_id,
            timestamp=datetime.now(),
            message_type=MessageType.USER,
            content=content
        )
        self.history_manager.record_message(record)
    
    def on_assistant_message(self, content: str) -> None:
        if not self.state_manager.session_id:
            return
        
        record = MessageRecord(
            record_id=str(uuid.uuid4()),
            session_id=self.state_manager.session_id,
            timestamp=datetime.now(),
            message_type=MessageType.ASSISTANT,
            content=content
        )
        self.history_manager.record_message(record)
    
    def on_tool_call(self, tool_name: str, tool_input: dict, tool_output: Optional[dict] = None) -> None:
        if not self.state_manager.session_id:
            return
        
        record = ToolCallRecord(
            record_id=str(uuid.uuid4()),
            session_id=self.state_manager.session_id,
            timestamp=datetime.now(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output
        )
        self.history_manager.record_tool_call(record)