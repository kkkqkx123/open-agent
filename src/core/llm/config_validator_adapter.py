"""LLM配置验证器适配器

复用通用配置验证框架，添加LLM特定的业务验证逻辑。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from src.services.logger import get_logger
from src.core.config.validation import BaseConfigValidator, ValidationResult, ValidationSeverity
from src.core.config.processor.validator import ConfigValidator
from src.core.config.models.llm_config import LLMConfig

logger = get_logger(__name__)


@dataclass
class LLMValidationRule:
    """LLM特定验证规则"""
    field_path: str
    validator: Callable[[Dict[str, Any]], bool]
    error_message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    description: Optional[str] = None


class LLMConfigValidatorAdapter:
    """LLM配置验证器适配器
    
    复用通用配置验证框架，添加LLM特定的业务验证逻辑。
    """
    
    def __init__(self, base_validator: Optional[ConfigValidator] = None):
        """初始化适配器
        
        Args:
            base_validator: 基础配置验证器
        """
        self.base_validator = base_validator or ConfigValidator()
        self.llm_rules: List[LLMValidationRule] = []
        self._setup_llm_specific_rules()
        logger.debug("LLM配置验证器适配器初始化完成")
    
    def _setup_llm_specific_rules(self) -> None:
        """设置LLM特定验证规则"""
        self.llm_rules.extend([
            # Provider特定验证规则
            LLMValidationRule(
                field_path="model_type",
                validator=lambda config: self._validate_provider_consistency(config),
                error_message="模型类型与配置不一致",
                severity=ValidationSeverity.WARNING,
                description="验证模型类型与Provider配置的一致性"
            ),
            
            # 任务组引用验证
            LLMValidationRule(
                field_path="task_group",
                validator=lambda config: self._validate_task_group_reference(config),
                error_message="任务组引用格式无效",
                severity=ValidationSeverity.ERROR,
                description="验证任务组引用的格式和存在性"
            ),
            
            # 降级配置验证
            LLMValidationRule(
                field_path="fallback_models",
                validator=lambda config: self._validate_fallback_models(config),
                error_message="降级模型配置无效",
                severity=ValidationSeverity.WARNING,
                description="验证降级模型配置的合理性"
            ),
            
            # 并发配置验证
            LLMValidationRule(
                field_path="concurrency_limit",
                validator=lambda config: self._validate_concurrency_config(config),
                error_message="并发配置不合理",
                severity=ValidationSeverity.WARNING,
                description="验证并发限制配置的合理性"
            ),
            
            # RPM限制验证
            LLMValidationRule(
                field_path="rpm_limit",
                validator=lambda config: self._validate_rpm_config(config),
                error_message="RPM限制配置不合理",
                severity=ValidationSeverity.WARNING,
                description="验证RPM限制配置的合理性"
            ),
            
            # 函数调用支持验证
            LLMValidationRule(
                field_path="function_calling_supported",
                validator=lambda config: self._validate_function_calling_config(config),
                error_message="函数调用配置不一致",
                severity=ValidationSeverity.WARNING,
                description="验证函数调用相关配置的一致性"
            )
        ])
    
    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置
        
        Args:
            config: LLM配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        logger.debug("开始LLM配置验证")
        
        # 1. 使用通用验证器进行基础验证
        try:
            base_result = self.base_validator.validate_llm_config(config)
            logger.debug("通用配置验证完成")
        except Exception as e:
            logger.error(f"通用配置验证失败: {e}")
            base_result = ValidationResult()
            base_result.add_error(f"通用验证失败: {e}")
        
        # 2. 添加LLM特定的业务验证
        llm_result = self._validate_llm_business_rules(config)
        logger.debug("LLM特定验证完成")
        
        # 3. 合并结果
        final_result = self._merge_results(base_result, llm_result)
        
        logger.info(f"LLM配置验证完成: {final_result.get_summary()}")
        return final_result
    
    def validate_provider_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Provider配置
        
        Args:
            config: Provider配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # Provider特定验证
        model_type = config.get("model_type")
        model_name = config.get("model_name")
        
        if not model_type:
            result.add_error("缺少model_type字段")
            return result
        
        if not model_name:
            result.add_error("缺少model_name字段")
            return result
        
        # 验证模型名称与类型的一致性
        if model_type == "openai" and not self._is_valid_openai_model(model_name):
            result.add_warning(f"OpenAI模型名称可能不标准: {model_name}")
        elif model_type == "anthropic" and not self._is_valid_anthropic_model(model_name):
            result.add_warning(f"Anthropic模型名称可能不标准: {model_name}")
        elif model_type == "gemini" and not self._is_valid_gemini_model(model_name):
            result.add_warning(f"Gemini模型名称可能不标准: {model_name}")
        
        # 验证API配置
        if not config.get("api_key") and not config.get("base_url"):
            result.add_warning(f"{model_type}模型建议配置api_key或base_url")
        
        return result
    
    def _validate_llm_business_rules(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM特定业务规则
        
        Args:
            config: 配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        for rule in self.llm_rules:
            try:
                if not rule.validator(config):
                    message = f"LLM业务规则验证失败 [{rule.field_path}]: {rule.error_message}"
                    if rule.severity == ValidationSeverity.ERROR:
                        result.add_error(message)
                    elif rule.severity == ValidationSeverity.WARNING:
                        result.add_warning(message)
                    else:
                        result.add_info(message)
                    logger.debug(f"规则验证失败: {rule.description}")
                else:
                    logger.debug(f"规则验证通过: {rule.description}")
            except Exception as e:
                error_msg = f"验证规则执行失败 [{rule.field_path}]: {e}"
                result.add_error(error_msg)
                logger.error(error_msg)
        
        return result
    
    def _validate_provider_consistency(self, config: Dict[str, Any]) -> bool:
        """验证Provider一致性
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否一致
        """
        model_type = config.get("model_type")
        provider = config.get("provider")
        
        if not model_type:
            return False
        
        # 如果指定了provider，检查与model_type的一致性
        if provider and provider != model_type:
            logger.warning(f"provider ({provider}) 与 model_type ({model_type}) 不一致")
            return False
        
        return True
    
    def _validate_task_group_reference(self, config: Dict[str, Any]) -> bool:
        """验证任务组引用
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否有效
        """
        task_group = config.get("task_group")
        
        if not task_group:
            return True  # 可选字段
        
        # 检查格式：group_name.echelon 或 group_name.task_type
        if isinstance(task_group, str):
            parts = task_group.split(".")
            if len(parts) != 2:
                return False
            
            group_name, echelon_or_task = parts
            if not group_name or not echelon_or_task:
                return False
            
            # 这里可以进一步验证group_name和echelon_or_task的有效性
            # 但需要访问任务组配置，暂时只验证格式
        
        return True
    
    def _validate_fallback_models(self, config: Dict[str, Any]) -> bool:
        """验证降级模型配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否有效
        """
        fallback_models = config.get("fallback_models", [])
        
        if not isinstance(fallback_models, list):
            return False
        
        # 检查降级模型数量是否合理
        if len(fallback_models) > 5:
            logger.warning("降级模型数量过多，可能影响性能")
        
        # 检查是否包含自身
        current_model = config.get("model_name")
        if current_model in fallback_models:
            logger.warning("降级模型列表包含当前模型")
        
        return True
    
    def _validate_concurrency_config(self, config: Dict[str, Any]) -> bool:
        """验证并发配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否合理
        """
        concurrency_limit = config.get("concurrency_limit")
        
        if concurrency_limit is None:
            return True  # 可选字段
        
        if not isinstance(concurrency_limit, int) or concurrency_limit <= 0:
            return False
        
        # 检查并发限制是否合理
        if concurrency_limit > 100:
            logger.warning(f"并发限制过高 ({concurrency_limit})，可能导致资源耗尽")
        elif concurrency_limit < 1:
            logger.warning(f"并发限制过低 ({concurrency_limit})，可能影响性能")
        
        return True
    
    def _validate_rpm_config(self, config: Dict[str, Any]) -> bool:
        """验证RPM配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否合理
        """
        rpm_limit = config.get("rpm_limit")
        
        if rpm_limit is None:
            return True  # 可选字段
        
        if not isinstance(rpm_limit, int) or rpm_limit <= 0:
            return False
        
        # 检查RPM限制是否合理
        if rpm_limit > 10000:
            logger.warning(f"RPM限制过高 ({rpm_limit})，可能触发提供商限制")
        elif rpm_limit < 1:
            logger.warning(f"RPM限制过低 ({rpm_limit})，可能影响响应速度")
        
        return True
    
    def _validate_function_calling_config(self, config: Dict[str, Any]) -> bool:
        """验证函数调用配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否一致
        """
        function_calling_supported = config.get("function_calling_supported", True)
        function_calling_mode = config.get("function_calling_mode", "auto")
        
        if not function_calling_supported and function_calling_mode != "none":
            logger.warning("函数调用不支持，但配置了调用模式")
            return False
        
        # 验证调用模式
        valid_modes = ["auto", "none", "required"]
        if function_calling_mode not in valid_modes:
            logger.warning(f"无效的函数调用模式: {function_calling_mode}")
            return False
        
        return True
    
    def _is_valid_openai_model(self, model_name: str) -> bool:
        """检查是否为有效的OpenAI模型名称
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否有效
        """
        valid_prefixes = ["gpt-", "text-", "code-", "davinci-", "curie-", "babbage-", "ada-"]
        return any(model_name.startswith(prefix) for prefix in valid_prefixes)
    
    def _is_valid_anthropic_model(self, model_name: str) -> bool:
        """检查是否为有效的Anthropic模型名称
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否有效
        """
        return "claude" in model_name.lower()
    
    def _is_valid_gemini_model(self, model_name: str) -> bool:
        """检查是否为有效的Gemini模型名称
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否有效
        """
        return "gemini" in model_name.lower()
    
    def _merge_results(self, base_result: ValidationResult, llm_result: ValidationResult) -> ValidationResult:
        """合并验证结果
        
        Args:
            base_result: 基础验证结果
            llm_result: LLM特定验证结果
            
        Returns:
            ValidationResult: 合并后的结果
        """
        merged = ValidationResult()
        
        # 合并错误
        merged.errors.extend(base_result.errors)
        merged.errors.extend(llm_result.errors)
        
        # 合并警告
        merged.warnings.extend(base_result.warnings)
        merged.warnings.extend(llm_result.warnings)
        
        # 合并信息
        merged.info.extend(base_result.info)
        merged.info.extend(llm_result.info)
        
        # 更新有效性状态
        merged.is_valid = len(merged.errors) == 0
        
        return merged
    
    def add_llm_rule(self, rule: LLMValidationRule) -> None:
        """添加LLM特定验证规则
        
        Args:
            rule: 验证规则
        """
        self.llm_rules.append(rule)
        logger.debug(f"添加LLM验证规则: {rule.field_path}")
    
    def remove_llm_rule(self, field_path: str) -> bool:
        """移除LLM特定验证规则
        
        Args:
            field_path: 字段路径
            
        Returns:
            bool: 是否成功移除
        """
        original_count = len(self.llm_rules)
        self.llm_rules = [rule for rule in self.llm_rules if rule.field_path != field_path]
        removed = len(self.llm_rules) < original_count
        
        if removed:
            logger.debug(f"移除LLM验证规则: {field_path}")
        
        return removed
    
    def get_llm_rules_summary(self) -> Dict[str, Any]:
        """获取LLM验证规则摘要
        
        Returns:
            Dict[str, Any]: 规则摘要信息
        """
        rules_by_severity = {}
        for rule in self.llm_rules:
            severity = rule.severity.value
            if severity not in rules_by_severity:
                rules_by_severity[severity] = []
            rules_by_severity[severity].append(rule.field_path)
        
        return {
            "total_rules": len(self.llm_rules),
            "rules_by_severity": rules_by_severity,
            "rule_descriptions": {
                rule.field_path: rule.description 
                for rule in self.llm_rules 
                if rule.description
            }
        }