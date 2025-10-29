"""独立演示增强功能

完全独立的演示脚本，不依赖复杂的导入路径。
"""

import tempfile
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# 直接复制EnhancedStateManager的实现
class ConflictType(Enum):
    """冲突类型枚举"""
    FIELD_MODIFICATION = "field_modification"
    LIST_OPERATION = "list_operation"
    STRUCTURE_CHANGE = "structure_change"

class ConflictResolutionStrategy(Enum):
    """冲突解决策略枚举"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE_CHANGES = "merge_changes"

@dataclass
class Conflict:
    """冲突信息"""
    field_path: str
    current_value: Any
    new_value: Any
    conflict_type: ConflictType
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class StateVersion:
    """状态版本信息"""
    version_id: str
    state_data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]

class StateConflictResolver:
    """状态冲突解决器"""
    
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        self.strategy = strategy
        self.conflict_history: List[Conflict] = []
    
    def resolve_conflict(self, current_state: Dict[str, Any], new_state: Dict[str, Any], 
                        conflict: Conflict) -> Tuple[Dict[str, Any], bool]:
        """解决单个冲突"""
        self.conflict_history.append(conflict)
        
        if self.strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            return self._last_write_wins(current_state, new_state, conflict)
        elif self.strategy == ConflictResolutionStrategy.FIRST_WRITE_WINS:
            return self._first_write_wins(current_state, new_state, conflict)
        elif self.strategy == ConflictResolutionStrategy.MERGE_CHANGES:
            return self._merge_changes(current_state, new_state, conflict)
        else:
            return current_state, False
    
    def _last_write_wins(self, current_state: Dict[str, Any], new_state: Dict[str, Any], 
                        conflict: Conflict) -> Tuple[Dict[str, Any], bool]:
        """最后写入获胜策略"""
        # 直接使用新值
        return new_state, True
    
    def _first_write_wins(self, current_state: Dict[str, Any], new_state: Dict[str, Any], 
                         conflict: Conflict) -> Tuple[Dict[str, Any], bool]:
        """首先写入获胜策略"""
        # 保持当前值
        return current_state, True
    
    def _merge_changes(self, current_state: Dict[str, Any], new_state: Dict[str, Any], 
                      conflict: Conflict) -> Tuple[Dict[str, Any], bool]:
        """合并更改策略"""
        # 简单合并：对于字典，合并字段；对于列表，合并元素
        if isinstance(current_state, dict) and isinstance(new_state, dict):
            merged = current_state.copy()
            merged.update(new_state)
            return merged, True
        return new_state, True

class EnhancedStateManager:
    """增强状态管理器"""
    
    def __init__(self, conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        self.conflict_resolver = StateConflictResolver(conflict_strategy)
        self.state_versions: Dict[str, StateVersion] = {}
        self.conflict_history: List[Conflict] = []
    
    def detect_conflicts(self, current_state: Dict[str, Any], new_state: Dict[str, Any]) -> List[Conflict]:
        """检测状态冲突"""
        conflicts = []
        
        # 检查字段修改冲突
        for key in set(current_state.keys()) | set(new_state.keys()):
            current_val = current_state.get(key)
            new_val = new_state.get(key)
            
            if key in current_state and key in new_state:
                if current_val != new_val:
                    conflicts.append(Conflict(
                        field_path=key,
                        current_value=current_val,
                        new_value=new_val,
                        conflict_type=ConflictType.FIELD_MODIFICATION
                    ))
            elif key in new_state and key not in current_state:
                # 新字段添加
                conflicts.append(Conflict(
                    field_path=key,
                    current_value=None,
                    new_value=new_val,
                    conflict_type=ConflictType.STRUCTURE_CHANGE
                ))
        
        return conflicts
    
    def update_state_with_conflict_resolution(self, current_state: Dict[str, Any], 
                                            new_state: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Conflict]]:
        """使用冲突解决策略更新状态"""
        conflicts = self.detect_conflicts(current_state, new_state)
        unresolved_conflicts = []
        
        result_state = current_state.copy()
        
        for conflict in conflicts:
            resolved_state, resolved = self.conflict_resolver.resolve_conflict(
                result_state, new_state, conflict
            )
            if resolved:
                result_state = resolved_state
            else:
                unresolved_conflicts.append(conflict)
        
        return result_state, unresolved_conflicts
    
    def create_state_version(self, state: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """创建状态版本"""
        version_id = f"v{len(self.state_versions) + 1}"
        version = StateVersion(
            version_id=version_id,
            state_data=state.copy(),
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.state_versions[version_id] = version
        return version_id
    
    def get_conflict_history(self) -> List[Conflict]:
        """获取冲突历史"""
        return self.conflict_resolver.conflict_history.copy()

# 直接复制EnhancedConfigValidator的实现
class ValidationLevel(Enum):
    """验证级别枚举"""
    SYNTAX = "syntax"
    SCHEMA = "schema"
    SEMANTIC = "semantic"
    DEPENDENCY = "dependency"
    PERFORMANCE = "performance"

class ValidationSeverity(Enum):
    """验证严重性枚举"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    """验证结果"""
    level: ValidationLevel
    rule_name: str
    message: str
    passed: bool
    severity: ValidationSeverity
    fix_suggestion: Optional[str] = None

@dataclass
class ValidationReport:
    """验证报告"""
    config_path: str
    level_results: Dict[ValidationLevel, List[ValidationResult]]
    summary: str
    is_valid: bool
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.level_results = {level: [] for level in ValidationLevel}
        self.summary = ""
        self.is_valid = True
    
    def add_result(self, result: ValidationResult):
        """添加验证结果"""
        self.level_results[result.level].append(result)
        if result.severity == ValidationSeverity.ERROR and not result.passed:
            self.is_valid = False
    
    def generate_summary(self):
        """生成摘要"""
        total_checks = sum(len(results) for results in self.level_results.values())
        passed_checks = sum(1 for results in self.level_results.values() 
                           for result in results if result.passed)
        
        self.summary = f"验证完成: {passed_checks}/{total_checks} 通过"

class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, name: str, level: ValidationLevel, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.name = name
        self.level = level
        self.severity = severity
    
    def validate(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证配置数据"""
        raise NotImplementedError

class RequiredFieldsRule(ValidationRule):
    """必需字段验证规则"""
    
    def __init__(self):
        super().__init__("required_fields", ValidationLevel.SCHEMA)
    
    def validate(self, config_data: Dict[str, Any]) -> ValidationResult:
        required_fields = ["name", "version", "nodes"]
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            return ValidationResult(
                level=self.level,
                rule_name=self.name,
                message=f"缺少必需字段: {', '.join(missing_fields)}",
                passed=False,
                severity=self.severity,
                fix_suggestion=f"添加缺失字段: {', '.join(missing_fields)}"
            )
        
        return ValidationResult(
            level=self.level,
            rule_name=self.name,
            message="所有必需字段都存在",
            passed=True,
            severity=self.severity
        )

class EnhancedConfigValidator:
    """增强配置验证器"""
    
    def __init__(self):
        self.validation_rules: List[ValidationRule] = []
        self._setup_default_rules()
        self.cache: Dict[str, ValidationReport] = {}
    
    def _setup_default_rules(self):
        """设置默认验证规则"""
        self.validation_rules.append(RequiredFieldsRule())
    
    def validate_config_data(self, config_data: Dict[str, Any]) -> ValidationReport:
        """验证配置数据"""
        report = ValidationReport("memory_config")
        
        for rule in self.validation_rules:
            result = rule.validate(config_data)
            report.add_result(result)
        
        report.generate_summary()
        return report
    
    def validate_config(self, config_path: str) -> ValidationReport:
        """验证配置文件"""
        # 简化实现：直接读取JSON/YAML文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    config_data = json.load(f)
                else:
                    # 简化处理：假设是YAML格式
                    import yaml
                    config_data = yaml.safe_load(f)
            
            return self.validate_config_data(config_data)
        except Exception as e:
            report = ValidationReport(config_path)
            report.add_result(ValidationResult(
                level=ValidationLevel.SYNTAX,
                rule_name="file_parsing",
                message=f"配置文件解析失败: {str(e)}",
                passed=False,
                severity=ValidationSeverity.ERROR
            ))
            report.generate_summary()
            return report

# 演示函数
def demo_enhanced_state_manager():
    """演示增强状态管理器功能"""
    print("=" * 60)
    print("增强状态管理器演示")
    print("=" * 60)
    
    # 创建增强的状态管理器
    manager = EnhancedStateManager(
        conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
    )
    
    # 创建测试状态
    state1 = {
        "input": "原始输入",
        "output": None,
        "tool_calls": [],
        "iteration_count": 0
    }
    
    state2 = {
        "input": "冲突输入",
        "output": "测试输出",
        "tool_calls": ["tool1"],
        "custom_field": "新字段值"
    }
    
    print("状态1:", {k: v for k, v in state1.items() if v is not None})
    print("状态2:", {k: v for k, v in state2.items() if v is not None})
    
    # 检测冲突
    conflicts = manager.detect_conflicts(state1, state2)
    print(f"检测到 {len(conflicts)} 个冲突:")
    for conflict in conflicts:
        print(f"  - {conflict.field_path}: {conflict.current_value} -> {conflict.new_value} ({conflict.conflict_type.value})")
    
    # 使用冲突解决策略更新状态
    resolved_state, unresolved = manager.update_state_with_conflict_resolution(state1, state2)
    print(f"解决冲突后的状态: {resolved_state}")
    print(f"未解决的冲突: {len(unresolved)}")
    
    # 测试不同冲突解决策略
    print("\n不同冲突解决策略测试:")
    strategies = [
        ConflictResolutionStrategy.LAST_WRITE_WINS,
        ConflictResolutionStrategy.FIRST_WRITE_WINS,
        ConflictResolutionStrategy.MERGE_CHANGES
    ]
    
    for strategy in strategies:
        manager.conflict_resolver.strategy = strategy
        resolved_state, _ = manager.update_state_with_conflict_resolution(state1, state2)
        print(f"  {strategy.value}: {resolved_state['input']}")
    
    # 状态版本控制
    version_id = manager.create_state_version(resolved_state, {"description": "解决冲突后的状态"})
    print(f"\n创建状态版本: {version_id}")
    
    # 获取冲突历史
    history = manager.get_conflict_history()
    print(f"冲突历史记录: {len(history)} 条")

def demo_enhanced_config_validator():
    """演示增强配置验证器功能"""
    print("\n" + "=" * 60)
    print("增强配置验证器演示")
    print("=" * 60)
    
    # 创建增强的配置验证器
    validator = EnhancedConfigValidator()
    
    # 测试配置数据
    test_configs = [
        {
            "name": "valid_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}}
        },
        {
            "name": "invalid_config"
            # 缺少version和nodes字段
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n配置 {i} 验证结果:")
        report = validator.validate_config_data(config)
        
        print(f"  配置是否有效: {report.is_valid}")
        print(f"  验证摘要: {report.summary}")
        
        for level, results in report.level_results.items():
            for result in results:
                status = "通过" if result.passed else "失败"
                print(f"  {level.value}: {status} - {result.message}")
    
    # 演示配置文件验证
    print("\n配置文件验证演示:")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "name": "test_workflow",
            "version": "1.0.0",
            "nodes": {
                "start_node": {"type": "input"}
            }
        }, f)
        temp_file = f.name
    
    try:
        report = validator.validate_config(temp_file)
        print(f"配置文件验证结果: {'有效' if report.is_valid else '无效'}")
    finally:
        os.unlink(temp_file)

def main():
    """主演示函数"""
    print("Modular Agent Framework - 第一阶段优化功能独立演示")
    print("实现内容:")
    print("1. EnhancedStateManager - 状态冲突解决基础框架")
    print("2. EnhancedConfigValidator - 多层次配置验证框架")
    print("3. 单元测试覆盖 - 确保功能正确性")
    print("4. 系统集成 - 依赖注入配置")
    print()
    
    demo_enhanced_state_manager()
    demo_enhanced_config_validator()
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)

if __name__ == "__main__":
    main()