"""LLM转换器接口定义

定义提供商转换器的标准契约，用于统一不同LLM提供商的格式转换。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Sequence, List

# 使用 TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..messages import IBaseMessage


class IProviderConverter(ABC):
    """提供商转换器接口
    
    定义提供商特定格式转换的标准契约，包括请求和响应的双向转换。
    """
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称（如 "openai", "gemini", "anthropic"）
        """
        pass
    
    @abstractmethod
    def convert_request(
        self, 
        messages: Sequence["IBaseMessage"], 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换为提供商API请求格式
        
        Args:
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            Dict[str, Any]: 提供商API请求格式
        """
        pass
    
    @abstractmethod
    def convert_response(
        self, 
        response: Dict[str, Any]
    ) -> "IBaseMessage":
        """从提供商API响应转换
        
        Args:
            response: 提供商API响应
            
        Returns:
            IBaseMessage: 基础消息
        """
        pass
    
    def convert_stream_response(
        self, 
        events: List[Dict[str, Any]]
    ) -> "IBaseMessage":
        """转换流式响应格式（可选实现）
        
        Args:
            events: 流式事件列表
            
        Returns:
            IBaseMessage: 基础消息
        """
        # 默认实现：将流式事件合并为完整响应后转换
        # 子类可以重写此方法以提供更高效的流式处理
        merged_response = {}
        for event in events:
            merged_response.update(event)
        return self.convert_response(merged_response)
    
    def validate_request(
        self, 
        messages: Sequence["IBaseMessage"], 
        parameters: Dict[str, Any]
    ) -> List[str]:
        """验证请求参数（可选实现）
        
        Args:
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            List[str]: 错误列表，空列表表示验证通过
        """
        # 默认实现：基本验证
        errors = []
        
        if not messages:
            errors.append("消息列表不能为空")
        
        return errors
    
    def handle_api_error(
        self, 
        error_response: Dict[str, Any]
    ) -> str:
        """处理API错误响应（可选实现）
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 格式化的错误消息
        """
        # 默认实现：基本错误处理
        error = error_response.get("error", {})
        error_message = error.get("message", "未知错误")
        error_code = error.get("code", "unknown")
        
        return f"API错误 ({error_code}): {error_message}"