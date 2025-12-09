"""状态缓存接口定义

定义状态缓存的基本契约，提供同步缓存操作接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .base import IState


class IStateCache(ABC):
    """状态缓存接口
    
    定义状态缓存的基本契约，提供同步缓存操作接口。
    
    职责：
    - 提供状态对象的高速缓存访问
    - 支持TTL（生存时间）管理
    - 提供批量操作以提高性能
    - 维护缓存统计信息
    
    使用示例：
        ```python
        # 创建缓存实现
        cache = MyStateCache()
        
        # 缓存状态
        state = MyState()
        cache.put("state_1", state, ttl=3600)
        
        # 获取缓存状态
        cached_state = cache.get("state_1")
        ```
    
    注意事项：
    - 缓存实现应该是线程安全的
    - 考虑内存使用限制和清理策略
    - TTL管理应该精确到秒级
    
    相关接口：
    - IState: 基础状态接口
    - IStateManager: 状态管理器接口
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[IState]:
        """获取缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            状态实例，如果未找到或已过期则返回None
            
        Examples:
            ```python
            # 获取缓存状态
            state = cache.get("user_session_123")
            if state:
                print(f"Found cached state: {state.get_id()}")
            else:
                print("State not found in cache")
            ```
        """
        pass
    
    @abstractmethod
    def put(self, key: str, state: IState, ttl: Optional[int] = None) -> None:
        """设置缓存状态
        
        Args:
            key: 状态ID
            state: 状态实例
            ttl: TTL（秒），如果为None则使用默认值
            
        Raises:
            ValueError: 当key或state无效时
            TypeError: 当state不是IState实例时
            
        Examples:
            ```python
            # 缓存状态1小时
            cache.put("session_123", state, ttl=3600)
            
            # 使用默认TTL缓存
            cache.put("session_456", state)
            ```
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            是否删除成功
            
        Examples:
            ```python
            # 删除特定状态
            if cache.delete("session_123"):
                print("State deleted successfully")
            else:
                print("State not found")
            ```
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存
        
        Examples:
            ```python
            # 清空所有缓存
            cache.clear()
            print("All cache cleared")
            ```
        """
        pass
    
    @abstractmethod
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存中的状态数量
            
        Examples:
            ```python
            cache_size = cache.size()
            print(f"Cache contains {cache_size} states")
            ```
        """
        pass
    
    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """获取所有键
        
        Returns:
            所有状态ID列表
            
        Examples:
            ```python
            keys = cache.get_all_keys()
            print(f"Cached state IDs: {keys}")
            ```
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典，包含：
            - hit_count: 命中次数
            - miss_count: 未命中次数
            - hit_rate: 命中率
            - size: 当前缓存大小
            - memory_usage: 内存使用量（可选）
            
        Examples:
            ```python
            stats = cache.get_statistics()
            print(f"Hit rate: {stats['hit_rate']:.2%}")
            print(f"Cache size: {stats['size']}")
            ```
        """
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, IState]:
        """批量获取缓存状态
        
        Args:
            keys: 状态ID列表
            
        Returns:
            状态字典，只包含找到的状态
            
        Examples:
            ```python
            # 批量获取多个状态
            keys = ["session_1", "session_2", "session_3"]
            states = cache.get_many(keys)
            
            for key, state in states.items():
                print(f"Found state {key}: {state.get_id()}")
            ```
        """
        pass
    
    @abstractmethod
    def set_many(self, states: Dict[str, IState], ttl: Optional[int] = None) -> None:
        """批量设置缓存状态
        
        Args:
            states: 状态字典
            ttl: TTL（秒）
            
        Examples:
            ```python
            # 批量缓存状态
            states = {
                "session_1": state1,
                "session_2": state2,
                "session_3": state3
            }
            cache.set_many(states, ttl=1800)
            ```
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """清理过期缓存项
        
        Returns:
            清理的项数
            
        Examples:
            ```python
            # 定期清理过期项
            cleaned_count = cache.cleanup_expired()
            print(f"Cleaned {cleaned_count} expired items")
            ```
        """
        pass