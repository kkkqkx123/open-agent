"""字典合并工具

提供通用的字典合并功能，可被多个模块使用。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IDictMerger(ABC):
    """字典合并器接口"""

    @abstractmethod
    def merge_dicts(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
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
    def merge_group_config(
        self, group_config: Dict[str, Any], individual_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并组配置和个体配置（向后兼容）

        Args:
            group_config: 组配置
            individual_config: 个体配置

        Returns:
            合并后的配置
        """
        pass


class DictMerger(IDictMerger):
    """字典合并器实现
    
    提供多种合并策略，包括深度合并、组配置合并等。
    """

    def merge_dicts(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并两个字典（通用方法）

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
        """
        return self.deep_merge(dict1, dict2)

    def merge_group_config(
        self, group_config: Dict[str, Any], individual_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并组配置和个体配置（向后兼容方法）

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

    def merge_multiple_dicts(self, dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个字典

        Args:
            dicts: 字典列表

        Returns:
            合并后的字典
        """
        if not dicts:
            return {}

        result = dicts[0].copy()

        for dict_item in dicts[1:]:
            result = self.deep_merge(result, dict_item)

        return result

    def merge_dicts_by_priority(
        self, dicts: List[Dict[str, Any]], priority_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """按优先级合并字典

        Args:
            dicts: 字典列表
            priority_keys: 优先级键列表，第一个字典中的优先级键会保留

        Returns:
            合并后的字典
        """
        if not dicts:
            return {}

        # 如果没有指定优先级键，使用所有键
        if not priority_keys:
            return self.merge_multiple_dicts(dicts)

        result = {}

        # 先处理优先级键（只从第一个字典中获取）
        if dicts:
            for key in priority_keys:
                if key in dicts[0]:
                    result[key] = dicts[0][key]

        # 然后合并所有字典的非优先级键
        for dict_item in dicts:
            for key, value in dict_item.items():
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
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取两个字典的差异

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            差异字典
        """
        differences = {}

        # 检查dict2中有但dict1中没有的键
        for key, value in dict2.items():
            if key not in dict1:
                differences[key] = {"added": value}
            elif isinstance(value, dict) and isinstance(dict1[key], dict):
                # 递归检查嵌套字典
                nested_diff = self.extract_differences(dict1[key], value)
                if nested_diff:
                    differences[key] = nested_diff
            elif value != dict1[key]:
                differences[key] = {"old": dict1[key], "new": value}

        # 检查dict1中有但dict2中没有的键
        for key in dict1:
            if key not in dict2:
                differences[key] = {"removed": dict1[key]}

        return differences