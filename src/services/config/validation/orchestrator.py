"""验证编排器

协调各种验证组件，提供完整的验证流程编排。
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

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
from src.infrastructure.config.loader import load_config_file


logger = get_logger(__name__)


class ValidationOrchestrator:
    """验证编排器
    
    协调基础设施层和核心层的验证组件，提供完整的验证流程。
    """
    
    def __init__(self,
                 rule_registry: Optional[ValidationRuleRegistry] = None,
                 base_validator: Optional[ConfigValidator] = None,
                 business_validators: Optional[Dict[str, IBusinessValidator]] = None):
        """初始化验证编排器
        
        Args:
            rule_registry: 规则注册表
            base_validator: 基础验证器
            business_validators: 业务验证器字典
        """
        self.rule_registry = rule_registry
        self.base_validator = base_validator
        self.business_validators = business_validators or {}
        self.logger = logger
        
        # 验证统计
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "average_validation_time": 0.0
        }
    
    def validate_config_complete(self,
                               config_type: str,
                               config: Dict[str, Any],
                               context: Optional[ValidationContext] = None,
                               enable_business_validation: bool = True,
                               enable_rule_validation: bool = True) -> Tuple[IValidationResult, ValidationReport]:
        """完整验证配置
        
        Args:
            config_type: 配置类型
            config: 配置数据
            context: 验证上下文
            enable_business_validation: 是否启用业务验证
            enable_rule_validation: 是否启用规则验证
            
        Returns:
            验证结果和验证报告的元组
        """
        start_time = datetime.now()
        
        try:
            # 创建验证上下文
            if context is None:
                context = ValidationContext(
                    config_type=config_type,
                    enable_business_rules=enable_business_validation
                )
            
            # 创建验证报告
            report = ValidationReport(config_type)
            
            # 1. 基础验证
            base_result = self._perform_base_validation(config, context)
            self._add_result_to_report(report, "base_validation", base_result, ValidationLevel.SYNTAX)
            
            # 2. 规则验证
            rule_result = ValidationResult(is_valid=True, errors=[], warnings=[])
            if enable_rule_validation and self.rule_registry:
                rule_result = self.rule_registry.validate_config(config_type, config, context)
                self._add_result_to_report(report, "rule_validation", rule_result, ValidationLevel.SCHEMA)
            
            # 3. 业务验证
            business_result = ValidationResult(is_valid=True, errors=[], warnings=[])
            if enable_business_validation and config_type in self.business_validators:
                business_validator = self.business_validators[config_type]
                business_result = business_validator.validate(config, context)
                self._add_result_to_report(report, "business_validation", business_result, ValidationLevel.SEMANTIC)
            
            # 合并所有验证结果
            final_result = self._merge_validation_results([base_result, rule_result, business_result])
            
            # 更新统计信息
            self._update_validation_stats(final_result, start_time)
            
            # 添加元数据到报告
            report.add_metadata("validation_time", (datetime.now() - start_time).total_seconds())
            report.add_metadata("context", context)
            
            self.logger.info(f"配置验证完成: {config_type}, 结果: {'通过' if final_result.is_valid else '失败'}")
            
            return final_result, report
            
        except Exception as e:
            self.logger.error(f"配置验证过程中发生错误: {e}")
            error_result = ValidationResult(
                is_valid=False,
                errors=[f"验证过程发生错误: {str(e)}"],
                warnings=[]
            )
            
            # 创建错误报告
            error_report = ValidationReport(config_type)
            error_report.add_metadata("error", str(e))
            error_report.add_metadata("validation_time", (datetime.now() - start_time).total_seconds())
            
            return error_result, error_report
    
    def validate_config_file(self,
                           config_path: str,
                           config_type: str,
                           context: Optional[ValidationContext] = None,
                           **context_kwargs) -> Tuple[IValidationResult, ValidationReport]:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型
            context: 验证上下文
            **context_kwargs: 上下文参数
            
        Returns:
            验证结果和验证报告的元组
        """
        try:
            # 加载配置文件
            config_data = load_config_file(config_path)
            
            # 创建验证上下文
            if context is None:
                context = ValidationContext(
                    config_type=config_type,
                    config_path=config_path,
                    **context_kwargs
                )
            
            # 验证配置
            return self.validate_config_complete(config_type, config_data, context)
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {config_path}, 错误: {e}")
            error_result = ValidationResult(
                is_valid=False,
                errors=[f"加载配置文件失败: {str(e)}"],
                warnings=[]
            )
            
            # 创建错误报告
            error_report = ValidationReport(config_type, config_path)
            error_report.add_metadata("error", str(e))
            
            return error_result, error_report
    
    def validate_multiple_configs(self,
                                configs: Dict[str, Dict[str, Any]],
                                global_context: Optional[ValidationContext] = None) -> Dict[str, Tuple[IValidationResult, ValidationReport]]:
        """验证多个配置
        
        Args:
            configs: 配置字典 {config_type: config_data}
            global_context: 全局验证上下文
            
        Returns:
            验证结果字典 {config_type: (result, report)}
        """
        results = {}
        
        for config_type, config_data in configs.items():
            try:
                # 创建特定于配置类型的上下文
                context = ValidationContext(
                    config_type=config_type,
                    environment=global_context.environment if global_context else "development",
                    strict_mode=global_context.strict_mode if global_context else False
                )
                
                # 添加依赖配置
                if global_context:
                    for dep_type, dep_config in global_context.dependent_configs.items():
                        context.add_dependency(dep_type, dep_config)
                
                # 验证配置
                result, report = self.validate_config_complete(config_type, config_data, context)
                results[config_type] = (result, report)
                
            except Exception as e:
                self.logger.error(f"验证配置 {config_type} 时发生错误: {e}")
                error_result = ValidationResult(
                    is_valid=False,
                    errors=[f"验证过程发生错误: {str(e)}"],
                    warnings=[]
                )
                error_report = ValidationReport(config_type)
                error_report.add_metadata("error", str(e))
                results[config_type] = (error_result, error_report)
        
        return results
    
    def _perform_base_validation(self, config: Dict[str, Any], context: ValidationContext) -> IValidationResult:
        """执行基础验证
        
        Args:
            config: 配置数据
            context: 验证上下文
            
        Returns:
            验证结果
        """
        if self.base_validator:
            return self.base_validator.validate_with_context(config, context)
        else:
            # 如果没有基础验证器，执行简单的基础验证
            result = ValidationResult(is_valid=True, errors=[], warnings=[])
            
            if not isinstance(config, dict):
                result.add_error("配置必须是字典类型")
                return result
            
            if not config:
                result.add_error("配置不能为空")
                return result
            
            return result
    
    def _add_result_to_report(self, 
                            report: ValidationReport,
                            stage_name: str,
                            result: IValidationResult,
                            level: ValidationLevel) -> None:
        """将验证结果添加到报告
        
        Args:
            report: 验证报告
            stage_name: 验证阶段名称
            result: 验证结果
            level: 验证级别
        """
        from src.infrastructure.config.validation.framework import FrameworkValidationResult
        
        enhanced_result = FrameworkValidationResult(
            rule_id=stage_name,
            level=level,
            passed=result.is_valid,
            message=f"{stage_name}结果"
        )
        
        if not result.is_valid:
            enhanced_result.message = "; ".join(result.errors)
            enhanced_result.severity = ValidationSeverity.ERROR
        elif result.has_warnings():
            enhanced_result.message = "; ".join(result.warnings)
            enhanced_result.severity = ValidationSeverity.WARNING
        
        enhanced_result.add_metadata("errors", result.errors)
        enhanced_result.add_metadata("warnings", result.warnings)
        
        report.add_level_results(level, [enhanced_result])
    
    def _merge_validation_results(self, results: List[IValidationResult]) -> IValidationResult:
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
    
    def _update_validation_stats(self, result: IValidationResult, start_time: datetime) -> None:
        """更新验证统计信息
        
        Args:
            result: 验证结果
            start_time: 开始时间
        """
        self.validation_stats["total_validations"] += 1
        
        if result.is_valid:
            self.validation_stats["successful_validations"] += 1
        else:
            self.validation_stats["failed_validations"] += 1
        
        # 更新平均验证时间
        validation_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.validation_stats["average_validation_time"]
        total_count = self.validation_stats["total_validations"]
        
        self.validation_stats["average_validation_time"] = (
            (current_avg * (total_count - 1) + validation_time) / total_count
        )
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息
        
        Returns:
            验证统计信息
        """
        return self.validation_stats.copy()
    
    def reset_validation_stats(self) -> None:
        """重置验证统计信息"""
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "average_validation_time": 0.0
        }
    
    def get_supported_config_types(self) -> List[str]:
        """获取支持的配置类型
        
        Returns:
            支持的配置类型列表
        """
        types = set()
        
        if self.rule_registry:
            types.update(self.rule_registry.get_supported_config_types())
        
        types.update(self.business_validators.keys())
        
        return list(types)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        # 检查规则注册表
        if self.rule_registry:
            health["components"]["rule_registry"] = {
                "status": "healthy",
                "supported_types": self.rule_registry.get_supported_config_types()
            }
        else:
            health["components"]["rule_registry"] = {"status": "disabled"}
        
        # 检查基础验证器
        if self.base_validator:
            health["components"]["base_validator"] = {"status": "healthy"}
        else:
            health["components"]["base_validator"] = {"status": "disabled"}
        
        # 检查业务验证器
        health["components"]["business_validators"] = {
            "status": "healthy",
            "validators": list(self.business_validators.keys())
        }
        
        # 检查统计信息
        health["components"]["validation_stats"] = self.validation_stats
        
        return health