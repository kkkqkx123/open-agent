"""验证上下文

提供验证过程中需要的上下文信息和状态管理。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationContext:
    """验证上下文
    
    封装验证过程中需要的上下文信息和状态。
    """
    
    # 基础信息
    config_type: str
    config_path: Optional[str] = None
    operation_id: Optional[str] = None
    
    # 验证配置
    strict_mode: bool = False
    enable_business_rules: bool = True
    enable_cross_module_validation: bool = True
    
    # 环境信息
    environment: str = "development"
    
    # 缓存和性能
    enable_cache: bool = True
    cache_key: Optional[str] = None
    
    # 依赖信息
    dependent_configs: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    
    # 验证历史
    validation_history: List[Dict[str, Any]] = field(default_factory=list)
    
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
    
    def get_validation_history(self) -> List[Dict[str, Any]]:
        """获取验证历史
        
        Returns:
            验证历史记录
        """
        return self.validation_history.copy()
    
    def is_production(self) -> bool:
        """检查是否为生产环境
        
        Returns:
            是否为生产环境
        """
        return self.environment.lower() == "production"
    
    def create_cache_key(self, config_data: Dict[str, Any]) -> str:
        """创建缓存键
        
        Args:
            config_data: 配置数据
            
        Returns:
            缓存键
        """
        import hashlib
        import json
        
        # 使用配置类型、路径和数据哈希创建缓存键
        data_str = json.dumps(config_data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        parts = [self.config_type]
        if self.config_path:
            parts.append(self.config_path)
        parts.append(data_hash)
        
        return "_".join(parts)