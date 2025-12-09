"""基础状态接口定义

定义状态管理系统的基础接口，所有状态对象必须遵循此接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from ..common_domain import ISerializable, ITimestamped


class IState(ISerializable, ITimestamped, ABC):
    """基础状态接口
    
    定义状态对象的基本契约，所有状态实现必须遵循此接口。
    这是纯粹的状态抽象，不包含特定于任何执行引擎的功能。
    
    职责：
    - 提供状态数据的基本访问操作
    - 管理状态元数据
    - 维护状态标识信息
    - 跟踪状态完成状态
    
    使用示例：
        ```python
        # 创建状态实现
        class MyState(IState):
            def get_data(self, key, default=None):
                return self._data.get(key, default)
            
            def set_data(self, key, value):
                self._data[key] = value
        
        # 使用状态
        state = MyState()
        state.set_data("user_id", "12345")
        user_id = state.get_data("user_id")
        ```
    
    注意事项：
    - 状态对象应该是不可变的或提供适当的并发控制
    - 状态数据应该是可序列化的
    - 避免在状态中存储大对象或引用
    
    相关接口：
    - IStateCache: 状态缓存接口
    - IStateManager: 状态管理器接口
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    @abstractmethod
    def get_data(self, key: str, default: Any = None) -> Any:
        """从状态中获取数据
        
        Args:
            key: 要获取数据的键
            default: 如果键不存在时返回的默认值
            
        Returns:
            与键关联的值，如果未找到则返回默认值
            
        Raises:
            KeyError: 当键不存在且未提供默认值时（可选实现）
            
        Examples:
            ```python
            # 获取存在的数据
            value = state.get_data("user_id")
            
            # 获取不存在的数据并提供默认值
            value = state.get_data("non_existent", "default_value")
            ```
        """
        pass
    
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """在状态中设置数据
        
        Args:
            key: 要设置的键
            value: 要与键关联的值
            
        Raises:
            ValueError: 当键或值无效时
            TypeError: 当值类型不支持时
            
        Examples:
            ```python
            # 设置简单值
            state.set_data("count", 42)
            
            # 设置复杂值
            state.set_data("config", {"key": "value"})
            ```
        """
        pass
    
    @abstractmethod
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """从状态中获取元数据
        
        Args:
            key: 要获取元数据的键
            default: 如果键不存在时返回的默认值
            
        Returns:
            与键关联的元数据值，如果未找到则返回默认值
            
        Examples:
            ```python
            # 获取创建时间
            created_at = state.get_metadata("created_at")
            
            # 获取状态版本
            version = state.get_metadata("version", "1.0")
            ```
        """
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """在状态中设置元数据
        
        Args:
            key: 要设置的键
            value: 要与键关联的元数据值
            
        Examples:
            ```python
            # 设置创建时间
            state.set_metadata("created_at", datetime.now())
            
            # 设置状态版本
            state.set_metadata("version", "2.0")
            ```
        """
        pass
    
    @abstractmethod
    def get_id(self) -> Optional[str]:
        """获取状态ID
        
        Returns:
            状态ID，如果未设置则返回None
            
        Examples:
            ```python
            state_id = state.get_id()
            if state_id:
                print(f"State ID: {state_id}")
            ```
        """
        pass
    
    @abstractmethod
    def set_id(self, id: str) -> None:
        """设置状态ID
        
        Args:
            id: 要设置的ID
            
        Raises:
            ValueError: 当ID无效时
            RuntimeError: 当ID已设置且不允许更改时
            
        Examples:
            ```python
            # 设置新ID
            state.set_id("unique_state_id")
            ```
        """
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """检查状态是否完成
        
        Returns:
            如果完成则返回True，否则返回False
            
        Examples:
            ```python
            if state.is_complete():
                print("State processing completed")
            else:
                print("State still in progress")
            ```
        """
        pass
    
    @abstractmethod
    def mark_complete(self) -> None:
        """将状态标记为完成
        
        Raises:
            RuntimeError: 当状态已经完成时（可选实现）
            
        Examples:
            ```python
            # 标记状态完成
            state.mark_complete()
            
            # 验证状态完成
            assert state.is_complete()
            ```
        """
        pass