"""改进脱敏器的测试用例"""

import pytest
import time
from typing import Dict, Any, List
import json

from core.common.utils.redactor.redactor import Redactor, RedactorPattern, PatternCategory, LogLevel
from src.core.common.utils.boundary_matcher import BoundaryMatcher, BoundaryType, UnicodeCategory
from core.common.utils.redactor.regex_optimizer import RegexOptimizer, OptimizationLevel
from core.common.utils.redactor.pattern_config import PatternConfigManager, PatternConfig, RedactorConfig, ConfigFormat


class TestBoundaryMatcher:
    """边界匹配器测试"""

    def setup_method(self):
        """测试前设置"""
        self.boundary_matcher = BoundaryMatcher()

    def test_unicode_category_detection(self):
        """测试Unicode字符分类检测"""
        # 测试中文字符
        assert self.boundary_matcher.get_unicode_category('中') == UnicodeCategory.CJK
        assert self.boundary_matcher.get_unicode_category('国') == UnicodeCategory.CJK
        
        # 测试拉丁字符
        assert self.boundary_matcher.get_unicode_category('A') == UnicodeCategory.LATIN
        assert self.boundary_matcher.get_unicode_category('z') == UnicodeCategory.LATIN
        
        # 测试数字
        assert self.boundary_matcher.get_unicode_category('1') == UnicodeCategory.NUMBER
        assert self.boundary_matcher.get_unicode_category('0') == UnicodeCategory.NUMBER
        
        # 测试标点
        assert self.boundary_matcher.get_unicode_category('.') == UnicodeCategory.PUNCTUATION
        assert self.boundary_matcher.get_unicode_category('，') == UnicodeCategory.PUNCTUATION

    def test_email_pattern_creation(self):
        """测试邮箱模式创建"""
        pattern = self.boundary_matcher.create_email_pattern()
        
        # 测试正常邮箱
        assert pattern.search('test@example.com')
        assert pattern.search('user.name@domain.co.uk')
        
        # 测试中文环境中的邮箱
        text = '请联系test@example.com获取更多信息'
        assert pattern.search(text)
        
        # 测试边界情况
        assert not pattern.search('notanemail')
        assert not pattern.search('test@example')  # 缺少域名后缀

    def test_phone_pattern_creation(self):
        """测试电话号码模式创建"""
        # 中国手机号
        china_pattern = self.boundary_matcher.create_phone_pattern("china")
        assert china_pattern.search('13812345678')
        assert china_pattern.search('我的手机号是15912345678，请联系')
        assert not china_pattern.search('12345678901')  # 不符合中国手机号格式
        
        # 国际电话
        intl_pattern = self.boundary_matcher.create_phone_pattern("international")
        assert intl_pattern.search('+1-555-123-4567')
        assert intl_pattern.search('+86 138 1234 5678')

    def test_chinese_name_pattern(self):
        """测试中文姓名模式"""
        pattern = self.boundary_matcher.create_chinese_name_pattern()
        
        # 测试常见中文姓名
        assert pattern.search('张三')
        assert pattern.search('李四')
        assert pattern.search('王小明')
        assert pattern.search('欧阳修')
        
        # 测试边界情况
        text = '我叫张三，他是李四'
        matches = pattern.findall(text)
        assert '张三' in matches
        assert '李四' in matches
        
        # 测试不应匹配的情况
        assert not pattern.search('中国')  # 国家名
        assert not pattern.search('人民')  # 通用词汇

    def test_id_card_pattern(self):
        """测试身份证号模式"""
        pattern = self.boundary_matcher.create_id_card_pattern("china")
        
        # 测试有效身份证号
        assert pattern.search('11010519491231002X')
        assert pattern.search('身份证号：11010519491231002X')
        
        # 测试无效身份证号
        assert not pattern.search('123456789012345678')  # 格式不正确
        assert not pattern.search('11010519491331002X')  # 月份无效

    def test_boundary_analysis(self):
        """测试边界分析"""
        text = 'Hello世界123'
        analysis = self.boundary_matcher.analyze_text_boundaries(text)
        
        assert analysis['length'] == 10
        assert len(analysis['unicode_categories']) > 0
        assert len(analysis['potential_boundaries']) > 0
        
        # 检查边界变化点
        boundaries = analysis['potential_boundaries']
        boundary_positions = [b['position'] for b in boundaries]
        assert 5 in boundary_positions  # Hello到世界的边界
        assert 8 in boundary_positions  # 世界到123的边界


class TestRegexOptimizer:
    """正则表达式优化器测试"""

    def setup_method(self):
        """测试前设置"""
        self.optimizer = RegexOptimizer(OptimizationLevel.BASIC)

    def test_basic_optimization(self):
        """测试基础优化"""
        # 测试字符类优化
        original = r'[a-zA-Z]'
        optimized = self.optimizer.optimize_pattern(original)
        assert r'[A-Za-z]' in optimized
        
        # 测试量词优化
        original = r'a{0,1}'
        optimized = self.optimizer.optimize_pattern(original)
        assert 'a?' in optimized

    def test_pattern_validation(self):
        """测试模式验证"""
        # 有效模式
        is_valid, error = self.optimizer.validate_pattern(r'\d+')
        assert is_valid
        assert error is None
        
        # 无效模式
        is_valid, error = self.optimizer.validate_pattern(r'[unclosed')
        assert not is_valid
        assert error is not None

    def test_performance_benchmark(self):
        """测试性能基准"""
        pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        test_text = 'SSN: 123-45-6789, another: 987-65-4321'
        
        metrics = self.optimizer.benchmark_pattern(pattern, test_text, iterations=100)
        
        assert metrics.pattern == pattern
        assert metrics.compilation_time >= 0
        assert metrics.match_time >= 0
        assert metrics.substitution_time >= 0
        assert metrics.match_count > 0

    def test_improvement_suggestions(self):
        """测试改进建议"""
        # 测试包含常见问题的模式
        pattern = r'.*.*test.*'
        suggestions = self.optimizer.suggest_improvements(pattern)
        assert len(suggestions) > 0
        
        # 测试括号不匹配
        pattern = r'(test'
        suggestions = self.optimizer.suggest_improvements(pattern)
        assert any('括号' in s for s in suggestions)


class TestPatternConfigManager:
    """模式配置管理器测试"""

    def setup_method(self):
        """测试前设置"""
        import tempfile
        import shutil
        
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = PatternConfigManager(self.temp_dir)

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_default_config_creation(self):
        """测试默认配置创建"""
        config = self.config_manager.get_config('default')
        
        assert isinstance(config, RedactorConfig)
        assert len(config.patterns) > 0
        assert config.default_replacement == "***"
        assert config.enable_unicode is True

    def test_config_save_and_load(self):
        """测试配置保存和加载"""
        # 创建测试配置
        pattern_config = PatternConfig(
            name="test_pattern",
            pattern=r"test_\d+",
            category="contact",
            description="测试模式",
            priority=80
        )
        
        config = RedactorConfig(
            patterns=[pattern_config],
            default_replacement="TEST"
        )
        
        # 保存配置
        filepath = self.config_manager.save_config('test', config, ConfigFormat.YAML)
        assert filepath.endswith('.yaml')
        
        # 加载配置
        loaded_config = self.config_manager.load_config('test')
        assert len(loaded_config.patterns) == 1
        assert loaded_config.patterns[0].name == "test_pattern"
        assert loaded_config.default_replacement == "TEST"

    def test_pattern_management(self):
        """测试模式管理"""
        config = self.config_manager.get_config('default')
        original_count = len(config.patterns)
        
        # 添加模式
        new_pattern = PatternConfig(
            name="new_test_pattern",
            pattern=r"new_test_\d+",
            category="contact",
            description="新测试模式"
        )
        
        success = self.config_manager.add_pattern_to_config('default', new_pattern)
        assert success
        
        # 验证模式已添加
        updated_config = self.config_manager.get_config('default')
        assert len(updated_config.patterns) == original_count + 1
        
        # 删除模式
        success = self.config_manager.remove_pattern_from_config('default', 'new_test_pattern')
        assert success
        
        # 验证模式已删除
        final_config = self.config_manager.get_config('default')
        assert len(final_config.patterns) == original_count

    def test_config_validation(self):
        """测试配置验证"""
        # 创建有效配置
        valid_pattern = PatternConfig(
            name="valid_pattern",
            pattern=r"\d+",
            category="contact",
            description="有效模式"
        )
        
        valid_config = RedactorConfig(patterns=[valid_pattern])
        errors = self.config_manager.validate_config(valid_config)
        assert len(errors) == 0
        
        # 创建无效配置
        invalid_pattern = PatternConfig(
            name="invalid_pattern",
            pattern=r"[unclosed",
            category="invalid_category",
            description="无效模式"
        )
        
        invalid_config = RedactorConfig(patterns=[invalid_pattern])
        errors = self.config_manager.validate_config(invalid_config)
        assert len(errors) > 0

    def test_pattern_filtering(self):
        """测试模式过滤"""
        # 添加测试模式
        test_pattern = PatternConfig(
            name="test_contact",
            pattern=r"test_\d+",
            category="contact",
            description="测试联系方式",
            tags=["test", "contact"]
        )
        
        self.config_manager.add_pattern_to_config('default', test_pattern)
        
        # 按分类过滤
        contact_patterns = self.config_manager.get_patterns_by_category('default', 'contact')
        assert len(contact_patterns) > 0
        assert any(p.name == 'test_contact' for p in contact_patterns)
        
        # 按标签过滤
        tagged_patterns = self.config_manager.get_patterns_by_tag('default', 'test')
        assert len(tagged_patterns) > 0
        assert all(p.tags and 'test' in p.tags for p in tagged_patterns)


class TestUnicodeRedactor:
    """Unicode脱敏器测试"""

    def setup_method(self):
        """测试前设置"""
        self.redactor = Redactor()

    def test_email_redaction(self):
        """测试邮箱脱敏"""
        # 基本邮箱
        text = '请联系test@example.com获取更多信息'
        result = self.redactor.redact(text)
        assert '***' in result
        assert 'test@example.com' not in result
        
        # 多个邮箱
        text = '邮箱1: user1@domain.com, 邮箱2: user2@domain.org'
        result = self.redactor.redact(text)
        assert result.count('***') >= 2

    def test_chinese_context_redaction(self):
        """测试中文环境下的脱敏"""
        # 中文中的邮箱
        text = '我的邮箱是zhang.san@example.com，请发邮件给我'
        result = self.redactor.redact(text)
        assert 'zhang.san@example.com' not in result
        assert '***' in result
        
        # 中文中的手机号
        text = '我的手机号是13812345678，请致电'
        result = self.redactor.redact(text)
        assert '13812345678' not in result
        assert '***' in result

    def test_chinese_name_redaction(self):
        """测试中文姓名脱敏"""
        text = '张三和李四是好朋友，王五也认识他们'
        result = self.redactor.redact(text, categories=[PatternCategory.CHINESE])
        
        # 检查姓名是否被脱敏
        assert '张三' not in result or '***' in result
        assert '李四' not in result or '***' in result
        assert '王五' not in result or '***' in result

    def test_id_card_redaction(self):
        """测试身份证号脱敏"""
        text = '身份证号：11010519491231002X，请妥善保管'
        result = self.redactor.redact(text)
        assert '11010519491231002X' not in result
        assert '***' in result

    def test_credit_card_redaction(self):
        """测试信用卡号脱敏"""
        # Visa卡
        text = '信用卡号：4111111111111111，有效期12/25'
        result = self.redactor.redact(text)
        assert '4111111111111111' not in result
        assert '***' in result
        
        # MasterCard
        text = 'MasterCard: 5555555555554444'
        result = self.redactor.redact(text)
        assert '5555555555554444' not in result

    def test_api_key_redaction(self):
        """测试API密钥脱敏"""
        # OpenAI API密钥
        text = 'API Key: sk-1234567890abcdef1234567890abcdef12345678'
        result = self.redactor.redact(text)
        assert 'sk-1234567890abcdef1234567890abcdef12345678' not in result
        assert '***' in result
        
        # Google API密钥
        text = 'Google Key: AIza1234567890abcdef1234567890abcdef12345'
        result = self.redactor.redact(text)
        assert 'AIza1234567890abcdef1234567890abcdef12345' not in result

    def test_dict_redaction(self):
        """测试字典脱敏"""
        data = {
            'name': '张三',
            'email': 'zhangsan@example.com',
            'phone': '13812345678',
            'id_card': '11010519491231002X',
            'nested': {
                'secret': 'password123'
            }
        }
        
        result = self.redactor.redact_dict(data)
        
        assert result['email'] == '***'
        assert result['phone'] == '***'
        assert result['id_card'] == '***'
        assert result['nested']['secret'] == '***'

    def test_json_redaction(self):
        """测试JSON脱敏"""
        json_str = json.dumps({
            'user': {
                'name': '李四',
                'contact': 'lisi@example.com',
                'phone': '15912345678'
            }
        }, ensure_ascii=False)
        
        result = self.redactor.redact_json(json_str)
        
        assert 'lisi@example.com' not in result
        assert '15912345678' not in result
        assert '***' in result

    def test_sensitive_detection(self):
        """测试敏感信息检测"""
        # 包含敏感信息的文本
        text = '请联系test@example.com，电话13812345678'
        assert self.redactor.is_sensitive(text)
        
        # 不包含敏感信息的文本
        text = '这是一段普通的文本，没有敏感信息'
        assert not self.redactor.is_sensitive(text)

    def test_sensitive_parts_extraction(self):
        """测试敏感信息部分提取"""
        text = '邮箱1: user1@domain.com, 邮箱2: user2@domain.org, 电话: 13812345678'
        parts = self.redactor.get_sensitive_parts(text)
        
        assert len(parts) >= 3
        assert any(p['pattern_name'] == 'email_unicode' for p in parts)
        assert any(p['pattern_name'] == 'phone_china' for p in parts)
        
        # 检查返回的信息结构
        for part in parts:
            assert 'text' in part
            assert 'start' in part
            assert 'end' in part
            assert 'pattern_name' in part
            assert 'category' in part

    def test_category_filtering(self):
        """测试分类过滤"""
        text = '邮箱: test@example.com, 姓名: 张三, 电话: 13812345678'
        
        # 只脱敏联系方式
        result = self.redactor.redact(text, categories=[PatternCategory.CONTACT])
        assert 'test@example.com' not in result
        assert '13812345678' not in result
        assert '张三' in result  # 姓名应该保留
        
        # 只脱敏中文信息
        result = self.redactor.redact(text, categories=[PatternCategory.CHINESE])
        assert '张三' not in result
        assert 'test@example.com' in result  # 邮箱应该保留
        assert '13812345678' in result  # 电话应该保留

    def test_unicode_validation(self):
        """测试Unicode验证"""
        # 纯ASCII文本
        text = 'Hello World 123'
        result = self.redactor.validate_unicode_text(text)
        assert result['has_chinese'] is False
        assert result['has_non_ascii'] is False
        
        # 包含中文的文本
        text = 'Hello 世界 123'
        result = self.redactor.validate_unicode_text(text)
        assert result['has_chinese'] is True
        assert result['has_non_ascii'] is True
        assert len(result['chinese_chars']) == 2

    def test_custom_pattern_addition(self):
        """测试自定义模式添加"""
        # 添加自定义模式
        custom_pattern = RedactorPattern(
            name="custom_test",
            pattern=r"TEST_\d+",
            category=PatternCategory.TECHNICAL,
            description="自定义测试模式",
            priority=90
        )
        
        self.redactor.add_pattern(custom_pattern)
        
        # 测试自定义模式
        text = '这是TEST_123，应该被脱敏'
        result = self.redactor.redact(text)
        assert 'TEST_123' not in result
        assert '***' in result

    def test_performance_comparison(self):
        """测试性能对比"""
        # 创建大量测试文本
        test_text = '请联系test@example.com，电话13812345678，身份证11010519491231002X' * 100
        
        # 测试改进版脱敏器性能
        start_time = time.time()
        result = self.redactor.redact(test_text)
        improved_time = time.time() - start_time
        
        # 验证结果正确性
        assert 'test@example.com' not in result
        assert '13812345678' not in result
        assert '11010519491231002X' not in result
        
        # 性能应该在合理范围内（这里只是简单检查）
        assert improved_time < 1.0  # 应该在1秒内完成


class TestIntegration:
    """集成测试"""

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 1. 创建配置管理器
        config_manager = PatternConfigManager()
        
        # 2. 加载默认配置
        config = config_manager.get_config('default')
        
        # 3. 创建脱敏器
        redactor = Redactor([p.to_redactor_pattern() for p in config.patterns])
        
        # 4. 测试复杂文本
        test_text = '''
        用户信息：
        姓名：张三
        邮箱：zhangsan@example.com
        电话：13812345678
        身份证：11010519491231002X
        信用卡：4111111111111111
        API密钥：sk-1234567890abcdef1234567890abcdef12345678
        '''
        
        # 5. 执行脱敏
        result = redactor.redact(test_text)
        
        # 6. 验证结果
        sensitive_info = [
            'zhangsan@example.com',
            '13812345678',
            '11010519491231002X',
            '4111111111111111',
            'sk-1234567890abcdef1234567890abcdef12345678'
        ]
        
        for info in sensitive_info:
            assert info not in result
        
        assert '***' in result

    def test_config_driven_redaction(self):
        """测试配置驱动的脱敏"""
        # 创建自定义配置
        custom_pattern = PatternConfig(
            name="custom_sensitive",
            pattern=r"SECRET_\w+",
            category="technical",
            description="自定义敏感信息",
            priority=95
        )
        
        config_manager = PatternConfigManager()
        config_manager.add_pattern_to_config('default', custom_pattern)
        
        # 重新加载配置
        config = config_manager.get_config('default')
        redactor = Redactor([p.to_redactor_pattern() for p in config.patterns])
        
        # 测试自定义模式
        text = '这里包含SECRET_DATA和SECRET_INFO'
        result = redactor.redact(text)
        
        assert 'SECRET_DATA' not in result
        assert 'SECRET_INFO' not in result
        assert result.count('***') >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])