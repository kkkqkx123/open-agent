"""Token计算器"""

import re
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class ITokenCounter(ABC):
    """Token计算器接口"""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        pass
    
    @abstractmethod
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        pass


class OpenAITokenCounter(ITokenCounter):
    """OpenAI Token计算器"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo") -> None:
        """
        初始化OpenAI Token计算器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self._encoding = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载编码器"""
        try:
            import tiktoken
            
            # 尝试获取模型特定的编码器
            try:
                self._encoding = tiktoken.encoding_for_model(self.model_name)
            except KeyError:
                # 如果模型没有特定编码器，使用默认的
                self._encoding = tiktoken.get_encoding("cl100k_base")
                
        except ImportError:
            # 如果没有安装tiktoken，使用简单的估算
            self._encoding = None
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        if self._encoding:
            return len(self._encoding.encode(text))
        else:
            # 简单估算：大约4个字符=1个token
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        if self._encoding:
            total_tokens = 0
            
            # 每条消息的开销
            tokens_per_message = 3
            tokens_per_name = 1
            
            for message in messages:
                # 计算消息内容的token
                total_tokens += tokens_per_message
                total_tokens += len(self._encoding.encode(message.content))
                
                # 如果有名称，添加名称的token
                if hasattr(message, 'name') and message.name:
                    total_tokens += tokens_per_name + len(self._encoding.encode(message.name))
            
            # 添加回复的token
            total_tokens += 3
            
            return total_tokens
        else:
            # 简单估算
            total_chars = sum(len(message.content) for message in messages)
            return total_chars // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model_name": self.model_name,
            "provider": "openai",
            "encoding": "cl100k_base" if self._encoding else "estimated",
            "supports_tiktoken": self._encoding is not None
        }


class GeminiTokenCounter(ITokenCounter):
    """Gemini Token计算器"""
    
    def __init__(self, model_name: str = "gemini-pro") -> None:
        """
        初始化Gemini Token计算器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        # Gemini使用简单的字符估算
        # 实际实现可能需要使用Google的token计算库
        # 这里使用简单的估算：大约4个字符=1个token
        return len(text) // 4
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        total_tokens = 0
        
        for message in messages:
            total_tokens += self.count_tokens(message.content)
            # 添加格式化的token（每个消息大约4个token）
            total_tokens += 4
        
        # 添加回复的token（大约3个token）
        total_tokens += 3
        
        return total_tokens
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model_name": self.model_name,
            "provider": "google",
            "encoding": "estimated",
            "supports_tiktoken": False
        }


class AnthropicTokenCounter(ITokenCounter):
    """Anthropic Token计算器"""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229") -> None:
        """
        初始化Anthropic Token计算器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        # Anthropic使用Claude的token计算方式
        # 实际实现可能需要使用Anthropic的token计算库
        # 这里使用简单的估算：大约4个字符=1个token
        return len(text) // 4
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        total_tokens = 0
        
        for message in messages:
            total_tokens += self.count_tokens(message.content)
            # 添加格式化的token（每个消息大约4个token）
            total_tokens += 4
        
        # 添加回复的token（大约3个token）
        total_tokens += 3
        
        return total_tokens
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model_name": self.model_name,
            "provider": "anthropic",
            "encoding": "estimated",
            "supports_tiktoken": False
        }


class MockTokenCounter(ITokenCounter):
    """Mock Token计算器"""
    
    def __init__(self, model_name: str = "mock-model") -> None:
        """
        初始化Mock Token计算器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        # 简单估算：大约4个字符=1个token
        return len(text) // 4
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        total_tokens = 0
        
        for message in messages:
            total_tokens += self.count_tokens(message.content)
            # 添加格式化的token（每个消息大约4个token）
            total_tokens += 4
        
        # 添加回复的token（大约3个token）
        total_tokens += 3
        
        return total_tokens
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model_name": self.model_name,
            "provider": "mock",
            "encoding": "estimated",
            "supports_tiktoken": False
        }


class TokenCounterFactory:
    """Token计算器工厂"""
    
    @staticmethod
    def create_counter(model_type: str, model_name: str) -> ITokenCounter:
        """
        创建Token计算器
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            ITokenCounter: Token计算器实例
        """
        if model_type == "openai":
            return OpenAITokenCounter(model_name)
        elif model_type == "gemini":
            return GeminiTokenCounter(model_name)
        elif model_type in ["anthropic", "claude"]:
            return AnthropicTokenCounter(model_name)
        elif model_type == "mock":
            return MockTokenCounter(model_name)
        else:
            # 默认使用OpenAI计算器
            return OpenAITokenCounter(model_name)
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """
        获取支持的模型类型
        
        Returns:
            List[str]: 支持的模型类型列表
        """
        return ["openai", "gemini", "anthropic", "claude", "mock"]