"""历史数据访问对象"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class HistoryDAO:
    """历史数据访问对象"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_session_file(self, session_id: str) -> Path:
        """获取会话历史文件路径"""
        date_prefix = datetime.now().strftime("%Y%m")
        session_dir = self.base_path / "history" / date_prefix
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"{session_id}.jsonl"
    
    def store_record(self, session_id: str, record_data: Dict[str, Any]) -> bool:
        """存储历史记录"""
        try:
            session_file = self._get_session_file(session_id)
            with open(session_file, 'a', encoding='utf-8') as f:
                json.dump(record_data, f, ensure_ascii=False)
                f.write('\n')
            return True
        except Exception:
            return False
    
    def get_session_records(
        self, 
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        record_types: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取会话历史记录"""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        
        records = []
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        try:
                            record = json.loads(line)
                            
                            # 应用过滤条件
                            if start_time or end_time:
                                record_time = datetime.fromisoformat(record.get('timestamp', ''))
                                if start_time and record_time < start_time:
                                    continue
                                if end_time and record_time > end_time:
                                    continue
                            
                            if record_types and record.get('record_type') not in record_types:
                                continue
                            
                            # 应用分页
                            if len(records) >= offset + limit:
                                break
                                
                            if len(records) >= offset:
                                records.append(record)
                                
                        except json.JSONDecodeError:
                            continue
                            
        except Exception:
            pass
        
        return records[offset:offset + limit]
    
    def search_session_records(
        self,
        session_id: str,
        query: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索会话历史记录"""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        
        results = []
        query_lower = query.lower()
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            
                            # 搜索内容
                            content = ""
                            if record.get('record_type') == 'message':
                                content = record.get('content', '')
                            elif record.get('record_type') == 'tool_call':
                                content = str(record.get('tool_input', '')) + str(record.get('tool_output', ''))
                            
                            if query_lower in content.lower():
                                results.append(record)
                                if len(results) >= limit:
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except Exception:
            pass
        
        return results
    
    def export_session_data(
        self,
        session_id: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """导出会话数据"""
        records = self.get_session_records(session_id, limit=10000)  # 获取所有记录
        
        if format == 'json':
            return {
                "session_id": session_id,
                "export_time": datetime.now().isoformat(),
                "total_records": len(records),
                "records": records
            }
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if records:
                # 获取所有可能的字段
                all_fields = set()
                for record in records:
                    all_fields.update(record.keys())
                
                writer = csv.DictWriter(output, fieldnames=sorted(all_fields))
                writer.writeheader()
                
                for record in records:
                    writer.writerow(record)
            
            return {
                "session_id": session_id,
                "format": "csv",
                "content": output.getvalue()
            }
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息"""
        records = self.get_session_records(session_id, limit=10000)
        
        # 计算统计信息
        message_count = len([r for r in records if r.get('record_type') == 'message'])
        tool_call_count = len([r for r in records if r.get('record_type') == 'tool_call'])
        error_count = len([r for r in records if r.get('record_type') == 'error'])
        
        # 计算时间范围
        if records:
            start_time = min(r.get('timestamp', '') for r in records)
            end_time = max(r.get('timestamp', '') for r in records)
            duration = self._calculate_duration(start_time, end_time)
        else:
            duration = 0
        
        return {
            "session_id": session_id,
            "total_messages": message_count,
            "total_tool_calls": tool_call_count,
            "total_errors": error_count,
            "duration_seconds": duration,
            "success_rate": (message_count - error_count) / message_count * 100 if message_count > 0 else 100
        }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """计算时间间隔（秒）"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            return (end - start).total_seconds()
        except:
            return 0