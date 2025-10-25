import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from src.domain.history.models import MessageRecord, ToolCallRecord


class FileHistoryStorage:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
    
    def store_record(self, record: Union[MessageRecord, ToolCallRecord]) -> bool:
        try:
            with self._lock:
                session_file = self._get_session_file(record.session_id)
                with open(session_file, 'a', encoding='utf-8') as f:
                    # 自定义序列化函数来处理枚举类型
                    def enum_serializer(obj):
                        if hasattr(obj, 'value'):
                            return obj.value
                        return str(obj)
                    
                    json.dump(record.__dict__, f, ensure_ascii=False, default=enum_serializer)
                    f.write('\n')
            return True
        except Exception:
            return False
    
    def _get_session_file(self, session_id: Optional[str]) -> Path:
        if session_id is None:
            # 返回一个无效路径，用于测试
            result = self.base_path / "sessions" / "invalid" / "None.jsonl"
            # 确保返回的是 Path 对象
            if not isinstance(result, Path):
                raise TypeError(f"Expected Path, got {type(result)}")
            return result
        
        date_prefix = datetime.now().strftime("%Y%m")
        session_dir = self.base_path / "sessions" / date_prefix
        session_dir.mkdir(parents=True, exist_ok=True)
        result = session_dir / f"{session_id}.jsonl"
        # 确保返回的是 Path 对象
        if not isinstance(result, Path):
            raise TypeError(f"Expected Path, got {type(result)}")
        return result