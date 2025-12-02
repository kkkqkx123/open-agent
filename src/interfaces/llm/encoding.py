"""编码相关接口定义"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 避免运行时循环依赖
    pass


class EncodingProtocol(ABC):
    """编码协议接口
    
    定义文本编码和解码的标准接口，支持不同的tokenizer实现。
    """
    
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
        """获取编码器名称
        
        Returns:
            str: 编码器名称
        """
        pass