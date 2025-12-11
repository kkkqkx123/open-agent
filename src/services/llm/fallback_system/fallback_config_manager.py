"""降级配置管理器

负责配置的管理和更新，包括配置的验证和状态查询。
"""

from typing import List, Optional, Dict, Any
from src.interfaces.llm import IClientFactory
from src.infrastructure.llm.fallback import FallbackConfig


class FallbackConfigManager:
    """降级配置管理器
    
    负责配置的管理和更新，包括：
    1. 配置的存储和更新
    2. 配置的验证和状态查询
    3. 可用模型的管理
    4. 配置的导出和导入
    """
    
    def __init__(self, 
                 config: Optional[FallbackConfig] = None,
                 client_factory: Optional[IClientFactory] = None):
        """
        初始化降级配置管理器
        
        Args:
            config: 降级配置
            client_factory: 客户端工厂
        """
        self.config = config
        self.client_factory = client_factory
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置
        
        Args:
            config: 新的降级配置
        """
        # 验证配置
        self._validate_config(config)
        self.config = config
    
    def get_config(self) -> Optional[FallbackConfig]:
        """
        获取当前降级配置
        
        Returns:
            当前降级配置
        """
        return self.config
    
    def is_enabled(self) -> bool:
        """
        检查降级是否启用
        
        Returns:
            降级是否启用
        """
        return self.config is not None and self.config.is_enabled()
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            可用模型列表
        """
        if not self.client_factory:
            return []
        return self.client_factory.get_available_models()
    
    def get_fallback_models(self) -> List[str]:
        """
        获取配置的降级模型列表
        
        Returns:
            降级模型列表
        """
        if not self.config:
            return []
        return self.config.get_fallback_models()
    
    def get_max_attempts(self) -> int:
        """
        获取最大尝试次数
        
        Returns:
            最大尝试次数
        """
        if not self.config:
            return 1  # 默认只尝试一次
        return self.config.get_max_attempts()
    
    def get_strategy_type(self) -> str:
        """
        获取策略类型
        
        Returns:
            策略类型
        """
        if not self.config:
            return "sequential"  # 默认策略
        return self.config.strategy_type
    
    def should_fallback_on_error(self, error: Exception) -> bool:
        """
        判断是否应该对特定错误进行降级
        
        Args:
            error: 错误对象
            
        Returns:
            是否应该降级
        """
        if not self.config:
            return False
        return self.config.should_fallback_on_error(error)
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算降级延迟时间
        
        Args:
            attempt: 尝试次数
            
        Returns:
            延迟时间（秒）
        """
        if not self.config:
            return 0.0
        return self.config.calculate_delay(attempt)
    
    def get_error_mappings(self) -> Dict[str, List[str]]:
        """
        获取错误类型映射
        
        Returns:
            错误类型映射字典
        """
        if not self.config:
            return {}
        return self.config.error_mappings
    
    def get_provider_config(self) -> Dict[str, Any]:
        """
        获取提供商配置
        
        Returns:
            提供商配置字典
        """
        if not self.config:
            return {}
        return self.config.provider_config
    
    def export_config(self) -> Dict[str, Any]:
        """
        导出配置为字典
        
        Returns:
            配置字典
        """
        if not self.config:
            return {}
        return self.config.to_dict()
    
    def import_config(self, config_dict: Dict[str, Any]) -> None:
        """
        从字典导入配置
        
        Args:
            config_dict: 配置字典
        """
        config = FallbackConfig.from_dict(config_dict)
        self.update_config(config)
    
    def _validate_config(self, config: FallbackConfig) -> None:
        """
        验证配置
        
        Args:
            config: 要验证的配置
            
        Raises:
            ValueError: 配置无效
        """
        # 检查最大尝试次数
        if config.max_attempts < 1:
            raise ValueError("最大尝试次数必须大于0")
        
        # 检查降级模型列表
        if config.enabled and not config.fallback_models:
            raise ValueError("启用降级时必须指定降级模型")
        
        # 检查延迟配置
        if config.base_delay < 0:
            raise ValueError("基础延迟不能为负数")
        
        if config.max_delay < 0:
            raise ValueError("最大延迟不能为负数")
        
        if config.exponential_base <= 1:
            raise ValueError("指数基数必须大于1")
        
        # 检查降级模型是否在可用模型列表中
        if self.client_factory:
            available_models = self.client_factory.get_available_models()
            for model in config.fallback_models:
                if model not in available_models:
                    raise ValueError(f"降级模型 '{model}' 不在可用模型列表中")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            配置摘要字典
        """
        if not self.config:
            return {
                "enabled": False,
                "max_attempts": 1,
                "fallback_models_count": 0,
                "strategy_type": "sequential",
                "base_delay": 0.0,
                "max_delay": 0.0
            }
        
        return {
            "enabled": self.config.enabled,
            "max_attempts": self.config.max_attempts,
            "fallback_models_count": len(self.config.fallback_models),
            "strategy_type": self.config.strategy_type,
            "base_delay": self.config.base_delay,
            "max_delay": self.config.max_delay,
            "exponential_base": self.config.exponential_base,
            "jitter": self.config.jitter,
            "error_mappings_count": len(self.config.error_mappings),
            "provider_config_keys": list(self.config.provider_config.keys())
        }