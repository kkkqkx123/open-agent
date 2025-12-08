"""
统一适配器基类

整合多模态、流式处理、工具处理和验证的适配器基类。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from src.services.logger.injection import get_logger
from .interfaces import IMultimodalAdapter, IStreamAdapter, IToolsAdapter, IValidationAdapter
from src.interfaces.llm.converters import IConversionContext


class BaseMultimodalAdapter(IMultimodalAdapter):
    """多模态适配器基类
    
    提供多模态内容处理的通用实现。
    """
    
    def __init__(self) -> None:
        """初始化多模态适配器"""
        self.logger = get_logger(__name__)
    
    def _process_content_list(self, content_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理内容列表（通用方法）"""
        processed_content = []
        
        for item in content_list:
            if isinstance(item, str):
                processed_content.append(self._create_text_content(item))
            elif isinstance(item, dict):
                processed_item = self._process_dict_content(item)
                if processed_item:
                    processed_content.append(processed_item)
            else:
                # 尝试将其他类型转换为文本
                processed_content.append(self._create_text_content(str(item)))
        
        return processed_content
    
    def _create_text_content(self, text: str) -> Dict[str, Any]:
        """创建文本内容（基础实现，子类可重写）"""
        return {"type": "text", "text": text}
    
    def _process_dict_content(self, content_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理字典内容（基础实现，子类可重写）"""
        content_type = content_dict.get("type")
        
        if content_type == "text":
            return {
                "type": "text",
                "text": content_dict.get("text", "")
            }
        elif content_type == "image":
            return self._process_image_content(content_dict)
        else:
            # 未知类型，转换为文本
            return self._create_text_content(str(content_dict))
    
    def _process_image_content(self, image_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理图像内容（基础实现，子类应重写）"""
        # 基础实现，子类应该根据具体API格式重写
        source = image_item.get("source", {})
        if not source:
            self.logger.warning("图像内容缺少source字段")
            return None
        
        return {
            "type": "image",
            "source": source
        }
    
    def _extract_text_from_content_list(self, content: List[Dict[str, Any]]) -> str:
        """从内容列表中提取文本（通用方法）"""
        text_parts = []
        
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "image":
                    text_parts.append("[图像内容]")
        
        return " ".join(text_parts)
    
    def _validate_content_structure(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证内容结构（通用方法）"""
        errors = []
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        if not content:
            errors.append("内容列表不能为空")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"内容项 {i} 必须是字典")
                continue
            
            content_type = item.get("type")
            if not content_type:
                errors.append(f"内容项 {i} 缺少type字段")
                continue
            
            # 验证特定类型的内容
            type_errors = self._validate_content_item(item, i)
            errors.extend(type_errors)
        
        return errors
    
    def _validate_content_item(self, item: Dict[str, Any], index: int) -> List[str]:
        """验证单个内容项（基础实现，子类可重写）"""
        errors = []
        content_type = item.get("type")
        
        if content_type == "text":
            text = item.get("text")
            if not isinstance(text, str):
                errors.append(f"文本内容项 {index} 的text字段必须是字符串")
        elif content_type == "image":
            image_errors = self._validate_image_item(item, index)
            errors.extend(image_errors)
        else:
            errors.append(f"内容项 {index} 有不支持的类型: {content_type}")
        
        return errors
    
    def _validate_image_item(self, image_item: Dict[str, Any], index: int) -> List[str]:
        """验证图像项（基础实现，子类可重写）"""
        errors = []
        
        source = image_item.get("source")
        if not isinstance(source, dict):
            errors.append(f"图像项 {index} 的source字段必须是字典")
            return errors
        
        # 基础验证，子类可以添加更多特定验证
        if not source.get("data"):
            errors.append(f"图像项 {index} 的source缺少data字段")
        
        return errors
    
    def create_image_content(
        self, 
        image_path: str, 
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件路径创建图像内容（通用方法）"""
        import base64
        import mimetypes
        
        try:
            # 自动检测媒体类型
            if not media_type:
                media_type, _ = mimetypes.guess_type(image_path)
                if not media_type:
                    media_type = "image/jpeg"  # 默认
            
            # 读取并编码图像
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # 检查大小限制（基础实现，子类可以重写）
            max_size = self._get_max_image_size()
            if len(image_data) > max_size:
                raise ValueError(f"图像大小超过限制: {len(image_data)} bytes")
            
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            
            return self._create_image_content_dict(media_type, encoded_data)
        except Exception as e:
            self.logger.error(f"创建图像内容失败: {e}")
            raise
    
    def _create_image_content_dict(self, media_type: str, encoded_data: str) -> Dict[str, Any]:
        """创建图像内容字典（基础实现，子类可重写）"""
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded_data
            }
        }
    
    def _get_max_image_size(self) -> int:
        """获取最大图像大小限制（基础实现，子类可重写）"""
        return 5 * 1024 * 1024  # 默认5MB
    
    def _get_supported_image_formats(self) -> set:
        """获取支持的图像格式（基础实现，子类可重写）"""
        return {"image/jpeg", "image/png", "image/gif", "image/webp"}


class BaseStreamAdapter(IStreamAdapter):
    """流式处理适配器基类
    
    提供流式响应处理的通用实现。
    """
    
    def __init__(self) -> None:
        """初始化流式适配器"""
        self.logger = get_logger(__name__)
    
    def validate_stream_events(self, events: List[Dict[str, Any]], context: Optional[IConversionContext] = None) -> List[str]:
        """验证流式事件（通用方法）"""
        errors = []
        
        if not isinstance(events, list):
            errors.append("流式事件必须是列表格式")
            return errors
        
        if not events:
            errors.append("流式事件列表不能为空")
            return errors
        
        for i, event in enumerate(events):
            event_errors = self._validate_single_event(event, i)
            errors.extend(event_errors)
        
        return errors
    
    def _validate_single_event(self, event: Dict[str, Any], index: int) -> List[str]:
        """验证单个流式事件（基础实现，子类可重写）"""
        errors = []
        
        if not isinstance(event, dict):
            errors.append(f"流式事件 {index} 必须是字典")
            return errors
        
        # 基础验证，子类可以添加更多特定验证
        if not event:
            errors.append(f"流式事件 {index} 不能为空")
        
        return errors
    
    def _merge_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并流式事件（通用方法）"""
        merged_response = {}
        
        for event in events:
            if isinstance(event, dict):
                self._merge_single_event(merged_response, event)
        
        return merged_response
    
    def _merge_single_event(self, merged: Dict[str, Any], event: Dict[str, Any]) -> None:
        """合并单个事件到响应中（基础实现，子类可重写）"""
        # 基础实现：简单更新字典
        merged.update(event)
    
    def _extract_text_from_events(self, events: List[Dict[str, Any]]) -> str:
        """从事件列表中提取文本（通用方法）"""
        text_parts = []
        
        for event in events:
            text = self._extract_text_from_single_event(event)
            if text:
                text_parts.append(text)
        
        return "".join(text_parts)
    
    def _extract_text_from_single_event(self, event: Dict[str, Any]) -> Optional[str]:
        """从单个事件中提取文本（基础实现，子类可重写）"""
        # 基础实现：尝试常见的文本字段
        text_fields = ["content", "text", "delta", "message"]
        
        for field in text_fields:
            if field in event:
                value = event[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict):
                    # 尝试从嵌套字典中提取文本
                    nested_text = self._extract_text_from_nested_dict(value)
                    if nested_text:
                        return nested_text
        
        return None
    
    def _extract_text_from_nested_dict(self, nested_dict: Dict[str, Any]) -> Optional[str]:
        """从嵌套字典中提取文本（辅助方法）"""
        for key, value in nested_dict.items():
            if isinstance(value, str) and key in ["content", "text"]:
                return value
            elif isinstance(value, dict):
                result = self._extract_text_from_nested_dict(value)
                if result:
                    return result
        
        return None
    
    def _parse_sse_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析Server-Sent Events格式（通用方法）"""
        import json
        try:
            if not event_line.strip():
                return None
            
            # 移除 "data: " 前缀
            if event_line.startswith("data: "):
                event_line = event_line[6:]
            
            # 检查是否为结束标记
            if event_line.strip() == "[DONE]":
                return {"type": "done"}
            
            # 尝试解析JSON
            return json.loads(event_line)
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析流式事件JSON: {event_line}")
            return None
        except Exception as e:
            self.logger.error(f"解析流式事件失败: {e}")
            return None
    
    def _filter_events_by_type(self, events: List[Dict[str, Any]], event_types: List[str]) -> List[Dict[str, Any]]:
        """按类型过滤事件（辅助方法）"""
        filtered_events = []
        
        for event in events:
            event_type = event.get("type")
            if event_type in event_types:
                filtered_events.append(event)
        
        return filtered_events
    
    def _group_events_by_type(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按类型分组事件（辅助方法）"""
        grouped_events = {}
        
        for event in events:
            event_type = event.get("type", "unknown")
            if event_type not in grouped_events:
                grouped_events[event_type] = []
            grouped_events[event_type].append(event)
        
        return grouped_events
    
    def _extract_tool_calls_from_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从事件中提取工具调用（通用方法）"""
        tool_calls = []
        
        for event in events:
            tool_call = self._extract_tool_call_from_single_event(event)
            if tool_call:
                tool_calls.append(tool_call)
        
        return tool_calls
    
    def _extract_tool_call_from_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从单个事件中提取工具调用（基础实现，子类可重写）"""
        # 基础实现：查找常见的工具调用字段
        if "tool_calls" in event:
            return event["tool_calls"]
        elif "function_call" in event:
            return event["function_call"]
        elif "tool_use" in event:
            return event["tool_use"]
        
        return None
    
    def _create_stream_response(
        self, 
        content: str, 
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建流式响应结构（通用方法）"""
        response = {
            "content": content,
            **kwargs
        }
        
        if tool_calls:
            response["tool_calls"] = tool_calls
        
        return response
    
    def _is_complete_event(self, event: Dict[str, Any]) -> bool:
        """检查事件是否为完成事件（基础实现，子类可重写）"""
        finish_reasons = ["stop", "end_turn", "max_tokens", "stop_sequence", "tool_use"]
        finish_reason = event.get("finish_reason") or event.get("stop_reason")
        
        return finish_reason in finish_reasons or event.get("type") == "done"


class BaseToolsAdapter(IToolsAdapter):
    """工具处理适配器基类
    
    提供工具调用处理的通用实现。
    """
    
    def __init__(self) -> None:
        """初始化工具适配器"""
        self.logger = get_logger(__name__)
    
    def validate_tools(self, tools: List[Dict[str, Any]], context: Optional[IConversionContext] = None) -> List[str]:
        """验证工具定义（通用方法）"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("工具必须是列表格式")
            return errors
        
        if len(tools) > self._get_max_tools_limit():
            errors.append(f"工具数量不能超过{self._get_max_tools_limit()}个")
        
        tool_names = set()
        
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_tool(tool, i, tool_names)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_tool(
        self, 
        tool: Dict[str, Any], 
        index: int, 
        existing_names: set
    ) -> List[str]:
        """验证单个工具（通用方法）"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"工具 {index} 必须是字典")
            return errors
        
        # 验证名称
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"工具 {index} 缺少有效的名称")
        elif name in existing_names:
            errors.append(f"工具 {index} 的名称 '{name}' 已存在")
        else:
            existing_names.add(name)
        
        # 验证描述
        description = tool.get("description", "")
        if not isinstance(description, str):
            errors.append(f"工具 {index} 的描述必须是字符串")
        
        # 验证参数
        if "parameters" in tool:
            parameters = tool["parameters"]
            if not isinstance(parameters, dict):
                errors.append(f"工具 {index} 的参数必须是字典")
            else:
                param_errors = self._validate_parameters(parameters, index)
                errors.extend(param_errors)
        
        return errors
    
    def _validate_parameters(self, parameters: Dict[str, Any], tool_index: int) -> List[str]:
        """验证工具参数（通用方法）"""
        errors = []
        
        # 验证类型
        param_type = parameters.get("type")
        if param_type != "object":
            errors.append(f"工具 {tool_index} 的参数类型必须是object")
        
        # 验证properties
        properties = parameters.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"工具 {tool_index} 的properties必须是字典")
        else:
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    errors.append(f"工具 {tool_index} 的属性 '{prop_name}' schema必须是字典")
                    continue
                
                if "type" not in prop_schema:
                    errors.append(f"工具 {tool_index} 的属性 '{prop_name}' 缺少type字段")
        
        # 验证required
        required = parameters.get("required", [])
        if not isinstance(required, list):
            errors.append(f"工具 {tool_index} 的required必须是列表")
        else:
            for req_name in required:
                if req_name not in properties:
                    errors.append(f"工具 {tool_index} 的required字段 '{req_name}' 不在properties中")
        
        return errors
    
    def _extract_single_tool_call(self, tool_call_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取单个工具调用（基础实现，子类可重写）"""
        try:
            tool_call = {
                "id": tool_call_item.get("id", ""),
                "type": "function",
                "function": {
                    "name": tool_call_item.get("name", ""),
                    "arguments": tool_call_item.get("input", tool_call_item.get("arguments", {}))
                }
            }
            
            # 验证必需字段
            if not tool_call["id"]:
                self.logger.warning("工具调用缺少ID")
                return None
            
            if not tool_call["function"]["name"]:
                self.logger.warning("工具调用缺少名称")
                return None
            
            return tool_call
        except Exception as e:
            self.logger.error(f"提取工具调用失败: {e}")
            return None
    
    def create_tool_result_content(
        self, 
        tool_use_id: str, 
        result: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建工具结果内容（基础实现，子类可重写）"""
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result if isinstance(result, str) else str(result)
        }
    
    def get_tool_names(self, tools: List[Dict[str, Any]]) -> List[str]:
        """获取工具名称列表（通用方法）"""
        names = []
        for tool in tools:
            if isinstance(tool, dict) and "name" in tool:
                names.append(tool["name"])
        return names
    
    def _convert_parameters_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换参数schema（通用方法）"""
        # 基础实现，大部分API使用JSON Schema格式
        schema = {
            "type": parameters.get("type", "object"),
            "properties": parameters.get("properties", {}),
            "required": parameters.get("required", [])
        }
        
        # 添加其他可选字段
        optional_fields = [
            "additionalProperties", "description", "format", "items",
            "maximum", "minimum", "maxLength", "minLength", "pattern",
            "enum", "const", "default", "examples", "title"
        ]
        
        for field in optional_fields:
            if field in parameters:
                schema[field] = parameters[field]
        
        return schema
    
    def _get_max_tools_limit(self) -> int:
        """获取最大工具数量限制（基础实现，子类可重写）"""
        return 100  # 默认限制
    
    def _process_tool_choice_dict(self, tool_choice: Dict[str, Any]) -> Any:
        """处理字典格式的工具选择策略（基础实现，子类可重写）"""
        choice_type = tool_choice.get("type")
        
        if choice_type == "any":
            return {"type": "any"}
        elif choice_type == "tool":
            tool_name = tool_choice.get("name")
            if not tool_name:
                self.logger.warning("tool类型的选择策略缺少name字段")
                return "auto"
            return {"type": "tool", "name": tool_name}
        else:
            self.logger.warning(f"不支持的工具选择类型: {choice_type}")
            return "auto"
    
    def _convert_single_tool(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换单个工具（基础实现，子类可重写）"""
        if not isinstance(tool, dict) or "name" not in tool:
            self.logger.warning(f"无效的工具定义: {tool}")
            return None
        
        converted_tool = {
            "name": tool["name"],
            "description": tool.get("description", "")
        }
        
        # 处理参数schema
        if "parameters" in tool:
            parameters = tool["parameters"]
            if isinstance(parameters, dict):
                converted_tool["parameters"] = self._convert_parameters_schema(parameters)
            else:
                self.logger.warning(f"工具 {tool['name']} 的参数格式无效")
                return None
        
        return converted_tool


class BaseValidationAdapter(IValidationAdapter):
    """验证适配器基类
    
    提供参数验证的通用实现。
    """
    
    def __init__(self) -> None:
        """初始化验证适配器"""
        self.logger = get_logger(__name__)
        # 使用统一的验证工具
        from ..common.validation_utils import validation_utils
        self.validation_utils = validation_utils
    
    def validate_request_parameters(self, parameters: Dict[str, Any], context: Optional[IConversionContext] = None) -> List[str]:
        """验证请求参数"""
        return self.validation_utils.validate_request_parameters(parameters)
    
    def validate_response(self, response: Dict[str, Any], context: Optional[IConversionContext] = None) -> List[str]:
        """验证响应格式"""
        return self.validation_utils.validate_response(response)
    
    def handle_api_error(self, error_response: Dict[str, Any], context: Optional[IConversionContext] = None) -> str:
        """处理API错误响应"""
        return self.validation_utils.handle_api_error(error_response)