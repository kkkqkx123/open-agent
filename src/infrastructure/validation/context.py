"""验证上下文实现

提供IValidationContext接口的基础设施实现。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from src.interfaces.config.validation import IValidationContext


@dataclass
class ValidationContext(IValidationContext):
    """验证上下文基础设施实现
    
    提供IValidationContext接口的标准实现，包含验证过程中所需的上下文信息。
    """
    config_type: str
    config_path: Optional[str] = None
    operation_id: Optional[str] = None
    strict_mode: bool = False
    enable_business_rules: bool = True
    enable_cross_module_validation: bool = True
    environment: str = "development"
    enable_cache: bool = True
    cache_key: Optional[str] = None
    dependent_configs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    validation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def add_dependency(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """添加依赖配置
        
        Args:
            config_type: 配置类型
            config_data: 配置数据
        """
        self.dependent_configs[config_type] = config_data
    
    def get_dependency(self, config_type: str) -> Optional[Dict[str, Any]]:
        """获取依赖配置
        
        Args:
            config_type: 配置类型
            
        Returns:
            配置数据或None
        """
        return self.dependent_configs.get(config_type)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def add_validation_step(self, step_name: str, result: Dict[str, Any]) -> None:
        """添加验证步骤记录
        
        Args:
            step_name: 步骤名称
            result: 验证结果
        """
        step_record = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        self.validation_history.append(step_record)
