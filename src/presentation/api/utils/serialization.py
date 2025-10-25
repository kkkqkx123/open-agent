"""序列化工具"""
from typing import Dict, Any, Optional, List
from datetime import datetime


def serialize_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """序列化会话数据"""
    if not session_data:
        return {}
    
    # 确保必要字段存在
    metadata = session_data.get("metadata", {})
    
    return {
        "session_id": metadata.get("session_id", ""),
        "workflow_config_path": metadata.get("workflow_config_path", ""),
        "workflow_id": metadata.get("workflow_id", ""),
        "status": metadata.get("status", "active"),
        "created_at": metadata.get("created_at", datetime.now().isoformat()),
        "updated_at": metadata.get("updated_at", datetime.now().isoformat()),
        "agent_config": metadata.get("agent_config", {}),
        "metadata": metadata.get("metadata", {})
    }


def serialize_workflow_data(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """序列化工作流数据"""
    if not workflow_data:
        return {}
    
    return {
        "workflow_id": workflow_data.get("workflow_id", ""),
        "name": workflow_data.get("name", ""),
        "description": workflow_data.get("description", ""),
        "version": workflow_data.get("version", "1.0.0"),
        "config_path": workflow_data.get("config_path", ""),
        "loaded_at": workflow_data.get("loaded_at"),
        "last_used": workflow_data.get("last_used"),
        "usage_count": workflow_data.get("usage_count", 0),
        "nodes": workflow_data.get("nodes", []),
        "edges": workflow_data.get("edges", [])
    }


def serialize_history_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """序列化历史记录"""
    if not record:
        return {}
    
    # 确保时间戳格式正确
    timestamp = record.get("timestamp")
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()
    
    return {
        "record_id": record.get("record_id", ""),
        "session_id": record.get("session_id", ""),
        "timestamp": timestamp or datetime.now().isoformat(),
        "record_type": record.get("record_type", ""),
        **record  # 包含所有其他字段
    }


def serialize_error(error: Exception) -> Dict[str, Any]:
    """序列化错误信息"""
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }


def safe_json_dumps(data: Any) -> str:
    """安全的JSON序列化"""
    import json
    
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            if isinstance(o, datetime):
                return o.isoformat()
            return super().default(o)
    
    try:
        return json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"error": "无法序列化数据"}, ensure_ascii=False)


def safe_json_loads(json_str: str) -> Any:
    """安全的JSON反序列化"""
    import json
    
    try:
        return json.loads(json_str)
    except (TypeError, ValueError):
        return {"error": "无效的JSON数据"}


def filter_sensitive_data(data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """过滤敏感数据"""
    if not sensitive_keys:
        sensitive_keys = ["password", "token", "api_key", "secret"]
    
    filtered_data: Dict[str, Any] = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered_data[key] = "***"
        elif isinstance(value, dict):
            filtered_data[key] = filter_sensitive_data(value, sensitive_keys)
        else:
            filtered_data[key] = value
    
    return filtered_data