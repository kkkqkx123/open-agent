"""配置合并器测试"""

import pytest
from src.config.config_merger import ConfigMerger


class TestConfigMerger:
    """配置合并器测试类"""

    def setup_method(self):
        """测试前设置"""
        self.merger = ConfigMerger()

    def test_merge_group_config(self):
        """测试组配置和个体配置合并"""
        group_config = {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "headers": {"User-Agent": "Agent/1.0", "Accept": "application/json"},
            "parameters": {"temperature": 0.7, "max_tokens": 2000},
        }

        individual_config = {
            "group": "test_group",
            "timeout": 60,  # 覆盖组配置
            "model": "gpt-4",  # 新增字段
            "headers": {"Authorization": "Bearer token"},  # 合并headers
            "parameters": {"temperature": 0.3, "top_p": 0.9},  # 覆盖参数  # 新增参数
        }

        result = self.merger.merge_group_config(group_config, individual_config)

        # 验证合并结果
        assert result["base_url"] == "https://api.example.com"  # 保留组配置
        assert result["timeout"] == 60  # 个体配置覆盖
        assert result["model"] == "gpt-4"  # 新增字段
        assert result["headers"]["User-Agent"] == "Agent/1.0"  # 保留组headers
        assert result["headers"]["Accept"] == "application/json"  # 保留组headers
        assert result["headers"]["Authorization"] == "Bearer token"  # 新增headers
        assert result["parameters"]["temperature"] == 0.3  # 个体配置覆盖
        assert result["parameters"]["max_tokens"] == 2000  # 保留组参数
        assert result["parameters"]["top_p"] == 0.9  # 新增参数
        assert "group" not in result  # 移除组标识

    def test_deep_merge(self):
        """测试深度合并"""
        dict1 = {
            "level1": {
                "level2": {"value1": "keep", "value2": "replace"},
                "list1": ["item1", "item2"],
            },
            "simple": "keep",
        }

        dict2 = {
            "level1": {
                "level2": {"value2": "replaced", "value3": "new"},
                "list1": ["item3"],
                "new_level2": "new_value",
            },
            "new_simple": "new_value",
        }

        result = self.merger.deep_merge(dict1, dict2)

        # 验证深度合并结果
        assert result["level1"]["level2"]["value1"] == "keep"  # 保留原值
        assert result["level1"]["level2"]["value2"] == "replaced"  # 覆盖值
        assert result["level1"]["level2"]["value3"] == "new"  # 新增值
        assert result["level1"]["list1"] == ["item1", "item2", "item3"]  # 合并列表
        assert result["level1"]["new_level2"] == "new_value"  # 新增字段
        assert result["simple"] == "keep"  # 保留原值
        assert result["new_simple"] == "new_value"  # 新增字段

    def test_resolve_inheritance(self):
        """测试配置继承解析"""
        config = {"group": "test_group", "model": "gpt-4", "timeout": 60}

        group_configs = {
            "test_group": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "headers": {"User-Agent": "Agent/1.0"},
            }
        }

        result = self.merger.resolve_inheritance(config, "llms", group_configs)

        # 验证继承结果
        assert result["base_url"] == "https://api.example.com"  # 继承自组配置
        assert result["timeout"] == 60  # 个体配置覆盖
        assert result["model"] == "gpt-4"  # 个体配置
        assert result["headers"]["User-Agent"] == "Agent/1.0"  # 继承自组配置
        assert "group" not in result  # 移除组标识

    def test_resolve_inheritance_no_group(self):
        """测试无组配置的继承解析"""
        config = {"model": "gpt-4", "timeout": 60}

        result = self.merger.resolve_inheritance(config, "llms")

        # 验证结果
        assert result["model"] == "gpt-4"
        assert result["timeout"] == 60

    def test_resolve_inheritance_group_not_found(self):
        """测试组配置不存在的继承解析"""
        config = {"group": "nonexistent_group", "model": "gpt-4"}

        group_configs = {"test_group": {"base_url": "https://api.example.com"}}

        result = self.merger.resolve_inheritance(config, "llms", group_configs)

        # 验证结果（应该返回原配置）
        assert result["group"] == "nonexistent_group"
        assert result["model"] == "gpt-4"

    def test_merge_lists(self):
        """测试列表合并"""
        list1 = ["item1", "item2", "item3"]
        list2 = ["item2", "item4", "item5"]

        result = self.merger._merge_lists(list1, list2)

        # 验证合并结果（去重）
        assert result == ["item1", "item2", "item3", "item4", "item5"]

    def test_merge_multiple_configs(self):
        """测试多配置合并"""
        config1 = {"base_url": "https://api.example.com", "timeout": 30}

        config2 = {"model": "gpt-4", "timeout": 60}

        config3 = {"headers": {"User-Agent": "Agent/1.0"}}

        result = self.merger.merge_multiple_configs([config1, config2, config3])

        # 验证合并结果
        assert result["base_url"] == "https://api.example.com"
        assert result["model"] == "gpt-4"
        assert result["timeout"] == 60  # 后面的配置覆盖
        assert result["headers"]["User-Agent"] == "Agent/1.0"

    def test_merge_configs_by_priority(self):
        """测试按优先级合并配置"""
        config1 = {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "model": "gpt-3.5",
        }

        config2 = {
            "timeout": 60,
            "model": "gpt-4",
            "headers": {"User-Agent": "Agent/1.0"},
        }

        config3 = {"model": "gpt-4-turbo", "parameters": {"temperature": 0.7}}

        # 按优先级合并，model和timeout为优先级键
        result = self.merger.merge_configs_by_priority(
            [config1, config2, config3], priority_keys=["model", "timeout"]
        )

        # 验证合并结果
        assert result["base_url"] == "https://api.example.com"  # 来自config1
        assert result["timeout"] == 30  # 来自config1（优先级键，使用第一个）
        assert result["model"] == "gpt-3.5"  # 来自config1（优先级键，使用第一个）
        assert result["headers"]["User-Agent"] == "Agent/1.0"  # 来自config2
        assert result["parameters"]["temperature"] == 0.7  # 来自config3

    def test_extract_differences(self):
        """测试提取配置差异"""
        config1 = {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "model": "gpt-3.5",
            "headers": {"User-Agent": "Agent/1.0", "Accept": "application/json"},
        }

        config2 = {
            "base_url": "https://api.newexample.com",
            "timeout": 60,
            "model": "gpt-4",
            "headers": {"User-Agent": "Agent/2.0", "Authorization": "Bearer token"},
        }

        differences = self.merger.extract_differences(config1, config2)

        # 验证差异结果
        assert differences["base_url"]["old"] == "https://api.example.com"
        assert differences["base_url"]["new"] == "https://api.newexample.com"
        assert differences["timeout"]["old"] == 30
        assert differences["timeout"]["new"] == 60
        assert differences["model"]["old"] == "gpt-3.5"
        assert differences["model"]["new"] == "gpt-4"
        assert differences["headers"]["User-Agent"]["old"] == "Agent/1.0"
        assert differences["headers"]["User-Agent"]["new"] == "Agent/2.0"
        assert differences["headers"]["Accept"]["removed"] == "application/json"
        assert differences["headers"]["Authorization"]["added"] == "Bearer token"

    def test_extract_differences_no_differences(self):
        """测试无差异的配置"""
        config = {"base_url": "https://api.example.com", "timeout": 30}

        differences = self.merger.extract_differences(config, config)

        # 验证无差异
        assert differences == {}
