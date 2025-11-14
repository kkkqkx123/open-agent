"""
工具检验管理器
协调各种验证器进行工具检验
"""

from typing import List, Dict, Any, Optional, Mapping
from pathlib import Path
import os

from infrastructure.config.config_loader import IConfigLoader
from src.infrastructure.logger.logger import ILogger
from src.infrastructure.tools.manager import ToolManager
from src.infrastructure.tools.interfaces import IToolManager

from .interfaces import IToolValidator
from .models import ValidationResult
from .validators.config_validator import ConfigValidator
from .validators.loading_validator import LoadingValidator
from .validators.builtin_validator import BuiltinToolValidator
from .validators.native_validator import NativeToolValidator
from .validators.mcp_validator import MCPToolValidator


class ToolValidationManager:
    """工具检验管理器"""
    
    def __init__(
        self,
        config_loader: IConfigLoader,
        logger: ILogger,
        tool_manager: Optional[IToolManager] = None
    ):
        """初始化工具检验管理器
        
        Args:
            config_loader: 配置加载器
            logger: 日志记录器
            tool_manager: 工具管理器（可选）
        """
        self.config_loader = config_loader
        self.logger = logger
        self.tool_manager: Optional[IToolManager] = tool_manager
        self.validators: Dict[str, IToolValidator] = {}
        self._register_validators()
    
    def _register_validators(self) -> None:
        """注册验证器"""
        self.validators["config"] = ConfigValidator(self.config_loader, self.logger)
        if self.tool_manager:
            self.validators["loading"] = LoadingValidator(self.tool_manager, self.logger)
        self.validators["builtin"] = BuiltinToolValidator(self.logger)
        self.validators["native"] = NativeToolValidator(self.logger)
        self.validators["mcp"] = MCPToolValidator(self.logger)
    
    def validate_tool(self, tool_name: str, config_path: str) -> Dict[str, ValidationResult]:
        """全面验证工具
        
        Args:
            tool_name: 工具名称
            config_path: 配置文件路径
            
        Returns:
            Dict[str, ValidationResult]: 各阶段验证结果
        """
        results = {}
        
        # 1. 配置验证
        # 确保配置路径在tools目录下
        if not config_path.startswith("tools/"):
            config_path = f"tools/{config_path}"
        config_result = self.validators["config"].validate_config(config_path)
        results["config"] = config_result
        
        # 2. 类型特定验证
        if config_result.is_successful():
            tool_type = config_result.metadata.get("tool_type")
            if tool_type in self.validators:
                type_result = self.validators[tool_type].validate_tool_type(
                    tool_type, config_result.metadata.get("config_data", {})
                )
                results["type"] = type_result
        
        # 3. 加载验证
        if self.tool_manager:
            loading_result = self.validators["loading"].validate_loading(tool_name)
            results["loading"] = loading_result
        
        return results
    
    def validate_all_tools(self, config_dir: str = "tools") -> Dict[str, Dict[str, ValidationResult]]:
        """验证所有工具
        
        Args:
            config_dir: 配置目录路径
            
        Returns:
            Dict[str, Dict[str, ValidationResult]]: 所有工具的验证结果
        """
        all_results = {}
        
        try:
            # 获取所有工具配置文件
            config_files = self._get_tool_config_files(config_dir)
            
            for config_file in config_files:
                tool_name = config_file.stem
                # 构建相对于配置加载器base_path的路径
                relative_path = f"{config_dir}/{config_file.name}"
                results = self.validate_tool(tool_name, relative_path)
                all_results[tool_name] = results
        
        except Exception as e:
            self.logger.error(f"验证所有工具时出错: {e}")
        
        return all_results
    
    def _get_tool_config_files(self, config_dir: str) -> List[Path]:
        """获取工具配置文件列表
        
        Args:
            config_dir: 配置目录路径
            
        Returns:
            List[Path]: 配置文件路径列表
        """
        # 注意：IConfigLoader接口没有base_path属性，我们需要通过其他方式获取基础路径
        base_path = getattr(self.config_loader, 'base_path', 'configs')
        self.logger.info(f"配置加载器base_path: {base_path}")
        self.logger.info(f"传入的config_dir: {config_dir}")
        # 使用配置加载器的base_path来构建完整路径
        base_path = getattr(self.config_loader, 'base_path', Path('configs'))
        full_config_path = Path(base_path) / config_dir
        self.logger.info(f"完整配置目录路径: {full_config_path}")
        self.logger.info(f"完整配置目录是否存在: {full_config_path.exists()}")
        if not full_config_path.exists():
            self.logger.warning(f"配置目录不存在: {full_config_path}")
            return []
        
        files = list(full_config_path.glob("*.yaml"))
        self.logger.info(f"找到 {len(files)} 个配置文件")
        for f in files:
            self.logger.info(f"配置文件: {f}")
        return files
    
    def generate_report(self, all_results: Mapping[str, Mapping[str, ValidationResult]], format: str = "text") -> str:
        """生成验证报告
        
        Args:
            all_results: 所有工具的验证结果
            format: 报告格式 ("text" 或 "json")
            
        Returns:
            str: 生成的报告
        """
        if format == "json":
            return self._generate_json_report(all_results)
        else:
            return self._generate_text_report(all_results)
    
    def _generate_text_report(self, all_results: Mapping[str, Mapping[str, ValidationResult]]) -> str:
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
        
        for tool_name, results in all_results.items():
            report_lines.append(f"\n工具: {tool_name}")
            report_lines.append("-" * 30)
            
            tool_successful = True
            for stage, result in results.items():
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
    
    def _generate_json_report(self, all_results: Mapping[str, Mapping[str, ValidationResult]]) -> str:
        """生成JSON格式报告
        
        Args:
            all_results: 所有工具的验证结果
            
        Returns:
            str: JSON格式报告
        """
        import json
        
        report_data: Dict[str, Any] = {
            "summary": {
                "total_tools": len(all_results),
                "successful_tools": 0,
                "failed_tools": 0
            },
            "tools": {}
        }
        
        successful_count = 0
        
        for tool_name, results in all_results.items():
            tool_data: Dict[str, Any] = {
                "name": tool_name,
                "stages": {}
            }

            tool_successful = True
            for stage, result in results.items():
                stage_data: Dict[str, Any] = {
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