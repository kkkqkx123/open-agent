"""
验证规则加载器
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import yaml
from src.interfaces.logger import ILogger


class IRuleLoader:
    """规则加载器接口"""
    
    def load_rules(self, rule_type: str) -> Dict[str, Any]:
        """加载验证规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            Dict[str, Any]: 验证规则
        """
        raise NotImplementedError


class FileRuleLoader(IRuleLoader):
    """文件规则加载器实现"""
    
    def __init__(
        self,
        rules_directory: Union[str, Path],
        logger: Optional[ILogger] = None,
        cache_enabled: bool = True
    ):
        """初始化文件规则加载器
        
        Args:
            rules_directory: 规则文件目录
            logger: 日志记录器
            cache_enabled: 是否启用缓存
        """
        self.rules_directory = Path(rules_directory)
        self.logger = logger
        self.cache_enabled = cache_enabled
        self._rules_cache: Dict[str, Dict[str, Any]] = {}
        
        if not self.rules_directory.exists():
            if self.logger:
                self.logger.warning(f"规则目录不存在: {self.rules_directory}")
    
    def load_rules(self, rule_type: str) -> Dict[str, Any]:
        """加载验证规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            Dict[str, Any]: 验证规则
        """
        if self.cache_enabled and rule_type in self._rules_cache:
            if self.logger:
                self.logger.debug(f"从缓存加载规则: {rule_type}")
            return self._rules_cache[rule_type]
        
        rules = self._load_rules_from_file(rule_type)
        
        if self.cache_enabled:
            self._rules_cache[rule_type] = rules
        
        return rules
    
    def _load_rules_from_file(self, rule_type: str) -> Dict[str, Any]:
        """从文件加载规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            Dict[str, Any]: 验证规则
        """
        # 尝试不同的文件扩展名
        possible_files = [
            self.rules_directory / f"{rule_type}.yaml",
            self.rules_directory / f"{rule_type}.yml",
            self.rules_directory / f"{rule_type}.json"
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                try:
                    rules = self._parse_file(file_path)
                    
                    if self.logger:
                        self.logger.info(f"成功加载规则文件: {file_path}")
                    
                    return rules
                
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"解析规则文件 {file_path} 失败: {e}")
                    continue
        
        # 如果没有找到文件，返回默认规则
        if self.logger:
            self.logger.warning(f"未找到规则类型 {rule_type} 的规则文件，使用默认规则")
        
        return self._get_default_rules(rule_type)
    
    def _parse_file(self, file_path: Path) -> Dict[str, Any]:
        """解析规则文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 解析后的规则
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif file_path.suffix.lower() == '.json':
                return json.load(f) or {}
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    def _get_default_rules(self, rule_type: str) -> Dict[str, Any]:
        """获取默认规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            Dict[str, Any]: 默认规则
        """
        default_rules = {
            "config": {
                "required_fields": ["name", "tool_type", "description", "parameters_schema"],
                "valid_tool_types": ["builtin", "native", "rest", "mcp"],
                "field_validations": {
                    "name": {"type": "str", "min_length": 1},
                    "tool_type": {"type": "str", "enum": ["builtin", "native", "rest", "mcp"]},
                    "description": {"type": "str", "min_length": 1}
                }
            },
            "schema": {
                "required_properties": ["type", "properties"],
                "valid_types": ["object"],
                "property_validations": {
                    "type": {"type": "str", "enum": ["object"]},
                    "properties": {"type": "dict"},
                    "required": {"type": "list", "items": {"type": "str"}}
                }
            },
            "loading": {
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "retry_delay": 1.0
            }
        }
        
        return default_rules.get(rule_type, {})
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._rules_cache.clear()
        
        if self.logger:
            self.logger.info("已清除规则缓存")
    
    def get_available_rule_types(self) -> List[str]:
        """获取可用的规则类型
        
        Returns:
            List[str]: 规则类型列表
        """
        if not self.rules_directory.exists():
            return []
        
        rule_types = set()
        
        for file_path in self.rules_directory.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.yaml', '.yml', '.json']:
                rule_type = file_path.stem
                rule_types.add(rule_type)
        
        return sorted(list(rule_types))
    
    def reload_rules(self, rule_type: Optional[str] = None) -> None:
        """重新加载规则
        
        Args:
            rule_type: 规则类型，如果为None则重新加载所有规则
        """
        if rule_type:
            if rule_type in self._rules_cache:
                del self._rules_cache[rule_type]
            
            # 预加载规则
            self.load_rules(rule_type)
            
            if self.logger:
                self.logger.info(f"已重新加载规则类型: {rule_type}")
        else:
            self.clear_cache()
            
            # 预加载所有可用规则
            for rt in self.get_available_rule_types():
                self.load_rules(rt)
            
            if self.logger:
                self.logger.info("已重新加载所有规则")


class MemoryRuleLoader(IRuleLoader):
    """内存规则加载器实现"""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """初始化内存规则加载器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self._rules: Dict[str, Dict[str, Any]] = {}
    
    def set_rules(self, rule_type: str, rules: Dict[str, Any]) -> None:
        """设置规则
        
        Args:
            rule_type: 规则类型
            rules: 规则内容
        """
        self._rules[rule_type] = rules
        
        if self.logger:
            self.logger.debug(f"设置内存规则: {rule_type}")
    
    def load_rules(self, rule_type: str) -> Dict[str, Any]:
        """加载验证规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            Dict[str, Any]: 验证规则
        """
        rules = self._rules.get(rule_type, {})
        
        if self.logger:
            if rules:
                self.logger.debug(f"从内存加载规则: {rule_type}")
            else:
                self.logger.warning(f"内存中未找到规则类型: {rule_type}")
        
        return rules
    
    def clear_rules(self, rule_type: Optional[str] = None) -> None:
        """清除规则
        
        Args:
            rule_type: 规则类型，如果为None则清除所有规则
        """
        if rule_type:
            if rule_type in self._rules:
                del self._rules[rule_type]
                
            if self.logger:
                self.logger.debug(f"已清除内存规则: {rule_type}")
        else:
            self._rules.clear()
            
            if self.logger:
                self.logger.info("已清除所有内存规则")


# 导出规则加载器
__all__ = [
    "IRuleLoader",
    "FileRuleLoader",
    "MemoryRuleLoader",
]