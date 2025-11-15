# Checkpoint 与 History 模块公用组件实施步骤

## 概述

本文档提供了将 Checkpoint 和 History 模块中的重复功能提取为公用组件的详细实施步骤。实施过程分为三个阶段，每个阶段都有明确的目标、任务和验收标准。

## 实施原则

1. **渐进式重构**: 分阶段实施，确保系统稳定性
2. **向后兼容**: 保持现有接口的兼容性
3. **测试驱动**: 每个组件都有完整的测试覆盖
4. **文档同步**: 及时更新相关文档

## 阶段一：核心公用组件实施（第1-2周）

### 1.1 创建公用组件基础设施

#### 步骤1.1.1: 创建目录结构
```bash
mkdir -p src/infrastructure/common/{serialization,cache,temporal,metadata,id_generator,storage}
mkdir -p tests/infrastructure/common/{serialization,cache,temporal,metadata,id_generator,storage}
```

#### 步骤1.1.2: 创建基础接口
创建 `src/infrastructure/common/interfaces.py`:

```python
"""公用组件基础接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from datetime import datetime


class ISerializable(ABC):
    """可序列化接口"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ISerializable':
        """从字典创建实例"""
        pass


class ICacheable(ABC):
    """可缓存接口"""
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """获取缓存键"""
        pass
    
    @abstractmethod
    def get_cache_ttl(self) -> int:
        """获取缓存TTL"""
        pass


class ITimestamped(ABC):
    """时间戳接口"""
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        pass


class IStorage(ABC):
    """统一存储接口"""
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any]) -> list[Dict[str, Any]]:
        """列出数据"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据"""
        pass
```

#### 步骤1.1.3: 创建时间管理器
创建 `src/infrastructure/common/temporal/temporal_manager.py`:

```python
"""统一时间管理器"""

from datetime import datetime, timedelta
from typing import Optional, Union
import iso8601


class TemporalManager:
    """统一时间管理器"""
    
    @staticmethod
    def now() -> datetime:
        """获取当前时间"""
        return datetime.now()
    
    @staticmethod
    def utc_now() -> datetime:
        """获取当前UTC时间"""
        return datetime.utcnow()
    
    @staticmethod
    def format_timestamp(dt: datetime, format: str = "iso") -> str:
        """格式化时间戳
        
        Args:
            dt: 时间对象
            format: 格式类型 ("iso", "timestamp", "readable")
            
        Returns:
            格式化的时间字符串
        """
        if format == "iso":
            return dt.isoformat()
        elif format == "timestamp":
            return str(int(dt.timestamp()))
        elif format == "readable":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def parse_timestamp(timestamp: str, format: str = "iso") -> datetime:
        """解析时间戳
        
        Args:
            timestamp: 时间字符串
            format: 格式类型 ("iso", "timestamp", "readable")
            
        Returns:
            解析后的时间对象
        """
        if format == "iso":
            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                # 尝试解析ISO8601格式
                return iso8601.parse_date(timestamp)
        elif format == "timestamp":
            return datetime.fromtimestamp(float(timestamp))
        elif format == "readable":
            return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def calculate_duration(start: datetime, end: datetime) -> float:
        """计算时间差（秒）
        
        Args:
            start: 开始时间
            end: 结束时间
            
        Returns:
            时间差（秒）
        """
        return (end - start).total_seconds()
    
    @staticmethod
    def add_duration(dt: datetime, seconds: float) -> datetime:
        """添加时间间隔
        
        Args:
            dt: 原始时间
            seconds: 秒数
            
        Returns:
            新的时间
        """
        return dt + timedelta(seconds=seconds)
    
    @staticmethod
    def is_expired(dt: datetime, ttl_seconds: float) -> bool:
        """检查是否过期
        
        Args:
            dt: 时间戳
            ttl_seconds: TTL秒数
            
        Returns:
            是否过期
        """
        return TemporalManager.calculate_duration(dt, TemporalManager.now()) > ttl_seconds
```

#### 步骤1.1.4: 创建元数据管理器
创建 `src/infrastructure/common/metadata/metadata_manager.py`:

```python
"""统一元数据管理器"""

from typing import Any, Dict, Optional, Union
import json


class MetadataManager:
    """统一元数据管理器"""
    
    @staticmethod
    def normalize_metadata(metadata: Any) -> Dict[str, Any]:
        """标准化元数据为字典格式
        
        Args:
            metadata: 原始元数据
            
        Returns:
            标准化的元数据字典
        """
        if metadata is None:
            return {}
        
        if isinstance(metadata, dict):
            return dict(metadata)
        elif hasattr(metadata, '__dict__'):
            return dict(metadata.__dict__)
        elif hasattr(metadata, '__getitem__'):
            try:
                return {k: metadata[k] for k in metadata}
            except (TypeError, KeyError):
                return {}
        else:
            return {}
    
    @staticmethod
    def merge_metadata(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并元数据
        
        Args:
            base: 基础元数据
            override: 覆盖元数据
            
        Returns:
            合并后的元数据
        """
        result = base.copy()
        result.update(override)
        return result
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """验证元数据
        
        Args:
            metadata: 元数据字典
            schema: 验证模式
            
        Returns:
            是否验证通过
        """
        # 简化的验证逻辑，实际可以使用jsonschema等库
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in metadata:
                return False
        
        return True
    
    @staticmethod
    def extract_field(metadata: Dict[str, Any], field: str, default: Any = None) -> Any:
        """提取字段值
        
        Args:
            metadata: 元数据字典
            field: 字段名
            default: 默认值
            
        Returns:
            字段值
        """
        return metadata.get(field, default)
    
    @staticmethod
    def set_field(metadata: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """设置字段值
        
        Args:
            metadata: 元数据字典
            field: 字段名
            value: 字段值
            
        Returns:
            更新后的元数据
        """
        result = metadata.copy()
        result[field] = value
        return result
    
    @staticmethod
    def remove_field(metadata: Dict[str, Any], field: str) -> Dict[str, Any]:
        """移除字段
        
        Args:
            metadata: 元数据字典
            field: 字段名
            
        Returns:
            更新后的元数据
        """
        result = metadata.copy()
        result.pop(field, None)
        return result
    
    @staticmethod
    def to_json(metadata: Dict[str, Any], indent: int = 2) -> str:
        """转换为JSON字符串
        
        Args:
            metadata: 元数据字典
            indent: 缩进空格数
            
        Returns:
            JSON字符串
        """
        return json.dumps(metadata, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def from_json(json_str: str) -> Dict[str, Any]:
        """从JSON字符串解析
        
        Args:
            json_str: JSON字符串
            
        Returns:
            元数据字典
        """
        return json.loads(json_str)
```

### 1.2 实施统一序列化器

#### 步骤1.2.1: 创建序列化器基类
创建 `src/infrastructure/common/serialization/base_serializer.py`:

```python
"""序列化器基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union
import json
import pickle
import hashlib
from datetime import datetime

from ..interfaces import ISerializable


class BaseSerializer(ABC):
    """序列化器基类"""
    
    FORMAT_JSON = "json"
    FORMAT_PICKLE = "pickle"
    FORMAT_COMPACT_JSON = "compact_json"
    
    @abstractmethod
    def serialize(self, data: Any, format: str = FORMAT_JSON, **kwargs) -> Union[str, bytes]:
        """序列化数据"""
        pass
    
    @abstractmethod
    def deserialize(self, data: Union[str, bytes], format: str = FORMAT_JSON, **kwargs) -> Any:
        """反序列化数据"""
        pass
    
    def handle_enums(self, data: Any) -> Any:
        """处理枚举类型"""
        if hasattr(data, 'value'):
            return data.value
        return data
    
    def handle_datetime(self, data: Any) -> Any:
        """处理日期时间类型"""
        if isinstance(data, datetime):
            return data.isoformat()
        return data
    
    def calculate_hash(self, data: Any) -> str:
        """计算数据哈希"""
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode()).hexdigest()
        except (TypeError, ValueError):
            return hashlib.md5(str(data).encode()).hexdigest()
```

#### 步骤1.2.2: 创建通用序列化器
创建 `src/infrastructure/common/serialization/universal_serializer.py`:

```python
"""通用序列化器"""

from typing import Any, Dict, Union, List
import json
import pickle
from datetime import datetime

from .base_serializer import BaseSerializer
from ..interfaces import ISerializable


class UniversalSerializer(BaseSerializer):
    """通用序列化器"""
    
    def __init__(self):
        self._type_handlers = {
            datetime: self._handle_datetime,
            'enum': self._handle_enum,
            'serializable': self._handle_serializable,
        }
    
    def serialize(self, data: Any, format: str = BaseSerializer.FORMAT_JSON, **kwargs) -> Union[str, bytes]:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            format: 序列化格式
            **kwargs: 其他参数
            
        Returns:
            序列化后的数据
        """
        try:
            processed_data = self._preprocess_data(data)
            
            if format == self.FORMAT_JSON:
                return json.dumps(processed_data, ensure_ascii=False, indent=2, default=str)
            elif format == self.FORMAT_COMPACT_JSON:
                return json.dumps(processed_data, ensure_ascii=False, separators=(',', ':'))
            elif format == self.FORMAT_PICKLE:
                return pickle.dumps(processed_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise SerializationError(f"Serialization failed: {e}")
    
    def deserialize(self, data: Union[str, bytes], format: str = BaseSerializer.FORMAT_JSON, **kwargs) -> Any:
        """反序列化数据
        
        Args:
            data: 要反序列化的数据
            format: 序列化格式
            **kwargs: 其他参数
            
        Returns:
            反序列化后的数据
        """
        try:
            if format == self.FORMAT_JSON or format == self.FORMAT_COMPACT_JSON:
                result = json.loads(data)
                return self._postprocess_data(result)
            elif format == self.FORMAT_PICKLE:
                return pickle.loads(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise SerializationError(f"Deserialization failed: {e}")
    
    def _preprocess_data(self, data: Any) -> Any:
        """预处理数据"""
        if isinstance(data, dict):
            return {k: self._preprocess_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._preprocess_data(item) for item in data]
        elif isinstance(data, datetime):
            return self._handle_datetime(data)
        elif hasattr(data, 'value'):  # 枚举类型
            return self._handle_enum(data)
        elif isinstance(data, ISerializable):
            return self._handle_serializable(data)
        else:
            return data
    
    def _postprocess_data(self, data: Any) -> Any:
        """后处理数据"""
        # 这里可以添加特定的反序列化逻辑
        return data
    
    def _handle_datetime(self, dt: datetime) -> str:
        """处理日期时间"""
        return dt.isoformat()
    
    def _handle_enum(self, enum_obj: Any) -> str:
        """处理枚举类型"""
        return f"{enum_obj.__class__.__name__}.{enum_obj.name}"
    
    def _handle_serializable(self, obj: ISerializable) -> Dict[str, Any]:
        """处理可序列化对象"""
        return obj.to_dict()


class SerializationError(Exception):
    """序列化错误"""
    pass
```

### 1.3 实施增强缓存管理器

#### 步骤1.3.1: 创建缓存条目类
创建 `src/infrastructure/common/cache/cache_entry.py`:

```python
"""缓存条目定义"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value
    
    def extend_ttl(self, seconds: int) -> None:
        """延长TTL"""
        if self.expires_at:
            self.expires_at = max(self.expires_at, datetime.now() + timedelta(seconds=seconds))
        else:
            self.expires_at = datetime.now() + timedelta(seconds=seconds)


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def record_hit(self) -> None:
        """记录命中"""
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self) -> None:
        """记录未命中"""
        self.misses += 1
        self.total_requests += 1
    
    def record_eviction(self) -> None:
        """记录淘汰"""
        self.evictions += 1
```

#### 步骤1.3.2: 创建增强缓存管理器
创建 `src/infrastructure/common/cache/enhanced_cache_manager.py`:

```python
"""增强缓存管理器"""

import threading
from collections import OrderedDict
from typing import Any, Dict, Optional, List, Pattern
import re
from datetime import datetime

from .cache_entry import CacheEntry, CacheStats
from ..temporal.temporal_manager import TemporalManager


class EnhancedCacheManager:
    """增强缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.record_miss()
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats.record_miss()
                return None
            
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            self._stats.record_hit()
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认TTL
        """
        with self._lock:
            now = TemporalManager.now()
            expires_at = None
            if ttl is not None and ttl > 0:
                expires_at = now + timedelta(seconds=ttl)
            elif self.default_ttl > 0:
                expires_at = now + timedelta(seconds=self.default_ttl)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expires_at
            )
            
            # 如果键已存在，更新值
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
                return
            
            # 检查容量限制
            while len(self._cache) >= self.max_size and self.max_size > 0:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.record_eviction()
            
            # 添加新项
            self._cache[key] = entry
    
    async def remove(self, key: str) -> bool:
        """移除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def remove_by_pattern(self, pattern: str) -> int:
        """根据模式移除缓存项
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            移除的缓存项数量
        """
        with self._lock:
            regex = re.compile(pattern)
            keys_to_remove = [key for key in self._cache.keys() if regex.match(key)]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    async def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """清理过期的缓存项
        
        Returns:
            清理的缓存项数量
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "total_requests": self._stats.total_requests,
                "hit_rate": self._stats.hit_rate,
                "keys": list(self._cache.keys())
            }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息
        
        Returns:
            详细缓存信息
        """
        with self._lock:
            cache_info = {}
            now = TemporalManager.now()
            
            for key, entry in self._cache.items():
                cache_info[key] = {
                    "created_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat(),
                    "is_expired": entry.is_expired(),
                    "ttl_remaining": (entry.expires_at - now).total_seconds() if entry.expires_at else None
                }
            
            return cache_info
    
    async def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """获取缓存值，如果不存在则通过工厂函数创建
        
        Args:
            key: 缓存键
            factory_func: 工厂函数
            ttl: TTL（秒）
            
        Returns:
            缓存值
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await factory_func()
        await self.set(key, value, ttl)
        return value
```

### 1.4 编写测试用例

#### 步骤1.4.1: 创建时间管理器测试
创建 `tests/infrastructure/common/temporal/test_temporal_manager.py`:

```python
"""时间管理器测试"""

import pytest
from datetime import datetime, timedelta
from src.infrastructure.common.temporal.temporal_manager import TemporalManager


class TestTemporalManager:
    """时间管理器测试类"""
    
    def test_now(self):
        """测试获取当前时间"""
        now = TemporalManager.now()
        assert isinstance(now, datetime)
        assert now <= datetime.now()
    
    def test_format_timestamp_iso(self):
        """测试ISO格式时间戳"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = TemporalManager.format_timestamp(dt, "iso")
        assert result == "2023-01-01T12:00:00"
    
    def test_format_timestamp_timestamp(self):
        """测试时间戳格式"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = TemporalManager.format_timestamp(dt, "timestamp")
        assert isinstance(int(result), int)
    
    def test_parse_timestamp_iso(self):
        """测试解析ISO时间戳"""
        timestamp = "2023-01-01T12:00:00"
        result = TemporalManager.parse_timestamp(timestamp, "iso")
        assert result == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_calculate_duration(self):
        """测试计算时间差"""
        start = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 1, 0)
        result = TemporalManager.calculate_duration(start, end)
        assert result == 60.0
    
    def test_is_expired(self):
        """测试过期检查"""
        past = datetime.now() - timedelta(seconds=10)
        assert TemporalManager.is_expired(past, 5) == True
        assert TemporalManager.is_expired(past, 15) == False
```

#### 步骤1.4.2: 创建序列化器测试
创建 `tests/infrastructure/common/serialization/test_universal_serializer.py`:

```python
"""通用序列化器测试"""

import pytest
import json
from datetime import datetime
from enum import Enum
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer, SerializationError
from src.infrastructure.common.interfaces import ISerializable


class TestEnum(Enum):
    """测试枚举"""
    VALUE1 = "value1"
    VALUE2 = "value2"


class TestSerializable(ISerializable):
    """测试可序列化类"""
    
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
    
    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestSerializable':
        return cls(data["name"], data["value"])


class TestUniversalSerializer:
    """通用序列化器测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.serializer = UniversalSerializer()
    
    def test_serialize_json(self):
        """测试JSON序列化"""
        data = {"name": "test", "value": 123}
        result = self.serializer.serialize(data, "json")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == data
    
    def test_serialize_compact_json(self):
        """测试紧凑JSON序列化"""
        data = {"name": "test", "value": 123}
        result = self.serializer.serialize(data, "compact_json")
        assert isinstance(result, str)
        assert ":" in result  # 紧凑格式包含冒号
    
    def test_serialize_pickle(self):
        """测试Pickle序列化"""
        data = {"name": "test", "value": 123}
        result = self.serializer.serialize(data, "pickle")
        assert isinstance(result, bytes)
    
    def test_deserialize_json(self):
        """测试JSON反序列化"""
        data = {"name": "test", "value": 123}
        serialized = json.dumps(data)
        result = self.serializer.deserialize(serialized, "json")
        assert result == data
    
    def test_serialize_datetime(self):
        """测试日期时间序列化"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        data = {"timestamp": dt}
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert parsed["timestamp"] == dt.isoformat()
    
    def test_serialize_enum(self):
        """测试枚举序列化"""
        data = {"enum_value": TestEnum.VALUE1}
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert "TestEnum" in parsed["enum_value"]
    
    def test_serialize_serializable(self):
        """测试可序列化对象"""
        obj = TestSerializable("test", 123)
        data = {"object": obj}
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert parsed["object"]["name"] == "test"
        assert parsed["object"]["value"] == 123
    
    def test_serialize_error(self):
        """测试序列化错误"""
        with pytest.raises(SerializationError):
            self.serializer.serialize(object(), "invalid_format")
```

### 1.5 验收标准

#### 1.5.1 功能验收标准
- [ ] 所有公用组件接口定义完成
- [ ] 时间管理器支持多种格式和时间计算
- [ ] 元数据管理器支持标准化、合并和验证
- [ ] 序列化器支持JSON、Pickle和自定义类型处理
- [ ] 缓存管理器支持TTL、LRU和统计功能

#### 1.5.2 质量验收标准
- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有公共方法都有文档字符串
- [ ] 类型注解完整
- [ ] 错误处理完善
- [ ] 性能测试通过

#### 1.5.3 集成验收标准
- [ ] 与现有代码兼容
- [ ] 不影响现有功能
- [ ] 性能不低于原有实现
- [ ] 日志记录正常

## 阶段二：存储抽象层实施（第3-4周）

### 2.1 创建统一存储接口

#### 步骤2.1.1: 实现基础存储类
创建 `src/infrastructure/common/storage/base_storage.py`:

```python
"""基础存储实现"""

from abc import ABC
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

from ..interfaces import IStorage
from ..serialization.universal_serializer import UniversalSerializer
from ..temporal.temporal_manager import TemporalManager
from ..metadata.metadata_manager import MetadataManager
from ..cache.enhanced_cache_manager import EnhancedCacheManager


class BaseStorage(IStorage):
    """存储基类，提供通用功能"""
    
    def __init__(
        self,
        serializer: Optional[UniversalSerializer] = None,
        temporal_manager: Optional[TemporalManager] = None,
        metadata_manager: Optional[MetadataManager] = None,
        cache_manager: Optional[EnhancedCacheManager] = None
    ):
        """初始化基础存储
        
        Args:
            serializer: 序列化器
            temporal_manager: 时间管理器
            metadata_manager: 元数据管理器
            cache_manager: 缓存管理器
        """
        self.serializer = serializer or UniversalSerializer()
        self.temporal = temporal_manager or TemporalManager()
        self.metadata = metadata_manager or MetadataManager()
        self.cache = cache_manager
    
    async def save_with_metadata(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """保存数据并处理元数据
        
        Args:
            data: 要保存的数据
            metadata: 元数据
            ttl: 缓存TTL
            
        Returns:
            是否保存成功
        """
        # 添加时间戳
        data["created_at"] = self.temporal.format_timestamp(
            self.temporal.now(), "iso"
        )
        data["updated_at"] = data["created_at"]
        
        # 处理元数据
        if metadata:
            normalized_metadata = self.metadata.normalize_metadata(metadata)
            data["metadata"] = normalized_metadata
        
        # 保存数据
        success = await self.save(data)
        
        # 缓存数据
        if success and self.cache and data.get("id"):
            await self.cache.set(data["id"], data, ttl)
        
        return success
    
    async def load_with_cache(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据（优先从缓存）
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
        """
        # 先从缓存获取
        if self.cache:
            cached_data = await self.cache.get(id)
            if cached_data:
                return cached_data
        
        # 从存储加载
        data = await self.load(id)
        
        # 缓存结果
        if data and self.cache:
            await self.cache.set(id, data)
        
        return data
    
    async def update_with_metadata(
        self,
        id: str,
        updates: Dict[str, Any],
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新数据并处理元数据
        
        Args:
            id: 数据ID
            updates: 更新数据
            metadata_updates: 元数据更新
            
        Returns:
            是否更新成功
        """
        # 加载现有数据
        existing_data = await self.load(id)
        if not existing_data:
            return False
        
        # 更新数据
        existing_data.update(updates)
        existing_data["updated_at"] = self.temporal.format_timestamp(
            self.temporal.now(), "iso"
        )
        
        # 更新元数据
        if metadata_updates and "metadata" in existing_data:
            updated_metadata = self.metadata.merge_metadata(
                existing_data["metadata"], metadata_updates
            )
            existing_data["metadata"] = updated_metadata
        
        # 保存更新
        success = await self.save(existing_data)
        
        # 更新缓存
        if success and self.cache:
            await self.cache.set(id, existing_data)
        
        return success
    
    async def list_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据元数据过滤列表
        
        Args:
            filters: 元数据过滤条件
            limit: 限制数量
            
        Returns:
            符合条件的数据列表
        """
        all_data = await self.list({})
        
        # 过滤数据
        filtered_data = []
        for item in all_data:
            metadata = item.get("metadata", {})
            match = True
            
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_data.append(item)
                if limit and len(filtered_data) >= limit:
                    break
        
        return filtered_data
    
    async def delete_with_cache(self, id: str) -> bool:
        """删除数据并清理缓存
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        # 删除数据
        success = await self.delete(id)
        
        # 清理缓存
        if success and self.cache:
            await self.cache.remove(id)
        
        return success
```

### 2.2 迁移现有存储实现

#### 步骤2.2.1: 创建Checkpoint存储适配器
创建 `src/infrastructure/common/storage/checkpoint_storage_adapter.py`:

```python
"""Checkpoint存储适配器"""

from typing import Dict, Any, Optional, List
from src.domain.checkpoint.interfaces import ICheckpointStore
from .base_storage import BaseStorage


class CheckpointStorageAdapter(ICheckpointStore):
    """Checkpoint存储适配器，将ICheckpointStore适配到BaseStorage"""
    
    def __init__(self, base_storage: BaseStorage):
        """初始化适配器
        
        Args:
            base_storage: 基础存储实例
        """
        self.base_storage = base_storage
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        return await self.base_storage.save_with_metadata(
            checkpoint_data,
            checkpoint_data.get("metadata", {}),
            ttl=3600  # 1小时缓存
        )
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        return await self.base_storage.list_by_metadata(
            {"thread_id": thread_id}
        )
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        if checkpoint_id:
            return await self.base_storage.load_with_cache(checkpoint_id)
        else:
            # 获取最新的checkpoint
            checkpoints = await self.list_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint"""
        if checkpoint_id:
            return await self.base_storage.delete_with_cache(checkpoint_id)
        else:
            # 删除所有checkpoint
            checkpoints = await self.list_by_thread(thread_id)
            success = True
            for checkpoint in checkpoints:
                if not await self.base_storage.delete_with_cache(checkpoint["id"]):
                    success = False
            return success
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        checkpoints = await self.list_by_thread(thread_id)
        return checkpoints[0] if checkpoints else None
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint"""
        checkpoints = await self.list_by_thread(thread_id)
        if len(checkpoints) <= max_count:
            return 0
        
        # 保留最新的max_count个
        checkpoints_to_keep = checkpoints[:max_count]
        checkpoints_to_delete = checkpoints[max_count:]
        
        # 删除多余的checkpoint
        deleted_count = 0
        for checkpoint in checkpoints_to_delete:
            if await self.base_storage.delete_with_cache(checkpoint["id"]):
                deleted_count += 1
        
        return deleted_count
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        return await self.base_storage.list_by_metadata({
            "thread_id": thread_id,
           