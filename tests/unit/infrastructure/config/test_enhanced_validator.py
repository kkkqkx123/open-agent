"""EnhancedConfigValidator单元测试"""

import pytest
import tempfile
import os
from pathlib import Path
from infrastructure.config.processor.enhanced_validator import (
    EnhancedConfigValidator,
    create_enhanced_config_validator,
    ValidationLevel,
    ValidationSeverity,
    ValidationRule,
    EnhancedValidationResult,
    ValidationReport,
    FixSuggestion,
    ConfigFixer
)


class TestEnhancedConfigValidator:
    """EnhancedConfigValidator测试类"""
    
    def setup_method(self):
        """测试方法设置"""
        self.validator = create_enhanced_config_validator()
    
    def test_create_enhanced_config_validator(self):
        """测试创建增强的配置验证器"""
        validator = create_enhanced_config_validator()
        assert isinstance(validator, EnhancedConfigValidator)
        assert len(validator.rules) > 0
    
    def test_validate_config_syntax_valid_yaml(self):
        """测试验证有效的YAML语法"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}}
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.SYNTAX])
        assert report.is_valid()
        assert len(report.level_results[ValidationLevel.SYNTAX]) == 1
        result = report.level_results[ValidationLevel.SYNTAX][0]
        assert result.passed is True
    
    def test_validate_config_schema_valid(self):
        """测试验证有效的配置结构"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}}
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.SCHEMA])
        assert report.is_valid()
        schema_results = report.level_results[ValidationLevel.SCHEMA]
        assert len(schema_results) == 1
        assert schema_results[0].passed is True
    
    def test_validate_config_schema_missing_required_fields(self):
        """测试验证缺少必需字段"""
        config_data = {
            "name": "test_config"
            # 缺少version和nodes字段
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.SCHEMA])
        assert not report.is_valid()
        schema_results = report.level_results[ValidationLevel.SCHEMA]
        assert len(schema_results) == 1
        assert schema_results[0].passed is False
        assert "缺少必需字段" in schema_results[0].message
    
    def test_validate_config_semantic_valid(self):
        """测试验证有效的语义"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {
                "node1": {"type": "input"},
                "node2": {"type": "processor"}
            },
            "edges": [
                {"from_node": "node1", "to_node": "node2"}
            ]
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.SEMANTIC])
        assert report.is_valid()
        semantic_results = report.level_results[ValidationLevel.SEMANTIC]
        assert len(semantic_results) == 1
        assert semantic_results[0].passed is True
    
    def test_validate_config_semantic_invalid_references(self):
        """测试验证无效的节点引用"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {
                "node1": {"type": "input"}
            },
            "edges": [
                {"from_node": "node1", "to_node": "nonexistent_node"}  # 引用不存在的节点
            ]
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.SEMANTIC])
        assert not report.is_valid()
        semantic_results = report.level_results[ValidationLevel.SEMANTIC]
        assert len(semantic_results) == 1
        assert semantic_results[0].passed is False
        assert "引用不存在的节点" in semantic_results[0].message
    
    def test_validate_config_dependency_valid(self):
        """测试验证有效的依赖配置"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}},
            "dependencies": {
                "external_service": {
                    "enabled": True,
                    "url": "https://api.example.com"
                }
            }
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.DEPENDENCY])
        assert report.is_valid()
        dependency_results = report.level_results[ValidationLevel.DEPENDENCY]
        assert len(dependency_results) == 1
        assert dependency_results[0].passed is True
    
    def test_validate_config_dependency_missing_url(self):
        """测试验证缺少URL的依赖配置"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}},
            "dependencies": {
                "external_service": {
                    "enabled": True
                    # 缺少url或path
                }
            }
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.DEPENDENCY])
        assert not report.is_valid()
        dependency_results = report.level_results[ValidationLevel.DEPENDENCY]
        assert len(dependency_results) == 1
        assert dependency_results[0].passed is False
        assert "缺少URL或路径配置" in dependency_results[0].message
    
    def test_validate_config_performance_warnings(self):
        """测试验证性能配置警告"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}},
            "performance": {
                "cache": {
                    "enabled": True,
                    "max_size": 50000  # 过大的缓存大小
                },
                "concurrency": {
                    "max_workers": 200  # 过大的并发数
                }
            }
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.PERFORMANCE])
        # 性能验证可能产生警告但不一定是错误
        performance_results = report.level_results[ValidationLevel.PERFORMANCE]
        assert len(performance_results) == 1
        # 检查是否有警告信息
        if not performance_results[0].passed:
            assert "警告" in performance_results[0].message
    
    def test_validate_config_file(self):
        """测试验证配置文件"""
        # 创建临时YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: test_config
version: 1.0.0
nodes:
  node1:
    type: input
            """)
            temp_file = f.name
        
        try:
            report = self.validator.validate_config(temp_file)
            assert report.is_valid()
            assert report.config_path == temp_file
        finally:
            os.unlink(temp_file)
    
    def test_validate_config_file_not_found(self):
        """测试验证不存在的配置文件"""
        with pytest.raises(FileNotFoundError):
            self.validator.validate_config("nonexistent.yaml")
    
    def test_validation_report_summary(self):
        """测试验证报告摘要"""
        config_data = {
            "name": "test_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}}
        }
        
        report = self.validator.validate_config_data(config_data)
        summary = report.summary
        assert summary["total_rules"] > 0
        assert summary["passed"] > 0
        assert summary["failed"] >= 0
    
    def test_get_fix_suggestions(self):
        """测试获取修复建议"""
        config_data = {
            "name": "test_config"
            # 缺少必需字段
        }
        
        report = self.validator.validate_config_data(config_data, [ValidationLevel.SCHEMA])
        suggestions = report.get_fix_suggestions()
        # 应该有修复建议
        assert len(suggestions) > 0
        assert isinstance(suggestions[0], FixSuggestion)


class TestConfigFixer:
    """ConfigFixer测试类"""
    
    def setup_method(self):
        """测试方法设置"""
        self.validator = create_enhanced_config_validator()
        self.fixer = ConfigFixer(self.validator)
    
    def test_auto_fix_config(self):
        """测试自动修复配置"""
        config_data = {
            "name": "test_config"
            # 缺少必需字段
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: test_config
            """)
            temp_file = f.name
        
        try:
            fixed_config = self.fixer.auto_fix_config(temp_file)
            # 修复后的配置应该包含必需字段
            assert "version" in fixed_config
            assert "nodes" in fixed_config
        finally:
            os.unlink(temp_file)
    
    def test_suggest_fixes(self):
        """测试提供修复建议"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: test_config
            """)
            temp_file = f.name
        
        try:
            suggestions = self.fixer.suggest_fixes(temp_file)
            assert len(suggestions) > 0
            assert isinstance(suggestions[0], FixSuggestion)
        finally:
            os.unlink(temp_file)


class TestValidationRule:
    """验证规则测试"""
    
    def test_validation_rule_creation(self):
        """测试创建验证规则"""
        class TestRule(ValidationRule):
            def validate(self, config, context):
                return EnhancedValidationResult(
                    rule_id=self.rule_id,
                    level=self.level,
                    passed=True
                )
        
        rule = TestRule("test_001", ValidationLevel.SYNTAX, "测试规则")
        assert rule.rule_id == "test_001"
        assert rule.level == ValidationLevel.SYNTAX
        assert rule.description == "测试规则"
    
    def test_custom_validation_rule(self):
        """测试自定义验证规则"""
        class CustomRule(ValidationRule):
            def validate(self, config, context):
                result = EnhancedValidationResult(
                    rule_id=self.rule_id,
                    level=self.level,
                    passed=True
                )
                
                if "custom_field" not in config:
                    result.passed = False
                    result.message = "缺少自定义字段"
                
                return result
        
        validator = create_enhanced_config_validator()
        validator.register_rule(CustomRule("custom_001", ValidationLevel.SCHEMA, "自定义规则"))
        
        config_data = {"name": "test"}
        report = validator.validate_config_data(config_data, [ValidationLevel.SCHEMA])
        
        # 查找自定义规则的结果
        custom_results = [r for r in report.level_results[ValidationLevel.SCHEMA] 
                         if r.rule_id == "custom_001"]
        assert len(custom_results) == 1
        assert custom_results[0].passed is False
        assert "缺少自定义字段" in custom_results[0].message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])