"""LLM配置处理器 - 重构版本

使用 infrastructure 层的配置加载器实现。
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.common_infra import ILogger


class LLMConfigProcessor:
    """LLM配置处理器 - 重构版本
    
    现在使用 infrastructure 层的配置加载器来提供统一的配置处理功能。
    """
    
    def __init__(self, base_config_path: str = "configs/llms", logger: Optional["ILogger"] = None):
        """初始化LLM配置处理器
        
        Args:
            base_config_path: LLM配置基础路径
            logger: 日志记录器实例（可选）
        """
        self.base_config_path = base_config_path
        self.logger = logger
        
        # 使用 infrastructure 层的配置加载器
        from src.infrastructure.llm.config import get_config_loader
        self._config_loader = get_config_loader()
        
        if self.logger:
            self.logger.debug(f"LLM配置处理器初始化完成，基础路径: {self.base_config_path}")
    
    def process_config(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        if self.logger:
            self.logger.debug(f"处理LLM配置: {config_path}")
        
        # 使用 infrastructure 层的配置加载器处理配置
        # 这里我们直接返回配置，因为 infrastructure 层已经处理了继承、环境变量等
        return config
    
    def load_config(self, config_type: str, provider: Optional[str] = None, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """加载配置
        
        Args:
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        return self._config_loader.load_config(config_type, provider, model)
    
    def load_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """加载提供商配置
        
        Args:
            provider: 提供商名称
            
        Returns:
            Optional[Dict[str, Any]]: 提供商配置数据
        """
        return self._config_loader.load_provider_config(provider)
    
    def load_model_config(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """加载模型配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            Optional[Dict[str, Any]]: 模型配置数据
        """
        return self._config_loader.load_model_config(provider, model)


# 为了向后兼容，保留原有的类名作为别名
LLMInheritanceProcessor = LLMConfigProcessor
LLMConfigProcessorChain = LLMConfigProcessor