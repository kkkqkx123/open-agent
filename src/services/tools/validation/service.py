"""
工具验证服务
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from src.interfaces.tool.validator import IValidationEngine
from src.interfaces.tool.reporter import IReporterFactory
from src.interfaces.config import IConfigLoader
from src.interfaces.logger import ILogger
from src.interfaces.tool.base import IToolManager
from src.core.tools.validation.models import ValidationResult
from src.interfaces.tool.exceptions import ToolValidationError


class ToolValidationService:
    """工具验证服务
    
    提供完整的工具验证功能，包括配置验证、加载验证和报告生成。
    """
    
    def __init__(
        self,
        validation_engine: IValidationEngine,
        reporter_factory: IReporterFactory,
        config_loader: Optional[IConfigLoader] = None,
        tool_manager: Optional[IToolManager] = None,
        logger: Optional[ILogger] = None
    ):
        """初始化工具验证服务
        
        Args:
            validation_engine: 验证引擎
            reporter_factory: 报告器工厂
            config_loader: 配置加载器
            tool_manager: 工具管理器
            logger: 日志记录器
        """
        self._engine = validation_engine
        self._reporter_factory = reporter_factory
        self._config_loader = config_loader
        self._tool_manager = tool_manager
        self._logger = logger
    
    def validate_tool(self, tool_config: Any) -> ValidationResult:
        """验证单个工具配置
        
        Args:
            tool_config: 工具配置
            
        Returns:
            ValidationResult: 验证结果
        """
        tool_name = getattr(tool_config, 'name', 'unknown')
        
        if self._logger:
            self._logger.info(f"开始验证工具: {tool_name}")
        
        try:
            result = self._engine.validate_tool(tool_config)
            
            if self._logger:
                status = "通过" if result.is_successful() else "失败"
                self._logger.info(f"工具 {tool_name} 验证{status}")
            
            return result
        
        except Exception as e:
            error_msg = f"验证工具 {tool_name} 时发生异常: {e}"
            
            if self._logger:
                self._logger.error(error_msg)
            
            # 创建错误结果
            from src.core.tools.validation.models import ValidationStatus, ValidationIssue
            error_result = ValidationResult(tool_name, getattr(tool_config, 'tool_type', 'unknown'), ValidationStatus.ERROR)
            error_result.add_issue(
                ValidationStatus.ERROR,
                error_msg,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )
            
            return error_result
    
    def validate_tool_loading(self, tool_name: str) -> ValidationResult:
        """验证工具加载
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ValidationResult: 验证结果
        """
        from src.core.tools.validation.models import ValidationStatus, ValidationIssue
        
        result = ValidationResult(tool_name, "unknown", ValidationStatus.SUCCESS)
        
        if not self._tool_manager:
            result.add_issue(
                ValidationStatus.WARNING,
                "工具管理器未设置，无法验证工具加载",
                suggestion="请设置工具管理器以进行加载验证"
            )
            return result
        
        try:
            if self._logger:
                self._logger.debug(f"验证工具加载: {tool_name}")
            
            # 尝试获取工具
            tool = self._tool_manager.get_tool(tool_name)
            
            if tool is None:
                result.add_issue(
                    ValidationStatus.ERROR,
                    f"工具 {tool_name} 未找到",
                    suggestion="请确保工具已正确注册"
                )
            else:
                if self._logger:
                    self._logger.debug(f"工具 {tool_name} 加载验证通过")
        
        except Exception as e:
            result.add_issue(
                ValidationStatus.ERROR,
                f"工具 {tool_name} 加载验证失败: {e}",
                exception_type=type(e).__name__,
                exception_message=str(e)
            )
            
            if self._logger:
                self._logger.error(f"工具 {tool_name} 加载验证失败: {e}")
        
        return result
    
    def validate_tool_comprehensive(self, tool_name: str, config_path: str) -> Dict[str, Any]:
        """全面验证工具（配置+加载）
        
        Args:
            tool_name: 工具名称
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        if self._logger:
            self._logger.info(f"开始全面验证工具: {tool_name}")
        
        try:
            # 加载工具配置
            tool_config = self._load_tool_config(config_path)
            
            # 执行配置验证
            config_result = self.validate_tool(tool_config)
            
            # 执行加载验证
            loading_result = self.validate_tool_loading(tool_name)
            
            # 合并结果
            final_result = self._merge_validation_results(config_result, loading_result)
            
            result_data = {
                "tool_name": tool_name,
                "config_path": config_path,
                "validation_result": final_result,
                "config_validation": config_result.to_dict(),
                "loading_validation": loading_result.to_dict()
            }
            
            if self._logger:
                status = "通过" if final_result.is_successful() else "失败"
                self._logger.info(f"工具 {tool_name} 全面验证{status}")
            
            return result_data
        
        except Exception as e:
            error_msg = f"全面验证工具 {tool_name} 时出错: {e}"
            
            if self._logger:
                self._logger.error(error_msg)
            
            # 返回错误结果
            from src.core.tools.validation.models import ValidationStatus, ValidationIssue
            error_result = ValidationResult(tool_name, "unknown", ValidationStatus.ERROR)
            error_result.add_issue(
                ValidationStatus.ERROR,
                error_msg,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )
            
            return {
                "tool_name": tool_name,
                "config_path": config_path,
                "validation_result": error_result,
                "error": error_msg
            }
    
    def validate_all_tools(self, config_dir: str = "tools", comprehensive: bool = False) -> Dict[str, Any]:
        """验证所有工具
        
        Args:
            config_dir: 配置目录
            comprehensive: 是否进行全面验证（包含加载验证）
            
        Returns:
            Dict[str, Any]: 所有工具的验证结果
        """
        if self._logger:
            validation_type = "全面" if comprehensive else "配置"
            self._logger.info(f"开始{validation_type}验证所有工具，目录: {config_dir}")
        
        try:
            # 加载工具配置
            tool_configs = self._load_tool_configs(config_dir)
            
            if not tool_configs:
                if self._logger:
                    self._logger.warning(f"在目录 {config_dir} 中没有找到工具配置")
                return {}
            
            results = {}
            
            if comprehensive:
                # 全面验证模式
                for config in tool_configs:
                    result = self.validate_tool_comprehensive(config.name, f"{config_dir}/{config.name}.yaml")
                    results[config.name] = result
            else:
                # 仅配置验证模式
                for config in tool_configs:
                    result = self.validate_tool(config)
                    results[config.name] = {
                        "tool_name": config.name,
                        "validation_result": result,
                        "config_validation": result.to_dict()
                    }
            
            # 统计结果
            successful = sum(1 for r in results.values() if r["validation_result"].is_successful())
            total = len(results)
            
            if self._logger:
                validation_type = "全面" if comprehensive else "配置"
                self._logger.info(f"{validation_type}验证完成，{successful}/{total} 个工具通过验证")
            
            return results
        
        except Exception as e:
            error_msg = f"验证所有工具时出错: {e}"
            
            if self._logger:
                self._logger.error(error_msg)
            
            raise ToolValidationError(error_msg, validation_errors=[str(e)])
    
    def generate_report(self, results: Dict[str, Any], format: str = "text") -> str:
        """生成验证报告
        
        Args:
            results: 验证结果
            format: 报告格式
            
        Returns:
            str: 生成的报告
        """
        try:
            if self._logger:
                self._logger.debug(f"生成 {format} 格式报告")
            
            # 提取验证结果
            validation_results = {}
            for tool_name, data in results.items():
                if "validation_result" in data:
                    validation_results[tool_name] = data["validation_result"]
                else:
                    validation_results[tool_name] = data
            
            reporter = self._reporter_factory.create_reporter(format)
            report = reporter.generate(validation_results)
            
            if self._logger:
                self._logger.debug(f"报告生成完成，格式: {format}")
            
            return report
        
        except Exception as e:
            error_msg = f"生成报告失败: {e}"
            
            if self._logger:
                self._logger.error(error_msg)
            
            raise ToolValidationError(error_msg)
    
    def get_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """获取验证摘要
        
        Args:
            results: 验证结果
            
        Returns:
            Dict[str, Any]: 验证摘要
        """
        total_tools = len(results)
        successful_tools = sum(1 for r in results.values() if r["validation_result"].is_successful())
        failed_tools = total_tools - successful_tools
        
        # 按工具类型统计
        tool_type_stats: Dict[str, Dict[str, int]] = {}
        for result_data in results.values():
            tool_type = result_data["validation_result"].tool_type
            if tool_type not in tool_type_stats:
                tool_type_stats[tool_type] = {"total": 0, "successful": 0, "failed": 0}
            
            tool_type_stats[tool_type]["total"] += 1
            if result_data["validation_result"].is_successful():
                tool_type_stats[tool_type]["successful"] += 1
            else:
                tool_type_stats[tool_type]["failed"] += 1
        
        # 统计错误和警告
        total_errors = sum(r["validation_result"].get_error_count() for r in results.values())
        total_warnings = sum(r["validation_result"].get_warning_count() for r in results.values())
        
        # 获取失败的工具列表
        failed_tool_list = [
            tool_name for tool_name, result_data in results.items()
            if not result_data["validation_result"].is_successful()
        ]
        
        return {
            "total_tools": total_tools,
            "successful_tools": successful_tools,
            "failed_tools": failed_tools,
            "success_rate": successful_tools / total_tools * 100 if total_tools > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "tool_type_distribution": tool_type_stats,
            "failed_tools": failed_tool_list
        }
    
    def get_supported_report_formats(self) -> List[str]:
        """获取支持的报告格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        return self._reporter_factory.get_supported_formats()
    
    def _load_tool_configs(self, config_dir: str) -> List[Any]:
        """加载工具配置
        
        Args:
            config_dir: 配置目录
            
        Returns:
            List[Any]: 工具配置列表
        """
        if not self._config_loader:
            raise ToolValidationError("配置加载器未设置")
        
        tool_configs = []
        
        try:
            # 获取配置文件列表
            config_files = self._get_config_files(config_dir)
            
            for config_file in config_files:
                try:
                    # 构建配置路径
                    config_path = f"{config_dir}/{config_file}"
                    
                    # 加载配置
                    config_data = self._config_loader.load_config(config_path, "tools")
                    
                    # 转换为配置对象
                    config_obj = self._create_config_object(config_data, config_file)
                    
                    if config_obj:
                        tool_configs.append(config_obj)
                
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"加载配置文件 {config_file} 失败: {e}")
                    continue
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"加载工具配置时出错: {e}")
            raise
        
        return tool_configs
    
    def _get_config_files(self, config_dir: str) -> List[str]:
        """获取配置文件列表
        
        Args:
            config_dir: 配置目录
            
        Returns:
            List[str]: 配置文件名列表
        """
        if hasattr(self._config_loader, 'list_config_files'):
            return self._config_loader.list_config_files(config_dir)
        
        # 默认实现：返回yaml文件
        base_path = getattr(self._config_loader, 'base_path', Path('configs'))
        full_path = Path(base_path) / config_dir
        
        if not full_path.exists():
            return []
        
        return [f.name for f in full_path.glob("*.yaml")]
    
    def _create_config_object(self, config_data: Dict[str, Any], config_file: str) -> Optional[Any]:
        """创建配置对象
        
        Args:
            config_data: 配置数据
            config_file: 配置文件名
            
        Returns:
            Optional[Any]: 配置对象
        """
        # 创建简单的配置对象
        class SimpleConfig:
            def __init__(self, data: Dict[str, Any], name: str):
                self.name = name
                self.tool_type = data.get('tool_type', 'unknown')
                self.description = data.get('description', '')
                self.parameters_schema = data.get('parameters_schema', {})
                self.function_path = data.get('function_path')
                self.api_url = data.get('api_url')
                self.mcp_server_url = data.get('mcp_server_url')
        
        tool_name = config_data.get('name', config_file.replace('.yaml', ''))
        return SimpleConfig(config_data, tool_name)
    
    def _load_tool_config(self, config_path: str) -> Any:
        """加载工具配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Any: 工具配置对象
        """
        # 创建简单的配置对象
        class SimpleConfig:
            def __init__(self, path: str):
                self.name = path.split('/')[-1].replace('.yaml', '')
                self.tool_type = "unknown"
                self.description = ""
                self.parameters_schema = {}
        
        return SimpleConfig(config_path)
    
    def _merge_validation_results(self, config_result: ValidationResult, loading_result: ValidationResult) -> ValidationResult:
        """合并验证结果
        
        Args:
            config_result: 配置验证结果
            loading_result: 加载验证结果
            
        Returns:
            ValidationResult: 合并后的结果
        """
        # 创建合并结果
        merged_result = ValidationResult(
            config_result.tool_name,
            config_result.tool_type,
            config_result.status
        )
        
        # 合并问题
        merged_result.issues.extend(config_result.issues)
        merged_result.issues.extend(loading_result.issues)
        
        # 合并元数据
        merged_result.metadata.update(config_result.metadata)
        merged_result.metadata.update(loading_result.metadata)
        
        # 更新状态（取最严重的）
        if loading_result.status.value == "error":
            merged_result.status = loading_result.status
        elif loading_result.status.value == "warning" and merged_result.status.value != "error":
            merged_result.status = loading_result.status
        
        return merged_result


# 为了向后兼容，保留ToolValidationManager的别名
ToolValidationManager = ToolValidationService

# 导出验证服务
__all__ = [
    "ToolValidationService",
    "ToolValidationManager",  # 向后兼容别名
]