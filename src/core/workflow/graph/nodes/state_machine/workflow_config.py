"""工作流配置领域实体 - 用于状态机工作流"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class WorkflowConfig:
    """工作流配置领域实体 - 用于状态机工作流"""
    name: str
    description: str = ""
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    # 业务方法
    def has_additional_config(self, key: str) -> bool:
        """检查是否有额外配置"""
        return key in self.additional_config
    
    def get_additional_config(self, key: str, default: Any = None) -> Any:
        """获取额外配置值"""
        return self.additional_config.get(key, default)
    
    def set_additional_config(self, key: str, value: Any) -> None:
        """设置额外配置值"""
        self.additional_config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """从字典创建工作流配置"""
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            additional_config=data.get("additional_config", {})
        )