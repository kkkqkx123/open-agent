"""
通用工具函数

提供转换器系统使用的通用工具函数。
"""

import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


def validate_image_data(image_data: str, max_size: int = 5 * 1024 * 1024) -> List[str]:
    """验证图像数据
    
    Args:
        image_data: base64编码的图像数据
        max_size: 最大允许大小（字节）
        
    Returns:
        List[str]: 验证错误列表
    """
    errors = []
    
    if not isinstance(image_data, str):
        errors.append("图像数据必须是字符串")
        return errors
    
    try:
        decoded_data = base64.b64decode(image_data)
        if len(decoded_data) > max_size:
            errors.append(f"图像大小超过限制: {len(decoded_data)} > {max_size}")
    except Exception as e:
        errors.append(f"图像数据解码失败: {e}")
    
    return errors


def validate_media_type(media_type: str, supported_types: List[str]) -> List[str]:
    """验证媒体类型
    
    Args:
        media_type: 媒体类型
        supported_types: 支持的媒体类型列表
        
    Returns:
        List[str]: 验证错误列表
    """
    errors = []
    
    if not isinstance(media_type, str):
        errors.append("媒体类型必须是字符串")
        return errors
    
    if media_type not in supported_types:
        errors.append(f"不支持的媒体类型: {media_type}")
    
    return errors


def extract_text_from_content(content: List[Dict[str, Any]]) -> str:
    """从内容列表中提取文本
    
    Args:
        content: 内容列表
        
    Returns:
        str: 提取的文本
    """
    text_parts = []
    
    for item in content:
        if item.get("type") == "text":
            text_parts.append(item.get("text", ""))
        elif item.get("type") == "image":
            text_parts.append("[图像内容]")
    
    return " ".join(text_parts)


def process_content_to_list(content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    """将内容转换为统一列表格式
    
    Args:
        content: 输入内容
        
    Returns:
        List[Dict[str, Any]]: 处理后的内容列表
    """
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    elif isinstance(content, list):
        processed = []
        for item in content:
            if isinstance(item, str):
                processed.append({"type": "text", "text": item})
            elif isinstance(item, dict):
                processed.append(item)
        return processed
    else:
        return [{"type": "text", "text": str(content)}]


def validate_tools(tools: List[Dict[str, Any]]) -> List[str]:
    """验证工具定义
    
    Args:
        tools: 工具定义列表
        
    Returns:
        List[str]: 验证错误列表
    """
    errors = []
    
    if not isinstance(tools, list):
        errors.append("工具必须是列表格式")
        return errors
    
    for i, tool in enumerate(tools):
        if not isinstance(tool, dict):
            errors.append(f"工具 {i} 必须是字典")
            continue
        
        if "type" not in tool:
            errors.append(f"工具 {i} 缺少type字段")
        
        if "function" not in tool:
            errors.append(f"工具 {i} 缺少function字段")
        elif not isinstance(tool["function"], dict):
            errors.append(f"工具 {i} 的function字段必须是字典")
        else:
            function = tool["function"]
            if "name" not in function:
                errors.append(f"工具 {i} 的function缺少name字段")
            if "description" not in function:
                errors.append(f"工具 {i} 的function缺少description字段")
            if "parameters" not in function:
                errors.append(f"工具 {i} 的function缺少parameters字段")
    
    return errors


def convert_tools_to_openai_format(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将工具转换为OpenAI格式
    
    Args:
        tools: 工具定义列表
        
    Returns:
        List[Dict[str, Any]]: OpenAI格式的工具定义
    """
    return tools  # 假设输入已经是OpenAI格式


def extract_tool_calls_from_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从响应中提取工具调用
    
    Args:
        response: API响应
        
    Returns:
        List[Dict[str, Any]]: 工具调用列表
    """
    choices = response.get("choices", [])
    if not choices:
        return []
    
    message = choices[0].get("message", {})
    return message.get("tool_calls", [])


def validate_stream_events(events: List[Dict[str, Any]]) -> List[str]:
    """验证流式事件
    
    Args:
        events: 流式事件列表
        
    Returns:
        List[str]: 验证错误列表
    """
    errors = []
    
    if not isinstance(events, list):
        errors.append("流式事件必须是列表格式")
        return errors
    
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"事件 {i} 必须是字典")
    
    return errors


def process_stream_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """处理流式事件为响应格式
    
    Args:
        events: 流式事件列表
        
    Returns:
        Dict[str, Any]: 处理后的响应
    """
    content_parts = []
    tool_calls = []
    
    for event in events:
        if "content" in event:
            content_parts.append(str(event["content"]))
        
        if "tool_calls" in event:
            tool_calls.extend(event["tool_calls"])
    
    # 构建响应格式
    response = {
        "choices": [{
            "message": {
                "content": "".join(content_parts),
                "role": "assistant"
            }
        }]
    }
    
    if tool_calls:
        response["choices"][0]["message"]["tool_calls"] = tool_calls  # type: ignore
    
    return response


def create_timestamp() -> datetime:
    """创建当前时间戳"""
    return datetime.now()


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """安全获取字典值"""
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个字典"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result