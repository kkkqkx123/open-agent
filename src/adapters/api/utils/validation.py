"""验证工具"""
import re
from typing import Any, Optional, List
from datetime import datetime
from pathlib import Path


def validate_session_id(session_id: str) -> bool:
    """验证会话ID格式"""
    if not session_id:
        return False
    
    # 会话ID格式：workflow-YYYYMMDD-HHMMSS-hash
    pattern = r'^[a-zA-Z0-9_-]+-\d{8}-\d{6}-[a-f0-9]{8}$'
    return bool(re.match(pattern, session_id))


def validate_workflow_id(workflow_id: str) -> bool:
    """验证工作流ID格式"""
    if not workflow_id:
        return False
    
    # 工作流ID格式：workflow_YYYYMMDD_HHMMSS_hash
    pattern = r'^[a-zA-Z0-9_-]+_\d{8}_\d{6}_[a-f0-9]{8}$'
    return bool(re.match(pattern, workflow_id))


def validate_config_path(config_path: str) -> bool:
    """验证配置文件路径"""
    if not config_path:
        return False
    
    # 检查路径格式
    path = Path(config_path)
    
    # 检查文件扩展名
    if path.suffix.lower() != '.yaml' and path.suffix.lower() != '.yml':
        return False
    
    # 检查路径中是否包含configs目录
    if 'configs' not in path.parts:
        return False
    
    return True


def validate_datetime_string(datetime_str: str) -> bool:
    """验证日期时间字符串格式"""
    if not datetime_str:
        return False
    
    try:
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def validate_page_params(page: int, page_size: int) -> tuple[bool, Optional[str]]:
    """验证分页参数"""
    if page < 1:
        return False, "页码必须大于0"
    
    if page_size < 1:
        return False, "每页大小必须大于0"
    
    if page_size > 100:
        return False, "每页大小不能超过100"
    
    return True, None


def validate_search_query(query: str) -> tuple[bool, Optional[str]]:
    """验证搜索查询"""
    if not query or not query.strip():
        return False, "搜索查询不能为空"
    
    if len(query) > 500:
        return False, "搜索查询长度不能超过500个字符"
    
    return True, None


def validate_record_types(record_types: List[str]) -> tuple[bool, Optional[str]]:
    """验证记录类型"""
    if not record_types:
        return True, None
    
    valid_types = [
        "message", "tool_call", "llm_request", "llm_response", 
        "token_usage", "cost", "error", "system"
    ]
    
    for record_type in record_types:
        if record_type not in valid_types:
            return False, f"无效的记录类型: {record_type}"
    
    return True, None


def validate_status(status: str) -> bool:
    """验证状态值"""
    valid_statuses = ["active", "paused", "completed", "error", "archived"]
    return status in valid_statuses


def validate_sort_params(sort_by: str, sort_order: str) -> tuple[bool, Optional[str]]:
    """验证排序参数"""
    valid_sort_fields = [
        "created_at", "updated_at", "session_id", "workflow_id", "status"
    ]
    
    if sort_by not in valid_sort_fields:
        return False, f"无效的排序字段: {sort_by}"
    
    if sort_order not in ["asc", "desc"]:
        return False, f"无效的排序方向: {sort_order}"
    
    return True, None


def validate_export_format(format: str) -> bool:
    """验证导出格式"""
    valid_formats = ["json", "csv"]
    return format in valid_formats


def validate_time_range(start_time: Optional[str], end_time: Optional[str]) -> tuple[bool, Optional[str]]:
    """验证时间范围"""
    if start_time and not validate_datetime_string(start_time):
        return False, "开始时间格式无效"
    
    if end_time and not validate_datetime_string(end_time):
        return False, "结束时间格式无效"
    
    if start_time and end_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if start_dt >= end_dt:
                return False, "开始时间必须早于结束时间"
        except ValueError:
            return False, "时间格式解析失败"
    
    return True, None


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """清理字符串"""
    if not value:
        return ""
    
    # 移除前后空白
    value = value.strip()
    
    # 限制长度
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def validate_json_data(data: Any) -> tuple[bool, Optional[str]]:
    """验证JSON数据"""
    import json
    
    try:
        json.dumps(data)
        return True, None
    except (TypeError, ValueError) as e:
        return False, f"无效的JSON数据: {str(e)}"