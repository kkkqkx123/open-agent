"""配置验证服务

提供统一的配置验证服务入口，协调各层组件。
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

from src.interfaces.config import IConfigValidator
from src.interfaces.common_domain import IValidationResult
from src.core.validation import ValidationResult
from src.interfaces.dependency_injection import get_logger
from src.core.config.validation import (
    ValidationRuleRegistry,
    IBusinessValidator
)
from src.infrastructure.validation.context import ValidationContext
from src.infrastructure.config.validation import (
    ConfigValidator,
    ValidationReport
)
from src.interfaces.config.validation import (
    ValidationLevel,
    ValidationSeverity
)


logger = get_logger(__name__)


class ConfigValidationService(IConfigValidator):
    """配置验证服务
    
    提供统一的配置验证服务，协调基础设施层和核心层的组件。
    """
    
    def __init__(self,
                 rule_registry: Optional[ValidationRuleRegistry] = None,
                 business_validator: Optional[IBusinessValidator] = None,
                 base_validator: Optional[ConfigValidator] = None,
                 config_type: str = "unknown"):
        """初始化配置验证服务
        
        Args:
            rule_registry: 规则注册表
            business_validator: 业务验证器
            base_validator: 基础验证器
            config_type: 配置类型
        """
        self.rule_registry = rule_registry
        self.business_validator = business_validator
        self.base_validator = base_validator
        self.config_type = config_type
        self.logger = logger
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        return module_type == self.config_type or module_type == "all"
    
    def validate(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 创建默认验证上下文
        context = ValidationContext(
            config_type=self.config_type,
            enable_business_rules=self.business_validator is not None
        )
        
        return self.validate_with_context(config, context)
    
    def validate_with_context(self, 
                            config: Dict[str, Any], 
                            context: ValidationContext) -> IValidationResult:
        """带上下文的验证
        
        Args:
            config: 配置字典
            context: 验证上下文
            
        Returns:
            验证结果
        """
        results = []
        
        # 1. 基础验证
        if self.base_validator:
            base_result = self.base_validator.validate_with_context(config, context)
            results.append(base_result)
        else:
            # 执行简单的基础验证
            base_result = self._perform_basic_validation(config)
            results.append(base_result)
        
        # 2. 规则验证
        if self.rule_registry and context.enable_business_rules:
            rule_result = self.rule_registry.validate_config(self.config_type, config, context)
            results.append(rule_result)
        
        # 3. 业务验证
        if self.business_validator and context.enable_business_rules:
            business_result = self.business_validator.validate(config, context)
            results.append(business_result)
        
        # 合并结果
        return self._merge_results(results)
    
    def validate_with_report(self, 
                           config: Dict[str, Any], 
                           context: Optional[ValidationContext] = None) -> Tuple[IValidationResult, ValidationReport]:
        """验证配置并生成详细报告
        
        Args:
            config: 配置字典
            context: 验证上下文
            
        Returns:
            验证结果和验证报告的元组
        """
        if context is None:
            context = ValidationContext(
                config_type=self.config_type,
                enable_business_rules=True
            )
        
        # 执行验证
        result = self.validate_with_context(config, context)
        
        # 生成报告
        report = self._generate_report(config, context, result)
        
        return result, report
    
    def validate_file(self, 
                     config_path: str, 
                     context: Optional[ValidationContext] = None) -> Tuple[IValidationResult, ValidationReport]:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            context: 验证上下文
            
        Returns:
            验证结果和验证报告的元组
        """
        try:
            # 加载配置文件
            from src.infrastructure.config.loader import load_config_file
            config_data = load_config_file(config_path)
            
            # 更新上下文
            if context is None:
                context = ValidationContext(
                    config_type=self.config_type,
                    config_path=config_path
                )
            else:
                context.config_path = config_path
            
            # 验证配置
            return self.validate_with_report(config_data, context)
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {config_path}, 错误: {e}")
            
            # 创建错误结果
            error_result = ValidationResult(
                is_valid=False,
                errors=[f"加载配置文件失败: {str(e)}"],
                warnings=[]
            )
            
            # 创建错误报告
            error_report = ValidationReport(self.config_type, config_path)
            error_report.add_metadata("error", str(e))
            
            return error_result, error_report
    
    def _perform_basic_validation(self, config: Dict[str, Any]) -> IValidationResult:
        """执行基础验证
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # 基础结构验证
        if not isinstance(config, dict):
            result.add_error("配置必须是字典类型")
            return result
        
        if not config:
            result.add_error("配置不能为空")
            return result
        
        return result
    
    def _merge_results(self, results: List[IValidationResult]) -> IValidationResult:
        """合并多个验证结果
        
        Args:
            results: 验证结果列表
            
        Returns:
            合并后的验证结果
        """
        merged_result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        for result in results:
            if not result.is_valid:
                merged_result.is_valid = False
                merged_result.errors.extend(result.errors)
            
            merged_result.warnings.extend(result.warnings)
        
        return merged_result
    
    def _generate_report(self, 
                        config: Dict[str, Any], 
                        context: ValidationContext, 
                        result: IValidationResult) -> ValidationReport:
        """生成验证报告
        
        Args:
            config: 配置数据
            context: 验证上下文
            result: 验证结果
            
        Returns:
            验证报告
        """
        from src.infrastructure.config.validation.framework import FrameworkValidationResult
        
        report = ValidationReport(self.config_type, context.config_path)
        
        # 添加基础验证结果
        base_result = FrameworkValidationResult(
            rule_id="basic_validation",
            level=ValidationLevel.SYNTAX,
            passed=result.is_valid,
            message="基础验证结果"
        )
        
        if not result.is_valid:
            base_result.message = "; ".join(result.errors)
            base_result.severity = ValidationSeverity.ERROR
        elif result.has_warnings():
            base_result.message = "; ".join(result.warnings)
            base_result.severity = ValidationSeverity.WARNING
        
        base_result.add_metadata("errors", result.errors)
        base_result.add_metadata("warnings", result.warnings)
        
        report.add_level_results(ValidationLevel.SYNTAX, [base_result])
        
        # 添加上下文信息
        report.add_metadata("context", context)
        report.add_metadata("config_size", len(str(config)))
        
        return report
    
    # 向后兼容的方法
    
    def validate_global_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证全局配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        if self.config_type != "global":
            self.logger.warning("使用非全局配置验证器验证全局配置")
        
        return self.validate(config)
    
    def validate_llm_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证LLM配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        if self.config_type != "llm":
            self.logger.warning("使用非LLM配置验证器验证LLM配置")
        
        return self.validate(config)
    
    def validate_tool_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证工具配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        if self.config_type != "tool":
            self.logger.warning("使用非工具配置验证器验证工具配置")
        
        return self.validate(config)
    
    def validate_token_counter_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证Token计数器配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        if self.config_type != "token_counter":
            self.logger.warning("使用非Token计数器配置验证器验证Token计数器配置")
        
        return self.validate(config)
    
    def get_validation_info(self) -> Dict[str, Any]:
        """获取验证器信息
        
        Returns:
            验证器信息
        """
        return {
            "config_type": self.config_type,
            "has_rule_registry": self.rule_registry is not None,
            "has_business_validator": self.business_validator is not None,
            "has_base_validator": self.base_validator is not None,
            "supported_module_types": [self.config_type, "all"]
        }