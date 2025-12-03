"""Anthropic工具使用处理工具

专门处理Anthropic API的工具使用功能，包括工具定义、工具选择策略等。
"""

from typing import Dict, Any, List, Optional, Union, Literal
from src.services.logger import get_logger


class AnthropicToolsUtils:
    """Anthropic工具使用处理工具类"""
    
    def __init__(self) -> None:
        """初始化工具使用工具"""
        self.logger = get_logger(__name__)
    
    def convert_tools_to_anthropic_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将工具转换为Anthropic格式
        
        Args:
            tools: 标准格式的工具列表
            
        Returns:
            List[Dict[str, Any]]: Anthropic格式的工具列表
        """
        anthropic_tools = []
        
        for tool in tools:
            try:
                anthropic_tool = self._convert_single_tool(tool)
                if anthropic_tool:
                    anthropic_tools.append(anthropic_tool)
            except Exception as e:
                self.logger.error(f"转换工具失败: {tool}, 错误: {e}")
                continue
        
        return anthropic_tools
    
    def _convert_single_tool(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换单个工具"""
        if not isinstance(tool, dict) or "name" not in tool:
            self.logger.warning(f"无效的工具定义: {tool}")
            return None
        
        anthropic_tool = {
            "name": tool["name"],
            "description": tool.get("description", "")
        }
        
        # 处理参数schema
        if "parameters" in tool:
            parameters = tool["parameters"]
            if isinstance(parameters, dict):
                anthropic_tool["input_schema"] = self._convert_parameters_schema(parameters)
            else:
                self.logger.warning(f"工具 {tool['name']} 的参数格式无效")
                return None
        
        return anthropic_tool
    
    def _convert_parameters_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换参数schema为Anthropic格式"""
        # Anthropic使用JSON Schema格式，大部分情况下可以直接使用
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
    
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Union[Literal["auto"], Literal["none"], Dict[str, Any]]:
        """处理工具选择策略
        
        Args:
            tool_choice: 工具选择策略
            
        Returns:
            Union[Literal["auto"], Literal["none"], Dict[str, Any]]: Anthropic格式的tool_choice
        """
        if tool_choice == "auto" or tool_choice is None:
            return "auto"
        elif tool_choice == "none":
            return "none"
        elif isinstance(tool_choice, dict):
            return self._process_tool_choice_dict(tool_choice)
        else:
            self.logger.warning(f"不支持的工具选择策略: {tool_choice}")
            return "auto"
    
    def _process_tool_choice_dict(self, tool_choice: Dict[str, Any]) -> Union[Literal["auto"], Dict[str, Any]]:
        """处理字典格式的工具选择策略"""
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
    
    def extract_tool_calls_from_response(self, response_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从响应中提取工具调用
        
        Args:
            response_content: Anthropic响应内容
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        tool_calls = []
        
        for item in response_content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_call = self._extract_single_tool_call(item)
                if tool_call:
                    tool_calls.append(tool_call)
        
        return tool_calls
    
    def _extract_single_tool_call(self, tool_use_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取单个工具调用"""
        try:
            tool_call = {
                "id": tool_use_item.get("id", ""),
                "type": "function",
                "function": {
                    "name": tool_use_item.get("name", ""),
                    "arguments": tool_use_item.get("input", {})
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
        """创建工具结果内容
        
        Args:
            tool_use_id: 工具使用ID
            result: 工具执行结果
            
        Returns:
            Dict[str, Any]: 工具结果内容
        """
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result if isinstance(result, str) else str(result)
        }
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证工具定义
        
        Args:
            tools: 工具列表
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(tools, list):
            errors.append("工具必须是列表格式")
            return errors
        
        if len(tools) > 100:
            errors.append("工具数量不能超过100个")
        
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
        """验证单个工具"""
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
        """验证工具参数"""
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
    
    def get_tool_names(self, tools: List[Dict[str, Any]]) -> List[str]:
        """获取工具名称列表
        
        Args:
            tools: 工具列表
            
        Returns:
            List[str]: 工具名称列表
        """
        names = []
        for tool in tools:
            if isinstance(tool, dict) and "name" in tool:
                names.append(tool["name"])
        return names