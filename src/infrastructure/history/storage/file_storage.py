import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.history.models import MessageRecord, ToolCallRecord


class FileHistoryStorage:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
    
    def store_record(self, record: MessageRecord) -> bool:
        try:
            with self._lock:
                session_file = self._get_session_file(record.session_id)
                with open(session_file, 'a', encoding='utf-8') as f:
                    json.dump(record.__dict__, f, ensure_ascii=False, default=str)
                    f.write('\n')
            return True
        except Exception:
            return False
    
    def _get_session_file(self, session_id: str) -> Path:
        date_prefix = datetime.now().strftime("%Y%m")
        session_dir = self.base_path / "sessions" / date_prefix
        session_dir.mkdir(exist_ok=True)
        return session_dir / f"{session_id}.jsonl"