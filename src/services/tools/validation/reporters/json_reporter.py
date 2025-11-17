"""
JSON报告生成器
生成机器可读的JSON格式报告
"""

import json
from typing import Dict
from .base_reporter import BaseReporter
from ..models import ValidationResult


class JSONReporter(BaseReporter):
    """JSON报告生成器"""
    
    def generate(self, all_results: Dict[str, Dict[str, ValidationResult]]) -> str:
        """生成JSON格式报告
        
        Args:
            all_results: 所有工具的验证结果
            
        Returns:
            str: JSON格式报告
        """
        report_data = {
            "summary": {
                "total_tools": len(all_results),
                "successful_tools": 0,
                "failed_tools": 0
            },
            "tools": {}
        }
        
        successful_count = 0
        
        for tool_name, results in all_results.items():
            tool_data = {
                "name": tool_name,
                "stages": {}
            }
            
            tool_successful = True
            for stage, result in results.items():
                stage_data = {
                    "status": result.status.value,
                    "issues": []
                }
                
                for issue in result.issues:
                    issue_data = {
                        "level": issue.level.value,
                        "message": issue.message,
                        "details": issue.details,
                        "suggestion": issue.suggestion
                    }
                    stage_data["issues"].append(issue_data)
                
                tool_data["stages"][stage] = stage_data
                
                if not result.is_successful():
                    tool_successful = False
            
            tool_data["successful"] = tool_successful
            report_data["tools"][tool_name] = tool_data
            
            if tool_successful:
                successful_count += 1
        
        report_data["summary"]["successful_tools"] = successful_count
        report_data["summary"]["failed_tools"] = len(all_results) - successful_count
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)