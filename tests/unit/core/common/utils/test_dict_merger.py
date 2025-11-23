"""DictMerger单元测试"""

from src.core.common.utils.dict_merger import DictMerger


class TestDictMerger:
    """DictMerger测试类"""

    def setup_method(self):
        """测试前准备"""
        self.merger = DictMerger()

    def test_merge_dicts(self):
        """测试合并字典"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        expected = {"a": 1, "b": 3, "c": 4}

        result = self.merger.merge_dicts(dict1, dict2)
        assert result == expected

    def test_deep_merge_simple(self):
        """测试简单深度合并"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        expected = {"a": 1, "b": 3, "c": 4}

        result = self.merger.deep_merge(dict1, dict2)
        assert result == expected

    def test_deep_merge_nested(self):
        """测试嵌套字典深度合并"""
        dict1 = {"a": 1, "b": {"x": 10, "y": 20}}
        dict2 = {"b": {"y": 30, "z": 40}, "c": 3}
        expected = {"a": 1, "b": {"x": 10, "y": 30, "z": 40}, "c": 3}

        result = self.merger.deep_merge(dict1, dict2)
        assert result == expected

    def test_deep_merge_with_lists(self):
        """测试包含列表的深度合并"""
        dict1 = {"a": [1, 2, 3], "b": {"x": [10, 20]}}
        dict2 = {"a": [3, 4, 5], "b": {"x": [20, 30], "y": [40]}}
        expected = {"a": [1, 2, 3, 4, 5], "b": {"x": [10, 20, 30], "y": [40]}}

        result = self.merger.deep_merge(dict1, dict2)
        assert result == expected

    def test_merge_group_config(self):
        """测试合并组配置和个体配置"""
        group_config = {"model": "gpt-3.5", "temperature": 0.7, "tools": ["tool1", "tool2"]}
        individual_config = {"model": "gpt-4", "max_tokens": 100, "tools": ["tool3"]}
        expected = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 100, "tools": ["tool3"]}

        result = self.merger.merge_group_config(group_config, individual_config)
        assert result == expected

    def test_merge_group_config_without_override_fields(self):
        """测试合并组配置和个体配置（不覆盖特定字段）"""
        group_config = {"model": "gpt-3.5", "temperature": 0.7, "other": "value"}
        individual_config = {"model": "gpt-4", "max_tokens": 1000}
        expected = {"model": "gpt-4", "temperature": 0.7, "other": "value", "max_tokens": 1000}

        result = self.merger.merge_group_config(group_config, individual_config)
        assert result == expected

    def test_merge_multiple_dicts(self):
        """测试合并多个字典"""
        dicts = [
            {"a": 1, "b": 2},
            {"b": 3, "c": 4},
            {"c": 5, "d": 6}
        ]
        expected = {"a": 1, "b": 3, "c": 5, "d": 6}

        result = self.merger.merge_multiple_dicts(dicts)
        assert result == expected

    def test_merge_multiple_dicts_empty(self):
        """测试合并空字典列表"""
        result = self.merger.merge_multiple_dicts([])
        assert result == {}

    def test_merge_dicts_by_priority(self):
        """测试按优先级合并字典"""
        dicts = [
            {"priority_field": "priority_value", "common_field": "dict1_value"},
            {"priority_field": "should_be_ignored", "common_field": "dict2_value", "extra_field": "extra_value"}
        ]
        priority_keys = ["priority_field"]
        expected = {"priority_field": "priority_value", "common_field": "dict2_value", "extra_field": "extra_value"}

        result = self.merger.merge_dicts_by_priority(dicts, priority_keys)
        assert result == expected

    def test_merge_dicts_by_priority_no_priority_keys(self):
        """测试没有指定优先级键的合并"""
        dicts = [
            {"a": 1, "b": 2},
            {"b": 3, "c": 4}
        ]
        expected = {"a": 1, "b": 3, "c": 4}

        result = self.merger.merge_dicts_by_priority(dicts)
        assert result == expected

    def test_extract_differences_simple(self):
        """测试提取简单差异"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"a": 1, "b": 3, "c": 4}
        expected = {"b": {"old": 2, "new": 3}, "c": {"added": 4}}

        result = self.merger.extract_differences(dict1, dict2)
        assert result == expected

    def test_extract_differences_nested(self):
        """测试提取嵌套字典差异"""
        dict1 = {"a": 1, "b": {"x": 10, "y": 20}}
        dict2 = {"a": 2, "b": {"x": 10, "y": 30, "z": 40}}
        expected = {"a": {"old": 1, "new": 2}, "b": {"y": {"old": 20, "new": 30}, "z": {"added": 40}}}

        result = self.merger.extract_differences(dict1, dict2)
        assert result == expected

    def test_extract_differences_removed_key(self):
        """测试提取被删除的键"""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"a": 1, "c": 4}
        expected = {"b": {"removed": 2}, "c": {"old": 3, "new": 4}}

        result = self.merger.extract_differences(dict1, dict2)
        assert result == expected

    def test_merge_lists_unique(self):
        """测试合并列表（去重）"""
        list1 = [1, 2, 3]
        list2 = [3, 4, 5]
        expected = [1, 2, 3, 4, 5]

        result = self.merger._merge_lists(list1, list2)
        assert result == expected

    def test_merge_lists_with_duplicates(self):
        """测试合并包含重复元素的列表"""
        list1 = [1, 2, 2, 3]
        list2 = [2, 3, 4, 4, 5]
        expected = [1, 2, 2, 3, 4, 4, 5]  # 保持原列表中的重复项

        result = self.merger._merge_lists(list1, list2)
        assert result == expected