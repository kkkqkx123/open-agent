"""
JSON报告生成器
"""

import json
from typing import Dict, Any
from src.interfaces.tool.reporter import IValidationReporter
from src.core.tools.validation.models import ValidationResult


class JsonReporter(IValidationReporter):
    """JSON报告生成器"""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """初始化JSON报告生成器
        
        Args:
            indent: JSON缩进空格数
            ensure_ascii: 是否确保ASCII编码
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
    
    def generate(self, results: Dict[str, Any]) -> str:
        """生成JSON格式报告
        
        Args:
            results: 验证结果字典，键为工具名称，值为ValidationResult
            
        Returns:
            str: 生成的JSON报告
        """
        report_data: Dict[str, Any] = {
            "summary": self._generate_summary(results),
            "tools": self._generate_tools_section(results),
            "metadata": {
                "generated_at": self._get_current_timestamp(),
                "format": "json",
                "version": "1.0"
            }
        }
        
        return json.dumps(
            report_data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            default=self._json_serializer
        )
    
    def get_format(self) -> str:
        """获取报告格式
        
        Returns:
            str: 报告格式名称
        """
        return "json"
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要部分"""
        total_tools = len(results)
        successful_tools = sum(1 for r in results.values() if r.is_successful())
        failed_tools = total_tools - successful_tools
        total_errors = sum(r.get_error_count() for r in results.values())
        total_warnings = sum(r.get_warning_count() for r in results.values())
        
        # 按工具类型统计
        tool_type_stats: Dict[str, Dict[str, int]] = {}
        for result in results.values():
            tool_type = result.tool_type
            if tool_type not in tool_type_stats:
                tool_type_stats[tool_type] = {"total": 0, "successful": 0, "failed": 0}
            
            tool_type_stats[tool_type]["total"] += 1
            if result.is_successful():
                tool_type_stats[tool_type]["successful"] += 1
            else:
                tool_type_stats[tool_type]["failed"] += 1
        
        return {
            "total_tools": total_tools,
            "successful_tools": successful_tools,
            "failed_tools": failed_tools,
            "success_rate": successful_tools / total_tools * 100 if total_tools > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "tool_type_distribution": tool_type_stats
        }
    
    def _generate_tools_section(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成工具详情部分"""
        tools_data = {}
        
        for tool_name, result in results.items():
            tools_data[tool_name] = {
                "name": tool_name,
                "type": result.tool_type,
                "status": result.status.value,
                "successful": result.is_successful(),
                "error_count": result.get_error_count(),
                "warning_count": result.get_warning_count(),
                "issues": [
                    {
                        "level": issue.level.value,
                        "message": issue.message,
                        "details": issue.details,
                        "suggestion": issue.suggestion,
                        "timestamp": issue.timestamp.isoformat()
                    }
                    for issue in result.issues
                ],
                "metadata": result.metadata,
                "timestamp": result.timestamp.isoformat()
            }
        
        return tools_data
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _json_serializer(self, obj):
        """JSON序列化器，处理特殊类型"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def generate_compact(self, results: Dict[str, Any]) -> str:
        """生成紧凑格式的JSON报告
        
        Args:
            results: 验证结果
            
        Returns:
            str: 紧凑格式的JSON报告
        """
        # 只包含关键信息
        compact_data = {
            "summary": self._generate_summary(results),
            "failed_tools": {
                name: {
                    "status": result.status.value,
                    "error_count": result.get_error_count(),
                    "warning_count": result.get_warning_count(),
                    "main_issues": [
                        {
                            "level": issue.level.value,
                            "message": issue.message,
                            "suggestion": issue.suggestion
                        }
                        for issue in result.issues[:3]  # 只显示前3个问题
                    ]
                }
                for name, result in results.items()
                if not result.is_successful()
            }
        }
        
        return json.dumps(
            compact_data,
            indent=None,  # 紧凑格式
            ensure_ascii=self.ensure_ascii,
            separators=(',', ':'),  # 去除多余空格
            default=self._json_serializer
        )


# 导出JSON报告器
__all__ = [
    "JsonReporter",
]