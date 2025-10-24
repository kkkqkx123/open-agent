"""LLM模块工具函数"""

from typing import Dict, Any, List, Union, Protocol


# 定义编码器协议
class EncodingProtocol(Protocol):
    """编码器协议，用于类型检查"""
    def encode(self, text: str) -> List[int]: ...


def extract_content_as_string(
    content: Union[str, List[Union[str, Dict[str, Any]]]]
) -> str:
    """
    将消息内容提取为字符串

    Args:
        content: 消息内容，可能是字符串或列表

    Returns:
        str: 提取的字符串内容
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
        return "".join(text_parts)
    else:
        return str(content)