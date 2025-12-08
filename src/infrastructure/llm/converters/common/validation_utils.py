"""
统一验证工具类

整合所有验证逻辑，避免代码重复。
"""

import re
from typing import Dict, Any, List, Optional, Union, Set
from src.services.logger.injection import get_logger


class ValidationUtils:
    """统一验证工具类
    
    整合所有验证逻辑，提供统一的验证接口。
    """
    
    def __init__(self) -> None:
        """初始化验证工具"""
        self.logger = get_logger(__name__)
    
    @staticmethod
    def validate_non_empty_string(value: Any, field_name: str) -> List[str]:
        """验证非空字符串
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name}必须是字符串")
        elif not value.strip():
            errors.append(f"{field_name}不能为空")
        
        return errors
    
    @staticmethod
    def validate_string_length(
        value: str, 
        field_name: str, 
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> List[str]:
        """验证字符串长度
        
        Args:
            value: 要验证的字符串
            field_name: 字段名称
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name}必须是字符串")
            return errors
        
        if min_length is not None and len(value) < min_length:
            errors.append(f"{field_name}长度不能小于{min_length}")
        
        if max_length is not None and len(value) > max_length:
            errors.append(f"{field_name}长度不能大于{max_length}")
        
        return errors
    
    @staticmethod
    def validate_numeric_range(
        value: Union[int, float], 
        field_name: str,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> List[str]:
        """验证数值范围
        
        Args:
            value: 要验证的数值
            field_name: 字段名称
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(value, (int, float)):
            errors.append(f"{field_name}必须是数字")
            return errors
        
        if min_value is not None and value < min_value:
            errors.append(f"{field_name}不能小于{min_value}")
        
        if max_value is not None and value > max_value:
            errors.append(f"{field_name}不能大于{max_value}")
        
        return errors
    
    @staticmethod
    def validate_list_length(
        value: List[Any], 
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> List[str]:
        """验证列表长度
        
        Args:
            value: 要验证的列表
            field_name: 字段名称
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(value, list):
            errors.append(f"{field_name}必须是列表")
            return errors
        
        if min_length is not None and len(value) < min_length:
            errors.append(f"{field_name}列表长度不能小于{min_length}")
        
        if max_length is not None and len(value) > max_length:
            errors.append(f"{field_name}列表长度不能大于{max_length}")
        
        return errors
    
    @staticmethod
    def validate_enum(value: Any, field_name: str, valid_values: Set[Any]) -> List[str]:
        """验证枚举值
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            valid_values: 有效值集合
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if value not in valid_values:
            valid_list = ", ".join(str(v) for v in sorted(valid_values))
            errors.append(f"{field_name}必须是以下值之一: {valid_list}")
        
        return errors
    
    @staticmethod
    def validate_regex(value: str, field_name: str, pattern: str, message: Optional[str] = None) -> List[str]:
        """验证正则表达式
        
        Args:
            value: 要验证的字符串
            field_name: 字段名称
            pattern: 正则表达式模式
            message: 自定义错误消息
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name}必须是字符串")
            return errors
        
        if not re.match(pattern, value):
            if message:
                errors.append(f"{field_name}{message}")
            else:
                errors.append(f"{field_name}格式不正确")
        
        return errors
    
    @staticmethod
    def validate_dict_structure(
        value: Dict[str, Any], 
        field_name: str,
        required_keys: Optional[List[str]] = None,
        optional_keys: Optional[List[str]] = None,
        allow_extra_keys: bool = True
    ) -> List[str]:
        """验证字典结构
        
        Args:
            value: 要验证的字典
            field_name: 字段名称
            required_keys: 必需键列表
            optional_keys: 可选键列表
            allow_extra_keys: 是否允许额外键
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(value, dict):
            errors.append(f"{field_name}必须是字典")
            return errors
        
        all_allowed_keys = (required_keys or []) + (optional_keys or [])
        
        # 检查必需键
        if required_keys:
            for key in required_keys:
                if key not in value:
                    errors.append(f"{field_name}缺少必需的键: {key}")
        
        # 检查额外键
        if not allow_extra_keys and all_allowed_keys:
            for key in value.keys():
                if key not in all_allowed_keys:
                    errors.append(f"{field_name}包含不支持的键: {key}")
        
        return errors
    
    def validate_api_key(self, api_key: str, provider: str) -> List[str]:
        """验证API密钥格式
        
        Args:
            api_key: API密钥
            provider: 提供商名称
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 基础验证
        base_errors = self.validate_non_empty_string(api_key, f"{provider} API密钥")
        errors.extend(base_errors)
        
        if errors:
            return errors
        
        # 提供商特定验证
        if provider.lower() == "openai":
            if not api_key.startswith("sk-"):
                errors.append("OpenAI API密钥必须以'sk-'开头")
        elif provider.lower() == "anthropic":
            if not api_key.startswith("sk-ant-"):
                errors.append("Anthropic API密钥必须以'sk-ant-'开头")
        elif provider.lower() == "gemini":
            # Gemini API密钥通常是较长的字母数字字符串
            if len(api_key) < 20:
                errors.append("Gemini API密钥长度不足")
        
        return errors
    
    def validate_model_name(self, model: str, provider: str, supported_models: Set[str]) -> List[str]:
        """验证模型名称
        
        Args:
            model: 模型名称
            provider: 提供商名称
            supported_models: 支持的模型集合
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 基础验证
        base_errors = self.validate_non_empty_string(model, f"{provider}模型名称")
        errors.extend(base_errors)
        
        if errors:
            return errors
        
        # 检查是否在支持列表中
        enum_errors = self.validate_enum(model, f"{provider}模型名称", supported_models)
        errors.extend(enum_errors)
        
        return errors
    
    def validate_request_size(self, messages: List[Dict[str, Any]], max_tokens: int, provider: str) -> List[str]:
        """验证请求大小
        
        Args:
            messages: 消息列表
            max_tokens: 最大token数
            provider: 提供商名称
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 估算token数量（简化版本）
        estimated_tokens = 0
        
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                # 简单估算：4个字符约等于1个token
                estimated_tokens += len(content) // 4
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        estimated_tokens += len(text) // 4
        
        # 检查是否超过限制
        provider_limits = {
            "openai": 128000,  # GPT-4-turbo
            "anthropic": 200000,  # Claude-3
            "gemini": 32768  # Gemini Pro
        }
        
        limit = provider_limits.get(provider.lower(), 4000)
        
        if estimated_tokens > limit:
            errors.append(f"{provider}请求内容过长，估算token数{estimated_tokens}超过限制{limit}")
        
        if max_tokens > limit - estimated_tokens:
            errors.append(f"{provider}max_tokens过大，可能导致总token数超过限制{limit}")
        
        return errors
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(parameters, dict):
            errors.append("请求参数必须是字典")
            return errors
        
        # 验证常见参数
        if "temperature" in parameters:
            temp_errors = self.validate_numeric_range(
                parameters["temperature"], "temperature", 0.0, 2.0
            )
            errors.extend(temp_errors)
        
        if "max_tokens" in parameters:
            max_tokens_errors = self.validate_numeric_range(
                parameters["max_tokens"], "max_tokens", 1, None
            )
            errors.extend(max_tokens_errors)
        
        if "top_p" in parameters:
            top_p_errors = self.validate_numeric_range(
                parameters["top_p"], "top_p", 0.0, 1.0
            )
            errors.extend(top_p_errors)
        
        return errors
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证响应格式
        
        Args:
            response: API响应
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(response, dict):
            errors.append("响应必须是字典")
            return errors
        
        # 检查基本结构
        if "choices" in response:
            if not isinstance(response["choices"], list):
                errors.append("响应的choices字段必须是列表")
        
        if "usage" in response:
            usage = response["usage"]
            if not isinstance(usage, dict):
                errors.append("响应的usage字段必须是字典")
            else:
                # 验证usage字段
                for field in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                    if field in usage and not isinstance(usage[field], int):
                        errors.append(f"usage.{field}必须是整数")
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            error_response: 错误响应
            
        Returns:
            str: 用户友好的错误消息
        """
        error_type = error_response.get("error", {}).get("type", "unknown")
        error_message = error_response.get("error", {}).get("message", "未知错误")
        
        error_mapping = {
            "invalid_request_error": "请求参数无效",
            "authentication_error": "认证失败，请检查API密钥",
            "permission_error": "权限不足",
            "not_found_error": "请求的资源不存在",
            "rate_limit_error": "请求频率过高，请稍后重试",
            "api_error": "API内部错误",
            "overloaded_error": "服务过载，请稍后重试"
        }
        
        friendly_message = error_mapping.get(error_type, f"未知错误类型: {error_type}")
        
        return f"{friendly_message}: {error_message}"


# 创建全局实例
validation_utils = ValidationUtils()