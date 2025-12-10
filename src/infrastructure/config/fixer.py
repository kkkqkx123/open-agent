"""配置修复模块

提供通用的配置修复建议和自动修复功能。
"""

from typing import Dict, Any, List, Callable, Type


class FixSuggestion:
    """修复建议"""
    
    def __init__(self, description: str, fix_action: Callable, confidence: float = 0.8):
        self.description = description
        self.fix_action = fix_action
        self.confidence = confidence
    
    def apply(self) -> None:
        """应用修复建议"""
        if self.fix_action:
            self.fix_action()


class ConfigFixer:
    """配置修复器"""
    
    def __init__(self):
        self.fix_strategies = {}
        self._register_fix_strategies()
    
    def suggest_fixes(self, config: Dict[str, Any], field_issues: List[Dict[str, Any]]) -> List[FixSuggestion]:
        """提供修复建议
        
        Args:
            config: 配置数据
            field_issues: 字段问题列表，格式为[{'field': '字段名', 'type': '问题类型', 'value': '当前值'}]
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        for issue in field_issues:
            field = issue['field']
            issue_type = issue['type']
            
            if issue_type == 'missing_field':
                default_value = issue.get('default_value')
                description = f"添加缺失字段 '{field}'"
                fix_action = lambda f=field, v=default_value: self._fix_missing_field(config, f, v)
                suggestions.append(FixSuggestion(description, fix_action))
            
            elif issue_type == 'invalid_type':
                expected_type = issue.get('expected_type', str)
                description = f"修复字段 '{field}' 的类型错误"
                fix_action = lambda f=field, t=expected_type: self._fix_invalid_type(config, f, t)
                suggestions.append(FixSuggestion(description, fix_action))
            
            elif issue_type == 'invalid_value':
                valid_values = issue.get('valid_values', [])
                description = f"修复字段 '{field}' 的无效值"
                fix_action = lambda f=field, v=valid_values: self._fix_invalid_value(config, f, v)
                suggestions.append(FixSuggestion(description, fix_action))
        
        return suggestions
    
    def _register_fix_strategies(self) -> None:
        """注册修复策略"""
        self.fix_strategies = {
            "missing_field": self._fix_missing_field,
            "invalid_type": self._fix_invalid_type,
            "invalid_value": self._fix_invalid_value
        }
    
    def _fix_missing_field(self, config: Dict[str, Any], field: str, default_value: Any) -> None:
        """修复缺失字段"""
        if field not in config:
            config[field] = default_value
    
    def _fix_invalid_type(self, config: Dict[str, Any], field: str, expected_type: Type) -> None:
        """修复类型错误"""
        if field in config and not isinstance(config[field], expected_type):
            # 尝试类型转换或使用默认值
            try:
                config[field] = expected_type(config[field])
            except (ValueError, TypeError):
                config[field] = self._get_default_value(expected_type)
    
    def _fix_invalid_value(self, config: Dict[str, Any], field: str, valid_values: List[Any]) -> None:
        """修复无效值"""
        if field in config and config[field] not in valid_values:
            # 使用第一个有效值作为默认值
            config[field] = valid_values[0] if valid_values else None
    
    def _get_default_value(self, expected_type: Type) -> Any:
        """获取默认值"""
        if expected_type == str:
            return ""
        elif expected_type == int:
            return 0
        elif expected_type == float:
            return 0.0
        elif expected_type == bool:
            return False
        elif expected_type == list:
            return []
        elif expected_type == dict:
            return {}
        else:
            return None