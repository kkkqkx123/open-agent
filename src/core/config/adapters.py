"""
配置适配器模块 - 提供模块特定配置加载的适配器模式实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..llm.config import LLMClientConfig, LLMModuleConfig


class BaseConfigAdapter(ABC):
    """配置适配器基类"""
    
    def __init__(self, base_manager):
        """
        初始化适配器
        
        Args:
            base_manager: 基础配置管理器
        """
        self.base_manager = base_manager
    
    @abstractmethod
    def load_config(self, config_path: str, **kwargs) -> Dict[str, Any]:
        """加载配置的适配方法"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置的适配方法"""
        pass


class LLMConfigAdapter(BaseConfigAdapter):
    """LLM模块配置适配器"""
    
    def __init__(self, base_manager):
        super().__init__(base_manager)
        self.client_configs: Dict[str, LLMClientConfig] = {}
        self.module_config: Optional[LLMModuleConfig] = None
        self._validator = None  # 延迟初始化验证器
    
    @property
    def validator(self):
        """延迟加载验证器以避免循环导入"""
        if self._validator is None:
            from ..llm.config_manager import ConfigValidator as LLMConfigValidator
            self._validator = LLMConfigValidator()
        return self._validator
    
    def load_config(self, config_path: str, **kwargs) -> Dict[str, Any]:
        """
        加载LLM配置
        
        Args:
            config_path: 配置文件路径
            **kwargs: 额外参数
            
        Returns:
            配置数据
        """
        config = self.base_manager.load_config_for_module(config_path, "llm")
        
        # LLM特定处理
        if config_path.endswith("_group.yaml"):
            self.module_config = LLMModuleConfig.from_dict(config)
        else:
            client_config = LLMClientConfig.from_dict(config)
            model_key = f"{client_config.model_type}:{client_config.model_name}"
            self.client_configs[model_key] = client_config
        
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证LLM配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证是否通过
        """
        errors = self.validator.validate_config(config)
        return len(errors) == 0


class WorkflowConfigAdapter(BaseConfigAdapter):
    """工作流模块配置适配器"""
    
    def load_config(self, config_path: str, **kwargs) -> Dict[str, Any]:
        """
        加载工作流配置
        
        Args:
            config_path: 配置文件路径
            **kwargs: 额外参数
            
        Returns:
            配置数据
        """
        return self.base_manager.load_config_for_module(config_path, "workflow")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证工作流配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证是否通过
        """
        # 工作流特定验证逻辑
        required_keys = ["name", "type"]
        return all(key in config for key in required_keys)


class ToolConfigAdapter(BaseConfigAdapter):
    """工具模块配置适配器"""
    
    def load_config(self, config_path: str, **kwargs) -> Dict[str, Any]:
        """
        加载工具配置
        
        Args:
            config_path: 配置文件路径
            **kwargs: 额外参数
            
        Returns:
            配置数据
        """
        return self.base_manager.load_config_for_module(config_path, "tools")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证工具配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证是否通过
        """
        # 工具特定验证逻辑
        required_keys = ["name", "tool_type", "description"]
        return all(key in config for key in required_keys)


class StateConfigAdapter(BaseConfigAdapter):
    """状态管理模块配置适配器"""
    
    def load_config(self, config_path: str, **kwargs) -> Dict[str, Any]:
        """
        加载状态管理配置
        
        Args:
            config_path: 配置文件路径
            **kwargs: 额外参数
            
        Returns:
            配置数据
        """
        return self.base_manager.load_config_for_module(config_path, "state")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证状态管理配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证是否通过
        """
        # 状态管理特定验证逻辑
        required_sections = ["core", "serializer", "cache", "storage"]
        return all(section in config for section in required_sections)