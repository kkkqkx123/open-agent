"""字典合并工具单元测试

测试基础设施层字典合并工具的基本功能。
"""

import pytest
from src.infrastructure.common.utils.dict_merger import DictMerger, IDictMerger


class TestDictMerger:
    """测试字典合并器"""

    @pytest.fixture
    def merger(self):
        """创建字典合并器实例"""
        return DictMerger()

    def test_merge_dicts_simple(self, merger):
        """测试简单字典合并"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        result = merger.merge_dicts(dict1, dict2)
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

    def test_merge_dicts_overlap(self, merger):
        """测试重叠键字典合并"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 20, "c": 3}
        result = merger.merge_dicts(dict1, dict2)
        # 默认行为：dict2的值覆盖dict1
        assert result == {"a": 1, "b": 20, "c": 3}

    def test_deep_merge_nested_dicts(self, merger):
        """测试深度合并嵌套字典"""
        dict1 = {"a": 1, "nested": {"x": 10, "y": 20}}
        dict2 = {"b": 2, "nested": {"y": 200, "z": 30}}
        result = merger.deep_merge(dict1, dict2)
        assert result == {
            "a": 1,
            "b": 2,
            "nested": {"x": 10, "y": 200, "z": 30}
        }

    def test_deep_merge_nested_lists(self, merger):
        """测试深度合并嵌套列表"""
        dict1 = {"a": 1, "list": [1, 2, 3]}
        dict2 = {"b": 2, "list": [3, 4, 5]}
        result = merger.deep_merge(dict1, dict2)
        # 列表合并去重
        assert result == {"a": 1, "b": 2, "list": [1, 2, 3, 4, 5]}

    def test_deep_merge_mixed_types(self, merger):
        """测试混合类型深度合并"""
        dict1 = {"a": {"x": 1}, "b": [1, 2], "c": "original"}
        dict2 = {"a": {"y": 2}, "b": [2, 3], "c": "overridden"}
        result = merger.deep_merge(dict1, dict2)
        assert result == {
            "a": {"x": 1, "y": 2},
            "b": [1, 2, 3],
            "c": "overridden"
        }

    def test_merge_group_config(self, merger):
        """测试组配置合并"""
        group_config = {
            "common": "value",
            "tools": ["tool1", "tool2"],
            "tool_sets": ["set1"],
            "group": "test_group"
        }
        individual_config = {
            "specific": "individual",
            "tools": ["tool3"],  # 应完全覆盖
            "tool_sets": ["set2"]
        }
        result = merger.merge_group_config(group_config, individual_config)
        
        assert result["common"] == "value"
        assert result["specific"] == "individual"
        assert result["tools"] == ["tool3"]  # 完全覆盖
        assert result["tool_sets"] == ["set2"]  # 完全覆盖
        assert "group" not in result  # 组标识字段被移除

    def test_merge_multiple_dicts(self, merger):
        """测试合并多个字典"""
        dicts = [
            {"a": 1, "b": 2},
            {"b": 20, "c": 3},
            {"c": 30, "d": 4}
        ]
        result = merger.merge_multiple_dicts(dicts)
        assert result == {"a": 1, "b": 20, "c": 30, "d": 4}

    def test_merge_multiple_dicts_empty(self, merger):
        """测试合并空字典列表"""
        assert merger.merge_multiple_dicts([]) == {}
        assert merger.merge_multiple_dicts([{}]) == {}

    def test_merge_dicts_by_priority(self, merger):
        """测试按优先级合并字典"""
        dicts = [
            {"a": 1, "b": 2, "c": 3},
            {"b": 20, "c": 30, "d": 40},
            {"c": 300, "d": 400, "e": 500}
        ]
        priority_keys = ["a", "b"]
        result = merger.merge_dicts_by_priority(dicts, priority_keys)
        
        # 优先级键应从第一个字典中获取
        assert result["a"] == 1
        assert result["b"] == 2
        # 非优先级键合并（c从最后一个字典，d从最后一个字典，e从最后一个字典）
        assert result["c"] == 300
        assert result["d"] == 400
        assert result["e"] == 500

    def test_merge_dicts_by_priority_no_priority(self, merger):
        """测试无优先级键的合并"""
        dicts = [
            {"a": 1},
            {"a": 2, "b": 3}
        ]
        result = merger.merge_dicts_by_priority(dicts, None)
        assert result == {"a": 2, "b": 3}

    def test_extract_differences(self, merger):
        """测试提取字典差异"""
        dict1 = {"a": 1, "b": 2, "c": {"x": 10, "y": 20}}
        dict2 = {"a": 1, "b": 20, "d": 4, "c": {"x": 10, "y": 200, "z": 30}}
        
        differences = merger.extract_differences(dict1, dict2)
        
        assert "b" in differences
        assert differences["b"] == {"old": 2, "new": 20}
        assert "d" in differences
        assert differences["d"] == {"added": 4}
        assert "c" in differences
        assert "y" in differences["c"]
        assert differences["c"]["y"] == {"old": 20, "new": 200}
        assert "z" in differences["c"]
        assert differences["c"]["z"] == {"added": 30}

    def test_extract_differences_removed(self, merger):
        """测试提取被删除的键"""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"a": 1}
        
        differences = merger.extract_differences(dict1, dict2)
        
        assert "b" in differences
        assert differences["b"] == {"removed": 2}
        assert "c" in differences
        assert differences["c"] == {"removed": 3}

    def test_interface_implementation(self):
        """测试接口实现"""
        merger = DictMerger()
        assert isinstance(merger, IDictMerger)
        
        # 验证所有抽象方法都已实现
        dict1 = {"a": 1}
        dict2 = {"b": 2}
        
        result = merger.merge_dicts(dict1, dict2)
        assert result is not None
        
        result = merger.deep_merge(dict1, dict2)
        assert result is not None
        
        result = merger.merge_group_config(dict1, dict2)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])