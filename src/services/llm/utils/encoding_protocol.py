"""编码协议和工具函数"""

from abc import ABC, abstractmethod
from typing import Any, Union
from langchain_core.messages import BaseMessage


def extract_content_as_string(content: Union[str, list, Any]) -> str:
    """从消息内容中提取字符串
    
    Args:
        content: 消息内容，可能是字符串、列表或其他类型
        
    Returns:
        str: 提取的字符串内容
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # 处理多模态内容
        result_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    result_parts.append(item.get("text", ""))
                elif item.get("type") == "image_url":
                    result_parts.append("[IMAGE]")
                else:
                    result_parts.append(f"[{item.get('type', 'UNKNOWN').upper()}]")
            elif isinstance(item, str):
                result_parts.append(item)
            else:
                result_parts.append(str(item))
        return "".join(result_parts)
    else:
        return str(content)


class EncodingProtocol(ABC):
    """编码协议接口"""
    
    @abstractmethod
    def encode(self, text: str) -> list[int]:
        """编码文本为token列表
        
        Args:
            text: 要编码的文本
            
        Returns:
            list[int]: token列表
        """
        pass
    
    @abstractmethod
    def decode(self, tokens: list[int]) -> str:
        """解码token列表为文本
        
        Args:
            tokens: token列表
            
        Returns:
            str: 解码的文本
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """获取编码器名称"""
        pass


class TiktokenEncoding(EncodingProtocol):
    """Tiktoken编码器适配器"""
    
    def __init__(self, encoding):
        """初始化Tiktoken编码器
        
        Args:
            encoding: tiktoken编码器实例
        """
        self._encoding = encoding
    
    def encode(self, text: str) -> list[int]:
        """编码文本为token列表"""
        return self._encoding.encode(text)
    
    def decode(self, tokens: list[int]) -> str:
        """解码token列表为文本"""
        return self._encoding.decode(tokens)
    
    @property
    def name(self) -> str:
        """获取编码器名称"""
        return getattr(self._encoding, 'name', 'tiktoken')
