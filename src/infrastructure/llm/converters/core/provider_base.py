"""
统一提供商基类

整合所有提供商功能的统一基类。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger.injection import get_logger
from .interfaces import IProvider
from .base_converter import BaseConverter
from .adapters import BaseMultimodalAdapter, BaseStreamAdapter, BaseToolsAdapter, BaseValidationAdapter
from src.interfaces.llm.converters import IConversionContext
from ..common.validation_utils import validation_utils


class BaseProvider(IProvider, BaseConverter):
    """统一提供商基类
    
    整合所有提供商功能的统一基类，使用组合模式。
    """
    
    def __init__(self, name: str):
        """初始化提供商基类
        
        Args:
            name: 提供商名称
        """
        super().__init__(name)
        self.logger = get_logger(__name__)
        
        # 初始化适配器
        self.multimodal_adapter = self._create_multimodal_adapter()
        self.stream_adapter = self._create_stream_adapter()
        self.tools_adapter = self._create_tools_adapter()
        self.validation_adapter = self._create_validation_adapter()
    
    def _create_multimodal_adapter(self) -> BaseMultimodalAdapter:
        """创建多模态适配器
        
        子类可以重写此方法来提供特定的多模态适配器。
        
        Returns:
            BaseMultimodalAdapter: 多模态适配器实例
        """
        return BaseMultimodalAdapter()
    
    def _create_stream_adapter(self) -> BaseStreamAdapter:
        """创建流式适配器
        
        子类可以重写此方法来提供特定的流式适配器。
        
        Returns:
            BaseStreamAdapter: 流式适配器实例
        """
        return BaseStreamAdapter()
    
    def _create_tools_adapter(self) -> BaseToolsAdapter:
        """创建工具适配器
        
        子类可以重写此方法来提供特定的工具适配器。
        
        Returns:
            BaseToolsAdapter: 工具适配器实例
        """
        return BaseToolsAdapter()
    
    def _create_validation_adapter(self) -> BaseValidationAdapter:
        """创建验证适配器
        
        子类可以重写此方法来提供特定的验证适配器。
        
        Returns:
            BaseValidationAdapter: 验证适配器实例
        """
        return BaseValidationAdapter()
    
    def get_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return self.name
    
    def convert_request(self, messages: List[Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求格式
        
        Args:
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            Dict[str, Any]: 提供商API请求格式
        """
        # 创建转换上下文
        context = self._create_conversion_context("request", parameters)
        
        # 验证请求
        errors = self.validate_request(messages, parameters)
        if errors:
            context.add_error(f"请求验证失败: {', '.join(errors)}")
            raise ValueError(f"请求验证失败: {', '.join(errors)}")
        
        # 执行转换
        return self._do_convert_request(messages, parameters, context)
    
    def convert_response(self, response: Dict[str, Any]) -> Any:
        """转换响应格式
        
        Args:
            response: 提供商API响应
            
        Returns:
            Any: 基础消息
        """
        # 创建转换上下文
        context = self._create_conversion_context("response", {"response": response})
        
        # 验证响应
        errors = self.validation_adapter.validate_response(response, context)
        if errors:
            context.add_warning(f"响应验证警告: {', '.join(errors)}")
        
        # 执行转换
        return self._do_convert_response(response, context)
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> Any:
        """转换流式响应格式
        
        Args:
            events: 流式事件列表
            
        Returns:
            Any: 基础消息
        """
        # 创建转换上下文
        context = self._create_conversion_context("stream", {"events": events})
        
        # 验证流式事件
        errors = self.stream_adapter.validate_stream_events(events, context)
        if errors:
            context.add_warning(f"流式事件验证警告: {', '.join(errors)}")
        
        # 执行转换
        return self._do_convert_stream_response(events, context)
    
    def validate_request(self, messages: List[Any], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证消息
        if not messages:
            errors.append("消息列表不能为空")
        
        # 验证参数
        param_errors = self.validation_adapter.validate_request_parameters(parameters)
        errors.extend(param_errors)
        
        # 验证工具（如果有）
        if "tools" in parameters:
            tools = parameters["tools"]
            if isinstance(tools, list):
                tool_errors = self.tools_adapter.validate_tools(tools)
                errors.extend(tool_errors)
        
        return errors
    
    def do_convert(self, source: Any, context: IConversionContext) -> Any:
        """执行具体的转换逻辑
        
        Args:
            source: 源数据
            context: 转换上下文
            
        Returns:
            Any: 转换结果
        """
        conversion_type = context.get_parameter("conversion_type", "unknown")
        
        if conversion_type == "request":
            messages = context.get_parameter("messages", [])
            parameters = context.get_parameter("parameters", {})
            return self._do_convert_request(messages, parameters, context)
        elif conversion_type == "response":
            response = context.get_parameter("response", {})
            return self._do_convert_response(response, context)
        elif conversion_type == "stream":
            events = context.get_parameter("events", [])
            return self._do_convert_stream_response(events, context)
        else:
            raise ValueError(f"不支持的转换类型: {conversion_type}")
    
    def _do_convert_request(self, messages: List[Any], parameters: Dict[str, Any], context: IConversionContext) -> Dict[str, Any]:
        """执行请求转换（子类应重写）
        
        Args:
            messages: 消息列表
            parameters: 请求参数
            context: 转换上下文
            
        Returns:
            Dict[str, Any]: 转换后的请求
        """
        # 基础实现
        return {
            "messages": messages,
            "parameters": parameters
        }
    
    def _do_convert_response(self, response: Dict[str, Any], context: IConversionContext) -> Any:
        """执行响应转换（子类应重写）
        
        Args:
            response: 响应数据
            context: 转换上下文
            
        Returns:
            Any: 转换后的响应
        """
        # 基础实现
        return response
    
    def _do_convert_stream_response(self, events: List[Dict[str, Any]], context: IConversionContext) -> Any:
        """执行流式响应转换（子类应重写）
        
        Args:
            events: 流式事件列表
            context: 转换上下文
            
        Returns:
            Any: 转换后的响应
        """
        # 基础实现：使用流式适配器处理事件
        return self.stream_adapter.process_stream_events(events, context)
    
    def _create_conversion_context(self, conversion_type: str, parameters: Dict[str, Any]) -> IConversionContext:
        """创建转换上下文
        
        Args:
            conversion_type: 转换类型
            parameters: 参数
            
        Returns:
            IConversionContext: 转换上下文
        """
        from .conversion_context import ConversionContext
        
        return ConversionContext(
            provider_name=self.name,
            conversion_type=conversion_type,
            parameters=parameters
        )
    
    def get_supported_conversions(self) -> List[tuple[type, type]]:
        """获取支持的转换类型列表
        
        Returns:
            List[tuple[type, type]]: 支持的转换类型列表
        """
        return [
            (list, dict),  # 请求转换
            (dict, object),  # 响应转换
            (list, object),  # 流式响应转换
        ]
    
    def get_type_from_format(self, format_name: str) -> Optional[type]:
        """根据格式名称获取类型
        
        Args:
            format_name: 格式名称
            
        Returns:
            Optional[type]: 对应的类型
        """
        format_mapping = {
            "request": dict,
            "response": object,
            "stream": object,
        }
        return format_mapping.get(format_name)
    
    def process_multimodal_content(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """处理多模态内容
        
        Args:
            content: 输入内容
            
        Returns:
            List[Dict[str, Any]]: 处理后的内容
        """
        return self.multimodal_adapter.process_content_to_provider_format(content)
    
    def extract_text_from_content(self, content: List[Dict[str, Any]]) -> str:
        """从内容中提取文本
        
        Args:
            content: 内容列表
            
        Returns:
            str: 提取的文本
        """
        return self.multimodal_adapter.extract_text_from_provider_content(content)
    
    def convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式
        
        Args:
            tools: 工具列表
            
        Returns:
            List[Dict[str, Any]]: 转换后的工具列表
        """
        return self.tools_adapter.convert_tools_to_provider_format(tools)
    
    def process_tool_choice(self, tool_choice: Any) -> Any:
        """处理工具选择策略
        
        Args:
            tool_choice: 工具选择策略
            
        Returns:
            Any: 处理后的工具选择策略
        """
        return self.tools_adapter.process_tool_choice(tool_choice)
    
    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从响应中提取工具调用
        
        Args:
            response: 响应数据
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        return self.tools_adapter.extract_tool_calls_from_response(response)
    
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析流式事件行
        
        Args:
            event_line: 流式事件行文本
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件数据
        """
        return self.stream_adapter.parse_stream_event(event_line)
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流式事件列表
        
        Args:
            events: 流式事件列表
            
        Returns:
            Dict[str, Any]: 合并后的响应数据
        """
        return self.stream_adapter.process_stream_events(events)
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从流式事件中提取文本
        
        Args:
            events: 流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        return self.stream_adapter.extract_text_from_stream_events(events)
    
    def handle_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 用户友好的错误消息
        """
        return self.validation_adapter.handle_api_error(error_response)
    
    def get_default_model(self) -> str:
        """获取默认模型
        
        子类应该重写此方法来提供特定的默认模型。
        
        Returns:
            str: 默认模型名称
        """
        return "default"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表
        
        子类应该重写此方法来提供特定的支持模型列表。
        
        Returns:
            List[str]: 支持的模型列表
        """
        return [self.get_default_model()]
    
    def validate_model(self, model: str) -> List[str]:
        """验证模型名称
        
        Args:
            model: 模型名称
            
        Returns:
            List[str]: 验证错误列表
        """
        supported_models = set(self.get_supported_models())
        return validation_utils.validate_model_name(model, self.name, supported_models)
    
    def validate_api_key(self, api_key: str) -> List[str]:
        """验证API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            List[str]: 验证错误列表
        """
        return validation_utils.validate_api_key(api_key, self.name)