"""通用验证器

提供跨提供商的通用验证功能。
"""

import re
from typing import Dict, Any, List, Optional, Union, Set
from src.services.logger import get_logger


class CommonValidators:
    """通用验证器类"""
    
    def __init__(self) -> None:
        """初始化通用验证器"""
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
    def validate_email(email: str, field_name: str = "邮箱") -> List[str]:
        """验证邮箱格式
        
        Args:
            email: 邮箱地址
            field_name: 字段名称
            
        Returns:
            List[str]: 验证错误列表
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return CommonValidators.validate_regex(
            email, 
            field_name, 
            email_pattern, 
            "必须是有效的邮箱地址"
        )
    
    @staticmethod
    def validate_url(url: str, field_name: str = "URL") -> List[str]:
        """验证URL格式
        
        Args:
            url: URL地址
            field_name: 字段名称
            
        Returns:
            List[str]: 验证错误列表
        """
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return CommonValidators.validate_regex(
            url, 
            field_name, 
            url_pattern, 
            "必须是有效的URL地址"
        )
    
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
    
    @staticmethod
    def validate_json_schema(value: Dict[str, Any], schema: Dict[str, Any], field_name: str = "数据") -> List[str]:
        """验证JSON Schema（简化版本）
        
        Args:
            value: 要验证的值
            schema: JSON Schema
            field_name: 字段名称
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查类型
        expected_type = schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"{field_name}必须是字符串")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"{field_name}必须是数字")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"{field_name}必须是整数")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{field_name}必须是布尔值")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"{field_name}必须是数组")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"{field_name}必须是对象")
        
        # 检查枚举值
        if "enum" in schema:
            enum_errors = CommonValidators.validate_enum(value, field_name, set(schema["enum"]))
            errors.extend(enum_errors)
        
        # 检查数值范围
        if isinstance(value, (int, float)):
            if "minimum" in schema:
                range_errors = CommonValidators.validate_numeric_range(value, field_name, schema["minimum"], None)
                errors.extend(range_errors)
            if "maximum" in schema:
                range_errors = CommonValidators.validate_numeric_range(value, field_name, None, schema["maximum"])
                errors.extend(range_errors)
        
        # 检查字符串长度
        if isinstance(value, str):
            if "minLength" in schema:
                length_errors = CommonValidators.validate_string_length(value, field_name, schema["minLength"], None)
                errors.extend(length_errors)
            if "maxLength" in schema:
                length_errors = CommonValidators.validate_string_length(value, field_name, None, schema["maxLength"])
                errors.extend(length_errors)
        
        # 检查数组长度
        if isinstance(value, list):
            if "minItems" in schema:
                length_errors = CommonValidators.validate_list_length(value, field_name, schema["minItems"], None)
                errors.extend(length_errors)
            if "maxItems" in schema:
                length_errors = CommonValidators.validate_list_length(value, field_name, None, schema["maxItems"])
                errors.extend(length_errors)
        
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