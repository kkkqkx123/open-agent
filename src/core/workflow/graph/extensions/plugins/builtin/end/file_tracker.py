"""文件追踪插件

追踪工作流执行期间的文件变更。
"""

import os
import json
import hashlib
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Set
from datetime import datetime
from pathlib import Path

from src.interfaces.workflow.plugins import IEndPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class FileTrackerPlugin(IEndPlugin):
    """文件追踪插件

    在工作流结束时追踪和分析文件变更。
    """

    def __init__(self):
        """初始化文件追踪插件"""
        self._config = {}
        self._initial_snapshot = None
        self._tracked_files = set()

    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="file_tracker",
            version="1.0.0",
            description="追踪工作流执行期间的文件变更",
            author="system",
            plugin_type=PluginType.END,
            config_schema={
                "type": "object",
                "properties": {
                    "track_created_files": {
                        "type": "boolean",
                        "description": "是否追踪创建的文件",
                        "default": True,
                    },
                    "track_modified_files": {
                        "type": "boolean",
                        "description": "是否追踪修改的文件",
                        "default": True,
                    },
                    "track_deleted_files": {
                        "type": "boolean",
                        "description": "是否追踪删除的文件",
                        "default": True,
                    },
                    "include_file_hashes": {
                        "type": "boolean",
                        "description": "是否包含文件哈希",
                        "default": False,
                    },
                    "generate_diff_report": {
                        "type": "boolean",
                        "description": "是否生成差异报告",
                        "default": True,
                    },
                    "save_to_file": {
                        "type": "boolean",
                        "description": "是否保存到文件",
                        "default": True,
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "输出目录",
                        "default": "./output",
                    },
                    "track_patterns": {
                        "type": "array",
                        "description": "要追踪的文件模式",
                        "default": ["*"],
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "description": "要排除的文件模式",
                        "default": ["*.tmp", "*.log", "__pycache__", ".git"],
                    },
                    "max_file_size_mb": {
                        "type": "integer",
                        "description": "最大文件大小限制（MB）",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件

        Args:
            config: 插件配置

        Returns:
            bool: 初始化是否成功
        """
        self._config = {
            "track_created_files": config.get("track_created_files", True),
            "track_modified_files": config.get("track_modified_files", True),
            "track_deleted_files": config.get("track_deleted_files", True),
            "include_file_hashes": config.get("include_file_hashes", False),
            "generate_diff_report": config.get("generate_diff_report", True),
            "save_to_file": config.get("save_to_file", True),
            "output_directory": config.get("output_directory", "./output"),
            "track_patterns": config.get("track_patterns", ["*"]),
            "exclude_patterns": config.get(
                "exclude_patterns", ["*.tmp", "*.log", "__pycache__", ".git"]
            ),
            "max_file_size_mb": config.get("max_file_size_mb", 10),
        }

        # 创建初始快照
        self._initial_snapshot = self._create_file_snapshot()

        logger.debug("文件追踪插件初始化完成")
        return True

    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑

        Args:
            state: 当前工作流状态
            context: 执行上下文

        Returns:
            Dict[str, Any]: 更新后的状态
        """
        logger.info("开始追踪文件变更")

        try:
            # 创建当前快照
            current_snapshot = self._create_file_snapshot()

            # 比较快照，检测变更
            changes = self._compare_snapshots(self._initial_snapshot, current_snapshot)  # type: ignore

            # 分析变更
            analysis = self._analyze_changes(changes)

            # 生成差异报告
            if self._config["generate_diff_report"]:
                diff_report = self._generate_diff_report(changes, analysis)
                analysis["diff_report"] = diff_report

            # 保存到文件
            if self._config["save_to_file"]:
                self._save_file_tracking_report(changes, analysis, context)

            # 更新状态
            state["file_tracking"] = {
                "changes": changes,
                "analysis": analysis,
                "snapshot_time": datetime.now().isoformat(),
            }

            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["file_tracking_completed"] = True

            logger.info(f"文件追踪完成，检测到 {len(changes.get('all', []))} 个变更")

        except Exception as e:
            logger.error(f"文件追踪失败: {e}")
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["file_tracking_error"] = str(e)

        return state

    def cleanup(self) -> bool:
        """清理插件资源

        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        self._initial_snapshot = None
        self._tracked_files.clear()
        return True

    def _create_file_snapshot(self) -> Dict[str, Any]:
        """创建文件快照

        Returns:
            Dict[str, Any]: 文件快照
        """
        snapshot = {"timestamp": datetime.now().isoformat(), "files": {}}

        try:
            current_dir = Path.cwd()
            track_patterns = self._config["track_patterns"]
            exclude_patterns = self._config["exclude_patterns"]
            max_file_size = self._config["max_file_size_mb"] * 1024 * 1024

            for pattern in track_patterns:
                for file_path in current_dir.rglob(pattern):
                    # 检查排除模式
                    if any(exclude in str(file_path) for exclude in exclude_patterns):
                        continue

                    # 只处理文件
                    if not file_path.is_file():
                        continue

                    try:
                        # 获取相对路径
                        rel_path = str(file_path.relative_to(current_dir))

                        # 获取文件信息
                        stat = file_path.stat()
                        file_info = {
                            "path": rel_path,
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                            "ctime": stat.st_ctime,
                        }

                        # 检查文件大小限制
                        if stat.st_size > max_file_size:
                            file_info["skipped"] = "文件过大"
                            snapshot["files"][rel_path] = file_info
                            continue

                        # 计算文件哈希（如果启用）
                        if self._config["include_file_hashes"]:
                            file_hash = self._calculate_file_hash(file_path)
                            file_info["hash"] = file_hash

                        snapshot["files"][rel_path] = file_info

                    except (OSError, PermissionError) as e:
                        logger.debug(f"无法访问文件 {file_path}: {e}")
                        continue

        except Exception as e:
            logger.error(f"创建文件快照失败: {e}")
            snapshot["error"] = str(e)

        return snapshot

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希

        Args:
            file_path: 文件路径

        Returns:
            str: 文件哈希
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # 分块读取大文件
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.debug(f"计算文件哈希失败 {file_path}: {e}")
            return "unknown"

    def _compare_snapshots(
        self, initial: Dict[str, Any], current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """比较文件快照，检测变更

        Args:
            initial: 初始快照
            current: 当前快照

        Returns:
            Dict[str, Any]: 变更信息
        """
        changes = {"created": [], "modified": [], "deleted": [], "all": []}

        try:
            initial_files = initial.get("files", {})
            current_files = current.get("files", {})

            # 检测创建和修改的文件
            for file_path, file_info in current_files.items():
                if file_path not in initial_files:
                    # 新创建的文件
                    if self._config["track_created_files"]:
                        changes["created"].append(file_info)
                        changes["all"].append(
                            {"type": "created", "path": file_path, "info": file_info}
                        )
                else:
                    # 检查是否修改
                    initial_info = initial_files[file_path]
                    if self._is_file_modified(initial_info, file_info):
                        if self._config["track_modified_files"]:
                            changes["modified"].append(
                                {
                                    "path": file_path,
                                    "old_info": initial_info,
                                    "new_info": file_info,
                                }
                            )
                            changes["all"].append(
                                {
                                    "type": "modified",
                                    "path": file_path,
                                    "old_info": initial_info,
                                    "new_info": file_info,
                                }
                            )

            # 检测删除的文件
            for file_path, file_info in initial_files.items():
                if file_path not in current_files:
                    if self._config["track_deleted_files"]:
                        changes["deleted"].append(file_info)
                        changes["all"].append(
                            {"type": "deleted", "path": file_path, "info": file_info}
                        )

        except Exception as e:
            logger.error(f"比较文件快照失败: {e}")
            changes["error"] = str(e)  # type: ignore

        return changes

    def _is_file_modified(
        self, initial_info: Dict[str, Any], current_info: Dict[str, Any]
    ) -> bool:
        """检查文件是否修改

        Args:
            initial_info: 初始文件信息
            current_info: 当前文件信息

        Returns:
            bool: 是否修改
        """
        # 检查大小
        if initial_info.get("size") != current_info.get("size"):
            return True

        # 检查修改时间
        if initial_info.get("mtime") != current_info.get("mtime"):
            return True

        # 检查哈希（如果可用）
        if "hash" in initial_info and "hash" in current_info:
            return initial_info["hash"] != current_info["hash"]

        return False

    def _analyze_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """分析文件变更

        Args:
            changes: 变更信息

        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            "summary": {},
            "by_extension": {},
            "by_directory": {},
            "size_analysis": {},
        }

        try:
            # 基本统计
            analysis["summary"] = {
                "total_changes": len(changes.get("all", [])),
                "created_count": len(changes.get("created", [])),
                "modified_count": len(changes.get("modified", [])),
                "deleted_count": len(changes.get("deleted", [])),
            }

            # 按扩展名分析
            ext_stats = {}
            for change in changes.get("all", []):
                file_path = change.get("path", "")
                ext = os.path.splitext(file_path)[1].lower()
                if not ext:
                    ext = "no_extension"

                if ext not in ext_stats:
                    ext_stats[ext] = {"created": 0, "modified": 0, "deleted": 0}

                ext_stats[ext][change["type"]] += 1

            analysis["by_extension"] = ext_stats

            # 按目录分析
            dir_stats = {}
            for change in changes.get("all", []):
                file_path = change.get("path", "")
                directory = os.path.dirname(file_path)
                if not directory:
                    directory = "root"

                if directory not in dir_stats:
                    dir_stats[directory] = {"created": 0, "modified": 0, "deleted": 0}

                dir_stats[directory][change["type"]] += 1

            analysis["by_directory"] = dir_stats

            # 大小分析
            size_analysis = {
                "total_size_created": 0,
                "total_size_modified": 0,
                "total_size_deleted": 0,
                "largest_file": None,
                "smallest_file": None,
            }

            all_files_with_size = []

            # 创建的文件大小
            for file_info in changes.get("created", []):
                size = file_info.get("size", 0)
                size_analysis["total_size_created"] += size
                all_files_with_size.append(
                    {"path": file_info.get("path"), "size": size, "type": "created"}
                )

            # 修改的文件大小
            for change in changes.get("modified", []):
                new_info = change.get("new_info", {})
                size = new_info.get("size", 0)
                size_analysis["total_size_modified"] += size
                all_files_with_size.append(
                    {"path": change.get("path"), "size": size, "type": "modified"}
                )

            # 删除的文件大小
            for file_info in changes.get("deleted", []):
                size = file_info.get("size", 0)
                size_analysis["total_size_deleted"] += size

            # 最大和最小文件
            if all_files_with_size:
                largest = max(all_files_with_size, key=lambda x: x["size"])
                smallest = min(all_files_with_size, key=lambda x: x["size"])

                size_analysis["largest_file"] = {
                    "path": largest["path"],
                    "size": largest["size"],
                    "type": largest["type"],
                }
                size_analysis["smallest_file"] = {
                    "path": smallest["path"],
                    "size": smallest["size"],
                    "type": smallest["type"],
                }

            analysis["size_analysis"] = size_analysis

        except Exception as e:
            logger.error(f"分析文件变更失败: {e}")
            analysis["error"] = str(e)  # type: ignore

        return analysis

    def _generate_diff_report(
        self, changes: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """生成差异报告

        Args:
            changes: 变更信息
            analysis: 分析结果

        Returns:
            str: 差异报告
        """
        lines = []

        # 标题
        lines.append("# 文件变更报告")
        lines.append("")

        # 摘要
        lines.append("## 变更摘要")
        summary = analysis.get("summary", {})
        lines.append(f"- **总变更数**: {summary.get('total_changes', 0)}")
        lines.append(f"- **创建文件**: {summary.get('created_count', 0)}")
        lines.append(f"- **修改文件**: {summary.get('modified_count', 0)}")
        lines.append(f"- **删除文件**: {summary.get('deleted_count', 0)}")
        lines.append("")

        # 按扩展名统计
        if analysis.get("by_extension"):
            lines.append("## 按文件类型统计")
            for ext, stats in analysis["by_extension"].items():
                lines.append(
                    f"- **{ext}**: 创建 {stats['created']}, 修改 {stats['modified']}, 删除 {stats['deleted']}"
                )
            lines.append("")

        # 按目录统计
        if analysis.get("by_directory"):
            lines.append("## 按目录统计")
            for directory, stats in analysis["by_directory"].items():
                lines.append(
                    f"- **{directory}**: 创建 {stats['created']}, 修改 {stats['modified']}, 删除 {stats['deleted']}"
                )
            lines.append("")

        # 大小分析
        if analysis.get("size_analysis"):
            lines.append("## 大小分析")
            size_analysis = analysis["size_analysis"]
            lines.append(
                f"- **创建文件总大小**: {self._format_size(size_analysis.get('total_size_created', 0))}"
            )
            lines.append(
                f"- **修改文件总大小**: {self._format_size(size_analysis.get('total_size_modified', 0))}"
            )
            lines.append(
                f"- **删除文件总大小**: {self._format_size(size_analysis.get('total_size_deleted', 0))}"
            )

            if size_analysis.get("largest_file"):
                largest = size_analysis["largest_file"]
                lines.append(
                    f"- **最大文件**: {largest['path']} ({self._format_size(largest['size'])})"
                )

            if size_analysis.get("smallest_file"):
                smallest = size_analysis["smallest_file"]
                lines.append(
                    f"- **最小文件**: {smallest['path']} ({self._format_size(smallest['size'])})"
                )

            lines.append("")

        # 详细变更列表
        if changes.get("all"):
            lines.append("## 详细变更列表")

            # 创建的文件
            if changes.get("created"):
                lines.append("### 创建的文件")
                for file_info in changes["created"]:
                    path = file_info.get("path", "")
                    size = self._format_size(file_info.get("size", 0))
                    lines.append(f"- `{path}` ({size})")
                lines.append("")

            # 修改的文件
            if changes.get("modified"):
                lines.append("### 修改的文件")
                for change in changes["modified"]:
                    path = change.get("path", "")
                    new_info = change.get("new_info", {})
                    size = self._format_size(new_info.get("size", 0))
                    lines.append(f"- `{path}` ({size})")
                lines.append("")

            # 删除的文件
            if changes.get("deleted"):
                lines.append("### 删除的文件")
                for file_info in changes["deleted"]:
                    path = file_info.get("path", "")
                    size = self._format_size(file_info.get("size", 0))
                    lines.append(f"- `{path}` ({size})")
                lines.append("")

        return "\n".join(lines)

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

    def _save_file_tracking_report(
        self, changes: Dict[str, Any], analysis: Dict[str, Any], context: PluginContext
    ) -> None:
        """保存文件追踪报告

        Args:
            changes: 变更信息
            analysis: 分析结果
            context: 执行上下文
        """
        try:
            output_dir = self._config["output_directory"]
            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存JSON格式的详细数据
            json_filename = f"file_tracking_{context.workflow_id}_{timestamp}.json"
            json_filepath = os.path.join(output_dir, json_filename)

            tracking_data = {
                "workflow_id": context.workflow_id,
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "analysis": analysis,
            }

            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(tracking_data, f, ensure_ascii=False, indent=2, default=str)

            # 保存Markdown格式的报告
            if "diff_report" in analysis:
                md_filename = (
                    f"file_tracking_report_{context.workflow_id}_{timestamp}.md"
                )
                md_filepath = os.path.join(output_dir, md_filename)

                with open(md_filepath, "w", encoding="utf-8") as f:
                    f.write(analysis["diff_report"])

            logger.info(f"文件追踪报告已保存到: {output_dir}")

        except Exception as e:
            logger.error(f"保存文件追踪报告失败: {e}")
