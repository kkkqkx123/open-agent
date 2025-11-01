"""
文本报告生成器
生成人类可读的文本格式报告
"""

from typing import Dict
from .base_reporter import BaseReporter
from ..models import ValidationResult


class TextReporter(BaseReporter):
    """文本报告生成器"""
    
    def generate(self, all_results: Dict[str, Dict[str, ValidationResult]]) -> str:
        """生成文本格式报告
        
        Args:
            all_results: 所有工具的验证结果
            
        Returns:
            str: 文本格式报告
        """
        report_lines = []
        report_lines.append("=" * 50)
        report_lines.append("工具检验报告")
        report_lines.append("=" * 50)
        
        total_tools = len(all_results)
        successful_tools = 0
        
        for tool_name, tool_results in all_results.items():
            report_lines.append(f"\n工具: {tool_name}")
            report_lines.append("-" * 30)
            
            tool_successful = True
            for stage, result in tool_results.items():
                status_icon = "✓" if result.is_successful() else "✗"
                report_lines.append(f"  {stage}: {status_icon}")
                
                if not result.is_successful():
                    tool_successful = False
                    for issue in result.issues:
                        level_str = issue.level.value.upper()
                        report_lines.append(f"    [{level_str}] {issue.message}")
                        if issue.suggestion:
                            report_lines.append(f"      建议: {issue.suggestion}")
            
            if tool_successful:
                successful_tools += 1
        
        report_lines.append("\n" + "=" * 50)
        report_lines.append(f"总结: {successful_tools}/{total_tools} 个工具验证通过")
        report_lines.append("=" * 50)
        
        return "\n".join(report_lines)