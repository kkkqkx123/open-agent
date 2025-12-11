"""配置验证辅助器实现

提供配置系统的验证辅助功能，包括结构验证、类型验证、值验证等。
"""

from typing import Dict, Any, List, Optional, Union
import logging
import re
from datetime import datetime

from src.infrastructure.validation.result import ValidationResult

logger = logging.getLogger(__name__)


class ValidationHelper:
    """配置验证辅助器
    
    提供配置系统的验证辅助功能，包括结构验证、类型验证、值验证等。
    """
    
    def __init__(self):
        """初始化验证辅助器"""
        logger.debug("初始化配置验证辅助器")
    
    def validate_structure(self, config: Dict[str, Any], required_keys: List[str]) -> ValidationResult:
        """验证配置结构
        
        Args:
            config: 配置数据
            required_keys: 必需的键列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        try:
            # 检查必需的键
            for key in required_keys:
                if key not in config:
                    errors.append(f"缺少必需的配置键: {key}")
            
            # 检查空值
            for key, value in config.items():
                if value is None:
                    warnings.append(f"配置键 {key} 的值为空")
            
            # 检查嵌套结构
            self._check_nested_structure(config, "", errors, warnings)
            
            is_valid = len(errors) == 0
            logger.debug(f"结构验证完成，有效: {is_valid}，错误: {len(errors)}，警告: {len(warnings)}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"结构验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"结构验证异常: {str(e)}"],
                warnings=[]
            )
    
    def validate_types(self, config: Dict[str, Any], type_schema: Dict[str, type]) -> ValidationResult:
        """验证配置类型
        
        Args:
            config: 配置数据
            type_schema: 类型模式
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        try:
            for key, expected_type in type_schema.items():
                if key not in config:
                    continue  # 跳过不存在的键
                
                value = config[key]
                
                # 检查类型
                if not isinstance(value, expected_type):
                    errors.append(
                        f"配置键 {key} 类型错误: 期望 {expected_type.__name__}，"
                        f"实际 {type(value).__name__}"
                    )
                
                # 特殊类型检查
                if expected_type == str and isinstance(value, str):
                    if not value.strip():
                        warnings.append(f"配置键 {key} 为空字符串")
                elif expected_type == list and isinstance(value, list):
                    if not value:
                        warnings.append(f"配置键 {key} 为空列表")
                elif expected_type == dict and isinstance(value, dict):
                    if not value:
                        warnings.append(f"配置键 {key} 为空字典")
            
            is_valid = len(errors) == 0
            logger.debug(f"类型验证完成，有效: {is_valid}，错误: {len(errors)}，警告: {len(warnings)}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"类型验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"类型验证异常: {str(e)}"],
                warnings=[]
            )
    
    def validate_values(self, config: Dict[str, Any], value_constraints: Dict[str, Any]) -> ValidationResult:
        """验证配置值
        
        Args:
            config: 配置数据
            value_constraints: 值约束
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        try:
            for key, constraints in value_constraints.items():
                if key not in config:
                    continue  # 跳过不存在的键
                
                value = config[key]
                
                # 检查枚举值
                if "enum" in constraints:
                    valid_values = constraints["enum"]
                    if value not in valid_values:
                        errors.append(
                            f"配置键 {key} 的值无效: {value}，"
                            f"有效值: {valid_values}"
                        )
                
                # 检查范围
                if "min" in constraints and value < constraints["min"]:
                    errors.append(
                        f"配置键 {key} 的值过小: {value}，最小值: {constraints['min']}"
                    )
                
                if "max" in constraints and value > constraints["max"]:
                    errors.append(
                        f"配置键 {key} 的值过大: {value}，最大值: {constraints['max']}"
                    )
                
                # 检查长度
                if "min_length" in constraints and len(value) < constraints["min_length"]:
                    errors.append(
                        f"配置键 {key} 的长度过短: {len(value)}，"
                        f"最小长度: {constraints['min_length']}"
                    )
                
                if "max_length" in constraints and len(value) > constraints["max_length"]:
                    errors.append(
                        f"配置键 {key} 的长度过长: {len(value)}，"
                        f"最大长度: {constraints['max_length']}"
                    )
                
                # 检查正则表达式
                if "pattern" in constraints:
                    pattern = constraints["pattern"]
                    if not re.match(pattern, str(value)):
                        errors.append(
                            f"配置键 {key} 的值不匹配模式 {pattern}: {value}"
                        )
                
                # 检查自定义验证函数
                if "validator" in constraints:
                    validator = constraints["validator"]
                    try:
                        if callable(validator):
                            result = validator(value)
                            if not result:
                                errors.append(f"配置键 {key} 的值未通过自定义验证: {value}")
                    except Exception as e:
                        warnings.append(f"配置键 {key} 的自定义验证失败: {e}")
            
            is_valid = len(errors) == 0
            logger.debug(f"值验证完成，有效: {is_valid}，错误: {len(errors)}，警告: {len(warnings)}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"值验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"值验证异常: {str(e)}"],
                warnings=[]
            )
    
    def validate_dependencies(self, config: Dict[str, Any], dependency_rules: Dict[str, Any]) -> ValidationResult:
        """验证配置依赖
        
        Args:
            config: 配置数据
            dependency_rules: 依赖规则
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        try:
            for key, rules in dependency_rules.items():
                if key not in config:
                    continue  # 跳过不存在的键
                
                value = config[key]
                
                # 检查必需的依赖键
                if "requires" in rules:
                    required_deps = rules["requires"]
                    if isinstance(required_deps, str):
                        required_deps = [required_deps]
                    
                    for dep_key in required_deps:
                        if dep_key not in config:
                            errors.append(
                                f"配置键 {key} 依赖的键 {dep_key} 不存在"
                            )
                
                # 检查互斥键
                if "conflicts" in rules:
                    conflicting_keys = rules["conflicts"]
                    if isinstance(conflicting_keys, str):
                        conflicting_keys = [conflicting_keys]
                    
                    for conflict_key in conflicting_keys:
                        if conflict_key in config:
                            errors.append(
                                f"配置键 {key} 与键 {conflict_key} 冲突，不能同时存在"
                            )
                
                # 检查条件依赖
                if "if" in rules:
                    condition = rules["if"]
                    then_requires = rules.get("then_requires", [])
                    
                    # 简单的条件检查
                    if self._evaluate_condition(value, condition):
                        for req_key in then_requires:
                            if req_key not in config:
                                errors.append(
                                    f"配置键 {key} 满足条件时需要键 {req_key}"
                                )
            
            is_valid = len(errors) == 0
            logger.debug(f"依赖验证完成，有效: {is_valid}，错误: {len(errors)}，警告: {len(warnings)}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"依赖验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"依赖验证异常: {str(e)}"],
                warnings=[]
            )
    
    def validate_with_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """使用JSON Schema验证配置
        
        Args:
            config: 配置数据
            schema: JSON Schema
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        try:
            # 简化的JSON Schema验证
            # 实际项目中应该使用jsonschema库
            
            # 检查类型
            if "type" in schema:
                expected_type = schema["type"]
                if expected_type == "object" and not isinstance(config, dict):
                    errors.append(f"配置必须是对象类型")
                elif expected_type == "array" and not isinstance(config, list):
                    errors.append(f"配置必须是数组类型")
            
            # 检查属性
            if isinstance(config, dict) and "properties" in schema:
                properties = schema["properties"]
                required = schema.get("required", [])
                
                # 检查必需属性
                for prop in required:
                    if prop not in config:
                        errors.append(f"缺少必需属性: {prop}")
                
                # 检查每个属性
                for prop, prop_schema in properties.items():
                    if prop in config:
                        prop_result = self.validate_with_schema(config[prop], prop_schema)
                        errors.extend(prop_result.errors)
                        warnings.extend(prop_result.warnings)
            
            # 检查数组项
            if isinstance(config, list) and "items" in schema:
                items_schema = schema["items"]
                for i, item in enumerate(config):
                    item_result = self.validate_with_schema(item, items_schema)
                    if item_result.errors:
                        for error in item_result.errors:
                            errors.append(f"数组项[{i}]: {error}")
                    warnings.extend(item_result.warnings)
            
            is_valid = len(errors) == 0
            logger.debug(f"Schema验证完成，有效: {is_valid}，错误: {len(errors)}，警告: {len(warnings)}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Schema验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema验证异常: {str(e)}"],
                warnings=[]
            )
    
    def normalize_config(self, config: Dict[str, Any], normalization_rules: Dict[str, Any]) -> Dict[str, Any]:
        """规范化配置
        
        Args:
            config: 原始配置数据
            normalization_rules: 规范化规则
            
        Returns:
            规范化后的配置数据
        """
        try:
            normalized = config.copy()
            
            for key, rules in normalization_rules.items():
                if key not in normalized:
                    continue
                
                value = normalized[key]
                
                # 类型转换
                if "type" in rules:
                    target_type = rules["type"]
                    try:
                        if target_type == int and isinstance(value, str):
                            normalized[key] = int(value)
                        elif target_type == float and isinstance(value, str):
                            normalized[key] = float(value)
                        elif target_type == bool and isinstance(value, str):
                            normalized[key] = value.lower() in ('true', '1', 'yes', 'on')
                        elif target_type == str and not isinstance(value, str):
                            normalized[key] = str(value)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"类型转换失败 {key}: {e}")
                
                # 默认值
                if "default" in rules and normalized[key] is None:
                    normalized[key] = rules["default"]
                
                # 枚举映射
                if "mapping" in rules:
                    mapping = rules["mapping"]
                    if value in mapping:
                        normalized[key] = mapping[value]
                
                # 字符串处理
                if isinstance(normalized[key], str):
                    # 去除空白
                    if "strip" in rules and rules["strip"]:
                        normalized[key] = normalized[key].strip()
                    
                    # 大小写转换
                    if "case" in rules:
                        case = rules["case"]
                        if case == "lower":
                            normalized[key] = normalized[key].lower()
                        elif case == "upper":
                            normalized[key] = normalized[key].upper()
                        elif case == "title":
                            normalized[key] = normalized[key].title()
            
            logger.debug("配置规范化完成")
            return normalized
            
        except Exception as e:
            logger.error(f"配置规范化失败: {e}")
            return config
    
    def merge_validation_results(self, results: List[ValidationResult]) -> ValidationResult:
        """合并多个验证结果
        
        Args:
            results: 验证结果列表
            
        Returns:
            合并后的验证结果
        """
        all_errors = []
        all_warnings = []
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        is_valid = len(all_errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def create_validation_context(self, config_path: str, module_type: str) -> Dict[str, Any]:
        """创建验证上下文
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型
            
        Returns:
            验证上下文
        """
        return {
            "config_path": config_path,
            "module_type": module_type,
            "timestamp": datetime.now().isoformat(),
            "validator": "ValidationHelper"
        }
    
    def format_validation_error(self, error: str, context: Dict[str, Any]) -> str:
        """格式化验证错误信息
        
        Args:
            error: 错误信息
            context: 验证上下文
            
        Returns:
            格式化后的错误信息
        """
        config_path = context.get("config_path", "unknown")
        module_type = context.get("module_type", "unknown")
        
        return f"[{module_type}] {config_path}: {error}"
    
    def _check_nested_structure(self, obj: Any, path: str, errors: List[str], warnings: List[str]) -> None:
        """检查嵌套结构"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # 检查键名
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    warnings.append(f"配置键名不符合规范: {current_path}")
                
                # 递归检查
                self._check_nested_structure(value, current_path, errors, warnings)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                self._check_nested_structure(item, current_path, errors, warnings)
    
    def _evaluate_condition(self, value: Any, condition: Any) -> bool:
        """评估条件"""
        if isinstance(condition, dict):
            if "equals" in condition:
                return value == condition["equals"]
            elif "not_equals" in condition:
                return value != condition["not_equals"]
            elif "in" in condition:
                return value in condition["in"]
            elif "not_in" in condition:
                return value not in condition["not_in"]
            elif "gt" in condition:
                return value > condition["gt"]
            elif "lt" in condition:
                return value < condition["lt"]
            elif "gte" in condition:
                return value >= condition["gte"]
            elif "lte" in condition:
                return value <= condition["lte"]
        
        # 简单相等比较
        return value == condition