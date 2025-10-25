import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from src.domain.history.models import MessageRecord, ToolCallRecord
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord


class FileHistoryStorage:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
    
    def store_record(self, record: Union[MessageRecord, ToolCallRecord, LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord]) -> bool:
        try:
            with self._lock:
                session_file = self._get_session_file(record.session_id)
                with open(session_file, 'a', encoding='utf-8') as f:
                    # 自定义序列化函数来处理枚举类型和datetime
                    def custom_serializer(obj):
                        if hasattr(obj, 'value'):  # 枚举类型
                            return obj.value
                        elif isinstance(obj, datetime):  # datetime类型
                            return obj.isoformat()
                        return str(obj)
                    
                    json.dump(record.__dict__, f, ensure_ascii=False, default=custom_serializer)
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
    
    def get_all_records(self, session_id: Optional[str]) -> List[Dict[str, Any]]:
        """
        获取会话的所有记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 记录列表
        """
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        
        records = []
        try:
            with self._lock:
                with open(session_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            record_data = json.loads(line)
                            records.append(record_data)
        except Exception:
            pass  # 如果文件损坏或不存在，返回空列表
        
        return records