"""状态管理接口定义

定义了状态管理的核心接口，支持状态转换、验证和持久化。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class IStateManager(ABC):
    """状态管理器接口"""
    
    @abstractmethod
    def register_converter(self, state_type: Type, converter: 'IStateConverter') -> None:
        """注册状态转换器
        
        Args:
            state_type: 状态类型
            converter: 转换器实例
        """
        pass
    
    @abstractmethod
    def register_validator(self, state_type: Type, validator: 'IStateValidator') -> None:
        """注册状态验证器
        
        Args:
            state_type: 状态类型
            validator: 验证器实例
        """
        pass
    
    @abstractmethod
    def convert_state(self, source_state: Any, target_type: Type) -> Any:
        """转换状态类型
        
        Args:
            source_state: 源状态
            target_type: 目标类型
            
        Returns:
            转换后的状态
        """
        pass
    
    @abstractmethod
    def validate_state(self, state: Any) -> bool:
        """验证状态
        
        Args:
            state: 要验证的状态
            
        Returns:
            bool: 验证是否通过
        """
        pass
    
    @abstractmethod
    def save_state_snapshot(self, state: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """保存状态快照
        
        Args:
            state: 状态对象
            metadata: 元数据
            
        Returns:
            str: 快照ID
        """
        pass
    
    @abstractmethod
    def load_state_snapshot(self, snapshot_id: str) -> Any:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态对象
        """
        pass
    
    @abstractmethod
    def get_state_history(self, state_type: Optional[Type] = None) -> List[Dict[str, Any]]:
        """获取状态历史
        
        Args:
            state_type: 状态类型过滤
            
        Returns:
            状态历史列表
        """
        pass
    
    @abstractmethod
    def clear_history(self) -> None:
        """清除状态历史"""
        pass


class IStateConverter(ABC):
    """状态转换器接口"""
    
    @abstractmethod
    def convert(self, source_state: Any, target_type: Type) -> Any:
        """转换状态
        
        Args:
            source_state: 源状态
            target_type: 目标类型
            
        Returns:
            转换后的状态
        """
        pass


class IStateValidator(ABC):
    """状态验证器接口"""
    
    @abstractmethod
    def validate(self, state: Any) -> bool:
        """验证状态
        
        Args:
            state: 要验证的状态
            
        Returns:
            bool: 验证是否通过
        """
        pass


class IStateSerializer(ABC):
    """状态序列化器接口"""
    
    @abstractmethod
    def serialize(self, state: Any) -> Dict[str, Any]:
        """序列化状态
        
        Args:
            state: 状态对象
            
        Returns:
            序列化后的数据
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Dict[str, Any], state_type: Type) -> Any:
        """反序列化状态
        
        Args:
            data: 序列化数据
            state_type: 状态类型
            
        Returns:
            状态对象
        """
        pass


class IStatePersistence(ABC):
    """状态持久化接口"""
    
    @abstractmethod
    def save(self, state_id: str, state: Any) -> bool:
        """保存状态
        
        Args:
            state_id: 状态ID
            state: 状态对象
            
        Returns:
            bool: 是否成功保存
        """
        pass
    
    @abstractmethod
    def load(self, state_id: str) -> Optional[Any]:
        """加载状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def delete(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def list(self) -> List[str]:
        """列出所有状态ID
        
        Returns:
            状态ID列表
        """
        pass
    
    @abstractmethod
    def exists(self, state_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            state_id: 状态ID
            
        Returns:
            bool: 是否存在
        """
        pass