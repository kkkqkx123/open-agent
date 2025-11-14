"""增强的配置验证器

提供多层次配置验证、智能修复和详细报告功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable, Tuple
from enum import Enum
from datetime import datetime
import yaml
import json
import logging
from pathlib import Path

from ..processor.validator import ConfigValidator, ValidationResult

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标


class ValidationSeverity(Enum):
    """验证严重性级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FixSuggestion:
    """修复建议"""
    
    def __init__(self, description: str, fix_action: Callable, confidence: float = 0.8):
        self.description = description
        self.fix_action = fix_action
        self.confidence = confidence


class EnhancedValidationResult:
    """增强的验证结果"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, passed: bool, message: str = ""):
        self.rule_id = rule_id
        self.level = level
        self.passed = passed
        self.message = message
        self.suggestions: List[str] = []
        self.fix_suggestions: List[FixSuggestion] = []
        self.timestamp = datetime.now()
        self.severity: ValidationSeverity = ValidationSeverity.WARNING
    
    def add_warning(self, warning: str) -> None:
        """添加警告信息"""
        self.message = warning
        self.severity = ValidationSeverity.WARNING


class ValidationRule(ABC):
    """验证规则基类"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, description: str):
        self.rule_id = rule_id
        self.level = level
        self.description = description
        self.severity: ValidationSeverity = ValidationSeverity.WARNING
    
    @abstractmethod
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        """执行验证"""
        pass


class ValidationContext:
    """验证上下文"""
    
    def __init__(self, config_path: str = "", config_data: Optional[Dict[str, Any]] = None):
        self.config_path = config_path
        self.config_data = config_data or {}
        self.validation_levels: List[ValidationLevel] = list(ValidationLevel)
        self.custom_rules: List[ValidationRule] = []


class ValidationReport:
    """验证报告"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.timestamp = datetime.now()
        self.level_results: Dict[ValidationLevel, List[EnhancedValidationResult]] = {}
        self.summary: Dict[str, int] = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": 0
        }
    
    def add_level_results(self, level: ValidationLevel, results: List[EnhancedValidationResult]) -> None:
        """添加级别验证结果"""
        self.level_results[level] = results
        self._update_summary(level, results)
    
    def get_fix_suggestions(self) -> List[FixSuggestion]:
        """获取所有修复建议"""
        suggestions = []
        for results in self.level_results.values():
            for result in results:
                if not result.passed:
                    suggestions.extend(result.fix_suggestions)
        return suggestions
    
    def is_valid(self, min_severity: ValidationSeverity = ValidationSeverity.ERROR) -> bool:
        """检查配置是否有效"""
        for results in self.level_results.values():
            for result in results:
                if not result.passed and result.severity.value >= min_severity.value:
                    return False
        return True
    
    @property
    def is_valid_property(self) -> bool:
        """配置是否有效的属性版本"""
        return self.is_valid()
    
    def _update_summary(self, level: ValidationLevel, results: List[EnhancedValidationResult]) -> None:
        """更新摘要统计"""
        self.summary["total_rules"] += len(results)
        
        for result in results:
            if result.passed:
                self.summary["passed"] += 1
            else:
                self.summary["failed"] += 1
                
                if result.severity == ValidationSeverity.WARNING:
                    self.summary["warnings"] += 1
                elif result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    self.summary["errors"] += 1


class ValidationCache:
    """验证缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self._cache: Dict[str, Tuple[ValidationReport, datetime]] = {}
    
    def get(self, key: str) -> Optional[ValidationReport]:
        """获取缓存结果"""
        if key in self._cache:
            report, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl:
                return report
            else:
                del self._cache[key]  # 过期清理
        return None
    
    def set(self, key: str, report: ValidationReport) -> None:
        """设置缓存结果"""
        if len(self._cache) >= self.max_size:
            # LRU淘汰策略
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[key] = (report, datetime.now())


# 内置验证规则
class SyntaxValidationRule(ValidationRule):
    """语法验证规则"""
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        result = EnhancedValidationResult(
            rule_id=self.rule_id,
            level=self.level,
            passed=True
        )
        
        try:
            # 检查YAML语法
            if isinstance(config, str):
                yaml.safe_load(config)
            # 其他语法检查...
        except yaml.YAMLError as e:
            result.passed = False
            result.message = f"YAML语法错误: {e}"
            result.fix_suggestions.append(
                FixSuggestion("修复YAML语法", self._fix_yaml_syntax)
            )
        
        return result
    
    def _fix_yaml_syntax(self) -> None:
        """修复YAML语法"""
        # 实现语法修复逻辑
        pass


class SchemaValidationRule(ValidationRule):
    """模式验证规则"""
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        result = EnhancedValidationResult(
            rule_id=self.rule_id,
            level=self.level,
            passed=True
        )
        
        # 检查必需字段
        required_fields = ["name", "version", "nodes"]
        for field in required_fields:
            if field not in config:
                result.passed = False
                result.message = f"缺少必需字段: {field}"
                # 创建修复函数，捕获当前field值
                def create_fix_function(field_name):
                    return lambda: self._add_required_field(config, field_name)
                
                result.fix_suggestions.append(
                    FixSuggestion(f"添加字段: {field}", create_fix_function(field))
                )
        
        # 检查字段类型
        if "nodes" in config and not isinstance(config["nodes"], dict):
            result.passed = False
            result.message = "nodes字段必须是字典类型"
        
        return result
    
    def _add_required_field(self, config: Dict[str, Any], field: str) -> None:
        """添加必需字段"""
        if field == "name":
            config[field] = "unnamed_config"
        elif field == "version":
            config[field] = "1.0.0"
        elif field == "nodes":
            config[field] = {}


class SemanticValidationRule(ValidationRule):
    """语义验证规则"""
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        result = EnhancedValidationResult(
            rule_id=self.rule_id,
            level=self.level,
            passed=True
        )
        
        # 检查节点引用
        nodes = config.get("nodes", {})
        edges = config.get("edges", [])
        
        for edge in edges:
            if edge.get("from_node") not in nodes:
                result.passed = False
                result.message = f"边引用不存在的节点: {edge.get('from_node')}"
            
            if edge.get("to_node") not in nodes and edge.get("to_node") != "__end__":
                result.passed = False
                result.message = f"边引用不存在的节点: {edge.get('to_node')}"
        
        return result


class DependencyValidationRule(ValidationRule):
    """依赖验证规则"""
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        result = EnhancedValidationResult(
            rule_id=self.rule_id,
            level=self.level,
            passed=True
        )
        
        # 检查外部依赖
        dependencies = config.get("dependencies", {})
        
        for dep_name, dep_config in dependencies.items():
            # 检查依赖配置
            if not dep_config.get("enabled", True):
                continue
            
            # 检查必需配置
            if not dep_config.get("url") and not dep_config.get("path"):
                result.passed = False
                result.message = f"依赖 '{dep_name}' 缺少URL或路径配置"
        
        return result


class PerformanceValidationRule(ValidationRule):
    """性能验证规则"""
    
    def validate(self, config: Dict[str, Any], context: Dict[str, Any]) -> EnhancedValidationResult:
        result = EnhancedValidationResult(
            rule_id=self.rule_id,
            level=self.level,
            passed=True
        )
        
        # 检查性能相关配置
        performance_config = config.get("performance", {})
        
        # 检查缓存配置
        cache_config = performance_config.get("cache", {})
        if cache_config.get("enabled", False):
            max_size = cache_config.get("max_size")
            if max_size is not None and max_size > 10000:
                result.message = "缓存大小过大，可能影响性能"
                result.severity = ValidationSeverity.WARNING
        
        # 检查并发配置
        concurrency_config = performance_config.get("concurrency", {})
        max_workers = concurrency_config.get("max_workers")
        if max_workers is not None and max_workers > 100:
            result.message = "并发工作线程数过大，可能影响系统稳定性"
            result.severity = ValidationSeverity.WARNING
        
        return result


class EnhancedConfigValidator:
    """增强的配置验证器"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._load_builtin_rules()
        self.cache = ValidationCache()
        self.base_validator = ConfigValidator()
    
    def register_rule(self, rule: ValidationRule) -> None:
        """注册验证规则"""
        self.rules[rule.rule_id] = rule
    
    def validate_config(self, config_path: str, levels: Optional[List[ValidationLevel]] = None) -> ValidationReport:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            levels: 要验证的级别列表，如果为None则验证所有级别
            
        Returns:
            验证报告
        """
        if levels is None:
            levels = list(ValidationLevel)
        
        # 检查缓存
        cache_key = self._generate_cache_key(config_path, levels)
        if cached_result := self.cache.get(cache_key):
            return cached_result
        
        config_data = self._load_config(config_path)
        report = ValidationReport(config_path)
        
        for level in levels:
            level_results = self._validate_level(config_data, level)
            report.add_level_results(level, level_results)
        
        # 缓存结果
        self.cache.set(cache_key, report)
        return report
    
    def validate_config_data(self, config_data: Dict[str, Any], levels: Optional[List[ValidationLevel]] = None) -> ValidationReport:
        """验证配置数据
        
        Args:
            config_data: 配置数据字典
            levels: 要验证的级别列表
            
        Returns:
            验证报告
        """
        if levels is None:
            levels = list(ValidationLevel)
        
        report = ValidationReport("memory_config")
        
        for level in levels:
            level_results = self._validate_level(config_data, level)
            report.add_level_results(level, level_results)
        
        return report
    
    def _validate_level(self, config: Dict[str, Any], level: ValidationLevel) -> List[EnhancedValidationResult]:
        """验证指定级别"""
        results = []
        level_rules = [rule for rule in self.rules.values() if rule.level == level]
        
        for rule in level_rules:
            context = {"config": config, "level": level}
            result = rule.validate(config, context)
            results.append(result)
        
        return results
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                return json.load(f)
            else:
                # 尝试作为YAML加载
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError:
                    raise ValueError(f"不支持的配置文件格式: {config_path}")
    
    def _generate_cache_key(self, config_path: str, levels: List[ValidationLevel]) -> str:
        """生成缓存键"""
        level_names = "_".join(level.value for level in sorted(levels, key=lambda x: x.value))
        return f"{config_path}_{level_names}"
    
    def _load_builtin_rules(self) -> None:
        """加载内置验证规则"""
        builtin_rules = [
            SyntaxValidationRule("syntax_001", ValidationLevel.SYNTAX, "YAML语法验证"),
            SchemaValidationRule("schema_001", ValidationLevel.SCHEMA, "配置结构验证"),
            SemanticValidationRule("semantic_001", ValidationLevel.SEMANTIC, "业务逻辑验证"),
            DependencyValidationRule("dependency_001", ValidationLevel.DEPENDENCY, "依赖验证"),
            PerformanceValidationRule("performance_001", ValidationLevel.PERFORMANCE, "性能配置验证")
        ]
        
        for rule in builtin_rules:
            self.register_rule(rule)


class ConfigFixer:
    """配置修复器"""
    
    def __init__(self, validator: EnhancedConfigValidator):
        self.validator = validator
        self.fix_strategies: Dict[str, Callable] = {}
        self._register_fix_strategies()
    
    def auto_fix_config(self, config_path: str, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """自动修复配置
        
        Args:
            config_path: 配置文件路径
            confidence_threshold: 置信度阈值
            
        Returns:
            修复后的配置
        """
        config_data = self.validator._load_config(config_path)
        report = self.validator.validate_config_data(config_data)
        fixes_applied = []
        
        for suggestion in report.get_fix_suggestions():
            if suggestion.confidence >= confidence_threshold:
                try:
                    # 应用修复到配置数据
                    suggestion.fix_action()
                    fixes_applied.append(suggestion.description)
                except Exception as e:
                    logger.warning(f"修复失败: {suggestion.description}, 错误: {e}")
        
        # 重新验证修复后的配置
        fixed_report = self.validator.validate_config_data(config_data)
        
        # 如果修复后仍然有错误，记录警告
        if not fixed_report.is_valid():
            logger.warning(f"自动修复后配置仍然存在问题: {fixed_report.summary}")
        
        return config_data
    
    def suggest_fixes(self, config_path: str) -> List[FixSuggestion]:
        """提供修复建议
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            修复建议列表
        """
        report = self.validator.validate_config(config_path)
        return report.get_fix_suggestions()
    
    def _register_fix_strategies(self) -> None:
        """注册修复策略"""
        self.fix_strategies = {
            "missing_field": self._fix_missing_field,
            "invalid_type": self._fix_invalid_type,
            "invalid_value": self._fix_invalid_value
        }
    
    def _fix_missing_field(self, config: Dict[str, Any], field: str, default_value: Any) -> None:
        """修复缺失字段"""
        if field not in config:
            config[field] = default_value
    
    def _fix_invalid_type(self, config: Dict[str, Any], field: str, expected_type: Type) -> None:
        """修复类型错误"""
        if field in config and not isinstance(config[field], expected_type):
            # 尝试类型转换或使用默认值
            try:
                config[field] = expected_type(config[field])
            except (ValueError, TypeError):
                config[field] = self._get_default_value(expected_type)
    
    def _fix_invalid_value(self, config: Dict[str, Any], field: str, valid_values: List[Any]) -> None:
        """修复无效值"""
        if field in config and config[field] not in valid_values:
            # 使用第一个有效值作为默认值
            config[field] = valid_values[0] if valid_values else None
    
    def _get_default_value(self, expected_type: Type) -> Any:
        """获取默认值"""
        if expected_type == str:
            return ""
        elif expected_type == int:
            return 0
        elif expected_type == float:
            return 0.0
        elif expected_type == bool:
            return False
        elif expected_type == list:
            return []
        elif expected_type == dict:
            return {}
        else:
            return None


# 便捷的创建函数
def create_enhanced_config_validator() -> EnhancedConfigValidator:
    """创建增强的配置验证器
    
    Returns:
        增强的配置验证器实例
    """
    return EnhancedConfigValidator()