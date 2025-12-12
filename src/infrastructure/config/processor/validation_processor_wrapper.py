"""配置验证处理器包装器

直接使用 validation 模块中的 ConfigValidator 提供验证功能。
"""

from typing import Dict, Any, Optional
import logging

from .base_processor import BaseConfigProcessor
from src.infrastructure.config.validation.config_validator import ConfigValidator
from src.infrastructure.config.validation.base_validator import IValidationContext

logger = logging.getLogger(__name__)


class ValidationProcessorWrapper(BaseConfigProcessor):
    """配置验证处理器包装器
    
    直接使用 validation 模块中的 ConfigValidator 提供验证功能。
    支持根据配置类型选择适当的验证方法。
    """
    
    def __init__(self, config_type: Optional[str] = None):
        """初始化验证处理器包装器
        
        Args:
            config_type: 配置类型，用于选择特定的验证方法
        """
        super().__init__("validation")
        self.config_type = config_type
        self.validator = ConfigValidator()
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """内部验证逻辑
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            验证后的配置数据
        """
        # 根据配置类型选择验证方法
        if self.config_type:
            result = self._validate_by_type(config, self.config_type)
        else:
            # 自动检测配置类型
            detected_type = self._detect_config_type(config_path)
            result = self._validate_by_type(config, detected_type)
        
        # 如果有错误，抛出异常
        if not result.is_valid:
            error_msg = f"配置验证失败 ({config_path}): " + "; ".join(result.errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 记录警告
        for warning in result.warnings:
            logger.warning(f"配置验证警告 ({config_path}): {warning}")
        
        logger.debug(f"配置验证通过: {config_path}")
        return config
    
    def _detect_config_type(self, config_path: str) -> str:
        """自动检测配置类型
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置类型
        """
        path_lower = config_path.lower()
        if "llm" in path_lower:
            return "llm"
        elif "tool" in path_lower:
            return "tool"
        elif "workflow" in path_lower:
            return "workflow"
        elif "global" in path_lower:
            return "global"
        else:
            return "generic"
    
    def _validate_by_type(self, config: Dict[str, Any], config_type: str) -> Any:
        """根据配置类型进行验证
        
        Args:
            config: 配置数据
            config_type: 配置类型
            
        Returns:
            验证结果
        """
        if config_type == "llm":
            return self.validator.validate_llm_config(config)
        elif config_type == "tool":
            return self.validator.validate_tool_config(config)
        elif config_type == "workflow":
            return self.validator.validate(config)  # 使用通用验证
        elif config_type == "global":
            return self.validator.validate_global_config(config)
        else:
            return self.validator.validate(config)