"""OpenAI工具处理工具类

提供OpenAI API的工具使用处理功能。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger
from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils


class OpenAIToolsUtils(BaseToolsUtils):
    """OpenAI工具处理工具类
    
    提供OpenAI API特定的工具使用处理功能。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI工具工具"""
        super().__init__()
        self._max_tools_limit = 128  # OpenAI限制
    
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将工具转换为OpenAI格式"""
        openai_tools = []
        
        for tool in tools:
            openai_tool = self._convert_single_tool_to_openai_format(tool)
            if openai_tool:
                openai_tools.append(openai_tool)
        
        return openai_tools
    
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Any:
        """处理工具选择策略"""
        if isinstance(tool_choice, str):
            if tool_choice in ["none", "auto", "required"]:
                return tool_choice
            else:
                self.logger.warning(f"不支持的tool_choice字符串: {tool_choice}")
                return "auto"
        elif isinstance(tool_choice, dict):
            return self._process_tool_choice_dict(tool_choice)
        else:
            self.logger.warning(f"不支持的tool_choice类型: {type(tool_choice)}")
            return "auto"
    
    def extract_tool_calls_from_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从OpenAI响应中提取工具调用"""
        tool_calls = []
        
        try:
            choices = response.get("choices", [])
            if not choices:
                return tool_calls
            
            choice = choices[0]  # 取第一个选择
            message = choice.get("message", {})
            
            # 提取tool_calls
            raw_tool_calls = message.get("tool_calls", [])
            if not isinstance(raw_tool_calls, list):
                return tool_calls
            
            for raw_call in raw_tool_calls:
                tool_call = self._extract_single_tool_call_from_response(raw_call)
                if tool_call:
                    tool_calls.append(tool_call)
        
        except Exception as e:
            self.logger.error(f"提取工具调用失败: {e}")
        
        return tool_calls
    
    def _convert_single_tool_to_openai_format(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换单个工具为OpenAI格式"""
        if not isinstance(tool, dict):
            self.logger.warning(f"工具定义必须是字典: {tool}")
            return None
        
        # OpenAI工具格式
        openai_tool = {
            "type": "function",
            "function": {}
        }
        
        # 处理工具名称
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            self.logger.warning("工具缺少有效的名称")
            return None
        
        openai_tool["function"]["name"] = name.strip()
        
        # 处理工具描述
        description = tool.get("description", "")
        if description:
            openai_tool["function"]["description"] = str(description)
        
        # 处理工具参数
        if "parameters" in tool:
            parameters = tool["parameters"]
            if isinstance(parameters, dict):
                openai_tool["function"]["parameters"] = self._convert_parameters_schema(parameters)
            else:
                self.logger.warning(f"工具 {name} 的参数格式无效")
        
        return openai_tool
    
    def _process_tool_choice_dict(self, tool_choice: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典格式的工具选择策略"""
        choice_type = tool_choice.get("type")
        
        if choice_type == "function":
            function = tool_choice.get("function", {})
            function_name = function.get("name")
            
            if not function_name:
                self.logger.warning("function类型的tool_choice缺少name字段")
                return {"type": "auto"}
            
            return {
                "type": "function",
                "function": {
                    "name": function_name
                }
            }
        else:
            self.logger.warning(f"不支持的tool_choice类型: {choice_type}")
            return {"type": "auto"}
    
    def _extract_single_tool_call_from_response(self, raw_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从OpenAI响应中提取单个工具调用"""
        import json
        try:
            # 验证必需字段
            call_id = raw_call.get("id")
            if not call_id:
                self.logger.warning("工具调用缺少ID")
                return None
            
            function = raw_call.get("function", {})
            function_name = function.get("name")
            if not function_name:
                self.logger.warning("工具调用缺少函数名称")
                return None
            
            # 解析参数
            arguments_str = function.get("arguments", "{}")
            arguments = {}
            
            if arguments_str:
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"工具调用参数解析失败: {e}")
                    arguments = {}
            
            # 构建标准格式的工具调用
            tool_call = {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": function_name,
                    "arguments": arguments
                }
            }
            
            return tool_call
        
        except Exception as e:
            self.logger.error(f"提取单个工具调用失败: {e}")
            return None
    
    def create_tool_result_content(
        self, 
        tool_use_id: str, 
        result: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建工具结果内容（OpenAI格式）"""
        # OpenAI使用字符串格式的工具结果
        if isinstance(result, dict):
            try:
                import json
                result_str = json.dumps(result, ensure_ascii=False)
            except Exception:
                result_str = str(result)
        else:
            result_str = str(result)
        
        return {
            "role": "tool",
            "tool_call_id": tool_use_id,
            "content": result_str
        }
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证工具定义"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("工具必须是列表格式")
            return errors
        
        if len(tools) > self._max_tools_limit:
            errors.append(f"工具数量不能超过{self._max_tools_limit}个")
        
        tool_names = set()
        
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_openai_tool(tool, i, tool_names)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_openai_tool(
        self, 
        tool: Dict[str, Any], 
        index: int, 
        existing_names: set
    ) -> List[str]:
        """验证单个OpenAI工具"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"工具 {index} 必须是字典")
            return errors
        
        # 验证type字段
        tool_type = tool.get("type")
        if tool_type != "function":
            errors.append(f"工具 {index} 的type必须是'function'")
        
        # 验证function字段
        function = tool.get("function")
        if not isinstance(function, dict):
            errors.append(f"工具 {index} 的function必须是字典")
            return errors
        
        # 验证function.name
        name = function.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"工具 {index} 的function.name必须是非空字符串")
        elif name in existing_names:
            errors.append(f"工具 {index} 的function.name '{name}' 已存在")
        else:
            existing_names.add(name)
        
        # 验证function.description
        description = function.get("description")
        if description is not None and not isinstance(description, str):
            errors.append(f"工具 {index} 的function.description必须是字符串")
        
        # 验证function.parameters
        if "parameters" in function:
            parameters = function["parameters"]
            if not isinstance(parameters, dict):
                errors.append(f"工具 {index} 的function.parameters必须是字典")
            else:
                param_errors = self._validate_openai_parameters(parameters, index)
                errors.extend(param_errors)
        
        return errors
    
    def _validate_openai_parameters(self, parameters: Dict[str, Any], tool_index: int) -> List[str]:
        """验证OpenAI工具参数"""
        errors = []
        
        # 验证类型
        param_type = parameters.get("type")
        if param_type != "object":
            errors.append(f"工具 {tool_index} 的function.parameters.type必须是object")
        
        # 验证properties
        properties = parameters.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"工具 {tool_index} 的function.parameters.properties必须是字典")
        else:
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    errors.append(f"工具 {tool_index} 的function.parameters.properties.{prop_name}必须是字典")
                    continue
                
                if "type" not in prop_schema:
                    errors.append(f"工具 {tool_index} 的function.parameters.properties.{prop_name}缺少type字段")
                else:
                    # 验证参数类型
                    prop_type = prop_schema["type"]
                    valid_types = ["string", "number", "integer", "boolean", "array", "object"]
                    if prop_type not in valid_types:
                        errors.append(f"工具 {tool_index} 的function.parameters.properties.{prop_name}.type必须是以下值之一: {', '.join(valid_types)}")
        
        # 验证required
        required = parameters.get("required", [])
        if not isinstance(required, list):
            errors.append(f"工具 {tool_index} 的function.parameters.required必须是列表")
        else:
            for req_name in required:
                if req_name not in properties:
                    errors.append(f"工具 {tool_index} 的function.parameters.required中的'{req_name}'不在properties中")
        
        return errors
    
    def _get_max_tools_limit(self) -> int:
        """获取最大工具数量限制"""
        return self._max_tools_limit
    
    def create_function_call_from_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """从工具调用创建函数调用格式（兼容性方法）"""
        if not isinstance(tool_call, dict):
            return {}
        
        function = tool_call.get("function", {})
        return {
            "name": function.get("name", ""),
            "arguments": function.get("arguments", {})
        }
    
    def extract_function_name_from_tool_call(self, tool_call: Dict[str, Any]) -> Optional[str]:
        """从工具调用中提取函数名称"""
        if not isinstance(tool_call, dict):
            return None
        
        function = tool_call.get("function", {})
        return function.get("name")
    
    def extract_function_arguments_from_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """从工具调用中提取函数参数"""
        if not isinstance(tool_call, dict):
            return {}
        
        function = tool_call.get("function", {})
        arguments = function.get("arguments", {})
        
        if isinstance(arguments, dict):
            return arguments
        else:
            return {}
    
    def format_tool_call_for_logging(self, tool_call: Dict[str, Any]) -> str:
        """格式化工具调用用于日志记录"""
        if not isinstance(tool_call, dict):
            return str(tool_call)
        
        call_id = tool_call.get("id", "unknown")
        function = tool_call.get("function", {})
        function_name = function.get("name", "unknown")
        arguments = function.get("arguments", {})
        
        return f"ToolCall(id={call_id}, function={function_name}, arguments={arguments})"
    
    def create_tool_call_from_function_call(
        self, 
        function_name: str, 
        arguments: Dict[str, Any],
        call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """从函数调用创建工具调用"""
        import uuid
        
        if not call_id:
            call_id = f"call_{uuid.uuid4().hex[:8]}"
        
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": function_name,
                "arguments": arguments
            }
        }
    
    def merge_tool_calls(self, tool_calls_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """合并多个工具调用列表"""
        merged_calls = []
        seen_ids = set()
        
        for calls in tool_calls_list:
            if not isinstance(calls, list):
                continue
            
            for call in calls:
                if not isinstance(call, dict):
                    continue
                
                call_id = call.get("id")
                if call_id and call_id not in seen_ids:
                    merged_calls.append(call)
                    seen_ids.add(call_id)
        
        return merged_calls
    
    def filter_tool_calls_by_name(self, tool_calls: List[Dict[str, Any]], function_names: List[str]) -> List[Dict[str, Any]]:
        """按函数名称过滤工具调用"""
        filtered_calls = []
        name_set = set(function_names)
        
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            
            function = call.get("function", {})
            function_name = function.get("name")
            
            if function_name in name_set:
                filtered_calls.append(call)
        
        return filtered_calls
    
    def count_tool_calls_by_function(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计每个函数的调用次数"""
        counts = {}
        
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            
            function = call.get("function", {})
            function_name = function.get("name", "unknown")
            
            counts[function_name] = counts.get(function_name, 0) + 1
        
        return counts