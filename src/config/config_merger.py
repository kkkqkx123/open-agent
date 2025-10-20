"""配置合并器"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IConfigMerger(ABC):
    """配置合并器接口"""

    @abstractmethod
    def merge_group_config(
        self, group_config: Dict[str, Any], individual_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并组配置和个体配置

        Args:
            group_config: 组配置
            individual_config: 个体配置

        Returns:
            合并后的配置
        """
        pass

    @abstractmethod
    def deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
        """
        pass

    @abstractmethod
    def resolve_inheritance(
        self,
        config: Dict[str, Any],
        config_type: str,
        group_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """解析配置继承

        Args:
            config: 配置字典
            config_type: 配置类型
            group_configs: 组配置字典（可选）

        Returns:
            解析后的配置
        """
        pass


class ConfigMerger(IConfigMerger):
    """配置合并器实现"""

    def merge_group_config(
        self, group_config: Dict[str, Any], individual_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并组配置和个体配置

        Args:
            group_config: 组配置
            individual_config: 个体配置

        Returns:
            合并后的配置
        """
        # 先深度合并配置
        result = self.deep_merge(group_config.copy(), individual_config)

        # 对于特定字段，个体配置应该完全覆盖组配置而不是合并
        override_fields = ["tools", "tool_sets"]  # 这些字段个体配置优先
        for field in override_fields:
            if field in individual_config:
                result[field] = individual_config[field]

        # 移除组标识字段，因为它已经完成了合并任务
        if "group" in result:
            del result["group"]

        return result

    def deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    result[key] = self.deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # 合并列表，去重
                    result[key] = self._merge_lists(result[key], value)
                else:
                    # 直接覆盖
                    result[key] = value
            else:
                result[key] = value

        return result

    def resolve_inheritance(
        self,
        config: Dict[str, Any],
        config_type: str,
        group_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """解析配置继承

        Args:
            config: 配置字典
            config_type: 配置类型
            group_configs: 组配置字典（可选）

        Returns:
            解析后的配置
        """
        if "group" not in config:
            return config

        group_name = config["group"]

        # 如果没有提供组配置，返回原配置
        if not group_configs or group_name not in group_configs:
            return config

        group_config = group_configs[group_name]

        # 合并组配置和个体配置
        return self.merge_group_config(group_config, config)

    def _merge_lists(self, list1: List[Any], list2: List[Any]) -> List[Any]:
        """合并两个列表，去重

        Args:
            list1: 第一个列表
            list2: 第二个列表

        Returns:
            合并后的列表
        """
        result = list1.copy()

        for item in list2:
            if item not in result:
                result.append(item)

        return result

    def merge_multiple_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个配置

        Args:
            configs: 配置列表

        Returns:
            合并后的配置
        """
        if not configs:
            return {}

        result = configs[0].copy()

        for config in configs[1:]:
            result = self.deep_merge(result, config)

        return result

    def merge_configs_by_priority(
        self, configs: List[Dict[str, Any]], priority_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """按优先级合并配置

        Args:
            configs: 配置列表
            priority_keys: 优先级键列表，第一个配置中的优先级键会保留

        Returns:
            合并后的配置
        """
        if not configs:
            return {}

        # 如果没有指定优先级键，使用所有键
        if not priority_keys:
            return self.merge_multiple_configs(configs)

        result = {}

        # 先处理优先级键（只从第一个配置中获取）
        if configs:
            for key in priority_keys:
                if key in configs[0]:
                    result[key] = configs[0][key]

        # 然后合并所有配置的非优先级键
        for config in configs:
            for key, value in config.items():
                if key not in priority_keys:
                    if key in result:
                        if isinstance(result[key], dict) and isinstance(value, dict):
                            result[key] = self.deep_merge(result[key], value)
                        elif isinstance(result[key], list) and isinstance(value, list):
                            result[key] = self._merge_lists(result[key], value)
                        else:
                            result[key] = value
                    else:
                        result[key] = value

        return result

    def extract_differences(
        self, config1: Dict[str, Any], config2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取两个配置的差异

        Args:
            config1: 第一个配置
            config2: 第二个配置

        Returns:
            差异字典
        """
        differences = {}

        # 检查config2中有但config1中没有的键
        for key, value in config2.items():
            if key not in config1:
                differences[key] = {"added": value}
            elif isinstance(value, dict) and isinstance(config1[key], dict):
                # 递归检查嵌套字典
                nested_diff = self.extract_differences(config1[key], value)
                if nested_diff:
                    differences[key] = nested_diff
            elif value != config1[key]:
                differences[key] = {"old": config1[key], "new": value}

        # 检查config1中有但config2中没有的键
        for key in config1:
            if key not in config2:
                differences[key] = {"removed": config1[key]}

        return differences
