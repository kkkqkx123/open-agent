"""Gemini工具使用处理工具

专门处理Gemini API的工具使用功能，包括工具定义、工具选择策略等。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger
from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils


class GeminiToolsUtils(BaseToolsUtils):
    """Gemini工具使用处理工具类"""
    
    def __init__(self) -> None:
        """初始化工具使用工具"""
        super().__init__()
    
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将工具转换为Gemini格式
        
        Args:
            tools: 标准格式的工具列表
            
        Returns:
            List[Dict[str, Any]]: Gemini格式的工具列表
        """
        gemini_tools = []
        
        for tool in tools:
            try:
                gemini_tool = self._convert_single_tool(tool)
                if gemini_tool:
                    gemini_tools.append(gemini_tool)
            except Exception as e:
                self.logger.error(f"转换工具失败: {tool}, 错误: {e}")
                continue
        
        return gemini_tools
    
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Any:
        """处理工具选择策略
        
        Args:
            tool_choice: 工具选择策略
            
        Returns:
            Any: Gemini格式的tool_choice
        """
        # Gemini使用tool_config而不是tool_choice
        if tool_choice == "auto" or tool_choice is None:
            return {"function_calling_config": {"mode": "AUTO"}}
        elif tool_choice == "none":
            return {"function_calling_config": {"mode": "NONE"}}
        elif isinstance(tool_choice, dict):
            return self._process_tool_config_dict(tool_choice)
        else:
            self.logger.warning(f"不支持的工具选择策略: {tool_choice}")
            return {"function_calling_config": {"mode": "AUTO"}}
    
    def extract_tool_calls_from_response(self, response: Any) -> List[Dict[str, Any]]:
        """从响应中提取工具调用
        
        Args:
            response: Gemini响应内容
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        tool_calls = []
        
        if isinstance(response, list):
            for item in response:
                if isinstance(item, dict) and "functionCall" in item:
                    tool_call = self._extract_single_tool_call(item)
                    if tool_call:
                        tool_calls.append(tool_call)
        elif isinstance(response, dict):
            if "functionCall" in response:
                tool_call = self._extract_single_tool_call(response)
                if tool_call:
                    tool_calls.append(tool_call)
        
        return tool_calls
    
    def _convert_single_tool(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换单个工具"""
        if not isinstance(tool, dict) or "name" not in tool:
            self.logger.warning(f"无效的工具定义: {tool}")
            return None
        
        gemini_tool = {
            "function_declarations": [
                {
                    "name": tool["name"],
                    "description": tool.get("description", "")
                }
            ]
        }
        
        # 处理参数schema
        if "parameters" in tool:
            parameters = tool["parameters"]
            if isinstance(parameters, dict):
                gemini_tool["function_declarations"][0]["parameters"] = self._convert_parameters_schema(parameters)
            else:
                self.logger.warning(f"工具 {tool['name']} 的参数格式无效")
                return None
        
        return gemini_tool
    
    def _convert_parameters_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换参数schema为Gemini格式"""
        # Gemini使用JSON Schema格式，大部分情况下可以直接使用
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
    
    def _process_tool_config_dict(self, tool_choice: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典格式的工具选择策略"""
        choice_type = tool_choice.get("type")
        
        if choice_type == "any":
            return {"function_calling_config": {"mode": "ANY"}}
        elif choice_type == "tool":
            tool_name = tool_choice.get("name")
            if not tool_name:
                self.logger.warning("tool类型的选择策略缺少name字段")
                return {"function_calling_config": {"mode": "AUTO"}}
            return {
                "function_calling_config": {
                    "mode": "ANY",
                    "allowed_function_names": [tool_name]
                }
            }
        else:
            self.logger.warning(f"不支持的工具选择类型: {choice_type}")
            return {"function_calling_config": {"mode": "AUTO"}}
    
    def _extract_single_tool_call(self, tool_call_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取单个工具调用"""
        try:
            function_call = tool_call_item.get("functionCall", {})
            
            tool_call = {
                "id": f"call_{hash(str(function_call))}",  # Gemini不提供ID，生成一个
                "type": "function",
                "function": {
                    "name": function_call.get("name", ""),
                    "arguments": function_call.get("args", {})
                }
            }
            
            # 验证必需字段
            if not tool_call["function"]["name"]:
                self.logger.warning("工具调用缺少名称")
                return None
            
            return tool_call
        except Exception as e:
            self.logger.error(f"提取工具调用失败: {e}")
            return None
    
    def create_tool_response_content(
        self, 
        tool_use_id: str, 
        result: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建工具结果内容
        
        Args:
            tool_use_id: 工具使用ID
            result: 工具执行结果
            
        Returns:
            Dict[str, Any]: 工具结果内容
        """
        return {
            "functionResponse": {
                "name": tool_use_id.replace("call_", ""),  # 移除前缀获取函数名
                "response": {
                    "result": result if isinstance(result, (str, int, float, bool, dict, list)) else str(result)
                }
            }
        }
    
    def process_tool_config(self, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理工具配置
        
        Args:
            parameters: 请求参数
            
        Returns:
            Optional[Dict[str, Any]]: 工具配置
        """
        if "tool_choice" in parameters:
            return self.process_tool_choice(parameters["tool_choice"])
        
        return None
    
    def _get_max_tools_limit(self) -> int:
        """获取最大工具数量限制"""
        return 128  # Gemini支持更多工具
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证工具定义"""
        errors = super().validate_tools(tools)
        
        # Gemini特定验证
        for i, tool in enumerate(tools):
            if isinstance(tool, dict) and "name" in tool:
                name = tool["name"]
                # Gemini工具名称限制
                if not name.replace("_", "").replace("-", "").isalnum():
                    errors.append(f"工具 {i} 的名称 '{name}' 只能包含字母、数字、下划线和连字符")
                
                # 长度限制
                if len(name) > 64:
                    errors.append(f"工具 {i} 的名称 '{name}' 长度不能超过64个字符")
        
        return errors
    
    def convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为Gemini格式（兼容性方法）"""
        return self.convert_tools_to_provider_format(tools)