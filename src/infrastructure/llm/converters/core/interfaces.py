"""
核心接口定义

定义转换器系统的所有核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage
    from src.interfaces.llm.converters import IConversionContext


class IProvider(ABC):
    """提供商接口
    
    定义所有LLM提供商必须实现的基础接口。
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        pass
    
    @abstractmethod
    def convert_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求格式
        
        Args:
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            Dict[str, Any]: 提供商API请求格式
        """
        pass
    
    @abstractmethod
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """转换响应格式
        
        Args:
            response: 提供商API响应
            
        Returns:
            IBaseMessage: 基础消息
        """
        pass
    
    @abstractmethod
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """转换流式响应格式
        
        Args:
            events: 流式事件列表
            
        Returns:
            IBaseMessage: 基础消息
        """
        pass
    
    @abstractmethod
    def validate_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass


class IConverter(ABC):
    """转换器接口
    
    定义所有转换器必须实现的基础接口。
    """
    
    @abstractmethod
    def can_convert(self, source_type: type, target_type: type) -> bool:
        """检查是否可以转换指定类型
        
        Args:
            source_type: 源类型
            target_type: 目标类型
            
        Returns:
            bool: 是否可以转换
        """
        pass
    
    @abstractmethod
    def convert(self, source: Any, context: "IConversionContext") -> Any:
        """执行转换
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Returns:
            Any: 转换结果
        """
        pass


class IMultimodalAdapter(ABC):
    """多模态适配器接口
    
    定义多模态内容处理的通用接口。
    """
    
    @abstractmethod
    def process_content_to_provider_format(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """将内容转换为提供商特定格式
        
        Args:
            content: 输入内容
            
        Returns:
            List[Dict[str, Any]]: 提供商格式的内容列表
        """
        pass
    
    @abstractmethod
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从提供商格式内容中提取文本
        
        Args:
            content: 提供商格式的内容列表
            
        Returns:
            str: 提取的文本内容
        """
        pass
    
    @abstractmethod
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证提供商格式内容
        
        Args:
            content: 提供商格式的内容列表
            
        Returns:
            List[str]: 验证错误列表
        """
        pass


class IStreamAdapter(ABC):
    """流式处理适配器接口
    
    定义流式响应处理的通用接口。
    """
    
    @abstractmethod
    def parse_stream_event(self, event_line: str, context: Optional["IConversionContext"] = None) -> Optional[Dict[str, Any]]:
        """解析流式事件行
        
        Args:
            event_line: 流式事件行文本
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件数据
        """
        pass
    
    @abstractmethod
    def process_stream_events(self, events: List[Dict[str, Any]], context: Optional["IConversionContext"] = None) -> Dict[str, Any]:
        """处理流式事件列表
        
        Args:
            events: 流式事件列表
            
        Returns:
            Dict[str, Any]: 合并后的响应数据
        """
        pass
    
    @abstractmethod
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]], context: Optional["IConversionContext"] = None) -> str:
        """从流式事件中提取文本
        
        Args:
            events: 流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        pass
    
    @abstractmethod
    def validate_stream_events(self, events: List[Dict[str, Any]], context: Optional["IConversionContext"] = None) -> List[str]:
        """验证流式事件
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[str]: 验证错误列表
        """
        pass


class IToolsAdapter(ABC):
    """工具处理适配器接口
    
    定义工具调用处理的通用接口。
    """
    
    @abstractmethod
    def validate_tools(self, tools: List[Dict[str, Any]], context: Optional["IConversionContext"] = None) -> List[str]:
        """验证工具定义
        
        Args:
            tools: 工具定义列表
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]], context: Optional["IConversionContext"] = None) -> List[Dict[str, Any]]:
        """转换工具格式为提供商特定格式
        
        Args:
            tools: 工具定义列表
            
        Returns:
            List[Dict[str, Any]]: 提供商格式的工具定义
        """
        pass
    
    @abstractmethod
    def process_tool_choice(self, tool_choice: Any, context: Optional["IConversionContext"] = None) -> Any:
        """处理工具选择策略
        
        Args:
            tool_choice: 工具选择策略
            
        Returns:
            Any: 处理后的工具选择策略
        """
        pass
    
    @abstractmethod
    def extract_tool_calls_from_response(self, response: Dict[str, Any], context: Optional["IConversionContext"] = None) -> List[Dict[str, Any]]:
        """从响应中提取工具调用
        
        Args:
            response: 提供商响应
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        pass


class IValidationAdapter(ABC):
    """验证适配器接口
    
    定义参数验证的通用接口。
    """
    
    @abstractmethod
    def validate_request_parameters(self, parameters: Dict[str, Any], context: Optional["IConversionContext"] = None) -> List[str]:
        """验证请求参数
        
        Args:
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: Dict[str, Any], context: Optional[IConversionContext] = None) -> List[str]:
        """验证响应格式
        
        Args:
            response: 提供商响应
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def handle_api_error(self, error_response: Dict[str, Any], context: Optional[IConversionContext] = None) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 格式化的错误信息
        """
        pass


class IProviderConfig(ABC):
    """提供商配置接口
    
    定义提供商配置的通用接口。
    """
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        pass
    
    @abstractmethod
    def validate(self, context: Optional[IConversionContext] = None) -> List[str]:
        """验证配置
        
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """获取默认模型
        
        Returns:
            str: 默认模型名称
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型列表
        """
        pass