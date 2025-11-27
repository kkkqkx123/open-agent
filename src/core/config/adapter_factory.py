"""
适配器工厂 - 负责创建和管理模块特定配置适配器
"""

from typing import Dict, Type, Any
from .adapters import (
    BaseConfigAdapter,
    LLMConfigAdapter,
    WorkflowConfigAdapter,
    ToolConfigAdapter,
    StateConfigAdapter
)
from .config_manager import ConfigManager


class AdapterFactory:
    """适配器工厂类"""
    
    def __init__(self, base_manager: ConfigManager):
        """
        初始化适配器工厂
        
        Args:
            base_manager: 基础配置管理器
        """
        self.base_manager = base_manager
        self._adapters: Dict[str, BaseConfigAdapter] = {}
        self._adapter_types: Dict[str, Type[BaseConfigAdapter]] = {
            'llm': LLMConfigAdapter,
            'workflow': WorkflowConfigAdapter,
            'tools': ToolConfigAdapter,
            'state': StateConfigAdapter,
        }
    
    def get_adapter(self, module_type: str) -> BaseConfigAdapter:
        """
        获取指定模块类型的适配器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置适配器实例
        """
        if module_type not in self._adapters:
            if module_type not in self._adapter_types:
                raise ValueError(f"不支持的模块类型: {module_type}")
            
            # 创建适配器实例
            adapter_class = self._adapter_types[module_type]
            self._adapters[module_type] = adapter_class(self.base_manager)
        
        return self._adapters[module_type]
    
    def register_adapter_type(self, module_type: str, adapter_class: Type[BaseConfigAdapter]) -> None:
        """
        注册新的适配器类型
        
        Args:
            module_type: 模块类型
            adapter_class: 适配器类
        """
        self._adapter_types[module_type] = adapter_class
        # 如果已有实例，需要重新创建
        if module_type in self._adapters:
            self._adapters[module_type] = adapter_class(self.base_manager)
    
    def create_adapter(self, module_type: str) -> BaseConfigAdapter:
        """
        创建新的适配器实例（不缓存）
        
        Args:
            module_type: 模块类型
            
        Returns:
            新的配置适配器实例
        """
        if module_type not in self._adapter_types:
            raise ValueError(f"不支持的模块类型: {module_type}")
        
        adapter_class = self._adapter_types[module_type]
        return adapter_class(self.base_manager)