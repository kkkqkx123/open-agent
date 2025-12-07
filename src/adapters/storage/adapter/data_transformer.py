"""数据转换器实现

提供领域对象和存储格式之间的转换功能。
"""

import json
from typing import Dict, Any, Optional, Union
from datetime import datetime
from src.services.logger.injection import get_logger
from src.interfaces.storage.adapter import IDataTransformer


logger = get_logger(__name__)


class DefaultDataTransformer(IDataTransformer):
    """默认数据转换器实现
    
    提供基本的数据转换功能，处理常见的数据类型转换。
    """
    
    def __init__(self, serialize_complex: bool = True) -> None:
        """初始化数据转换器
        
        Args:
            serialize_complex: 是否序列化复杂对象
        """
        self.serialize_complex = serialize_complex
        self.logger = get_logger(self.__class__.__name__)
    
    def to_storage_format(self, domain_object: Any) -> Dict[str, Any]:
        """领域对象转存储格式
        
        Args:
            domain_object: 领域对象
            
        Returns:
            存储格式数据
        """
        try:
            if domain_object is None:
                return {}
            
            # 如果已经是字典，直接处理
            if isinstance(domain_object, dict):
                return self._process_dict_for_storage(domain_object)
            
            # 如果对象有to_dict方法，使用它
            if hasattr(domain_object, 'to_dict') and callable(getattr(domain_object, 'to_dict')):
                return self._process_dict_for_storage(domain_object.to_dict())
            
            # 如果对象有__dict__属性，使用它
            if hasattr(domain_object, '__dict__'):
                return self._process_dict_for_storage(domain_object.__dict__)
            
            # 如果是基本类型，包装为字典
            if isinstance(domain_object, (str, int, float, bool)):
                return {"value": domain_object, "type": type(domain_object).__name__}
            
            # 如果是列表或元组，转换为字典
            if isinstance(domain_object, (list, tuple)):
                return {"value": list(domain_object), "type": "array"}
            
            # 复杂对象序列化
            if self.serialize_complex:
                try:
                    serialized = json.dumps(domain_object, default=str)
                    return {"value": serialized, "type": "serialized"}
                except (TypeError, ValueError) as e:
                    self.logger.warning(f"无法序列化对象: {e}")
                    return {"value": str(domain_object), "type": "string"}
            
            # 默认转换为字符串
            return {"value": str(domain_object), "type": "string"}
            
        except Exception as e:
            self.logger.error(f"转换为存储格式失败: {e}")
            raise
    
    def from_storage_format(self, storage_data: Dict[str, Any]) -> Any:
        """存储格式转领域对象
        
        Args:
            storage_data: 存储格式数据
            
        Returns:
            领域对象
        """
        try:
            if storage_data is None:
                return None
            
            if not isinstance(storage_data, dict):
                return storage_data
            
            # 检查是否有类型信息
            if "type" in storage_data and "value" in storage_data:
                return self._convert_by_type(storage_data["value"], storage_data["type"])
            
            # 否则返回处理后的字典
            return self._process_dict_from_storage(storage_data)
            
        except Exception as e:
            self.logger.error(f"从存储格式转换失败: {e}")
            raise
    
    def _process_dict_for_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典用于存储
        
        Args:
            data: 原始字典
            
        Returns:
            处理后的字典
        """
        processed = {}
        
        for key, value in data.items():
            # 跳过私有属性
            if key.startswith('_'):
                continue
            
            # 处理特殊值
            if isinstance(value, datetime):
                processed[key] = {
                    "value": value.isoformat(),
                    "type": "datetime"
                }
            elif isinstance(value, (dict, list, tuple)):
                processed[key] = {
                    "value": value,
                    "type": type(value).__name__
                }
            elif hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
                processed[key] = value.to_dict()
            else:
                processed[key] = value
        
        # 添加处理时间戳
        processed["_processed_at"] = datetime.now().isoformat()
        
        return processed
    
    def _process_dict_from_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典从存储格式
        
        Args:
            data: 存储格式字典
            
        Returns:
            处理后的字典
        """
        processed = {}
        
        for key, value in data.items():
            # 跳过元数据
            if key.startswith('_'):
                continue
            
            # 处理特殊值
            if isinstance(value, dict) and "type" in value and "value" in value:
                processed[key] = self._convert_by_type(value["value"], value["type"])
            else:
                processed[key] = value
        
        return processed
    
    def _convert_by_type(self, value: Any, type_name: str) -> Any:
        """根据类型转换值
        
        Args:
            value: 原始值
            type_name: 类型名称
            
        Returns:
            转换后的值
        """
        try:
            if type_name == "datetime":
                return datetime.fromisoformat(value)
            elif type_name == "int":
                return int(value)
            elif type_name == "float":
                return float(value)
            elif type_name == "bool":
                return bool(value)
            elif type_name == "array":
                return list(value)
            elif type_name == "serialized":
                return json.loads(value)
            else:
                return value
        except (ValueError, TypeError) as e:
            self.logger.warning(f"类型转换失败 ({type_name}): {e}")
            return value


class StateDataTransformer(IDataTransformer):
    """状态数据转换器
    
    专门用于状态数据的转换，处理状态特有的数据结构。
    """
    
    def __init__(self) -> None:
        """初始化状态数据转换器"""
        self.logger = get_logger(self.__class__.__name__)
        self.default_transformer = DefaultDataTransformer()
    
    def to_storage_format(self, domain_object: Any) -> Dict[str, Any]:
        """领域对象转存储格式
        
        Args:
            domain_object: 领域对象
            
        Returns:
            存储格式数据
        """
        try:
            # 使用默认转换器处理
            storage_data = self.default_transformer.to_storage_format(domain_object)
            
            # 添加状态特有的元数据
            if isinstance(storage_data, dict):
                storage_data["_data_type"] = "state"
                storage_data["_version"] = "1.0"
            
            return storage_data
            
        except Exception as e:
            self.logger.error(f"状态数据转换为存储格式失败: {e}")
            raise
    
    def from_storage_format(self, storage_data: Dict[str, Any]) -> Any:
        """存储格式转领域对象
        
        Args:
            storage_data: 存储格式数据
            
        Returns:
            领域对象
        """
        try:
            # 验证状态数据
            if isinstance(storage_data, dict) and storage_data.get("_data_type") != "state":
                self.logger.warning("数据类型不匹配，可能不是状态数据")
            
            # 使用默认转换器处理
            return self.default_transformer.from_storage_format(storage_data)
            
        except Exception as e:
            self.logger.error(f"状态数据从存储格式转换失败: {e}")
            raise


class HistoryDataTransformer(IDataTransformer):
    """历史数据转换器
    
    专门用于历史数据的转换，处理历史记录特有的数据结构。
    """
    
    def __init__(self) -> None:
        """初始化历史数据转换器"""
        self.logger = get_logger(self.__class__.__name__)
        self.default_transformer = DefaultDataTransformer()
    
    def to_storage_format(self, domain_object: Any) -> Dict[str, Any]:
        """领域对象转存储格式
        
        Args:
            domain_object: 领域对象
            
        Returns:
            存储格式数据
        """
        try:
            # 使用默认转换器处理
            storage_data = self.default_transformer.to_storage_format(domain_object)
            
            # 添加历史特有的元数据
            if isinstance(storage_data, dict):
                storage_data["_data_type"] = "history"
                storage_data["_version"] = "1.0"
                
                # 确保有时间戳
                if "timestamp" not in storage_data:
                    storage_data["timestamp"] = datetime.now().isoformat()
            
            return storage_data
            
        except Exception as e:
            self.logger.error(f"历史数据转换为存储格式失败: {e}")
            raise
    
    def from_storage_format(self, storage_data: Dict[str, Any]) -> Any:
        """存储格式转领域对象
        
        Args:
            storage_data: 存储格式数据
            
        Returns:
            领域对象
        """
        try:
            # 验证历史数据
            if isinstance(storage_data, dict) and storage_data.get("_data_type") != "history":
                self.logger.warning("数据类型不匹配，可能不是历史数据")
            
            # 使用默认转换器处理
            return self.default_transformer.from_storage_format(storage_data)
            
        except Exception as e:
            self.logger.error(f"历史数据从存储格式转换失败: {e}")
            raise


class SnapshotDataTransformer(IDataTransformer):
    """快照数据转换器
    
    专门用于快照数据的转换，处理快照特有的数据结构。
    """
    
    def __init__(self) -> None:
        """初始化快照数据转换器"""
        self.logger = get_logger(self.__class__.__name__)
        self.default_transformer = DefaultDataTransformer()
    
    def to_storage_format(self, domain_object: Any) -> Dict[str, Any]:
        """领域对象转存储格式
        
        Args:
            domain_object: 领域对象
            
        Returns:
            存储格式数据
        """
        try:
            # 使用默认转换器处理
            storage_data = self.default_transformer.to_storage_format(domain_object)
            
            # 添加快照特有的元数据
            if isinstance(storage_data, dict):
                storage_data["_data_type"] = "snapshot"
                storage_data["_version"] = "1.0"
                
                # 确保有快照ID和时间戳
                if "snapshot_id" not in storage_data:
                    storage_data["snapshot_id"] = f"snapshot_{datetime.now().timestamp()}"
                if "timestamp" not in storage_data:
                    storage_data["timestamp"] = datetime.now().isoformat()
            
            return storage_data
            
        except Exception as e:
            self.logger.error(f"快照数据转换为存储格式失败: {e}")
            raise
    
    def from_storage_format(self, storage_data: Dict[str, Any]) -> Any:
        """存储格式转领域对象
        
        Args:
            storage_data: 存储格式数据
            
        Returns:
            领域对象
        """
        try:
            # 验证快照数据
            if isinstance(storage_data, dict) and storage_data.get("_data_type") != "snapshot":
                self.logger.warning("数据类型不匹配，可能不是快照数据")
            
            # 使用默认转换器处理
            return self.default_transformer.from_storage_format(storage_data)
            
        except Exception as e:
            self.logger.error(f"快照数据从存储格式转换失败: {e}")
            raise