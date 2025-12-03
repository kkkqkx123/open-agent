"""工具使用基础工具类

定义所有LLM提供商的工具使用处理通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger


class BaseToolsUtils(ABC):
    """工具使用基础工具类
    
    定义工具使用处理的通用接口和基础功能。
    """
    
    def __init__(self) -> None:
        """初始化工具使用工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将工具转换为提供商特定格式
        
        Args:
            tools: 标准格式的工具列表
            
        Returns:
            List[Dict[str, Any]]: 提供商格式的工具列表
        """
        pass
    
    @abstractmethod
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Any:
        """处理工具选择策略
        
        Args:
            tool_choice: 工具选择策略
            
        Returns:
            Any: 提供商格式的tool_choice
        """
        pass
    
    @abstractmethod
    def extract_tool_calls_from_response(self, response: Any) -> List[Dict[str, Any]]:
        """从响应中提取工具调用
        
        Args:
            response: 提供商响应内容
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        pass
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
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