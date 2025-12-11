"""结果汇总插件

生成工作流执行结果的汇总报告。
"""

import os
import json
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List
from datetime import datetime

from src.interfaces.workflow.plugins import IEndPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class ResultSummaryPlugin(IEndPlugin):
    """结果汇总插件
    
    在工作流结束时生成执行结果汇总报告。
    """
    
    def __init__(self):
        """初始化结果汇总插件"""
        self._config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="result_summary",
            version="1.0.0",
            description="生成工作流执行结果的汇总报告",
            author="system",
            plugin_type=PluginType.END,
            config_schema={
                "type": "object",
                "properties": {
                    "include_tool_results": {
                        "type": "boolean",
                        "description": "是否包含工具执行结果",
                        "default": True
                    },
                    "include_error_analysis": {
                        "type": "boolean",
                        "description": "是否包含错误分析",
                        "default": True
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "是否包含改进建议",
                        "default": True
                    },
                    "output_format": {
                        "type": "string",
                        "description": "输出格式",
                        "enum": ["markdown", "json", "text"],
                        "default": "markdown"
                    },
                    "save_to_file": {
                        "type": "boolean",
                        "description": "是否保存到文件",
                        "default": True
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "输出目录",
                        "default": "./output"
                    },
                    "max_summary_length": {
                        "type": "integer",
                        "description": "最大摘要长度",
                        "default": 5000,
                        "minimum": 1000,
                        "maximum": 20000
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
            "include_tool_results": config.get("include_tool_results", True),
            "include_error_analysis": config.get("include_error_analysis", True),
            "include_recommendations": config.get("include_recommendations", True),
            "output_format": config.get("output_format", "markdown"),
            "save_to_file": config.get("save_to_file", True),
            "output_directory": config.get("output_directory", "./output"),
            "max_summary_length": config.get("max_summary_length", 5000)
        }
        
        logger.debug("结果汇总插件初始化完成")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        logger.info("开始生成结果汇总")
        
        try:
            # 生成汇总报告
            summary = self._generate_summary(state, context)
            
            # 保存到文件
            if self._config["save_to_file"]:
                self._save_summary_to_file(summary, context)
            
            # 更新状态
            state["result_summary"] = summary
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["result_summary_generated"] = True
            state["end_metadata"]["result_summary_length"] = len(summary)
            
            logger.info(f"结果汇总生成完成，长度: {len(summary)} 字符")
            
        except Exception as e:
            logger.error(f"生成结果汇总失败: {e}")
            state["end_metadata"] = state.get("end_metadata", {})
            state["end_metadata"]["result_summary_error"] = str(e)
        
        return state
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        return True
    
    def _generate_summary(self, state: Dict[str, Any], context: PluginContext) -> str:
        """生成汇总报告
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            str: 汇总报告
        """
        output_format = self._config["output_format"]
        
        if output_format == "markdown":
            return self._generate_markdown_summary(state, context)
        elif output_format == "json":
            return self._generate_json_summary(state, context)
        elif output_format == "text":
            return self._generate_text_summary(state, context)
        else:
            return self._generate_markdown_summary(state, context)
    
    def _generate_markdown_summary(self, state: Dict[str, Any], context: PluginContext) -> str:
        """生成Markdown格式的汇总报告
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            str: Markdown格式的汇总报告
        """
        lines = []
        
        # 标题
        lines.append("# 工作流执行结果汇总")
        lines.append("")
        
        # 基本信息
        lines.append("## 基本信息")
        lines.append(f"- **工作流ID**: {context.workflow_id}")
        if context.thread_id:
            lines.append(f"- **线程ID**: {context.thread_id}")
        if context.session_id:
            lines.append(f"- **会话ID**: {context.session_id}")
        lines.append(f"- **完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 执行概览
        lines.append("## 执行概览")
        execution_overview = self._get_execution_overview(state, context)
        lines.extend(execution_overview)
        lines.append("")
        
        # 输入输出
        lines.append("## 输入输出")
        input_output = self._get_input_output_summary(state)
        lines.extend(input_output)
        lines.append("")
        
        # 工具执行结果
        if self._config["include_tool_results"]:
            lines.append("## 工具执行结果")
            tool_results = self._get_tool_results_summary(state)
            lines.extend(tool_results)
            lines.append("")
        
        # 错误分析
        if self._config["include_error_analysis"]:
            lines.append("## 错误分析")
            error_analysis = self._get_error_analysis(state)
            lines.extend(error_analysis)
            lines.append("")
        
        # 改进建议
        if self._config["include_recommendations"]:
            lines.append("## 改进建议")
            recommendations = self._get_recommendations(state)
            lines.extend(recommendations)
            lines.append("")
        
        # 性能统计
        lines.append("## 性能统计")
        performance_stats = self._get_performance_stats(state)
        lines.extend(performance_stats)
        lines.append("")
        
        # 生成完整报告
        summary = '\n'.join(lines)
        max_length = self._config["max_summary_length"]
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "\n\n... (报告已截断)"
        
        return summary
    
    def _generate_json_summary(self, state: Dict[str, Any], context: PluginContext) -> str:
        """生成JSON格式的汇总报告
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            str: JSON格式的汇总报告
        """
        summary_data = {
            "workflow_id": context.workflow_id,
            "thread_id": context.thread_id,
            "session_id": context.session_id,
            "completion_time": datetime.now().isoformat(),
            "execution_overview": self._get_execution_overview_data(state, context),
            "input_output": self._get_input_output_data(state),
            "tool_results": self._get_tool_results_data(state) if self._config["include_tool_results"] else None,
            "error_analysis": self._get_error_analysis_data(state) if self._config["include_error_analysis"] else None,
            "recommendations": self._get_recommendations_data(state) if self._config["include_recommendations"] else None,
            "performance_stats": self._get_performance_stats_data(state)
        }
        
        return json.dumps(summary_data, ensure_ascii=False, indent=2)
    
    def _generate_text_summary(self, state: Dict[str, Any], context: PluginContext) -> str:
        """生成纯文本格式的汇总报告
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            str: 纯文本格式的汇总报告
        """
        lines = []
        
        # 标题
        lines.append("=" * 50)
        lines.append("工作流执行结果汇总")
        lines.append("=" * 50)
        lines.append("")
        
        # 基本信息
        lines.append("基本信息:")
        lines.append(f"  工作流ID: {context.workflow_id}")
        if context.thread_id:
            lines.append(f"  线程ID: {context.thread_id}")
        if context.session_id:
            lines.append(f"  会话ID: {context.session_id}")
        lines.append(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 执行概览
        lines.append("执行概览:")
        execution_overview = self._get_execution_overview(state, context)
        for line in execution_overview:
            if line.startswith("-"):
                lines.append(f"  {line[2:]}")
        lines.append("")
        
        # 输入输出
        lines.append("输入输出:")
        input_output = self._get_input_output_summary(state)
        for line in input_output:
            if line.startswith("-"):
                lines.append(f"  {line[2:]}")
        lines.append("")
        
        # 工具执行结果
        if self._config["include_tool_results"]:
            lines.append("工具执行结果:")
            tool_results = self._get_tool_results_summary(state)
            for line in tool_results:
                if line.startswith("-"):
                    lines.append(f"  {line[2:]}")
            lines.append("")
        
        # 错误分析
        if self._config["include_error_analysis"]:
            lines.append("错误分析:")
            error_analysis = self._get_error_analysis(state)
            for line in error_analysis:
                if line.startswith("-"):
                    lines.append(f"  {line[2:]}")
            lines.append("")
        
        # 改进建议
        if self._config["include_recommendations"]:
            lines.append("改进建议:")
            recommendations = self._get_recommendations(state)
            for line in recommendations:
                if line.startswith("-"):
                    lines.append(f"  {line[2:]}")
            lines.append("")
        
        # 性能统计
        lines.append("性能统计:")
        performance_stats = self._get_performance_stats(state)
        for line in performance_stats:
            if line.startswith("-"):
                lines.append(f"  {line[2:]}")
        
        return '\n'.join(lines)
    
    def _get_execution_overview(self, state: Dict[str, Any], context: PluginContext) -> List[str]:
        """获取执行概览
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            List[str]: 执行概览列表
        """
        lines = []
        
        # 执行状态
        success = not state.get("errors", [])
        lines.append(f"- **执行状态**: {'成功' if success else '失败'}")
        
        # 执行时间
        if context.execution_start_time:
            import time
            execution_time = time.time() - context.execution_start_time
            lines.append(f"- **执行时间**: {execution_time:.2f} 秒")
        
        # 迭代次数
        if "iteration_count" in state:
            lines.append(f"- **迭代次数**: {state['iteration_count']}")
        
        # 插件执行情况
        if "plugin_executions" in state:
            plugin_executions = state["plugin_executions"]
            total_plugins = len(plugin_executions)
            successful_plugins = len([p for p in plugin_executions if p.get("status") == "success"])
            lines.append(f"- **插件执行**: {successful_plugins}/{total_plugins} 成功")
        
        return lines
    
    def _get_execution_overview_data(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """获取执行概览数据
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行概览数据
        """
        data = {}
        
        # 执行状态
        data["success"] = not state.get("errors", [])
        
        # 执行时间
        if context.execution_start_time:
            import time
            data["execution_time"] = time.time() - context.execution_start_time
        
        # 迭代次数
        if "iteration_count" in state:
            data["iteration_count"] = state["iteration_count"]
        
        # 插件执行情况
        if "plugin_executions" in state:
            plugin_executions = state["plugin_executions"]
            data["plugin_executions"] = {
                "total": len(plugin_executions),
                "successful": len([p for p in plugin_executions if p.get("status") == "success"]),
                "failed": len([p for p in plugin_executions if p.get("status") == "error"])
            }
        
        return data
    
    def _get_input_output_summary(self, state: Dict[str, Any]) -> List[str]:
        """获取输入输出摘要
        
        Args:
            state: 当前工作流状态
            
        Returns:
            List[str]: 输入输出摘要列表
        """
        lines = []
        
        # 输入
        if "input" in state:
            input_text = str(state["input"])
            if len(input_text) > 200:
                input_text = input_text[:200] + "..."
            lines.append(f"- **输入**: {input_text}")
        
        # 输出
        if "output" in state:
            output_text = str(state["output"])
            if len(output_text) > 200:
                output_text = output_text[:200] + "..."
            lines.append(f"- **输出**: {output_text}")
        
        # 消息数量
        if "messages" in state:
            messages = state["messages"]
            if isinstance(messages, list):
                lines.append(f"- **消息数量**: {len(messages)}")
        
        return lines
    
    def _get_input_output_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """获取输入输出数据
        
        Args:
            state: 当前工作流状态
            
        Returns:
            Dict[str, Any]: 输入输出数据
        """
        data = {}
        
        # 输入
        if "input" in state:
            data["input"] = str(state["input"])
        
        # 输出
        if "output" in state:
            data["output"] = str(state["output"])
        
        # 消息数量
        if "messages" in state:
            messages = state["messages"]
            if isinstance(messages, list):
                data["message_count"] = len(messages)
        
        return data
    
    def _get_tool_results_summary(self, state: Dict[str, Any]) -> List[str]:
        """获取工具执行结果摘要
        
        Args:
            state: 当前工作流状态
            
        Returns:
            List[str]: 工具执行结果摘要列表
        """
        lines = []
        
        # 工具调用
        if "tool_calls" in state:
            tool_calls = state["tool_calls"]
            if isinstance(tool_calls, list):
                lines.append(f"- **工具调用次数**: {len(tool_calls)}")
                
                # 按工具类型统计
                tool_stats = {}
                for call in tool_calls:
                    tool_name = call.get("name", "unknown")
                    tool_stats[tool_name] = tool_stats.get(tool_name, 0) + 1
                
                for tool_name, count in tool_stats.items():
                    lines.append(f"  - {tool_name}: {count} 次")
        
        # 工具结果
        if "tool_results" in state:
            tool_results = state["tool_results"]
            if isinstance(tool_results, list):
                successful_results = len([r for r in tool_results if not r.get("error")])
                lines.append(f"- **工具结果**: {successful_results}/{len(tool_results)} 成功")
        
        return lines
    
    def _get_tool_results_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """获取工具执行结果数据
        
        Args:
            state: 当前工作流状态
            
        Returns:
            Dict[str, Any]: 工具执行结果数据
        """
        data = {}
        
        # 工具调用
        if "tool_calls" in state:
            tool_calls = state["tool_calls"]
            if isinstance(tool_calls, list):
                data["tool_calls"] = {
                    "total": len(tool_calls),
                    "by_tool": {}
                }
                
                for call in tool_calls:
                    tool_name = call.get("name", "unknown")
                    data["tool_calls"]["by_tool"][tool_name] = data["tool_calls"]["by_tool"].get(tool_name, 0) + 1
        
        # 工具结果
        if "tool_results" in state:
            tool_results = state["tool_results"]
            if isinstance(tool_results, list):
                successful_results = len([r for r in tool_results if not r.get("error")])
                data["tool_results"] = {
                    "total": len(tool_results),
                    "successful": successful_results,
                    "failed": len(tool_results) - successful_results
                }
        
        return data
    
    def _get_error_analysis(self, state: Dict[str, Any]) -> List[str]:
        """获取错误分析
        
        Args:
            state: 当前工作流状态
            
        Returns:
            List[str]: 错误分析列表
        """
        lines = []
        
        # 错误列表
        errors = state.get("errors", [])
        if errors:
            lines.append(f"- **错误数量**: {len(errors)}")
            
            # 错误类型统计
            error_types = {}
            for error in errors:
                error_str = str(error)
                if ":" in error_str:
                    error_type = error_str.split(":")[0]
                else:
                    error_type = "unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                lines.append(f"  - {error_type}: {count} 次")
        else:
            lines.append("- **错误数量**: 0")
        
        # 插件错误
        if "plugin_errors" in state:
            plugin_errors = state["plugin_errors"]
            if plugin_errors:
                lines.append(f"- **插件错误**: {len(plugin_errors)} 个插件")
                for plugin_name, error in plugin_errors.items():
                    lines.append(f"  - {plugin_name}: {str(error)[:100]}...")
        
        return lines
    
    def _get_error_analysis_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """获取错误分析数据
        
        Args:
            state: 当前工作流状态
            
        Returns:
            Dict[str, Any]: 错误分析数据
        """
        data = {}
        
        # 错误列表
        errors = state.get("errors", [])
        data["errors"] = {
            "total": len(errors),
            "by_type": {}
        }
        
        for error in errors:
            error_str = str(error)
            if ":" in error_str:
                error_type = error_str.split(":")[0]
            else:
                error_type = "unknown"
            data["errors"]["by_type"][error_type] = data["errors"]["by_type"].get(error_type, 0) + 1
        
        # 插件错误
        if "plugin_errors" in state:
            plugin_errors = state["plugin_errors"]
            data["plugin_errors"] = {
                "total": len(plugin_errors),
                "details": plugin_errors
            }
        
        return data
    
    def _get_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """获取改进建议
        
        Args:
            state: 当前工作流状态
            
        Returns:
            List[str]: 改进建议列表
        """
        lines = []
        
        # 基于执行时间的建议
        if "plugin_executions" in state:
            plugin_executions = state["plugin_executions"]
            slow_plugins = [p for p in plugin_executions if p.get("execution_time", 0) > 5.0]
            if slow_plugins:
                lines.append("- **性能优化建议**:")
                for plugin in slow_plugins:
                    lines.append(f"  - 考虑优化 {plugin['plugin_name']} 插件，执行时间较长 ({plugin['execution_time']:.2f}s)")
        
        # 基于错误的建议
        errors = state.get("errors", [])
        if errors:
            lines.append("- **错误处理建议**:")
            lines.append("  - 检查输入数据格式和完整性")
            lines.append("  - 增加错误重试机制")
            lines.append("  - 改进错误日志记录")
        
        # 基于工具使用的建议
        if "tool_calls" in state:
            tool_calls = state["tool_calls"]
            if len(tool_calls) > 10:
                lines.append("- **工具使用建议**:")
                lines.append("  - 考虑减少工具调用次数")
                lines.append("  - 优化工具参数以提高效率")
        
        # 通用建议
        if not lines:
            lines.append("- 工作流执行良好，暂无特别建议")
        
        return lines
    
    def _get_recommendations_data(self, state: Dict[str, Any]) -> List[str]:
        """获取改进建议数据
        
        Args:
            state: 当前工作流状态
            
        Returns:
            List[str]: 改进建议数据列表
        """
        recommendations = []
        
        # 基于执行时间的建议
        if "plugin_executions" in state:
            plugin_executions = state["plugin_executions"]
            slow_plugins = [p for p in plugin_executions if p.get("execution_time", 0) > 5.0]
            if slow_plugins:
                for plugin in slow_plugins:
                    recommendations.append({
                        "type": "performance",
                        "plugin": plugin['plugin_name'],
                        "suggestion": f"优化插件执行性能，当前耗时 {plugin['execution_time']:.2f}s"
                    })
        
        # 基于错误的建议
        errors = state.get("errors", [])
        if errors:
            recommendations.extend([
                {"type": "error_handling", "suggestion": "检查输入数据格式和完整性"},
                {"type": "error_handling", "suggestion": "增加错误重试机制"},
                {"type": "error_handling", "suggestion": "改进错误日志记录"}
            ])
        
        # 基于工具使用的建议
        if "tool_calls" in state:
            tool_calls = state["tool_calls"]
            if len(tool_calls) > 10:
                recommendations.extend([
                    {"type": "tool_usage", "suggestion": "考虑减少工具调用次数"},
                    {"type": "tool_usage", "suggestion": "优化工具参数以提高效率"}
                ])
        
        return recommendations
    
    def _get_performance_stats(self, state: Dict[str, Any]) -> List[str]:
        """获取性能统计
        
        Args:
            state: 当前工作流状态
            
        Returns:
            List[str]: 性能统计列表
        """
        lines = []
        
        # 插件执行统计
        if "plugin_executions" in state:
            plugin_executions = state["plugin_executions"]
            
            total_time = sum(p.get("execution_time", 0) for p in plugin_executions)
            lines.append(f"- **总插件执行时间**: {total_time:.2f} 秒")
            
            if plugin_executions:
                avg_time = total_time / len(plugin_executions)
                lines.append(f"- **平均插件执行时间**: {avg_time:.2f} 秒")
                
                # 最慢的插件
                slowest = max(plugin_executions, key=lambda p: p.get("execution_time", 0))
                lines.append(f"- **最慢插件**: {slowest['plugin_name']} ({slowest['execution_time']:.2f}s)")
        
        # 内存使用情况
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            lines.append(f"- **内存使用**: {memory_mb:.1f} MB")
        except ImportError:
            lines.append("- **内存使用**: psutil未安装，无法获取内存信息")
        
        return lines
    
    def _get_performance_stats_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """获取性能统计数据
        
        Args:
            state: 当前工作流状态
            
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        data = {}
        
        # 插件执行统计
        if "plugin_executions" in state:
            plugin_executions = state["plugin_executions"]
            
            total_time = sum(p.get("execution_time", 0) for p in plugin_executions)
            data["plugin_executions"] = {
                "total_time": total_time,
                "average_time": total_time / len(plugin_executions) if plugin_executions else 0,
                "slowest_plugin": max(plugin_executions, key=lambda p: p.get("execution_time", 0)) if plugin_executions else None
            }
        
        # 内存使用情况
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            data["memory_usage"] = {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024)
            }
        except ImportError:
            data["memory_usage"] = {"note": "psutil未安装，无法获取内存信息"}
        
        return data
    
    def _save_summary_to_file(self, summary: str, context: PluginContext) -> None:
        """保存汇总报告到文件
        
        Args:
            summary: 汇总报告内容
            context: 执行上下文
        """
        try:
            output_dir = self._config["output_directory"]
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workflow_summary_{context.workflow_id}_{timestamp}.{self._config['output_format']}"
            filepath = os.path.join(output_dir, filename)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"汇总报告已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存汇总报告失败: {e}")