"""Gemini验证工具

专门处理Gemini API的响应和请求验证。
"""

from typing import Dict, Any, List, Optional, Set
from src.services.logger import get_logger


class GeminiValidationError(Exception):
    """Gemini验证错误异常"""
    pass


class GeminiFormatError(Exception):
    """Gemini格式错误异常"""
    pass


class GeminiValidationUtils:
    """Gemini验证工具类"""
    
    def __init__(self) -> None:
        """初始化验证工具"""
        self.logger = get_logger(__name__)
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证Gemini响应
        
        Args:
            response: Gemini响应对象
            
        Returns:
            List[str]: 验证错误列表，为空表示验证通过
        """
        errors = []
        
        if not isinstance(response, dict):
            errors.append("响应必须是字典格式")
            return errors
        
        # 验证必需字段
        if "candidates" not in response:
            errors.append("响应缺少candidates字段")
        else:
            candidates_errors = self._validate_candidates(response["candidates"])
            errors.extend(candidates_errors)
        
        # 验证可选字段
        if "usageMetadata" in response:
            usage_errors = self._validate_usage_metadata(response["usageMetadata"])
            errors.extend(usage_errors)
        
        return errors
    
    def validate_request(self, request: Dict[str, Any]) -> List[str]:
        """验证Gemini请求
        
        Args:
            request: Gemini请求对象
            
        Returns:
            List[str]: 验证错误列表，为空表示验证通过
        """
        errors = []
        
        if not isinstance(request, dict):
            errors.append("请求必须是字典格式")
            return errors
        
        # 验证必需字段
        if "model" not in request:
            errors.append("请求缺少model字段")
        
        if "contents" not in request:
            errors.append("请求缺少contents字段")
        else:
            contents_errors = self._validate_contents(request["contents"])
            errors.extend(contents_errors)
        
        # 验证可选字段
        if "tools" in request:
            tools_errors = self._validate_tools(request["tools"])
            errors.extend(tools_errors)
        
        return errors
    
    def _validate_candidates(self, candidates: Any) -> List[str]:
        """验证候选列表"""
        errors = []
        
        if not isinstance(candidates, list):
            errors.append("candidates必须是列表格式")
            return errors
        
        if not candidates:
            errors.append("candidates不能为空")
            return errors
        
        for i, candidate in enumerate(candidates):
            candidate_errors = self._validate_single_candidate(candidate, i)
            errors.extend(candidate_errors)
        
        return errors
    
    def _validate_single_candidate(self, candidate: Any, index: int) -> List[str]:
        """验证单个候选"""
        errors = []
        
        if not isinstance(candidate, dict):
            errors.append(f"候选 {index} 必须是字典格式")
            return errors
        
        # 验证content
        if "content" not in candidate:
            errors.append(f"候选 {index} 缺少content字段")
        else:
            if not isinstance(candidate["content"], dict):
                errors.append(f"候选 {index} 的content必须是字典")
            elif "parts" not in candidate["content"]:
                errors.append(f"候选 {index} 的content缺少parts字段")
            else:
                if not isinstance(candidate["content"]["parts"], list):
                    errors.append(f"候选 {index} 的parts必须是列表")
        
        # 验证finishReason
        if "finishReason" in candidate:
            finish_reason = candidate["finishReason"]
            valid_reasons = ["STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"]
            if finish_reason not in valid_reasons:
                errors.append(f"候选 {index} 的finishReason值 '{finish_reason}' 无效")
        
        return errors
    
    def _validate_contents(self, contents: Any) -> List[str]:
        """验证内容列表"""
        errors = []
        
        if not isinstance(contents, list):
            errors.append("contents必须是列表格式")
            return errors
        
        if not contents:
            errors.append("contents不能为空")
            return errors
        
        for i, content in enumerate(contents):
            content_errors = self._validate_single_content(content, i)
            errors.extend(content_errors)
        
        return errors
    
    def _validate_single_content(self, content: Any, index: int) -> List[str]:
        """验证单个内容"""
        errors = []
        
        if not isinstance(content, dict):
            errors.append(f"内容 {index} 必须是字典格式")
            return errors
        
        # 验证role
        if "role" not in content:
            errors.append(f"内容 {index} 缺少role字段")
        else:
            role = content["role"]
            valid_roles = ["user", "model"]
            if role not in valid_roles:
                errors.append(f"内容 {index} 的role值 '{role}' 无效，必须是 {valid_roles}")
        
        # 验证parts
        if "parts" not in content:
            errors.append(f"内容 {index} 缺少parts字段")
        else:
            if not isinstance(content["parts"], list):
                errors.append(f"内容 {index} 的parts必须是列表")
        
        return errors
    
    def _validate_usage_metadata(self, metadata: Any) -> List[str]:
        """验证使用元数据"""
        errors = []
        
        if not isinstance(metadata, dict):
            errors.append("usageMetadata必须是字典格式")
            return errors
        
        # 验证字段类型
        for field in ["promptTokenCount", "candidatesTokenCount", "totalTokenCount"]:
            if field in metadata:
                if not isinstance(metadata[field], int):
                    errors.append(f"usageMetadata的 {field} 必须是整数")
        
        return errors
    
    def _validate_tools(self, tools: Any) -> List[str]:
        """验证工具列表"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("tools必须是列表格式")
            return errors
        
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_tool(tool, i)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_tool(self, tool: Any, index: int) -> List[str]:
        """验证单个工具"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"工具 {index} 必须是字典格式")
            return errors
        
        # Gemini工具必须包含function_declarations
        if "function_declarations" not in tool:
            errors.append(f"工具 {index} 缺少function_declarations字段")
        else:
            declarations = tool["function_declarations"]
            if not isinstance(declarations, list):
                errors.append(f"工具 {index} 的function_declarations必须是列表")
        
        return errors
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """验证内容是否合法
        
        Args:
            content: 内容对象
            
        Returns:
            bool: 验证结果
        """
        if not isinstance(content, dict):
            return False
        
        # 至少需要role和parts
        if "role" not in content or "parts" not in content:
            return False
        
        return isinstance(content["parts"], list)
    
    def validate_candidate(self, candidate: Dict[str, Any]) -> bool:
        """验证候选是否合法
        
        Args:
            candidate: 候选对象
            
        Returns:
            bool: 验证结果
        """
        if not isinstance(candidate, dict):
            return False
        
        # 至少需要content
        if "content" not in candidate:
            return False
        
        content = candidate["content"]
        if not isinstance(content, dict) or "parts" not in content:
            return False
        
        return isinstance(content["parts"], list)
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表，为空表示验证通过
        """
        errors = []
        
        # 验证必需参数
        if not isinstance(parameters, dict):
            errors.append("参数必须是字典格式")
            return errors
        
        # 验证可选参数的类型
        if "temperature" in parameters:
            if not isinstance(parameters["temperature"], (int, float)):
                errors.append("temperature必须是数字类型")
            elif not 0 <= parameters["temperature"] <= 2:
                errors.append("temperature必须在0-2之间")
        
        if "max_tokens" in parameters:
            if not isinstance(parameters["max_tokens"], int):
                errors.append("max_tokens必须是整数")
            elif parameters["max_tokens"] <= 0:
                errors.append("max_tokens必须大于0")
        
        if "top_p" in parameters:
            if not isinstance(parameters["top_p"], (int, float)):
                errors.append("top_p必须是数字类型")
            elif not 0 <= parameters["top_p"] <= 1:
                errors.append("top_p必须在0-1之间")
        
        if "top_k" in parameters:
            if not isinstance(parameters["top_k"], int):
                errors.append("top_k必须是整数")
            elif parameters["top_k"] < 0:
                errors.append("top_k必须大于等于0")
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            error_response: API错误响应
            
        Returns:
            str: 格式化的错误信息
        """
        if not isinstance(error_response, dict):
            return "未知API错误"
        
        error = error_response.get("error", {})
        if isinstance(error, dict):
            error_message = error.get("message", "未知错误")
            error_code = error.get("code", "unknown")
            return f"Gemini API错误 ({error_code}): {error_message}"
        else:
            return f"Gemini API错误: {str(error)}"
