"""数据映射器实现

负责工作流间的数据传递、输入输出映射配置、数据转换和验证。
"""

from typing import Dict, Any, List, Optional, Union
import re
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.composition import IDataMapper
from src.infrastructure.validation.result import ValidationResult

logger = get_logger(__name__)


class DataMapper(IDataMapper):
    """数据映射器实现"""
    
    def __init__(self):
        """初始化数据映射器"""
        self._logger = get_logger(f"{__name__}.DataMapper")
        self._mapping_cache: Dict[str, Any] = {}
    
    def map_input_data(self, source_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """映射输入数据
        
        Args:
            source_data: 源数据
            mapping_config: 映射配置
            
        Returns:
            Dict[str, Any]: 映射后的数据
            
        Raises:
            ValueError: 映射配置无效
            RuntimeError: 映射失败
        """
        try:
            self._logger.debug(f"开始输入数据映射，源数据键: {list(source_data.keys())}")
            
            if not mapping_config:
                self._logger.debug("映射配置为空，返回源数据")
                return source_data
            
            mapped_data = {}
            
            for target_key, mapping_rule in mapping_config.items():
                try:
                    mapped_value = self._apply_mapping_rule(source_data, mapping_rule)
                    mapped_data[target_key] = mapped_value
                    self._logger.debug(f"映射成功: {mapping_rule} -> {target_key}")
                    
                except Exception as e:
                    self._logger.warning(f"映射规则失败 {mapping_rule}: {e}")
                    # 可以选择跳过失败的映射或抛出异常
                    continue
            
            self._logger.debug(f"输入数据映射完成，结果键: {list(mapped_data.keys())}")
            return mapped_data
            
        except Exception as e:
            self._logger.error(f"输入数据映射失败: {e}")
            raise RuntimeError(f"输入数据映射失败: {e}") from e
    
    def map_output_data(self, source_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """映射输出数据
        
        Args:
            source_data: 源数据
            mapping_config: 映射配置
            
        Returns:
            Dict[str, Any]: 映射后的数据
        """
        try:
            self._logger.debug(f"开始输出数据映射，源数据键: {list(source_data.keys())}")
            
            # 输出映射与输入映射逻辑相同，可以复用
            return self.map_input_data(source_data, mapping_config)
            
        except Exception as e:
            self._logger.error(f"输出数据映射失败: {e}")
            raise RuntimeError(f"输出数据映射失败: {e}") from e
    
    def validate_mapping_config(self, mapping_config: Dict[str, Any]) -> ValidationResult:
        """验证映射配置
        
        Args:
            mapping_config: 映射配置
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        
        try:
            if not isinstance(mapping_config, dict):
                errors.append("映射配置必须是字典类型")
                return ValidationResult(is_valid=False, errors=errors, warnings=[])
            
            if not mapping_config:
                # 空配置是有效的
                return ValidationResult(is_valid=True, errors=errors, warnings=[])
            
            for target_key, mapping_rule in mapping_config.items():
                # 验证目标键
                if not isinstance(target_key, str):
                    errors.append(f"目标键必须是字符串: {target_key}")
                    continue
                
                if not target_key.strip():
                    errors.append("目标键不能为空字符串")
                    continue
                
                # 验证映射规则
                rule_errors = self._validate_mapping_rule(mapping_rule)
                errors.extend([f"目标键 '{target_key}': {err}" for err in rule_errors])
            
            return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])
            
        except Exception as e:
            self._logger.error(f"验证映射配置时发生错误: {e}")
            errors.append(f"验证过程发生错误: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors, warnings=[])
    
    def _apply_mapping_rule(self, source_data: Dict[str, Any], mapping_rule: Any) -> Any:
        """应用映射规则
        
        Args:
            source_data: 源数据
            mapping_rule: 映射规则
            
        Returns:
            Any: 映射后的值
        """
        # 简单值映射
        if isinstance(mapping_rule, str):
            return self._apply_string_mapping(source_data, mapping_rule)
        
        # 字典映射（复杂规则）
        elif isinstance(mapping_rule, dict):
            return self._apply_dict_mapping(source_data, mapping_rule)
        
        # 直接值
        else:
            return mapping_rule
    
    def _apply_string_mapping(self, source_data: Dict[str, Any], mapping_rule: str) -> Any:
        """应用字符串映射规则
        
        Args:
            source_data: 源数据
            mapping_rule: 字符串映射规则
            
        Returns:
            Any: 映射后的值
        """
        # 支持点号分隔的路径访问，如 "user.name"
        if '.' in mapping_rule:
            return self._get_nested_value(source_data, mapping_rule)
        
        # 简单的键值映射
        if mapping_rule in source_data:
            return source_data[mapping_rule]
        
        # 支持默认值语法，如 "key:default_value"
        if ':' in mapping_rule:
            key, default_value = mapping_rule.split(':', 1)
            if key in source_data:
                return source_data[key]
            else:
                # 尝试转换默认值类型
                return self._convert_value(default_value)
        
        # 如果键不存在，返回None
        self._logger.warning(f"映射键 '{mapping_rule}' 不存在于源数据中")
        return None
    
    def _apply_dict_mapping(self, source_data: Dict[str, Any], mapping_rule: Dict[str, Any]) -> Any:
        """应用字典映射规则
        
        Args:
            source_data: 源数据
            mapping_rule: 字典映射规则
            
        Returns:
            Any: 映射后的值
        """
        rule_type = mapping_rule.get('type', 'direct')
        
        if rule_type == 'direct':
            # 直接映射
            source_key = mapping_rule.get('source')
            if source_key:
                return self._apply_string_mapping(source_data, source_key)
        
        elif rule_type == 'template':
            # 模板映射
            template = mapping_rule.get('template', '')
            variables = mapping_rule.get('variables', {})
            
            # 替换模板变量
            for var_key, var_path in variables.items():
                var_value = self._get_nested_value(source_data, var_path)
                template = template.replace(f"{{{var_key}}}", str(var_value))
            
            return template
        
        elif rule_type == 'function':
            # 函数映射（简单的内置函数）
            func_name = mapping_rule.get('function')
            source_key = mapping_rule.get('source')
            
            if func_name and source_key:
                source_value = self._apply_string_mapping(source_data, source_key)
                return self._apply_function(func_name, source_value)
        
        elif rule_type == 'conditional':
            # 条件映射
            conditions = mapping_rule.get('conditions', [])
            default_value = mapping_rule.get('default')
            
            for condition in conditions:
                if self._evaluate_condition(source_data, condition):
                    return condition.get('value')
            
            return default_value
        
        # 不支持的规则类型
        self._logger.warning(f"不支持的映射规则类型: {rule_type}")
        return None
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套值
        
        Args:
            data: 数据字典
            path: 点号分隔的路径
            
        Returns:
            Any: 嵌套值
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _convert_value(self, value: str) -> Any:
        """转换字符串值为合适的类型
        
        Args:
            value: 字符串值
            
        Returns:
            Any: 转换后的值
        """
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 字符串（默认）
        return value
    
    def _apply_function(self, func_name: str, value: Any) -> Any:
        """应用函数
        
        Args:
            func_name: 函数名称
            value: 输入值
            
        Returns:
            Any: 函数结果
        """
        # 内置简单函数
        if func_name == 'upper':
            return str(value).upper() if value is not None else None
        elif func_name == 'lower':
            return str(value).lower() if value is not None else None
        elif func_name == 'strip':
            return str(value).strip() if value is not None else None
        elif func_name == 'length':
            return len(value) if value is not None else 0
        elif func_name == 'abs':
            return abs(value) if isinstance(value, (int, float)) else None
        
        # 不支持的函数
        self._logger.warning(f"不支持的函数: {func_name}")
        return value
    
    def _evaluate_condition(self, source_data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            source_data: 源数据
            condition: 条件配置
            
        Returns:
            bool: 条件结果
        """
        field = condition.get('field')
        operator = condition.get('operator', 'equals')
        expected_value = condition.get('value')
        
        if not field:
            return False
        
        actual_value = self._get_nested_value(source_data, field)
        
        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'not_equals':
            return actual_value != expected_value
        elif operator == 'exists':
            return actual_value is not None
        elif operator == 'not_exists':
            return actual_value is None
        elif operator == 'greater_than':
            return actual_value is not None and actual_value > expected_value
        elif operator == 'less_than':
            return actual_value is not None and actual_value < expected_value
        
        # 不支持的操作符
        self._logger.warning(f"不支持的条件操作符: {operator}")
        return False
    
    def _validate_mapping_rule(self, mapping_rule: Any) -> List[str]:
        """验证映射规则
        
        Args:
            mapping_rule: 映射规则
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        # 简单字符串规则
        if isinstance(mapping_rule, str):
            if not mapping_rule.strip():
                errors.append("映射规则字符串不能为空")
            return errors
        
        # 字典规则
        elif isinstance(mapping_rule, dict):
            rule_type = mapping_rule.get('type', 'direct')
            
            if rule_type == 'direct':
                source = mapping_rule.get('source')
                if not source or not isinstance(source, str):
                    errors.append("直接映射规则必须包含有效的source字段")
            
            elif rule_type == 'template':
                template = mapping_rule.get('template')
                variables = mapping_rule.get('variables', {})
                
                if not template or not isinstance(template, str):
                    errors.append("模板映射规则必须包含有效的template字段")
                
                if not isinstance(variables, dict):
                    errors.append("模板映射规则的variables必须是字典类型")
            
            elif rule_type == 'function':
                func_name = mapping_rule.get('function')
                source = mapping_rule.get('source')
                
                if not func_name or not isinstance(func_name, str):
                    errors.append("函数映射规则必须包含有效的function字段")
                
                if not source or not isinstance(source, str):
                    errors.append("函数映射规则必须包含有效的source字段")
                
                # 验证函数名称
                supported_functions = ['upper', 'lower', 'strip', 'length', 'abs']
                if func_name not in supported_functions:
                    errors.append(f"不支持的函数: {func_name}")
            
            elif rule_type == 'conditional':
                conditions = mapping_rule.get('conditions', [])
                
                if not isinstance(conditions, list):
                    errors.append("条件映射规则的conditions必须是列表类型")
                else:
                    for i, condition in enumerate(conditions):
                        if not isinstance(condition, dict):
                            errors.append(f"条件[{i}]必须是字典类型")
                            continue
                        
                        if 'field' not in condition:
                            errors.append(f"条件[{i}]必须包含field字段")
                        
                        if 'value' not in condition and condition.get('operator') in ['equals', 'not_equals', 'greater_than', 'less_than']:
                            errors.append(f"条件[{i}]必须包含value字段")
            
            else:
                errors.append(f"不支持的映射规则类型: {rule_type}")
        
        else:
            errors.append("映射规则必须是字符串或字典类型")
        
        return errors
    
    def clear_cache(self) -> None:
        """清除映射缓存"""
        self._mapping_cache.clear()
        self._logger.info("数据映射缓存已清除")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return {
            'cache_size': len(self._mapping_cache),
            'cache_keys': list(self._mapping_cache.keys()),
        }


# 便捷函数
def create_data_mapper() -> DataMapper:
    """创建数据映射器实例
    
    Returns:
        DataMapper: 数据映射器实例
    """
    return DataMapper()


# 导出实现
__all__ = [
    "DataMapper",
    "create_data_mapper",
]