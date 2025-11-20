"""过滤器和查询操作符定义

提供统一的过滤器操作符和构建器接口，支持跨存储类型的一致性查询。
"""

from enum import Enum
from typing import Dict, Any, Protocol, Optional, List, Union
from abc import ABC, abstractmethod


class FilterOperator(Enum):
    """过滤操作符定义"""
    EQ = "$eq"           # 相等
    NE = "$ne"           # 不等于
    IN = "$in"           # 在列表中
    NIN = "$nin"         # 不在列表中
    GT = "$gt"           # 大于
    GTE = "$gte"         # 大于等于
    LT = "$lt"           # 小于
    LTE = "$lte"         # 小于等于
    LIKE = "$like"       # 模糊匹配
    REGEX = "$regex"     # 正则表达式


class FilterValidator:
    """过滤器验证器
    
    验证过滤器定义的有效性。
    """
    
    SUPPORTED_OPERATORS = {op.value for op in FilterOperator}
    
    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> bool:
        """验证过滤器定义
        
        Args:
            filters: 过滤器字典
            
        Returns:
            是否有效
        """
        if not isinstance(filters, dict):
            return False
        
        for key, value in filters.items():
            if not isinstance(key, str):
                return False
            
            if isinstance(value, dict):
                # 检查操作符
                for op in value.keys():
                    if op not in FilterValidator.SUPPORTED_OPERATORS:
                        return False
        
        return True
    
    @staticmethod
    def get_operator(value: Any) -> Optional[FilterOperator]:
        """从过滤值中提取操作符
        
        Args:
            value: 过滤值
            
        Returns:
            操作符或 None
        """
        if not isinstance(value, dict):
            return None
        
        for op in FilterOperator:
            if op.value in value:
                return op
        
        return None


class FilterBuilder(ABC):
    """过滤器构建器基类
    
    子类应该针对特定的存储类型实现具体的过滤逻辑。
    """
    
    @abstractmethod
    def matches(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        pass
    
    @abstractmethod
    def validate_filters(self, filters: Dict[str, Any]) -> bool:
        """验证过滤器是否对该存储类型有效
        
        Args:
            filters: 过滤条件
            
        Returns:
            是否有效
        """
        pass
    
    def _check_condition(self, data_value: Any, filter_value: Any, operator: str) -> bool:
        """检查单个条件
        
        Args:
            data_value: 数据中的值
            filter_value: 过滤条件中的值
            operator: 操作符
            
        Returns:
            条件是否满足
        """
        if operator == FilterOperator.EQ.value:
            return data_value == filter_value
        elif operator == FilterOperator.NE.value:
            return data_value != filter_value
        elif operator == FilterOperator.IN.value:
            return data_value in filter_value
        elif operator == FilterOperator.NIN.value:
            return data_value not in filter_value
        elif operator == FilterOperator.GT.value:
            return data_value > filter_value
        elif operator == FilterOperator.GTE.value:
            return data_value >= filter_value
        elif operator == FilterOperator.LT.value:
            return data_value < filter_value
        elif operator == FilterOperator.LTE.value:
            return data_value <= filter_value
        elif operator == FilterOperator.LIKE.value:
            return isinstance(data_value, str) and filter_value.lower() in data_value.lower()
        elif operator == FilterOperator.REGEX.value:
            import re
            return isinstance(data_value, str) and bool(re.search(filter_value, data_value))
        else:
            return False


class MemoryFilterBuilder(FilterBuilder):
    """内存存储过滤器构建器
    
    为内存存储实现过滤逻辑。
    """
    
    def matches(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查内存中的数据是否匹配过滤器
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in data:
                return False
            
            if isinstance(value, dict):
                # 处理操作符
                match_found = False
                for op_key, op_value in value.items():
                    if self._check_condition(data[key], op_value, op_key):
                        match_found = True
                        break
                
                if not match_found and value:  # 如果有操作符但都不匹配
                    return False
            else:
                # 直接相等比较
                if data[key] != value:
                    return False
        
        return True
    
    def validate_filters(self, filters: Dict[str, Any]) -> bool:
        """验证过滤器
        
        Args:
            filters: 过滤条件
            
        Returns:
            是否有效
        """
        return FilterValidator.validate_filters(filters)


class SQLiteFilterBuilder(FilterBuilder):
    """SQLite 存储过滤器构建器
    
    为 SQLite 存储生成 SQL WHERE 子句。
    """
    
    def build_where_clause(self, filters: Dict[str, Any]) -> tuple[str, List[Any]]:
        """构建 WHERE 子句
        
        Args:
            filters: 过滤条件
            
        Returns:
            (WHERE子句, 参数列表) 元组
        """
        if not filters:
            return "", []
        
        conditions = []
        params: List[Any] = []
        
        for key, value in filters.items():
            if isinstance(value, (list, tuple)):
                # IN 查询
                placeholders = ",".join(["?" for _ in value])
                conditions.append(f"{key} IN ({placeholders})")
                params.extend(value)
            elif isinstance(value, dict):
                # 处理操作符
                for op_key, op_value in value.items():
                    if op_key == FilterOperator.GT.value:
                        conditions.append(f"{key} > ?")
                        params.append(op_value)
                    elif op_key == FilterOperator.GTE.value:
                        conditions.append(f"{key} >= ?")
                        params.append(op_value)
                    elif op_key == FilterOperator.LT.value:
                        conditions.append(f"{key} < ?")
                        params.append(op_value)
                    elif op_key == FilterOperator.LTE.value:
                        conditions.append(f"{key} <= ?")
                        params.append(op_value)
                    elif op_key == FilterOperator.NE.value:
                        conditions.append(f"{key} != ?")
                        params.append(op_value)
                    elif op_key == FilterOperator.EQ.value:
                        conditions.append(f"{key} = ?")
                        params.append(op_value)
                    elif op_key == FilterOperator.IN.value:
                        placeholders = ",".join(["?" for _ in op_value])
                        conditions.append(f"{key} IN ({placeholders})")
                        params.extend(op_value)
                    elif op_key == FilterOperator.NIN.value:
                        placeholders = ",".join(["?" for _ in op_value])
                        conditions.append(f"{key} NOT IN ({placeholders})")
                        params.extend(op_value)
                    elif op_key == FilterOperator.LIKE.value:
                        conditions.append(f"{key} LIKE ?")
                        params.append(f"%{op_value}%")
                    elif op_key == FilterOperator.REGEX.value:
                        # SQLite 需要使用 REGEXP，可能需要自定义函数
                        # 这里简化处理
                        conditions.append(f"{key} LIKE ?")
                        params.append(op_value)
            else:
                # 直接相等
                conditions.append(f"{key} = ?")
                params.append(value)
        
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            return where_clause, params
        
        return "", params
    
    def matches(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配（用于内存中的验证）
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        # 使用内存构建器的逻辑来验证
        builder = MemoryFilterBuilder()
        return builder.matches(data, filters)
    
    def validate_filters(self, filters: Dict[str, Any]) -> bool:
        """验证过滤器
        
        Args:
            filters: 过滤条件
            
        Returns:
            是否有效
        """
        return FilterValidator.validate_filters(filters)


class FileFilterBuilder(FilterBuilder):
    """文件存储过滤器构建器
    
    为文件存储实现过滤逻辑。
    """
    
    def matches(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查文件中的数据是否匹配过滤器
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        # 文件存储使用与内存相同的逻辑
        builder = MemoryFilterBuilder()
        return builder.matches(data, filters)
    
    def validate_filters(self, filters: Dict[str, Any]) -> bool:
        """验证过滤器
        
        Args:
            filters: 过滤条件
            
        Returns:
            是否有效
        """
        return FilterValidator.validate_filters(filters)
