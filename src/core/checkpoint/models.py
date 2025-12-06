"""
检查点核心数据模型

定义检查点相关的核心数据模型，包括检查点、元数据和元组等。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class CheckpointMetadata:
    """检查点元数据
    
    包含检查点的描述性信息，如来源、步数、父检查点等。
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化检查点元数据。
        
        Args:
            **kwargs: 元数据字段
        """
        self._data: Dict[str, Any] = {}
        self.update(kwargs)
    
    def update(self, data: Dict[str, Any]) -> None:
        """更新元数据
        
        Args:
            data: 要更新的数据
        """
        self._data.update(data)
    
    @property
    def source(self) -> Optional[str]:
        """检查点来源"""
        return self._data.get("source")
    
    @source.setter
    def source(self, value: str) -> None:
        """设置检查点来源"""
        self._data["source"] = value
    
    @property
    def step(self) -> Optional[int]:
        """检查点步数"""
        return self._data.get("step")
    
    @step.setter
    def step(self, value: int) -> None:
        """设置检查点步数"""
        self._data["step"] = value
    
    @property
    def parents(self) -> Optional[Dict[str, str]]:
        """父检查点ID映射"""
        return self._data.get("parents")
    
    @parents.setter
    def parents(self, value: Dict[str, str]) -> None:
        """设置父检查点ID映射"""
        self._data["parents"] = value
    
    @property
    def created_at(self) -> Optional[datetime]:
        """创建时间"""
        timestamp = self._data.get("created_at")
        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)
        return timestamp
    
    @created_at.setter
    def created_at(self, value: datetime) -> None:
        """设置创建时间"""
        self._data["created_at"] = value.isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            元数据字典
        """
        return self._data.copy()
    
    def __getitem__(self, key: str) -> Any:
        """获取元数据项"""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """设置元数据项"""
        self._data[key] = value
    
    def __contains__(self, key: str) -> bool:
        """检查是否包含键"""
        return key in self._data
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取元数据项（带默认值）"""
        return self._data.get(key, default)


class Checkpoint:
    """检查点数据模型
    
    表示特定时间点的状态快照，包含通道值、版本信息等。
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        channel_values: Optional[Dict[str, Any]] = None,
        channel_versions: Optional[Dict[str, Any]] = None,
        versions_seen: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """初始化检查点
        
        Args:
            id: 检查点ID
            channel_values: 通道值映射
            channel_versions: 通道版本映射
            versions_seen: 每个节点看到的通道版本映射
            **kwargs: 其他字段
        """
        self.id = id or str(uuid.uuid4())
        self.channel_values = channel_values or {}
        self.channel_versions = channel_versions or {}
        self.versions_seen = versions_seen or {}
        self.ts = datetime.now().isoformat()
        
        # 存储其他字段
        self._additional_data = kwargs
    
    @property
    def timestamp(self) -> datetime:
        """时间戳"""
        return datetime.fromisoformat(self.ts)
    
    def get_channel_value(self, channel: str, default: Any = None) -> Any:
        """获取通道值
        
        Args:
            channel: 通道名称
            default: 默认值
            
        Returns:
            通道值
        """
        return self.channel_values.get(channel, default)
    
    def set_channel_value(self, channel: str, value: Any) -> None:
        """设置通道值
        
        Args:
            channel: 通道名称
            value: 通道值
        """
        self.channel_values[channel] = value
    
    def get_channel_version(self, channel: str, default: Any = None) -> Any:
        """获取通道版本
        
        Args:
            channel: 通道名称
            default: 默认值
            
        Returns:
            通道版本
        """
        return self.channel_versions.get(channel, default)
    
    def set_channel_version(self, channel: str, version: Any) -> None:
        """设置通道版本
        
        Args:
            channel: 通道名称
            version: 通道版本
        """
        self.channel_versions[channel] = version
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            检查点字典
        """
        data = {
            "id": self.id,
            "ts": self.ts,
            "channel_values": self.channel_values,
            "channel_versions": self.channel_versions,
            "versions_seen": self.versions_seen
        }
        data.update(self._additional_data)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """从字典创建检查点
        
        Args:
            data: 检查点数据
            
        Returns:
            检查点实例
        """
        # 提取已知字段
        known_fields = ["id", "channel_values", "channel_versions", "versions_seen"]
        kwargs = {}
        additional_data = {}
        
        for key, value in data.items():
            if key in known_fields:
                kwargs[key] = value
            elif key != "ts":  # ts 由构造函数自动生成
                additional_data[key] = value
        
        kwargs.update(additional_data)
        return cls(**kwargs)
    
    def __getitem__(self, key: str) -> Any:
        """获取检查点字段"""
        if hasattr(self, key):
            return getattr(self, key)
        return self._additional_data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """设置检查点字段"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self._additional_data[key] = value
    
    def __contains__(self, key: str) -> bool:
        """检查是否包含字段"""
        return hasattr(self, key) or key in self._additional_data


class CheckpointTuple:
    """检查点元组
    
    包含检查点及其相关数据的组合结构。
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        parent_config: Optional[Dict[str, Any]] = None,
        pending_writes: Optional[List[Any]] = None
    ):
        """初始化检查点元组
        
        Args:
            config: 可运行配置
            checkpoint: 检查点数据
            metadata: 检查点元数据
            parent_config: 父配置
            pending_writes: 待写入数据
        """
        self.config = config
        self.checkpoint = checkpoint
        self.metadata = metadata
        self.parent_config = parent_config
        self.pending_writes = pending_writes or []
    
    def get_thread_id(self) -> str:
        """获取线程ID
        
        Returns:
            线程ID
        """
        return self.config.get("configurable", {}).get("thread_id", "")
    
    def get_checkpoint_ns(self) -> str:
        """获取检查点命名空间
        
        Returns:
            检查点命名空间
        """
        return self.config.get("configurable", {}).get("checkpoint_ns", "")
    
    def get_checkpoint_id(self) -> str:
        """获取检查点ID
        
        Returns:
            检查点ID
        """
        return self.config.get("configurable", {}).get("checkpoint_id", "") or self.checkpoint.id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            元组字典
        """
        return {
            "config": self.config,
            "checkpoint": self.checkpoint.to_dict(),
            "metadata": self.metadata.to_dict(),
            "parent_config": self.parent_config,
            "pending_writes": self.pending_writes
        }