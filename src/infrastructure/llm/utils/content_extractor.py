"""内容提取器

用于从响应中提取和处理内容。
"""

from typing import Dict, List, Any, Optional


class ContentExtractor:
    """内容提取器"""
    
    def __init__(self) -> None:
        """初始化内容提取器"""
        pass
    
    def extract_text_content(self, content: Any) -> Optional[str]:
        """提取文本内容
        
        Args:
            content: 内容对象
            
        Returns:
            文本内容或None
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            return content.get("text")
        return None
    
    def extract_content_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """从响应中提取内容
        
        Args:
            response: 响应对象
            
        Returns:
            提取的内容字典
        """
        extracted = {
            "text": None,
            "content": None,
            "raw": response
        }
        
        # 尝试从常见字段提取内容
        if isinstance(response, dict):
            if "text" in response:
                extracted["text"] = response["text"]
            if "content" in response:
                extracted["content"] = response["content"]
            if "message" in response:
                message = response["message"]
                if isinstance(message, dict):
                    if "content" in message:
                        extracted["content"] = message["content"]
        
        return extracted
    
    def extract_messages(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取消息列表
        
        Args:
            response: 响应对象
            
        Returns:
            消息列表
        """
        messages = []
        
        if isinstance(response, dict):
            if "messages" in response and isinstance(response["messages"], list):
                messages = response["messages"]
            elif "choices" in response and isinstance(response["choices"], list):
                for choice in response["choices"]:
                    if isinstance(choice, dict) and "message" in choice:
                        messages.append(choice["message"])
        
        return messages
