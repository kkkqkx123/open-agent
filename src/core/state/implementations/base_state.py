"""基础状态实现

提供状态的基础实现，所有具体状态类型都可以继承此类。
"""

import uuid
from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, Optional
from datetime import datetime

from ..core.base import BaseState
from src.interfaces.state.base import IState
from src.interfaces.state.exceptions import StateError, StateValidationError
from src.infrastructure.error_management import handle_error, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class BaseStateImpl(BaseState):
    """基础状态实现类
    
    提供状态的基础功能实现，所有具体状态类型都可以继承此类。
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化基础状态实现"""
        super().__init__(**kwargs)
        
        # 如果没有提供ID，生成一个
        if not self._id:
            self._id = f"state_{uuid.uuid4().hex[:8]}"
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._id = id
        self._updated_at = datetime.now()
    
    def update_data(self, updates: Dict[str, Any]) -> None:
        """批量更新状态数据
        
        Args:
            updates: 更新的数据字典
        """
        self._data.update(updates)
        self._updated_at = datetime.now()
    
    def clear_data(self) -> None:
        """清空状态数据"""
        self._data.clear()
        self._updated_at = datetime.now()
    
    def has_data(self, key: str) -> bool:
        """检查是否包含指定数据
        
        Args:
            key: 数据键
            
        Returns:
            是否包含
        """
        return key in self._data
    
    def get_data_keys(self) -> list:
        """获取所有数据键
        
        Returns:
            数据键列表
        """
        return list(self._data.keys())
    
    def get_data_size(self) -> int:
        """获取数据大小
        
        Returns:
            数据项数量
        """
        return len(self._data)
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """批量更新元数据
        
        Args:
            updates: 更新的元数据字典
        """
        self._metadata.update(updates)
        self._updated_at = datetime.now()
    
    def clear_metadata(self) -> None:
        """清空元数据"""
        self._metadata.clear()
        self._updated_at = datetime.now()
    
    def has_metadata(self, key: str) -> bool:
        """检查是否包含指定元数据
        
        Args:
            key: 元数据键
            
        Returns:
            是否包含
        """
        return key in self._metadata
    
    def get_metadata_keys(self) -> list:
        """获取所有元数据键
        
        Returns:
            元数据键列表
        """
        return list(self._metadata.keys())
    
    def get_metadata_size(self) -> int:
        """获取元数据大小
        
        Returns:
            元数据项数量
        """
        return len(self._metadata)
    
    def clone(self) -> 'BaseStateImpl':
        """创建状态克隆
        
        Returns:
            克隆的状态实例
        """
        cloned_data = self.to_dict()
        return self.from_dict(cloned_data)
    
    def merge(self, other: IState) -> 'BaseStateImpl':
        """合并另一个状态
        
        Args:
            other: 另一个状态
            
        Returns:
            合并后的状态实例
            
        Raises:
            StateValidationError: 输入验证失败
            StateError: 合并操作失败
        """
        try:
            # 输入验证
            if other is None:
                raise StateValidationError("合并的状态对象不能为None")
            
            if not isinstance(other, IState):
                raise StateValidationError(
                    f"只能合并IState实例，实际类型: {type(other).__name__}"
                )
            
            # 获取其他状态的数据
            try:
                other_dict = other.to_dict()
            except Exception as e:
                raise StateError(f"获取其他状态数据失败: {e}") from e
            
            other_data = other_dict.get('data', {})
            other_metadata = other_dict.get('metadata', {})
            
            # 验证数据类型
            if not isinstance(other_data, dict):
                raise StateValidationError(
                    f"状态数据必须是字典类型，实际类型: {type(other_data).__name__}"
                )
            
            if not isinstance(other_metadata, dict):
                raise StateValidationError(
                    f"状态元数据必须是字典类型，实际类型: {type(other_metadata).__name__}"
                )
            
            # 备份当前状态，以便合并失败时回滚
            backup_data = self._data.copy()
            backup_metadata = self._metadata.copy()
            
            try:
                # 合并数据
                for key, value in other_data.items():
                    if value is None:
                        logger.warning(f"合并状态时字段 {key} 的值为None")
                    self._data[key] = value
                
                # 合并元数据
                for key, value in other_metadata.items():
                    if value is None:
                        logger.warning(f"合并元数据时字段 {key} 的值为None")
                    self._metadata[key] = value
                
                self._updated_at = datetime.now()
                
                logger.info(f"状态合并成功: {self._id} <- {other.get_id() if hasattr(other, 'get_id') else 'unknown'}")
                return self
                
            except Exception as e:
                # 回滚到合并前的状态
                self._data = backup_data
                self._metadata = backup_metadata
                raise StateError(f"状态合并失败，已回滚: {e}") from e
                
        except StateValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "state_id": self._id,
                "other_state_type": type(other).__name__ if other else None,
                "operation": "merge",
                "state_class": self.__class__.__name__
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise StateError(
                f"状态合并失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e
    
    def get_age(self) -> float:
        """获取状态年龄（秒）
        
        Returns:
            状态年龄
        """
        return (datetime.now() - self._created_at).total_seconds()
    
    def get_last_modified_age(self) -> float:
        """获取最后修改年龄（秒）
        
        Returns:
            最后修改年龄
        """
        return (datetime.now() - self._updated_at).total_seconds()
    
    def is_recent(self, max_age_seconds: float = 300) -> bool:
        """检查是否为最近创建的状态
        
        Args:
            max_age_seconds: 最大年龄（秒）
            
        Returns:
            是否为最近创建
        """
        return self.get_age() <= max_age_seconds
    
    def is_recently_modified(self, max_age_seconds: float = 60) -> bool:
        """检查是否为最近修改的状态
        
        Args:
            max_age_seconds: 最大年龄（秒）
            
        Returns:
            是否为最近修改
        """
        return self.get_last_modified_age() <= max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data": self._data,
            "metadata": self._metadata,
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "complete": self._complete,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseStateImpl':
        """从字典创建状态
        
        Args:
            data: 状态数据字典
            
        Returns:
            状态实例
            
        Raises:
            StateValidationError: 输入验证失败
            StateError: 创建操作失败
        """
        try:
            # 输入验证
            if data is None:
                raise StateValidationError("状态数据不能为None")
            
            if not isinstance(data, dict):
                raise StateValidationError(
                    f"状态数据必须是字典类型，实际类型: {type(data).__name__}"
                )
            
            # 创建实例
            instance = cls()
            
            try:
                # 验证并设置数据
                state_data = data.get("data", {})
                if not isinstance(state_data, dict):
                    raise StateValidationError(
                        f"状态数据必须是字典类型，实际类型: {type(state_data).__name__}"
                    )
                instance._data = state_data
                
                # 验证并设置元数据
                metadata = data.get("metadata", {})
                if not isinstance(metadata, dict):
                    raise StateValidationError(
                        f"状态元数据必须是字典类型，实际类型: {type(metadata).__name__}"
                    )
                instance._metadata = metadata
                
                # 设置ID
                state_id = data.get("id")
                if state_id is not None:
                    if not isinstance(state_id, str):
                        raise StateValidationError(
                            f"状态ID必须是字符串类型，实际类型: {type(state_id).__name__}"
                        )
                    instance._id = state_id
                
                # 设置完成状态
                complete = data.get("complete", False)
                if not isinstance(complete, bool):
                    raise StateValidationError(
                        f"完成状态必须是布尔类型，实际类型: {type(complete).__name__}"
                    )
                instance._complete = complete
                
                # 处理时间字段
                created_at_str = data.get("created_at")
                if created_at_str is not None:
                    if not isinstance(created_at_str, str):
                        raise StateValidationError(
                            f"创建时间必须是字符串类型，实际类型: {type(created_at_str).__name__}"
                        )
                    try:
                        instance._created_at = datetime.fromisoformat(created_at_str)
                    except ValueError as e:
                        raise StateValidationError(f"创建时间格式无效: {e}") from e
                
                updated_at_str = data.get("updated_at")
                if updated_at_str is not None:
                    if not isinstance(updated_at_str, str):
                        raise StateValidationError(
                            f"更新时间必须是字符串类型，实际类型: {type(updated_at_str).__name__}"
                        )
                    try:
                        instance._updated_at = datetime.fromisoformat(updated_at_str)
                    except ValueError as e:
                        raise StateValidationError(f"更新时间格式无效: {e}") from e
                
                logger.debug(f"从字典成功创建状态实例: {instance._id}")
                return instance
                
            except StateValidationError:
                # 重新抛出验证错误
                raise
            except Exception as e:
                raise StateError(f"设置状态属性失败: {e}") from e
                
        except StateValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "data_keys": list(data.keys()) if isinstance(data, dict) else None,
                "operation": "from_dict",
                "state_class": cls.__name__
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise StateError(
                f"从字典创建状态失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(id={self._id}, complete={self._complete})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}(id={self._id}, "
                f"created_at={self._created_at.isoformat()}, "
                f"updated_at={self._updated_at.isoformat()}, "
                f"complete={self._complete}, "
                f"data_size={len(self._data)}, "
                f"metadata_size={len(self._metadata)})")
    
    def __eq__(self, other: Any) -> bool:
        """相等性比较"""
        if not isinstance(other, BaseStateImpl):
            return False
        
        return (self._id == other._id and
                self._data == other._data and
                self._metadata == other._metadata and
                self._complete == other._complete)
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self._id) if self._id else hash(id(self))