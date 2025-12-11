"""配置验证器模块

提供配置验证的基础实现，不依赖核心层。
"""

from typing import Dict, Any, List, Optional, Callable, Protocol
import logging

from src.interfaces.config.validation import ValidationLevel, ValidationSeverity
from .framework import ValidationReport, FrameworkValidationResult
from .base_validator import BaseConfigValidator, IValidationContext

# 导入通用验证器
from src.infrastructure.common.utils.validator import Validator as UtilsValidator
from src.infrastructure.common.utils.validator import ValidationResult as UtilsValidationResult

# 导入基础设施层的配置加载器
from src.infrastructure.config.loader import load_config_file

# 导入接口
from src.interfaces.config import IConfigValidator
from src.interfaces.common_domain import IValidationResult
from src.infrastructure.validation.result import ValidationResult

# 为了兼容性，创建一个别名
UtilsConfigValidationResult = UtilsValidationResult


def generate_cache_key(config_path: str, config_type: str) -> str:
    """生成缓存键
    
    Args:
        config_path: 配置路径
        config_type: 配置类型
        
    Returns:
        缓存键
    """
    return f"{config_path}_{config_type}"


class ICacheManager(Protocol):
    """缓存管理器接口"""
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        ...
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        ...


class ConfigValidator(IConfigValidator):
    """配置验证器
    
    提供基础的配置验证功能，不包含业务逻辑。
    业务逻辑应该通过服务层调用核心层的组件来实现。
    """
    
    def __init__(self, 
                 cache_manager: Optional[ICacheManager] = None, 
                 config_fixer: Optional[Any] = None,
                 logger: Optional[logging.Logger] = None):
        """初始化验证器
        
        Args:
            cache_manager: 缓存管理器
            config_fixer: 配置修复器
            logger: 日志记录器
        """
        self.cache = cache_manager
        self.config_fixer = config_fixer
        self.logger = logger or logging.getLogger(__name__)
        
        # 使用组合方式持有工具验证器实例
        self._utils_validator = UtilsValidator()
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        # 基础验证器支持所有类型，但具体验证逻辑由服务层处理
        return True
    
    def validate(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 创建基础验证结果
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        
        # 基础结构验证
        if not isinstance(config, dict):
            result.add_error("配置必须是字典类型")
            return result
        
        if not config:
            result.add_error("配置不能为空")
            return result
        
        return result
    
    def validate_with_context(self, config: Dict[str, Any], 
                            context: Optional[IValidationContext] = None) -> IValidationResult:
        """带上下文的验证
        
        Args:
            config: 配置字典
            context: 验证上下文
            
        Returns:
            验证结果
        """
        result = self.validate(config)
        
        # 根据上下文调整验证
        if context:
            self._apply_context_validation(config, context, result)
        
        return result
    
    def _apply_context_validation(self, config: Dict[str, Any], 
                                context: IValidationContext, 
                                result: IValidationResult) -> None:
        """应用上下文相关的验证
        
        Args:
            config: 配置字典
            context: 验证上下文
            result: 验证结果
        """
        # 根据环境调整验证严格性
        if context.environment == "production" and context.strict_mode:
            # 生产环境严格模式下的额外检查
            self._validate_production_strict(config, result)
    
    def _validate_production_strict(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """生产环境严格模式验证
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 检查是否包含调试信息
        if config.get("debug"):
            result.add_warning("生产环境不建议启用调试模式")
    
    def _validate_with_model(self, config: Dict[str, Any], model: Any) -> UtilsConfigValidationResult:
        """使用模型验证配置
        
        Args:
            config: 配置字典
            model: 验证模型
            
        Returns:
            验证结果
        """
        return self._utils_validator.validate(config, model)
    
    # 以下方法保留用于向后兼容，但实际业务逻辑应该移至服务层
    
    def validate_global_config(self, config: Dict[str, Any]) -> UtilsConfigValidationResult:
        """验证全局配置（基础版本）
        
        注意：此方法只进行基础验证，业务逻辑验证应该通过服务层调用核心层组件。
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 只进行基础结构验证
        result = self.validate(config)
        
        # 转换为Utils验证结果格式
        utils_result = UtilsConfigValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings
        )
        
        return utils_result
    
    def validate_llm_config(self, config: Dict[str, Any]) -> UtilsConfigValidationResult:
        """验证LLM配置（基础版本）
        
        注意：此方法只进行基础验证，业务逻辑验证应该通过服务层调用核心层组件。
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 只进行基础结构验证
        result = self.validate(config)
        
        # 基础字段验证
        if result.is_valid:
            if not config.get("model_type"):
                result.add_error("LLM配置缺少model_type字段")
        
        # 转换为Utils验证结果格式
        utils_result = UtilsConfigValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings
        )
        
        return utils_result
    
    def validate_tool_config(self, config: Dict[str, Any]) -> UtilsConfigValidationResult:
        """验证工具配置（基础版本）
        
        注意：此方法只进行基础验证，业务逻辑验证应该通过服务层调用核心层组件。
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 只进行基础结构验证
        result = self.validate(config)
        
        # 转换为Utils验证结果格式
        utils_result = UtilsConfigValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings
        )
        
        return utils_result
    
    def validate_token_counter_config(self, config: Dict[str, Any]) -> UtilsConfigValidationResult:
        """验证Token计数器配置（基础版本）
        
        注意：此方法只进行基础验证，业务逻辑验证应该通过服务层调用核心层组件。
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 只进行基础结构验证
        result = self.validate(config)
        
        # 转换为Utils验证结果格式
        utils_result = UtilsConfigValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings
        )
        
        return utils_result
    
    # 增强功能方法
    
    def _validate_config_with_report(self, config: Dict[str, Any], config_type: str,
                                    validation_method: Callable[[Dict[str, Any]], Any]) -> ValidationReport:
        """通用验证报告方法
        
        Args:
            config: 配置字典
            config_type: 配置类型
            validation_method: 验证方法
            
        Returns:
            验证报告
        """
        report = ValidationReport(config_type)
        
        # 基础验证
        basic_result = validation_method(config)
        
        # 创建增强验证结果
        enhanced_result = FrameworkValidationResult(
            rule_id=f"{config_type}_config_basic",
            level=ValidationLevel.SCHEMA,
            passed=basic_result.is_valid,
            message="基础验证结果"
        )
                
        # 将基础验证结果转换为增强验证结果
        if not basic_result.is_valid:
            enhanced_result.message = "; ".join(basic_result.errors)
            enhanced_result.severity = ValidationSeverity.ERROR
        elif basic_result.has_warnings():
            enhanced_result.message = "; ".join(basic_result.warnings)
            enhanced_result.severity = ValidationSeverity.WARNING
                
        report.add_level_results(ValidationLevel.SCHEMA, [enhanced_result])
        return report
    
    def validate_global_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证全局配置并返回详细报告"""
        return self._validate_config_with_report(config, "global", self.validate_global_config)

    def validate_llm_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证LLM配置并返回详细报告"""
        return self._validate_config_with_report(config, "llm", self.validate_llm_config)

    def validate_tool_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证工具配置并返回详细报告"""
        return self._validate_config_with_report(config, "tool", self.validate_tool_config)

    def validate_token_counter_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证Token计数器配置并返回详细报告"""
        return self._validate_config_with_report(config, "token_counter", self.validate_token_counter_config)

    def validate_config_with_cache(self, config_path: str, config_type: str) -> ValidationReport:
        """带缓存的配置验证
        
        Args:
            config_path: 配置路径
            config_type: 配置类型
            
        Returns:
            验证报告
        """
        cache_key = generate_cache_key(config_path, config_type)
        
        # 检查缓存
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # 根据配置类型加载并验证配置
        try:
            config_data = load_config_file(config_path)
        except Exception as e:
            # 创建错误报告
            report = ValidationReport(config_type, config_path)
            error_result = FrameworkValidationResult(
                rule_id="config_load_error",
                level=ValidationLevel.SYNTAX,
                passed=False,
                message=f"加载配置文件失败: {str(e)}"
            )
            error_result.severity = ValidationSeverity.ERROR
            report.add_level_results(ValidationLevel.SYNTAX, [error_result])
            return report
        
        if config_type == "global":
            result = self.validate_global_config_with_report(config_data)
        elif config_type == "llm":
            result = self.validate_llm_config_with_report(config_data)
        elif config_type == "tool":
            result = self.validate_tool_config_with_report(config_data)
        elif config_type == "token_counter":
            result = self.validate_token_counter_config_with_report(config_data)
        else:
            # 创建不支持的配置类型报告
            result = ValidationReport(config_type, config_path)
            error_result = FrameworkValidationResult(
                rule_id="unsupported_config_type",
                level=ValidationLevel.SCHEMA,
                passed=False,
                message=f"不支持的配置类型: {config_type}"
            )
            error_result.severity = ValidationSeverity.ERROR
            result.add_level_results(ValidationLevel.SCHEMA, [error_result])
        
        # 设置缓存
        if self.cache:
            self.cache.set(cache_key, result)
        
        return result

    def suggest_config_fixes(self, config: Dict[str, Any], config_type: str) -> List[Any]:
        """为配置提供修复建议
        
        注意：此方法为基础实现，具体的修复建议应该通过服务层调用核心层组件。
        
        Args:
            config: 配置字典
            config_type: 配置类型
            
        Returns:
            修复建议列表
        """
        # 先验证配置获取问题
        if config_type == "global":
            report = self.validate_global_config_with_report(config)
        elif config_type == "llm":
            report = self.validate_llm_config_with_report(config)
        elif config_type == "tool":
            report = self.validate_tool_config_with_report(config)
        elif config_type == "token_counter":
            report = self.validate_token_counter_config_with_report(config)
        else:
            return []
        
        # 从报告中提取修复建议
        return report.get_fix_suggestions()