"""业务验证器

提供配置的业务逻辑验证，处理复杂的业务规则和跨模块验证。
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from src.interfaces.config.validation import IValidationContext, IBusinessValidator
from src.interfaces.common_domain import IValidationResult
from src.infrastructure.validation.result import ValidationResult


class BaseBusinessValidator(ABC, IBusinessValidator):
    """业务验证器基类"""
    
    def __init__(self, config_type: str):
        """初始化业务验证器
        
        Args:
            config_type: 配置类型
        """
        self.config_type = config_type
    
    def validate(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """执行业务验证
        
        Args:
            config: 配置数据
            context: 验证上下文
            
        Returns:
            验证结果
        """
        return self.validate_with_context(config, context)
    
    @abstractmethod
    def validate_with_context(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """带上下文的业务验证
        
        Args:
            config: 配置数据
            context: 验证上下文
            
        Returns:
            验证结果
        """
        pass
    
    def _validate_cross_module_dependencies(self, config: Dict[str, Any], 
                                           context: IValidationContext,
                                           result: ValidationResult) -> None:
        """验证跨模块依赖
        
        Args:
            config: 配置数据
            context: 验证上下文
            result: 验证结果
        """
        if not context.enable_cross_module_validation:
            return
        
        # 子类可以重写此方法实现具体的跨模块验证逻辑
        pass


class GlobalConfigBusinessValidator(BaseBusinessValidator):
    """全局配置业务验证器"""
    
    def __init__(self):
        super().__init__("global")
    
    def validate_with_context(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """验证全局配置的业务逻辑"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # 验证环境特定配置
        self._validate_environment_config(config, context, result)
        
        # 验证日志配置一致性
        self._validate_log_consistency(config, context, result)
        
        # 验证跨模块依赖
        self._validate_cross_module_dependencies(config, context, result)
        
        return result
    
    def _validate_environment_config(self, config: Dict[str, Any], 
                                   context: IValidationContext,
                                   result: ValidationResult) -> None:
        """验证环境特定配置"""
        env = config.get("env", "development")
        
        if env == "production":
            # 生产环境特定验证
            if config.get("debug"):
                result.add_warning("生产环境不建议启用调试模式")
            
            # 检查日志级别
            log_level = config.get("log_level", "INFO")
            if log_level.upper() == "DEBUG":
                result.add_warning("生产环境不建议使用DEBUG日志级别")
        
        elif env == "development":
            # 开发环境特定验证
            if not config.get("debug"):
                result.add_info("开发环境建议启用调试模式")
    
    def _validate_log_consistency(self, config: Dict[str, Any], 
                                context: IValidationContext,
                                result: ValidationResult) -> None:
        """验证日志配置一致性"""
        log_level = config.get("log_level", "INFO")
        log_outputs = config.get("log_outputs", [])
        
        # 检查日志输出配置与日志级别的一致性
        if log_level.upper() == "DEBUG" and not log_outputs:
            result.add_warning("DEBUG日志级别建议配置至少一个日志输出")
        
        # 检查文件日志输出
        for output in log_outputs:
            if output.get("type") == "file":
                log_format = output.get("format", "text")
                if log_format == "json" and log_level.upper() == "DEBUG":
                    result.add_info("JSON格式的DEBUG日志可能产生大量输出")


class LLMConfigBusinessValidator(BaseBusinessValidator):
    """LLM配置业务验证器"""
    
    def __init__(self):
        super().__init__("llm")
    
    def validate_with_context(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """验证LLM配置的业务逻辑"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # 验证模型配置一致性
        self._validate_model_consistency(config, context, result)
        
        # 验证性能配置
        self._validate_performance_config(config, context, result)
        
        # 验证跨模块依赖
        self._validate_cross_module_dependencies(config, context, result)
        
        return result
    
    def _validate_model_consistency(self, config: Dict[str, Any], 
                                  context: IValidationContext,
                                  result: ValidationResult) -> None:
        """验证模型配置一致性"""
        model_type = config.get("model_type")
        model_name = config.get("model_name")
        base_url = config.get("base_url")
        
        # 检查模型类型和名称的一致性
        if model_type and model_name:
            if model_type == "openai" and base_url and "api.openai.com" not in base_url:
                result.add_warning("OpenAI模型使用了非官方API端点")
            elif model_type == "anthropic" and not base_url:
                result.add_warning("Anthropic模型建议配置自定义API端点")
    
    def _validate_performance_config(self, config: Dict[str, Any], 
                                   context: IValidationContext,
                                   result: ValidationResult) -> None:
        """验证性能配置"""
        retry_config = config.get("retry_config", {})
        timeout_config = config.get("timeout_config", {})
        
        # 检查重试和超时配置的合理性
        if retry_config and timeout_config:
            max_retries = retry_config.get("max_retries", 3)
            request_timeout = timeout_config.get("request_timeout", 60)
            
            # 估算最大等待时间
            base_delay = retry_config.get("base_delay", 1)
            exponential_base = retry_config.get("exponential_base", 2)
            
            if max_retries > 5:
                result.add_warning("重试次数过多可能导致请求延迟")
            
            if request_timeout < 30:
                result.add_warning("请求超时时间过短可能导致频繁失败")
    
    def _validate_cross_module_dependencies(self, config: Dict[str, Any], 
                                           context: IValidationContext,
                                           result: ValidationResult) -> None:
        """验证跨模块依赖"""
        # 检查与token_counter配置的兼容性
        token_counter_config = context.get_dependency("token_counter")
        if token_counter_config:
            model_type = config.get("model_type")
            counter_model_type = token_counter_config.get("model_type")
            
            if model_type and counter_model_type and model_type != counter_model_type:
                result.add_warning(f"LLM模型类型({model_type})与Token计数器模型类型({counter_model_type})不匹配")


class ToolConfigBusinessValidator(BaseBusinessValidator):
    """工具配置业务验证器"""
    
    def __init__(self):
        super().__init__("tool")
    
    def validate_with_context(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """验证工具配置的业务逻辑"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # 验证工具集配置
        self._validate_tool_sets(config, context, result)
        
        # 验证工具依赖
        self._validate_tool_dependencies(config, context, result)
        
        # 验证跨模块依赖
        self._validate_cross_module_dependencies(config, context, result)
        
        return result
    
    def _validate_tool_sets(self, config: Dict[str, Any], 
                          context: IValidationContext,
                          result: ValidationResult) -> None:
        """验证工具集配置"""
        tools = config.get("tools", [])
        
        if not tools:
            result.add_warning("未配置任何工具")
            return
        
        # 检查工具重复
        tool_names = [tool.get("name") for tool in tools if tool.get("name")]
        duplicate_names = [name for name in set(tool_names) if tool_names.count(name) > 1]
        
        if duplicate_names:
            result.add_error(f"发现重复的工具名称: {', '.join(duplicate_names)}")
    
    def _validate_tool_dependencies(self, config: Dict[str, Any], 
                                  context: IValidationContext,
                                  result: ValidationResult) -> None:
        """验证工具依赖"""
        tools = config.get("tools", [])
        
        for tool in tools:
            tool_type = tool.get("type")
            
            # 检查MCP工具的依赖
            if tool_type == "mcp":
                server_config = tool.get("server_config", {})
                if not server_config.get("server_name"):
                    result.add_error(f"MCP工具 {tool.get('name')} 缺少服务器配置")
            
            # 检查REST工具的依赖
            elif tool_type == "rest":
                api_config = tool.get("api_config", {})
                if not api_config.get("base_url"):
                    result.add_error(f"REST工具 {tool.get('name')} 缺少API基础URL")


class TokenCounterConfigBusinessValidator(BaseBusinessValidator):
    """Token计数器配置业务验证器"""
    
    def __init__(self):
        super().__init__("token_counter")
    
    def validate_with_context(self, config: Dict[str, Any], context: IValidationContext) -> ValidationResult:
        """验证Token计数器配置的业务逻辑"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # 验证缓存配置
        self._validate_cache_config(config, context, result)
        
        # 验证校准配置
        self._validate_calibration_config(config, context, result)
        
        # 验证跨模块依赖
        self._validate_cross_module_dependencies(config, context, result)
        
        return result
    
    def _validate_cache_config(self, config: Dict[str, Any], 
                             context: IValidationContext,
                             result: ValidationResult) -> None:
        """验证缓存配置"""
        cache_config = config.get("cache", {})
        enhanced = config.get("enhanced", False)
        
        if enhanced and not cache_config:
            result.add_warning("增强模式建议配置缓存")
            return
        
        if cache_config:
            cache_type = cache_config.get("type")
            if cache_type == "redis":
                # 检查Redis配置
                if not cache_config.get("host"):
                    result.add_error("Redis缓存缺少主机配置")
                if not cache_config.get("port"):
                    result.add_warning("Redis缓存未指定端口，将使用默认端口")
    
    def _validate_calibration_config(self, config: Dict[str, Any], 
                                   context: IValidationContext,
                                   result: ValidationResult) -> None:
        """验证校准配置"""
        calibration_config = config.get("calibration", {})
        enhanced = config.get("enhanced", False)
        
        if enhanced and not calibration_config:
            result.add_warning("增强模式建议配置校准")
            return
        
        if calibration_config:
            # 检查校准数据源
            data_source = calibration_config.get("data_source")
            if not data_source:
                result.add_warning("校准配置未指定数据源")
            
            # 检查校准频率
            frequency = calibration_config.get("frequency")
            if frequency and frequency < 3600:  # 小于1小时
                result.add_warning("校准频率过高可能影响性能")
    
    def _validate_cross_module_dependencies(self, config: Dict[str, Any], 
                                           context: IValidationContext,
                                           result: ValidationResult) -> None:
        """验证跨模块依赖"""
        # 检查与LLM配置的兼容性
        llm_config = context.get_dependency("llm")
        if llm_config:
            model_type = config.get("model_type")
            llm_model_type = llm_config.get("model_type")
            
            if model_type and llm_model_type and model_type != llm_model_type:
                result.add_warning(f"Token计数器模型类型({model_type})与LLM模型类型({llm_model_type})不匹配")