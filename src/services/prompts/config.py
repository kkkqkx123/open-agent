"""提示词配置管理器

管理提示词配置的创建、验证和缓存。
"""

from typing import Dict, Any, Optional, List
from ...interfaces.prompts import PromptConfig


class PromptConfigManager:
    """提示词配置管理器
    
    管理提示词配置的创建、验证和缓存。
    """
    
    def __init__(self) -> None:
        """初始化配置管理器"""
        self._config_cache: Dict[str, PromptConfig] = {}
    
    def create_config(self, system_prompt: Optional[str] = None,
                      rules: Optional[List[str]] = None,
                      user_command: Optional[str] = None,
                      cache_enabled: bool = True,
                      context: Optional[List[str]] = None,
                      examples: Optional[List[str]] = None,
                      constraints: Optional[List[str]] = None,
                      format: Optional[str] = None) -> PromptConfig:
        """创建提示词配置
        
        Args:
            system_prompt: 系统提示词名称
            rules: 规则提示词列表
            user_command: 用户指令名称
            cache_enabled: 是否启用缓存
            context: 上下文列表
            examples: 示例列表
            constraints: 约束列表
            format: 提示词格式
            
        Returns:
            PromptConfig: 提示词配置
        """
        return PromptConfig(
            system_prompt=system_prompt,
            rules=rules or [],
            user_command=user_command,
            cache_enabled=cache_enabled,
            context=context,
            examples=examples,
            constraints=constraints,
            format=format
        )
    
    def create_from_dict(self, config_dict: Dict[str, Any]) -> PromptConfig:
        """从字典创建提示词配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            PromptConfig: 提示词配置
        """
        return self.create_config(
            system_prompt=config_dict.get("system_prompt"),
            rules=config_dict.get("rules", []),
            user_command=config_dict.get("user_command"),
            cache_enabled=config_dict.get("cache_enabled", True)
        )
    
    def get_agent_config(self) -> PromptConfig:
        """获取默认Agent配置
        
        Returns:
            PromptConfig: 默认Agent配置
        """
        cache_key = "default_agent"
        if cache_key not in self._config_cache:
            self._config_cache[cache_key] = self.create_config(
                system_prompt="assistant",
                rules=["safety", "format"],
                user_command="data_analysis",
                cache_enabled=True
            )
        return self._config_cache[cache_key]
    
    def get_simple_config(self) -> PromptConfig:
        """获取简单配置
        
        Returns:
            PromptConfig: 简单配置
        """
        cache_key = "simple"
        if cache_key not in self._config_cache:
            self._config_cache[cache_key] = self.create_config(
                system_prompt="assistant",
                rules=["safety"],
                user_command="general",
                cache_enabled=True
            )
        return self._config_cache[cache_key]
    
    def validate_config(self, config: PromptConfig) -> List[str]:
        """验证提示词配置
        
        Args:
            config: 提示词配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors: List[str] = []
        
        # 验证系统提示词
        if config.system_prompt and not isinstance(config.system_prompt, str):
            errors.append("系统提示词必须是字符串类型")
        
        # 验证规则列表
        if config.rules and not isinstance(config.rules, list):
            errors.append("规则列表必须是数组类型")
        elif config.rules:
            for i, rule in enumerate(config.rules):
                if not isinstance(rule, str):
                    errors.append(f"规则[{i}]必须是字符串类型")
        
        # 验证用户指令
        if config.user_command and not isinstance(config.user_command, str):
            errors.append("用户指令必须是字符串类型")
        
        # 验证缓存标志
        if not isinstance(config.cache_enabled, bool):
            errors.append("缓存标志必须是布尔类型")
        
        return errors
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        self._config_cache.clear()
    
    def get_cached_configs(self) -> List[str]:
        """获取缓存的配置键列表
        
        Returns:
            List[str]: 缓存的配置键列表
        """
        return list(self._config_cache.keys())


# 全局配置管理器实例
_global_config_manager: Optional[PromptConfigManager] = None


def get_global_config_manager() -> PromptConfigManager:
    """获取全局配置管理器
    
    Returns:
        PromptConfigManager: 全局配置管理器
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = PromptConfigManager()
    return _global_config_manager