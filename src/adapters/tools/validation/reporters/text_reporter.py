"""
文本报告生成器
"""

from typing import Dict, Any
from src.interfaces.tool.reporter import IValidationReporter
from src.core.tools.validation.models import ValidationResult, ValidationStatus


class TextReporter(IValidationReporter):
    """文本报告生成器"""
    
    def __init__(self):
        """初始化文本报告生成器"""
        pass
    
    def generate(self, results: Dict[str, Any]) -> str:
        """生成文本格式报告
        
        Args:
            results: 验证结果字典，键为工具名称，值为ValidationResult
            
        Returns:
            str: 生成的文本报告
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("工具验证报告")
        report_lines.append("=" * 60)
        
        total_tools = len(results)
        successful_tools = 0
        failed_tools = 0
        total_errors = 0
        total_warnings = 0
        
        # 按工具名称排序
        sorted_tools = sorted(results.keys())
        
        for tool_name in sorted_tools:
            result = results[tool_name]
            
            report_lines.append(f"\n工具: {tool_name}")
            report_lines.append("-" * 40)
            
            # 显示工具类型和状态
            status_icon = "✓" if result.is_successful() else "✗"
            report_lines.append(f"  类型: {result.tool_type}")
            report_lines.append(f"  状态: {status_icon} {result.status.value.upper()}")
            
            # 显示问题详情
            if result.issues:
                report_lines.append("  问题:")
                for i, issue in enumerate(result.issues, 1):
                    level_str = issue.level.value.upper()
                    level_icon = "🔴" if issue.level == ValidationStatus.ERROR else "🟡"
                    
                    report_lines.append(f"    {i}. {level_icon} [{level_str}] {issue.message}")
                    
                    # 显示详细信息
                    if issue.details:
                        for key, value in issue.details.items():
                            report_lines.append(f"       {key}: {value}")
                    
                    # 显示建议
                    if issue.suggestion:
                        report_lines.append(f"       💡 建议: {issue.suggestion}")
                
                # 统计
                error_count = result.get_error_count()
                warning_count = result.get_warning_count()
                total_errors += error_count
                total_warnings += warning_count
                
                report_lines.append(f"  统计: {error_count} 错误, {warning_count} 警告")
            else:
                report_lines.append("  ✅ 没有问题")
            
            if result.is_successful():
                successful_tools += 1
            else:
                failed_tools += 1
        
        # 生成总结
        report_lines.append("\n" + "=" * 60)
        report_lines.append("验证总结")
        report_lines.append("=" * 60)
        report_lines.append(f"总工具数: {total_tools}")
        report_lines.append(f"通过验证: {successful_tools} ({successful_tools/total_tools*100:.1f}%)")
        report_lines.append(f"验证失败: {failed_tools} ({failed_tools/total_tools*100:.1f}%)")
        report_lines.append(f"总错误数: {total_errors}")
        report_lines.append(f"总警告数: {total_warnings}")
        
        # 添加状态图标说明
        report_lines.append("\n图标说明:")
        report_lines.append("  ✓ - 验证通过")
        report_lines.append("  ✗ - 验证失败")
        report_lines.append("  🔴 - 错误")
        report_lines.append("  🟡 - 警告")
        report_lines.append("  💡 - 建议")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def get_format(self) -> str:
        """获取报告格式
        
        Returns:
            str: 报告格式名称
        """
        return "text"
    
    def generate_summary(self, results: Dict[str, Any]) -> str:
        """生成简短摘要
        
        Args:
            results: 验证结果
            
        Returns:
            str: 摘要文本
        """
        total_tools = len(results)
        successful_tools = sum(1 for r in results.values() if r.is_successful())
        failed_tools = total_tools - successful_tools
        total_errors = sum(r.get_error_count() for r in results.values())
        total_warnings = sum(r.get_warning_count() for r in results.values())
        
        summary = f"验证完成: {successful_tools}/{total_tools} 通过"
        
        if failed_tools > 0:
            summary += f", {failed_tools} 失败"
        
        if total_errors > 0:
            summary += f", {total_errors} 错误"
        
        if total_warnings > 0:
            summary += f", {total_warnings} 警告"
        
        return summary


# 导出文本报告器
__all__ = [
    "TextReporter",
]