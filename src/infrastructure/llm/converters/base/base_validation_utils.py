"""验证基础工具类

定义所有LLM提供商的验证和错误处理通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from src.services.logger.injection import get_logger


class BaseValidationError(Exception):
    """基础验证错误"""
    pass


class BaseFormatError(Exception):
    """基础格式错误"""
    pass


class BaseValidationUtils(ABC):
    """验证基础工具类
    
    定义验证和错误处理的通用接口和基础功能。
    """
    
    def __init__(self) -> None:
        """初始化验证工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证响应格式
        
        Args:
            response: API响应
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 用户友好的错误消息
        """
        pass
    
    def _validate_required_parameters(self, parameters: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """验证必需参数（通用方法）"""
        errors = []
        
        for field in required_fields:
            if field not in parameters:
                errors.append(f"缺少必需的{field}参数")
        
        return errors
    
    def _validate_parameter_type(self, value: Any, expected_type: type, param_name: str) -> List[str]:
        """验证参数类型（通用方法）"""
        errors = []
        
        if not isinstance(value, expected_type):
            errors.append(f"{param_name}参数必须是{expected_type.__name__}类型")
        
        return errors
    
    def _validate_parameter_range(
        self, 
        value: Union[int, float], 
        min_val: Optional[Union[int, float]], 
        max_val: Optional[Union[int, float]], 
        param_name: str
    ) -> List[str]:
        """验证参数范围（通用方法）"""
        errors = []
        
        if min_val is not None and value < min_val:
            errors.append(f"{param_name}参数不能小于{min_val}")
        
        if max_val is not None and value > max_val:
            errors.append(f"{param_name}参数不能大于{max_val}")
        
        return errors
    
    def _validate_string_length(
        self, 
        value: str, 
        min_length: Optional[int], 
        max_length: Optional[int], 
        param_name: str
    ) -> List[str]:
        """验证字符串长度（通用方法）"""
        errors = []
        
        if min_length is not None and len(value) < min_length:
            errors.append(f"{param_name}参数长度不能小于{min_length}")
        
        if max_length is not None and len(value) > max_length:
            errors.append(f"{param_name}参数长度不能大于{max_length}")
        
        return errors
    
    def _validate_list_length(
        self, 
        value: List[Any], 
        min_length: Optional[int], 
        max_length: Optional[int], 
        param_name: str
    ) -> List[str]:
        """验证列表长度（通用方法）"""
        errors = []
        
        if min_length is not None and len(value) < min_length:
            errors.append(f"{param_name}参数列表长度不能小于{min_length}")
        
        if max_length is not None and len(value) > max_length:
            errors.append(f"{param_name}参数列表长度不能大于{max_length}")
        
        return errors
    
    def _validate_enum_value(self, value: Any, valid_values: List[Any], param_name: str) -> List[str]:
        """验证枚举值（通用方法）"""
        errors = []
        
        if value not in valid_values:
            errors.append(f"{param_name}参数必须是以下值之一: {', '.join(map(str, valid_values))}")
        
        return errors
    
    def _validate_dict_keys(
        self, 
        value: Dict[str, Any], 
        required_keys: Optional[List[str]] = None,
        optional_keys: Optional[List[str]] = None,
        param_name: str = "参数"
    ) -> List[str]:
        """验证字典键（通用方法）"""
        errors = []
        
        if required_keys:
            for key in required_keys:
                if key not in value:
                    errors.append(f"{param_name}缺少必需的键: {key}")
        
        if optional_keys:
            for key in value.keys():
                allowed_keys = (required_keys or []) + optional_keys
                if key not in allowed_keys:
                    errors.append(f"{param_name}包含不支持的键: {key}")
        
        return errors
    
    def _validate_model(self, model: str, supported_models: set) -> List[str]:
        """验证模型参数（通用方法）"""
        errors = []
        
        if not isinstance(model, str):
            errors.append("model参数必须是字符串")
        elif model not in supported_models:
            errors.append(f"不支持的模型: {model}，支持的模型: {', '.join(supported_models)}")
        
        return errors
    
    def _validate_temperature(self, temperature: Union[int, float], min_val: float = 0.0, max_val: float = 2.0) -> List[str]:
        """验证temperature参数（通用方法）"""
        errors = []
        
        if not isinstance(temperature, (int, float)):
            errors.append("temperature参数必须是数字")
        else:
            range_errors = self._validate_parameter_range(temperature, min_val, max_val, "temperature")
            errors.extend(range_errors)
        
        return errors
    
    def _validate_top_p(self, top_p: Union[int, float], min_val: float = 0.0, max_val: float = 1.0) -> List[str]:
        """验证top_p参数（通用方法）"""
        errors = []
        
        if not isinstance(top_p, (int, float)):
            errors.append("top_p参数必须是数字")
        else:
            range_errors = self._validate_parameter_range(top_p, min_val, max_val, "top_p")
            errors.extend(range_errors)
        
        return errors
    
    def _validate_max_tokens(self, max_tokens: int, model: Optional[str] = None, limits: Optional[Dict[str, int]] = None) -> List[str]:
        """验证max_tokens参数（通用方法）"""
        errors = []
        
        if not isinstance(max_tokens, int):
            errors.append("max_tokens参数必须是整数")
        else:
            # 基础范围验证
            range_errors = self._validate_parameter_range(max_tokens, 1, None, "max_tokens")
            errors.extend(range_errors)
            
            # 模型特定限制
            if model and limits and model in limits:
                limit = limits[model]
                if max_tokens > limit:
                    errors.append(f"模型 {model} 的max_tokens不能超过 {limit}")
        
        return errors
    
    def _validate_stop_sequences(self, stop_sequences: List[str], max_count: int = 4) -> List[str]:
        """验证stop_sequences参数（通用方法）"""
        errors = []
        
        if not isinstance(stop_sequences, list):
            errors.append("stop_sequences参数必须是列表")
        else:
            # 验证列表长度
            length_errors = self._validate_list_length(stop_sequences, None, max_count, "stop_sequences")
            errors.extend(length_errors)
            
            # 验证每个序列
            for i, sequence in enumerate(stop_sequences):
                if not isinstance(sequence, str):
                    errors.append(f"stop_sequences[{i}]必须是字符串")
                elif not sequence.strip():
                    errors.append(f"stop_sequences[{i}]不能为空")
        
        return errors
    
    def _validate_tools(self, tools: List[Dict[str, Any]], max_count: int = 100) -> List[str]:
        """验证tools参数（通用方法）"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("tools参数必须是列表")
        else:
            # 验证列表长度
            length_errors = self._validate_list_length(tools, None, max_count, "tools")
            errors.extend(length_errors)
            
            # 验证每个工具
            tool_names = set()
            for i, tool in enumerate(tools):
                tool_errors = self._validate_single_tool(tool, i, tool_names)
                errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_tool(self, tool: Dict[str, Any], index: int, existing_names: set) -> List[str]:
        """验证单个工具（通用方法）"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"tools[{index}]必须是字典")
            return errors
        
        # 验证名称
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"tools[{index}]缺少有效的名称")
        elif name in existing_names:
            errors.append(f"tools[{index}]的名称'{name}'已存在")
        else:
            existing_names.add(name)
        
        # 验证描述
        description = tool.get("description", "")
        if not isinstance(description, str):
            errors.append(f"tools[{index}]的描述必须是字符串")
        
        # 验证参数
        if "parameters" in tool:
            parameters = tool["parameters"]
            if not isinstance(parameters, dict):
                errors.append(f"tools[{index}]的参数必须是字典")
            else:
                param_errors = self._validate_tool_parameters(parameters, index)
                errors.extend(param_errors)
        
        return errors
    
    def _validate_tool_parameters(self, parameters: Dict[str, Any], tool_index: int) -> List[str]:
        """验证工具参数（通用方法）"""
        errors = []
        
        # 验证类型
        param_type = parameters.get("type")
        if param_type != "object":
            errors.append(f"tools[{tool_index}].parameters.type必须是object")
        
        # 验证properties
        properties = parameters.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"tools[{tool_index}].parameters.properties必须是字典")
        else:
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    errors.append(f"tools[{tool_index}].parameters.properties.{prop_name}必须是字典")
                    continue
                
                if "type" not in prop_schema:
                    errors.append(f"tools[{tool_index}].parameters.properties.{prop_name}缺少type字段")
        
        # 验证required
        required = parameters.get("required", [])
        if not isinstance(required, list):
            errors.append(f"tools[{tool_index}].parameters.required必须是列表")
        else:
            for req_name in required:
                if req_name not in properties:
                    errors.append(f"tools[{tool_index}].parameters.required中的'{req_name}'不在properties中")
        
        return errors
    
    def _create_error_mapping(self) -> Dict[str, str]:
        """创建错误类型映射（基础实现，子类可重写）"""
        return {
            "invalid_request_error": "请求参数无效",
            "authentication_error": "认证失败，请检查API密钥",
            "permission_error": "权限不足",
            "not_found_error": "请求的资源不存在",
            "rate_limit_error": "请求频率过高，请稍后重试",
            "api_error": "API内部错误",
            "overloaded_error": "服务过载，请稍后重试"
        }
    
    def _handle_error_with_mapping(self, error_response: Dict[str, Any]) -> str:
        """使用错误映射处理错误（通用方法）"""
        error_type = error_response.get("error", {}).get("type", "unknown")
        error_message = error_response.get("error", {}).get("message", "未知错误")
        
        error_mapping = self._create_error_mapping()
        friendly_message = error_mapping.get(error_type, f"未知错误类型: {error_type}")
        
        return f"{friendly_message}: {error_message}"