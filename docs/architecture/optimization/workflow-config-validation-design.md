# WorkflowManager配置验证增强方案

## 问题分析

当前WorkflowManager的配置验证功能相对基础，缺乏全面的配置验证、错误处理和配置修复机制。需要增强配置验证能力以确保工作流配置的质量和可靠性。

## 设计目标

1. **全面验证** - 支持多层次配置验证
2. **智能修复** - 提供配置自动修复建议
3. **详细报告** - 生成详细的验证报告
4. **性能优化** - 高效的验证算法和缓存机制

## 详细设计方案

### 1. 多层次验证架构

```python
class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标

class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, description: str):
        self.rule_id = rule_id
        self.level = level
        self.description = description
        self.severity: ValidationSeverity = ValidationSeverity.WARNING
    
    def validate(self, config: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """执行验证"""
        pass

class ValidationResult:
    """验证结果"""
    
    def __init__(self, rule: ValidationRule, passed: bool, message: str = ""):
        self.rule = rule
        self.passed = passed
        self.message = message
        self.suggestions: List[str] = []
        self.fix_suggestions: List[FixSuggestion] = []
        self.timestamp = datetime.now()

class FixSuggestion:
    """修复建议"""
    
    def __init__(self, description: str, fix_action: Callable, confidence: float = 0.8):
        self.description = description
        self.fix_action = fix_action
        self.confidence = confidence
```

### 2. 增强的验证器实现

```python
class EnhancedConfigValidator:
    """增强的配置验证器"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._load_builtin_rules()
        self.cache = ValidationCache()
    
    def register_rule(self, rule: ValidationRule) -> None:
        """注册验证规则"""
        self.rules[rule.rule_id] = rule
    
    def validate_config(self, config_path: str, levels: List[ValidationLevel] = None) -> ValidationReport:
        """验证配置文件"""
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
    
    def _validate_level(self, config: Dict[str, Any], level: ValidationLevel) -> List[ValidationResult]:
        """验证指定级别"""
        results = []
        level_rules = [rule for rule in self.rules.values() if rule.level == level]
        
        for rule in level_rules:
            context = ValidationContext(config=config, level=level)
            result = rule.validate(config, context)
            results.append(result)
        
        return results

class ValidationReport:
    """验证报告"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.timestamp = datetime.now()
        self.level_results: Dict[ValidationLevel, List[ValidationResult]] = {}
        self.summary: Dict[str, int] = {}
    
    def add_level_results(self, level: ValidationLevel, results: List[ValidationResult]) -> None:
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
                if not result.passed and result.rule.severity.value >= min_severity.value:
                    return False
        return True
```

### 3. 内置验证规则

```python
# 语法验证规则
class SyntaxValidationRule(ValidationRule):
    """语法验证规则"""
    
    def validate(self, config: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        result = ValidationResult(self, True)
        
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

# 模式验证规则
class SchemaValidationRule(ValidationRule):
    """模式验证规则"""
    
    def validate(self, config: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        result = ValidationResult(self, True)
        
        # 检查必需字段
        required_fields = ["name", "version", "nodes"]
        for field in required_fields:
            if field not in config:
                result.passed = False
                result.message = f"缺少必需字段: {field}"
                result.fix_suggestions.append(
                    FixSuggestion(f"添加字段: {field}", lambda: self._add_required_field(config, field))
                )
        
        # 检查字段类型
        if "nodes" in config and not isinstance(config["nodes"], dict):
            result.passed = False
            result.message = "nodes字段必须是字典类型"
        
        return result

# 语义验证规则
class SemanticValidationRule(ValidationRule):
    """语义验证规则"""
    
    def validate(self, config: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        result = ValidationResult(self, True)
        
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
```

### 4. 智能修复机制

```python
class ConfigFixer:
    """配置修复器"""
    
    def __init__(self, validator: EnhancedConfigValidator):
        self.validator = validator
        self.fix_strategies: Dict[str, FixStrategy] = {}
        self._register_fix_strategies()
    
    def auto_fix_config(self, config_path: str, confidence_threshold: float = 0.7) -> FixResult:
        """自动修复配置"""
        report = self.validator.validate_config(config_path)
        fixes_applied = []
        
        for suggestion in report.get_fix_suggestions():
            if suggestion.confidence >= confidence_threshold:
                try:
                    suggestion.fix_action()
                    fixes_applied.append(suggestion.description)
                except Exception as e:
                    logger.warning(f"修复失败: {suggestion.description}, 错误: {e}")
        
        return FixResult(fixes_applied, len(report.get_fix_suggestions()))
    
    def suggest_fixes(self, config_path: str) -> List[FixSuggestion]:
        """提供修复建议"""
        report = self.validator.validate_config(config_path)
        return report.get_fix_suggestions()

class FixStrategy:
    """修复策略"""
    
    def fix_missing_field(self, config: Dict[str, Any], field: str, default_value: Any) -> None:
        """修复缺失字段"""
        if field not in config:
            config[field] = default_value
    
    def fix_invalid_type(self, config: Dict[str, Any], field: str, expected_type: Type) -> None:
        """修复类型错误"""
        if field in config and not isinstance(config[field], expected_type):
            # 尝试类型转换或使用默认值
            try:
                config[field] = expected_type(config[field])
            except (ValueError, TypeError):
                config[field] = self._get_default_value(expected_type)
```

### 5. 性能优化和缓存

```python
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
```

## 实施计划

### 阶段1：基础验证框架（1周）
- 实现ValidationRule和ValidationResult基类
- 实现EnhancedConfigValidator核心逻辑
- 添加基本的内置验证规则

### 阶段2：高级验证功能（1周）
- 实现语义验证和依赖验证
- 添加智能修复机制
- 实现验证缓存和性能优化

### 阶段3：集成和测试（3天）
- 集成到WorkflowManager
- 编写全面的测试用例
- 性能测试和优化

## 配置示例

```yaml
# 验证规则配置
validation:
  levels:
    - syntax
    - schema
    - semantic
    - dependency
  rules:
    syntax:
      enabled: true
      strict_mode: false
    schema:
      enabled: true
      custom_schema: "path/to/schema.yaml"
    semantic:
      enabled: true
      business_rules: "path/to/rules.yaml"
  auto_fix:
    enabled: true
    confidence_threshold: 0.7
    backup_original: true
```

## 预期效果

1. **配置质量提升** - 全面的验证确保配置正确性
2. **开发效率提高** - 智能修复减少手动调试时间
3. **系统稳定性增强** - 提前发现配置问题
4. **维护成本降低** - 清晰的验证报告和修复建议

这个设计方案将为WorkflowManager提供强大的配置验证能力，显著提升工作流配置的质量和可靠性。