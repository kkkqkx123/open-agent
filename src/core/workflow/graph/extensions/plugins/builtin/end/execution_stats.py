"""执行统计插件

收集和分析工作流执行统计信息。
"""

import os
import json
import time
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List
from datetime import datetime

from src.interfaces.workflow.plugins import IEndPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class ExecutionStatsPlugin(IEndPlugin):
    """执行统计插件

    在工作流结束时收集和分析执行统计信息。
    """

    def __init__(self) -> None:
        """初始化执行统计插件"""
        self._config = {}
        self._start_time = None
        self._initial_state = None

    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="execution_stats",
            version="1.0.0",
            description="收集和分析工作流执行统计信息",
            author="system",
            plugin_type=PluginType.END,
            config_schema={
                "type": "object",
                "properties": {
                    "track_execution_time": {
                        "type": "boolean",
                        "description": "是否跟踪执行时间",
                        "default": True,
                    },
                    "track_resource_usage": {
                        "type": "boolean",
                        "description": "是否跟踪资源使用",
                        "default": True,
                    },
                    "track_node_performance": {
                        "type": "boolean",
                        "description": "是否跟踪节点性能",
                        "default": True,
                    },
                    "generate_report": {
                        "type": "boolean",
                        "description": "是否生成统计报告",
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
                    "include_memory_profiling": {
                        "type": "boolean",
                        "description": "是否包含内存分析",
                        "default": False,
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
            "track_execution_time": config.get("track_execution_time", True),
            "track_resource_usage": config.get("track_resource_usage", True),
            "track_node_performance": config.get("track_node_performance", True),
            "generate_report": config.get("generate_report", True),
            "save_to_file": config.get("save_to_file", True),
            "output_directory": config.get("output_directory", "./output"),
            "include_memory_profiling": config.get("include_memory_profiling", False),
        }

        logger.debug("执行统计插件初始化完成")
        return True

    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑

        Args:
            state: 当前工作流状态
            context: 执行上下文

        Returns:
            Dict[str, Any]: 更新后的状态
        """
        logger.info("开始收集执行统计")

        try:
            # 收集执行统计
            stats = self._collect_execution_stats(state, context)

            # 生成报告
            if self._config["generate_report"]:
                report = self._generate_stats_report(stats, context)
                stats["report"] = report

                # 保存到文件
                if self._config["save_to_file"]:
                    self._save_stats_to_file(stats, context)

            # 更新状态
            state["execution_stats"] = stats
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["execution_stats_collected"] = True

            logger.info("执行统计收集完成")

        except Exception as e:
            logger.error(f"收集执行统计失败: {e}")
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["execution_stats_error"] = str(e)

        return state

    def cleanup(self) -> bool:
        """清理插件资源

        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        self._start_time = None
        self._initial_state = None
        return True

    def _collect_execution_stats(
        self, state: Dict[str, Any], context: PluginContext
    ) -> Dict[str, Any]:
        """收集执行统计

        Args:
            state: 当前工作流状态
            context: 执行上下文

        Returns:
            Dict[str, Any]: 执行统计数据
        """
        stats = {
            "workflow_id": context.workflow_id,
            "collection_timestamp": datetime.now().isoformat(),
            "thread_id": context.thread_id,
            "session_id": context.session_id,
        }

        # 执行时间统计
        if self._config["track_execution_time"]:
            stats["execution_time"] = self._collect_execution_time_stats(state, context)

        # 资源使用统计
        if self._config["track_resource_usage"]:
            stats["resource_usage"] = self._collect_resource_usage_stats()

        # 节点性能统计
        if self._config["track_node_performance"]:
            stats["node_performance"] = self._collect_node_performance_stats(state)

        # 插件执行统计
        stats["plugin_performance"] = self._collect_plugin_performance_stats(state)

        # 工作流统计
        stats["workflow_stats"] = self._collect_workflow_stats(state)

        return stats

    def _collect_execution_time_stats(
        self, state: Dict[str, Any], context: PluginContext
    ) -> Dict[str, Any]:
        """收集执行时间统计

        Args:
            state: 当前工作流状态
            context: 执行上下文

        Returns:
            Dict[str, Any]: 执行时间统计
        """
        time_stats = {}

        try:
            # 总执行时间
            if context.execution_start_time:
                total_time = time.time() - context.execution_start_time
                time_stats["total_execution_time"] = round(total_time, 3)
                time_stats["total_execution_time_formatted"] = self._format_duration(
                    total_time
                )

            # 插件执行时间
            if "plugin_executions" in state:
                plugin_executions = state["plugin_executions"]

                # 计算插件执行时间统计
                plugin_times = [p.get("execution_time", 0) for p in plugin_executions]
                if plugin_times:
                    time_stats["plugin_execution"] = {
                        "total_time": round(sum(plugin_times), 3),
                        "average_time": round(sum(plugin_times) / len(plugin_times), 3),
                        "min_time": round(min(plugin_times), 3),
                        "max_time": round(max(plugin_times), 3),
                        "count": len(plugin_times),
                    }

                    # 最慢和最快的插件
                    slowest = max(
                        plugin_executions, key=lambda p: p.get("execution_time", 0)
                    )
                    fastest = min(
                        plugin_executions, key=lambda p: p.get("execution_time", 0)
                    )

                    time_stats["plugin_execution"]["slowest"] = {
                        "name": slowest["plugin_name"],
                        "time": round(slowest.get("execution_time", 0), 3),
                    }
                    time_stats["plugin_execution"]["fastest"] = {
                        "name": fastest["plugin_name"],
                        "time": round(fastest.get("execution_time", 0), 3),
                    }

            # 节点执行时间（如果有记录）
            if "node_executions" in state:
                node_executions = state["node_executions"]
                node_times = [n.get("execution_time", 0) for n in node_executions]
                if node_times:
                    time_stats["node_execution"] = {
                        "total_time": round(sum(node_times), 3),
                        "average_time": round(sum(node_times) / len(node_times), 3),
                        "count": len(node_times),
                    }

        except Exception as e:
            logger.error(f"收集执行时间统计失败: {e}")
            time_stats["error"] = str(e)

        return time_stats

    def _collect_resource_usage_stats(self) -> Dict[str, Any]:
        """收集资源使用统计

        Returns:
            Dict[str, Any]: 资源使用统计
        """
        resource_stats = {}

        try:
            # 内存使用
            memory_stats = self._get_memory_stats()
            resource_stats["memory"] = memory_stats

            # CPU使用
            cpu_stats = self._get_cpu_stats()
            resource_stats["cpu"] = cpu_stats

            # 磁盘使用
            disk_stats = self._get_disk_stats()
            resource_stats["disk"] = disk_stats

            # 进程信息
            process_stats = self._get_process_stats()
            resource_stats["process"] = process_stats

        except Exception as e:
            logger.error(f"收集资源使用统计失败: {e}")
            resource_stats["error"] = str(e)

        return resource_stats

    def _get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计

        Returns:
            Dict[str, Any]: 内存统计
        """
        memory_stats = {}

        try:
            import psutil

            memory = psutil.virtual_memory()

            memory_stats["system"] = {
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "available_mb": round(memory.available / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "percent": memory.percent,
            }

            # 进程内存
            process = psutil.Process()
            process_memory = process.memory_info()

            memory_stats["process"] = {
                "rss_mb": round(process_memory.rss / (1024 * 1024), 2),
                "vms_mb": round(process_memory.vms / (1024 * 1024), 2),
            }

            # 内存详细信息
            if self._config["include_memory_profiling"]:
                memory_details = (
                    process.memory_full_info()
                    if hasattr(process, "memory_full_info")
                    else None
                )
                if memory_details:
                    memory_stats["process"]["details"] = {
                        "uss_mb": round(memory_details.uss / (1024 * 1024), 2),
                        "pss_mb": round(
                            getattr(memory_details, "pss", 0) / (1024 * 1024), 2
                        ),
                        "shared_mb": round(
                            getattr(memory_details, "shared", 0) / (1024 * 1024), 2
                        ),
                    }

        except ImportError:
            memory_stats = {"note": "psutil未安装，无法获取内存统计"}
        except Exception as e:
            memory_stats = {"error": str(e)}

        return memory_stats

    def _get_cpu_stats(self) -> Dict[str, Any]:
        """获取CPU统计

        Returns:
            Dict[str, Any]: CPU统计
        """
        cpu_stats = {}

        try:
            import psutil

            # 系统CPU
            cpu_stats["system"] = {
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "percent": psutil.cpu_percent(interval=1),
            }

            # 进程CPU
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            cpu_stats["process"] = {"percent": process_cpu}

            # CPU频率（如果可用）
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    cpu_stats["system"]["frequency"] = {
                        "current_mhz": round(cpu_freq.current, 2),
                        "min_mhz": round(cpu_freq.min, 2) if cpu_freq.min else None,
                        "max_mhz": round(cpu_freq.max, 2) if cpu_freq.max else None,
                    }
            except (AttributeError, OSError):
                pass

        except ImportError:
            cpu_stats = {"note": "psutil未安装，无法获取CPU统计"}
        except Exception as e:
            cpu_stats = {"error": str(e)}

        return cpu_stats

    def _get_disk_stats(self) -> Dict[str, Any]:
        """获取磁盘统计

        Returns:
            Dict[str, Any]: 磁盘统计
        """
        disk_stats = {}

        try:
            import psutil

            # 当前目录的磁盘使用情况
            disk = psutil.disk_usage(os.getcwd())
            disk_stats["current_directory"] = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 1),
            }

            # 磁盘I/O统计
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    disk_stats["io"] = {
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count,
                        "read_bytes_mb": round(disk_io.read_bytes / (1024**2), 2),
                        "write_bytes_mb": round(disk_io.write_bytes / (1024**2), 2),
                    }
            except (AttributeError, OSError):
                pass

        except ImportError:
            disk_stats = {"note": "psutil未安装，无法获取磁盘统计"}
        except Exception as e:
            disk_stats = {"error": str(e)}

        return disk_stats

    def _get_process_stats(self) -> Dict[str, Any]:
        """获取进程统计

        Returns:
            Dict[str, Any]: 进程统计
        """
        process_stats = {}

        try:
            import psutil

            process = psutil.Process()

            # 基本进程信息
            process_stats["basic"] = {
                "pid": process.pid,
                "name": process.name(),
                "status": process.status(),
                "create_time": datetime.fromtimestamp(
                    process.create_time()
                ).isoformat(),
                "cwd": process.cwd(),
            }

            # 线程数
            process_stats["threads"] = {"count": process.num_threads()}

            # 文件描述符
            if hasattr(process, "num_fds"):
                try:
                    process_stats["file_descriptors"] = {
                        "count": process.num_fds()  # type: ignore[attr-defined]
                    }
                except (AttributeError, OSError):
                    pass

            # 网络连接
            try:
                connections = process.connections()
                process_stats["network"] = {"connections_count": len(connections)}
            except (OSError, psutil.AccessDenied):
                pass

        except ImportError:
            process_stats = {"note": "psutil未安装，无法获取进程统计"}
        except Exception as e:
            process_stats = {"error": str(e)}

        return process_stats

    def _collect_node_performance_stats(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """收集节点性能统计

        Args:
            state: 当前工作流状态

        Returns:
            Dict[str, Any]: 节点性能统计
        """
        node_stats = {}

        try:
            # 节点执行记录
            if "node_executions" in state:
                node_executions = state["node_executions"]

                # 按节点类型统计
                node_types: Dict[str, List[Dict[str, Any]]] = {}
                for execution in node_executions:
                    node_type = execution.get("node_type", "unknown")
                    if node_type not in node_types:
                        node_types[node_type] = []
                    node_types[node_type].append(execution)

                # 计算每种节点类型的统计
                for node_type, executions in node_types.items():
                    times = [e.get("execution_time", 0) for e in executions]
                    node_stats[node_type] = {
                        "count": len(executions),
                        "total_time": round(sum(times), 3),
                        "average_time": (
                            round(sum(times) / len(times), 3) if times else 0
                        ),
                        "min_time": round(min(times), 3) if times else 0,
                        "max_time": round(max(times), 3) if times else 0,
                    }

            # 节点错误统计
            if "node_errors" in state:
                node_errors = state["node_errors"]
                error_stats: Dict[str, int] = {}
                for error in node_errors:
                    node_type = error.get("node_type", "unknown")
                    error_stats[node_type] = error_stats.get(node_type, 0) + 1

                node_stats["errors"] = error_stats

        except Exception as e:
            logger.error(f"收集节点性能统计失败: {e}")
            node_stats["error"] = str(e)

        return node_stats

    def _collect_plugin_performance_stats(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """收集插件性能统计

        Args:
            state: 当前工作流状态

        Returns:
            Dict[str, Any]: 插件性能统计
        """
        plugin_stats = {}

        try:
            if "plugin_executions" in state:
                plugin_executions = state["plugin_executions"]

                # 按插件类型统计
                plugin_types: Dict[str, List[Dict[str, Any]]] = {}
                for execution in plugin_executions:
                    plugin_type = execution.get("plugin_type", "unknown")
                    if plugin_type not in plugin_types:
                        plugin_types[plugin_type] = []
                    plugin_types[plugin_type].append(execution)

                # 计算每种插件类型的统计
                for plugin_type, executions in plugin_types.items():
                    times = [e.get("execution_time", 0) for e in executions]
                    plugin_stats[plugin_type] = {
                        "count": len(executions),
                        "total_time": round(sum(times), 3),
                        "average_time": (
                            round(sum(times) / len(times), 3) if times else 0
                        ),
                        "min_time": round(min(times), 3) if times else 0,
                        "max_time": round(max(times), 3) if times else 0,
                    }

                # 成功率统计
                successful = len(
                    [e for e in plugin_executions if e.get("status") == "success"]
                )
                plugin_stats["success_rate"] = (
                    round(successful / len(plugin_executions) * 100, 2)
                    if plugin_executions
                    else 0.0
                )

            # 插件错误统计
            if "plugin_errors" in state:
                plugin_errors = state["plugin_errors"]
                plugin_stats["error_count"] = len(plugin_errors)
                plugin_stats["error_details"] = plugin_errors

        except Exception as e:
            logger.error(f"收集插件性能统计失败: {e}")
            plugin_stats = {"error": str(e)}

        return plugin_stats

    def _collect_workflow_stats(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """收集工作流统计

        Args:
            state: 当前工作流状态

        Returns:
            Dict[str, Any]: 工作流统计
        """
        workflow_stats = {}

        try:
            # 基本统计
            workflow_stats["iteration_count"] = state.get("iteration_count", 0)
            workflow_stats["max_iterations"] = state.get("max_iterations", 0)

            # 消息统计
            if "messages" in state:
                messages = state["messages"]
                if isinstance(messages, list):
                    workflow_stats["message_count"] = len(messages)

                    # 按消息类型统计
                    message_types: Dict[str, int] = {}
                    for message in messages:
                        msg_type = message.get("role", "unknown")
                        message_types[msg_type] = message_types.get(msg_type, 0) + 1

                    workflow_stats["message_types"] = message_types

            # 工具调用统计
            if "tool_calls" in state:
                tool_calls = state["tool_calls"]
                if isinstance(tool_calls, list):
                    workflow_stats["tool_call_count"] = len(tool_calls)

                    # 按工具类型统计
                    tool_types: Dict[str, int] = {}
                    for call in tool_calls:
                        tool_name = call.get("name", "unknown")
                        tool_types[tool_name] = tool_types.get(tool_name, 0) + 1

                    workflow_stats["tool_types"] = tool_types

            # 工具结果统计
            if "tool_results" in state:
                tool_results = state["tool_results"]
                if isinstance(tool_results, list):
                    successful = len([r for r in tool_results if not r.get("error")])
                    workflow_stats["tool_results"] = {
                        "total": len(tool_results),
                        "successful": successful,
                        "failed": len(tool_results) - successful,
                    }

            # 错误统计
            if "errors" in state:
                errors = state["errors"]
                workflow_stats["error_count"] = len(errors)

            # 状态大小统计
            state_size = len(str(state))
            workflow_stats["state_size_bytes"] = state_size
            workflow_stats["state_size_kb"] = round(state_size / 1024, 2)

        except Exception as e:
            logger.error(f"收集工作流统计失败: {e}")
            workflow_stats["error"] = str(e)

        return workflow_stats

    def _generate_stats_report(
        self, stats: Dict[str, Any], context: PluginContext
    ) -> str:
        """生成统计报告

        Args:
            stats: 统计数据
            context: 执行上下文

        Returns:
            str: 统计报告
        """
        lines = []

        # 标题
        lines.append("# 工作流执行统计报告")
        lines.append("")

        # 基本信息
        lines.append("## 基本信息")
        lines.append(f"- **工作流ID**: {stats['workflow_id']}")
        lines.append(f"- **收集时间**: {stats['collection_timestamp']}")
        if stats.get("thread_id"):
            lines.append(f"- **线程ID**: {stats['thread_id']}")
        if stats.get("session_id"):
            lines.append(f"- **会话ID**: {stats['session_id']}")
        lines.append("")

        # 执行时间统计
        if "execution_time" in stats:
            lines.append("## 执行时间统计")
            time_stats = stats["execution_time"]

            if "total_execution_time" in time_stats:
                lines.append(
                    f"- **总执行时间**: {time_stats['total_execution_time_formatted']}"
                )

            if "plugin_execution" in time_stats:
                plugin_exec = time_stats["plugin_execution"]
                lines.append(
                    f"- **插件执行时间**: {plugin_exec['total_time']}s (平均: {plugin_exec['average_time']}s)"
                )
                lines.append(
                    f"  - 最慢插件: {plugin_exec['slowest']['name']} ({plugin_exec['slowest']['time']}s)"
                )
                lines.append(
                    f"  - 最快插件: {plugin_exec['fastest']['name']} ({plugin_exec['fastest']['time']}s)"
                )

            lines.append("")

        # 资源使用统计
        if "resource_usage" in stats:
            lines.append("## 资源使用统计")
            resource_stats = stats["resource_usage"]

            # 内存
            if "memory" in resource_stats:
                memory = resource_stats["memory"]
                if "system" in memory:
                    sys_mem = memory["system"]
                    lines.append(
                        f"- **系统内存**: {sys_mem['used_mb']}MB / {sys_mem['total_mb']}MB ({sys_mem['percent']}%)"
                    )

                if "process" in memory:
                    proc_mem = memory["process"]
                    lines.append(f"- **进程内存**: {proc_mem['rss_mb']}MB RSS")

            # CPU
            if "cpu" in resource_stats:
                cpu = resource_stats["cpu"]
                if "system" in cpu:
                    sys_cpu = cpu["system"]
                    lines.append(
                        f"- **系统CPU**: {sys_cpu['percent']}% ({sys_cpu['count']} 核心)"
                    )

                if "process" in cpu:
                    proc_cpu = cpu["process"]
                    lines.append(f"- **进程CPU**: {proc_cpu['percent']}%")

            lines.append("")

        # 插件性能统计
        if "plugin_performance" in stats:
            lines.append("## 插件性能统计")
            plugin_perf = stats["plugin_performance"]

            if "success_rate" in plugin_perf:
                lines.append(f"- **成功率**: {plugin_perf['success_rate']}%")

            for plugin_type, stats_data in plugin_perf.items():
                if isinstance(stats_data, dict) and "count" in stats_data:
                    lines.append(
                        f"- **{plugin_type}**: {stats_data['count']} 次，平均 {stats_data['average_time']}s"
                    )

            lines.append("")

        # 工作流统计
        if "workflow_stats" in stats:
            lines.append("## 工作流统计")
            workflow_stats = stats["workflow_stats"]

            if "iteration_count" in workflow_stats:
                lines.append(f"- **迭代次数**: {workflow_stats['iteration_count']}")

            if "message_count" in workflow_stats:
                lines.append(f"- **消息数量**: {workflow_stats['message_count']}")

            if "tool_call_count" in workflow_stats:
                lines.append(f"- **工具调用次数**: {workflow_stats['tool_call_count']}")

            if "error_count" in workflow_stats:
                lines.append(f"- **错误数量**: {workflow_stats['error_count']}")

            if "state_size_kb" in workflow_stats:
                lines.append(f"- **状态大小**: {workflow_stats['state_size_kb']} KB")

            lines.append("")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """格式化持续时间

        Args:
            seconds: 秒数

        Returns:
            str: 格式化的时间字符串
        """
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.0f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            return f"{hours}h {remaining_minutes}m"

    def _save_stats_to_file(
        self, stats: Dict[str, Any], context: PluginContext
    ) -> None:
        """保存统计到文件

        Args:
            stats: 统计数据
            context: 执行上下文
        """
        try:
            output_dir = self._config["output_directory"]
            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"execution_stats_{context.workflow_id}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            # 保存文件
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"执行统计已保存到: {filepath}")

        except Exception as e:
            logger.error(f"保存执行统计失败: {e}")
