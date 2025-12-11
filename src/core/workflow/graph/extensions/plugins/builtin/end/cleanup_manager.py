"""清理管理插件

管理工作流结束时的清理操作。
"""

import os
import shutil
import glob
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.interfaces.workflow.plugins import IEndPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class CleanupManagerPlugin(IEndPlugin):
    """清理管理插件
    
    在工作流结束时执行各种清理操作。
    """
    
    def __init__(self):
        """初始化清理管理插件"""
        self._config = {}
        self._cleanup_stats = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="cleanup_manager",
            version="1.0.0",
            description="管理工作流结束时的清理操作",
            author="system",
            plugin_type=PluginType.END,
            config_schema={
                "type": "object",
                "properties": {
                    "cleanup_temp_files": {
                        "type": "boolean",
                        "description": "是否清理临时文件",
                        "default": True
                    },
                    "cleanup_cache": {
                        "type": "boolean",
                        "description": "是否清理缓存",
                        "default": False
                    },
                    "cleanup_logs": {
                        "type": "boolean",
                        "description": "是否清理日志文件",
                        "default": False
                    },
                    "retain_patterns": {
                        "type": "array",
                        "description": "要保留的文件模式",
                        "default": ["*.log", "*.report", "*.md"]
                    },
                    "temp_file_patterns": {
                        "type": "array",
                        "description": "临时文件模式",
                        "default": ["*.tmp", "*.temp", "*.bak", "*~", ".#*"]
                    },
                    "cache_directories": {
                        "type": "array",
                        "description": "缓存目录列表",
                        "default": ["__pycache__", ".pytest_cache", ".mypy_cache"]
                    },
                    "log_retention_days": {
                        "type": "integer",
                        "description": "日志保留天数",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 365
                    },
                    "max_file_age_hours": {
                        "type": "integer",
                        "description": "最大文件保留时间（小时）",
                        "default": 24,
                        "minimum": 1,
                        "maximum": 168
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "是否只执行试运行（不实际删除）",
                        "default": True
                    },
                    "generate_cleanup_report": {
                        "type": "boolean",
                        "description": "是否生成清理报告",
                        "default": True
                    },
                    "save_report_to_file": {
                        "type": "boolean",
                        "description": "是否保存清理报告到文件",
                        "default": True
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "输出目录",
                        "default": "./output"
                    }
                },
                "required": []
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        self._config = {
            "cleanup_temp_files": config.get("cleanup_temp_files", True),
            "cleanup_cache": config.get("cleanup_cache", False),
            "cleanup_logs": config.get("cleanup_logs", False),
            "retain_patterns": config.get("retain_patterns", ["*.log", "*.report", "*.md"]),
            "temp_file_patterns": config.get("temp_file_patterns", ["*.tmp", "*.temp", "*.bak", "*~", ".#*"]),
            "cache_directories": config.get("cache_directories", ["__pycache__", ".pytest_cache", ".mypy_cache"]),
            "log_retention_days": config.get("log_retention_days", 7),
            "max_file_age_hours": config.get("max_file_age_hours", 24),
            "dry_run": config.get("dry_run", True),
            "generate_cleanup_report": config.get("generate_cleanup_report", True),
            "save_report_to_file": config.get("save_report_to_file", True),
            "output_directory": config.get("output_directory", "./output")
        }
        
        # 初始化统计信息
        self._cleanup_stats = {
            "files_scanned": 0,
            "files_deleted": 0,
            "directories_deleted": 0,
            "space_freed": 0,
            "errors": []
        }
        
        logger.debug(f"清理管理插件初始化完成 (试运行: {self._config['dry_run']})")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        logger.info("开始执行清理操作")
        
        try:
            # 重置统计信息
            self._reset_stats()
            
            # 执行各种清理操作
            if self._config["cleanup_temp_files"]:
                self._cleanup_temp_files()
            
            if self._config["cleanup_cache"]:
                self._cleanup_cache_directories()
            
            if self._config["cleanup_logs"]:
                self._cleanup_old_logs()
            
            # 生成清理报告
            cleanup_report = None
            if self._config["generate_cleanup_report"]:
                cleanup_report = self._generate_cleanup_report()
                
                # 保存报告到文件
                if self._config["save_report_to_file"]:
                    self._save_cleanup_report(cleanup_report, context)
            
            # 更新状态
            state["cleanup_results"] = {
                "stats": self._cleanup_stats,
                "report": cleanup_report,
                "dry_run": self._config["dry_run"],
                "timestamp": datetime.now().isoformat()
            }
            
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["cleanup_completed"] = True
            
            logger.info(f"清理操作完成: 扫描 {self._cleanup_stats['files_scanned']} 个文件, "
                       f"删除 {self._cleanup_stats['files_deleted']} 个文件, "
                       f"释放 {self._format_size(self._cleanup_stats['space_freed'])}")
            
        except Exception as e:
            logger.error(f"清理操作失败: {e}")
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["cleanup_error"] = str(e)
        
        return state
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        self._cleanup_stats.clear()
        return True
    
    def _reset_stats(self) -> None:
        """重置统计信息"""
        self._cleanup_stats = {
            "files_scanned": 0,
            "files_deleted": 0,
            "directories_deleted": 0,
            "space_freed": 0,
            "errors": []
        }
    
    def _cleanup_temp_files(self) -> None:
        """清理临时文件"""
        logger.debug("开始清理临时文件")
        
        try:
            current_dir = os.getcwd()
            temp_patterns = self._config["temp_file_patterns"]
            retain_patterns = self._config["retain_patterns"]
            max_age_hours = self._config["max_file_age_hours"]
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for pattern in temp_patterns:
                # 查找匹配的文件
                for file_path in glob.glob(os.path.join(current_dir, "**", pattern), recursive=True):
                    try:
                        self._process_file_for_cleanup(file_path, retain_patterns, cutoff_time, "temp_file")
                    except Exception as e:
                        error_msg = f"处理临时文件失败 {file_path}: {e}"
                        logger.warning(error_msg)
                        self._cleanup_stats["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"清理临时文件失败: {e}"
            logger.error(error_msg)
            self._cleanup_stats["errors"].append(error_msg)
    
    def _cleanup_cache_directories(self) -> None:
        """清理缓存目录"""
        logger.debug("开始清理缓存目录")
        
        try:
            current_dir = os.getcwd()
            cache_dirs = self._config["cache_directories"]
            max_age_hours = self._config["max_file_age_hours"]
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for cache_dir in cache_dirs:
                cache_path = os.path.join(current_dir, cache_dir)
                if os.path.exists(cache_path):
                    try:
                        self._process_directory_for_cleanup(cache_path, cutoff_time, "cache_directory")
                    except Exception as e:
                        error_msg = f"清理缓存目录失败 {cache_path}: {e}"
                        logger.warning(error_msg)
                        self._cleanup_stats["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"清理缓存目录失败: {e}"
            logger.error(error_msg)
            self._cleanup_stats["errors"].append(error_msg)
    
    def _cleanup_old_logs(self) -> None:
        """清理旧日志文件"""
        logger.debug("开始清理旧日志文件")
        
        try:
            current_dir = os.getcwd()
            retain_patterns = self._config["retain_patterns"]
            retention_days = self._config["log_retention_days"]
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            
            # 查找日志文件
            log_patterns = ["*.log", "*.log.*", "logs/*.log", "logs/*.log.*"]
            
            for pattern in log_patterns:
                for file_path in glob.glob(os.path.join(current_dir, pattern), recursive=True):
                    try:
                        self._process_file_for_cleanup(file_path, retain_patterns, cutoff_time, "log_file")
                    except Exception as e:
                        error_msg = f"处理日志文件失败 {file_path}: {e}"
                        logger.warning(error_msg)
                        self._cleanup_stats["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"清理旧日志文件失败: {e}"
            logger.error(error_msg)
            self._cleanup_stats["errors"].append(error_msg)
    
    def _process_file_for_cleanup(self, file_path: str, retain_patterns: List[str], 
                                 cutoff_time: datetime, file_type: str) -> None:
        """处理文件清理
        
        Args:
            file_path: 文件路径
            retain_patterns: 保留模式列表
            cutoff_time: 截止时间
            file_type: 文件类型
        """
        if not os.path.isfile(file_path):
            return
        
        self._cleanup_stats["files_scanned"] += 1
        
        # 检查是否应该保留
        if self._should_retain_file(file_path, retain_patterns):
            logger.debug(f"保留文件: {file_path}")
            return
        
        # 检查文件年龄
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mtime > cutoff_time:
            logger.debug(f"文件太新，跳过: {file_path}")
            return
        
        # 获取文件大小
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = 0
        
        # 删除文件
        action = "将删除" if self._config["dry_run"] else "已删除"
        logger.debug(f"{action} {file_type}: {file_path} ({self._format_size(file_size)})")
        
        if not self._config["dry_run"]:
            try:
                os.remove(file_path)
                self._cleanup_stats["files_deleted"] += 1
                self._cleanup_stats["space_freed"] += file_size
            except OSError as e:
                error_msg = f"删除文件失败 {file_path}: {e}"
                logger.warning(error_msg)
                self._cleanup_stats["errors"].append(error_msg)
    
    def _process_directory_for_cleanup(self, dir_path: str, cutoff_time: datetime, dir_type: str) -> None:
        """处理目录清理
        
        Args:
            dir_path: 目录路径
            cutoff_time: 截止时间
            dir_type: 目录类型
        """
        if not os.path.isdir(dir_path):
            return
        
        # 检查目录年龄
        dir_mtime = datetime.fromtimestamp(os.path.getmtime(dir_path))
        if dir_mtime > cutoff_time:
            logger.debug(f"目录太新，跳过: {dir_path}")
            return
        
        # 计算目录大小
        dir_size = self._get_directory_size(dir_path)
        
        action = "将删除" if self._config["dry_run"] else "已删除"
        logger.debug(f"{action} {dir_type}: {dir_path} ({self._format_size(dir_size)})")
        
        if not self._config["dry_run"]:
            try:
                shutil.rmtree(dir_path)
                self._cleanup_stats["directories_deleted"] += 1
                self._cleanup_stats["space_freed"] += dir_size
            except OSError as e:
                error_msg = f"删除目录失败 {dir_path}: {e}"
                logger.warning(error_msg)
                self._cleanup_stats["errors"].append(error_msg)
    
    def _should_retain_file(self, file_path: str, retain_patterns: List[str]) -> bool:
        """检查是否应该保留文件
        
        Args:
            file_path: 文件路径
            retain_patterns: 保留模式列表
            
        Returns:
            bool: 是否应该保留
        """
        filename = os.path.basename(file_path)
        
        for pattern in retain_patterns:
            if self._match_pattern(filename, pattern):
                return True
        
        return False
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """匹配文件模式
        
        Args:
            filename: 文件名
            pattern: 模式
            
        Returns:
            bool: 是否匹配
        """
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def _get_directory_size(self, dir_path: str) -> int:
        """获取目录大小
        
        Args:
            dir_path: 目录路径
            
        Returns:
            int: 目录大小（字节）
        """
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        continue
        except OSError:
            pass
        
        return total_size
    
    def _generate_cleanup_report(self) -> str:
        """生成清理报告
        
        Returns:
            str: 清理报告
        """
        lines = []
        
        # 标题
        lines.append("# 清理操作报告")
        lines.append("")
        
        # 基本信息
        lines.append("## 基本信息")
        lines.append(f"- **执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **试运行模式**: {'是' if self._config['dry_run'] else '否'}")
        lines.append("")
        
        # 统计信息
        lines.append("## 清理统计")
        stats = self._cleanup_stats
        lines.append(f"- **扫描文件数**: {stats['files_scanned']}")
        lines.append(f"- **删除文件数**: {stats['files_deleted']}")
        lines.append(f"- **删除目录数**: {stats['directories_deleted']}")
        lines.append(f"- **释放空间**: {self._format_size(stats['space_freed'])}")
        lines.append("")
        
        # 配置信息
        lines.append("## 清理配置")
        lines.append(f"- **清理临时文件**: {'是' if self._config['cleanup_temp_files'] else '否'}")
        lines.append(f"- **清理缓存**: {'是' if self._config['cleanup_cache'] else '否'}")
        lines.append(f"- **清理日志**: {'是' if self._config['cleanup_logs'] else '否'}")
        lines.append(f"- **最大文件年龄**: {self._config['max_file_age_hours']} 小时")
        lines.append(f"- **日志保留天数**: {self._config['log_retention_days']} 天")
        lines.append("")
        
        # 错误信息
        if stats["errors"]:
            lines.append("## 错误信息")
            for error in stats["errors"]:
                lines.append(f"- {error}")
            lines.append("")
        
        # 保留模式
        if self._config["retain_patterns"]:
            lines.append("## 保留文件模式")
            for pattern in self._config["retain_patterns"]:
                lines.append(f"- `{pattern}`")
            lines.append("")
        
        # 临时文件模式
        if self._config["temp_file_patterns"]:
            lines.append("## 临时文件模式")
            for pattern in self._config["temp_file_patterns"]:
                lines.append(f"- `{pattern}`")
            lines.append("")
        
        # 缓存目录
        if self._config["cache_directories"]:
            lines.append("## 缓存目录")
            for cache_dir in self._config["cache_directories"]:
                lines.append(f"- `{cache_dir}`")
            lines.append("")
        
        # 总结
        lines.append("## 总结")
        if self._config["dry_run"]:
            lines.append("本次运行为试运行模式，没有实际删除任何文件。")
            lines.append("如需执行实际清理，请设置 `dry_run: false`。")
        else:
            if stats["files_deleted"] > 0 or stats["directories_deleted"] > 0:
                lines.append("清理操作已成功完成。")
            else:
                lines.append("没有找到需要清理的文件或目录。")
        
        return '\n'.join(lines)
    
    def _save_cleanup_report(self, report: str, context: PluginContext) -> None:
        """保存清理报告
        
        Args:
            report: 清理报告
            context: 执行上下文
        """
        try:
            output_dir = self._config["output_directory"]
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cleanup_report_{context.workflow_id}_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"清理报告已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存清理报告失败: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            str: 格式化的大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"