"""OpenAI Responses API工具处理工具类

提供OpenAI Responses API的工具使用处理功能。
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger
from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils


class OpenAIResponsesToolsUtils(BaseToolsUtils):
    """OpenAI Responses API工具处理工具类
    
    提供OpenAI Responses API特定的工具使用处理功能。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI Responses API工具工具"""
        super().__init__()
        self._max_tools_limit = 128  # 假设的限制
    
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将工具转换为OpenAI Responses API格式"""
        responses_tools = []
        
        for tool in tools:
            responses_tool = self._convert_single_tool_to_responses_format(tool)
            if responses_tool:
                responses_tools.append(responses_tool)
        
        return responses_tools
    
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Any:
        """处理工具选择策略（Responses API简化了工具选择）"""
        # Responses API的工具选择策略相对简化
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
        """从OpenAI Responses API响应中提取工具调用"""
        tool_calls: List[Dict[str, Any]] = []
        
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
    
    def _convert_single_tool_to_responses_format(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换单个工具为OpenAI Responses API格式"""
        if not isinstance(tool, dict):
            self.logger.warning(f"工具定义必须是字典: {tool}")
            return None
        
        # Responses API工具格式（简化版）
        responses_tool = {
            "type": "custom"
        }
        
        # 处理工具名称
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            self.logger.warning("工具缺少有效的名称")
            return None
        
        responses_tool["name"] = name.strip()
        
        # 处理工具描述
        description = tool.get("description", "")
        if description:
            responses_tool["description"] = str(description)
        
        # Responses API的工具格式相对简化，不包含详细的参数schema
        # 参数信息通过其他方式传递或由模型推断
        
        return responses_tool
    
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
        """从OpenAI Responses API响应中提取单个工具调用"""
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
                    import json
                    json_module = json  # Avoid unbound variable warning
                    arguments = json_module.loads(arguments_str)
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
        """创建工具结果内容（OpenAI Responses API格式）"""
        # Responses API使用字符串格式的工具结果
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
        
        tool_names: set[str] = set()
        
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_responses_tool(tool, i, tool_names)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_responses_tool(
        self, 
        tool: Dict[str, Any], 
        index: int, 
        existing_names: set
    ) -> List[str]:
        """验证单个OpenAI Responses API工具"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"工具 {index} 必须是字典")
            return errors
        
        # 验证type字段
        tool_type = tool.get("type")
        if tool_type != "custom":
            errors.append(f"工具 {index} 的type必须是'custom'")
        
        # 验证name字段
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"工具 {index} 的name必须是非空字符串")
        elif name in existing_names:
            errors.append(f"工具 {index} 的name '{name}' 已存在")
        else:
            existing_names.add(name)
        
        # 验证description字段
        description = tool.get("description")
        if description is not None and not isinstance(description, str):
            errors.append(f"工具 {index} 的description必须是字符串")
        
        # 验证其他字段（Responses API工具格式相对简化）
        allowed_fields = ["type", "name", "description"]
        for field in tool.keys():
            if field not in allowed_fields:
                errors.append(f"工具 {index} 不支持字段: {field}")
        
        return errors
    
    def _get_max_tools_limit(self) -> int:
        """获取最大工具数量限制"""
        return self._max_tools_limit
    
    def convert_from_openai_format(self, openai_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从OpenAI格式转换为Responses API格式"""
        responses_tools = []
        
        for openai_tool in openai_tools:
            if not isinstance(openai_tool, dict):
                continue
            
            # 提取function信息
            function = openai_tool.get("function", {})
            if not isinstance(function, dict):
                continue
            
            name = function.get("name")
            description = function.get("description", "")
            
            if name:
                responses_tool = {
                    "type": "custom",
                    "name": name,
                    "description": description
                }
                responses_tools.append(responses_tool)
        
        return responses_tools
    
    def convert_to_openai_format(self, responses_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从Responses API格式转换为OpenAI格式"""
        openai_tools = []
        
        for responses_tool in responses_tools:
            if not isinstance(responses_tool, dict):
                continue
            
            name = responses_tool.get("name")
            description = responses_tool.get("description", "")
            
            if name:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                openai_tools.append(openai_tool)
        
        return openai_tools
    
    def create_tool_call_from_name(
        self, 
        function_name: str, 
        arguments: Dict[str, Any],
        call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """从函数名称创建工具调用"""
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
    
    def extract_tool_name_from_call(self, tool_call: Dict[str, Any]) -> Optional[str]:
        """从工具调用中提取函数名称"""
        if not isinstance(tool_call, dict):
            return None
        
        function = tool_call.get("function", {})
        name = function.get("name")
        return name if isinstance(name, str) else None
    
    def extract_tool_arguments_from_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """从工具调用中提取函数参数"""
        if not isinstance(tool_call, dict):
            return {}
        
        function = tool_call.get("function", {})
        arguments = function.get("arguments", {})
        
        if isinstance(arguments, dict):
            return arguments
        else:
            return {}
    
    def format_tool_for_logging(self, tool: Dict[str, Any]) -> str:
        """格式化工具用于日志记录"""
        if not isinstance(tool, dict):
            return str(tool)
        
        name = tool.get("name", "unknown")
        description = tool.get("description", "")
        
        return f"ResponsesTool(name={name}, description={description[:50]}...)"
    
    def format_tool_call_for_logging(self, tool_call: Dict[str, Any]) -> str:
        """格式化工具调用用于日志记录"""
        if not isinstance(tool_call, dict):
            return str(tool_call)
        
        call_id = tool_call.get("id", "unknown")
        function = tool_call.get("function", {})
        function_name = function.get("name", "unknown")
        arguments = function.get("arguments", {})
        
        return f"ResponsesToolCall(id={call_id}, function={function_name}, arguments={arguments})"
    
    def merge_tool_definitions(self, tools_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """合并多个工具定义列表"""
        merged_tools = []
        seen_names = set()
        
        for tools in tools_list:
            if not isinstance(tools, list):
                continue
            
            for tool in tools:
                if not isinstance(tool, dict):
                    continue
                
                name = tool.get("name")
                if name and name not in seen_names:
                    merged_tools.append(tool)
                    seen_names.add(name)
        
        return merged_tools
    
    def filter_tools_by_name(self, tools: List[Dict[str, Any]], function_names: List[str]) -> List[Dict[str, Any]]:
        """按函数名称过滤工具"""
        filtered_tools = []
        name_set = set(function_names)
        
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name")
            if name in name_set:
                filtered_tools.append(tool)
        
        return filtered_tools
    
    def get_tool_names(self, tools: List[Dict[str, Any]]) -> List[str]:
        """获取工具名称列表"""
        names = []
        for tool in tools:
            if isinstance(tool, dict) and "name" in tool:
                names.append(tool["name"])
        return names