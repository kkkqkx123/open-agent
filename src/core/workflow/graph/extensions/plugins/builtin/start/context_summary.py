"""上下文摘要插件

生成项目上下文摘要，包括文件结构、Git状态和最近变更。
"""

import os
import subprocess
from src.interfaces.dependency_injection import get_logger
from pathlib import Path
from typing import Dict, Any, List

from src.interfaces.workflow.plugins import IStartPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class ContextSummaryPlugin(IStartPlugin):
    """上下文摘要插件
    
    在工作流开始时生成项目上下文摘要，帮助理解当前项目状态。
    """
    
    def __init__(self):
        """初始化上下文摘要插件"""
        self._config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="context_summary",
            version="1.0.0",
            description="生成项目上下文摘要，包括文件结构、Git状态和最近变更",
            author="system",
            plugin_type=PluginType.START,
            config_schema={
                "type": "object",
                "properties": {
                    "include_file_structure": {
                        "type": "boolean",
                        "description": "是否包含文件结构摘要",
                        "default": True
                    },
                    "include_recent_changes": {
                        "type": "boolean", 
                        "description": "是否包含最近变更",
                        "default": True
                    },
                    "include_git_status": {
                        "type": "boolean",
                        "description": "是否包含Git状态",
                        "default": True
                    },
                    "max_summary_length": {
                        "type": "integer",
                        "description": "最大摘要长度",
                        "default": 1000,
                        "minimum": 100,
                        "maximum": 5000
                    },
                    "file_patterns": {
                        "type": "array",
                        "description": "要包含的文件模式",
                        "default": ["*.py", "*.yaml", "*.yml", "*.md", "*.txt", "*.json"]
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "description": "要排除的文件模式",
                        "default": ["__pycache__", "*.pyc", ".git", "node_modules"]
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "最大文件数量",
                        "default": 50,
                        "minimum": 10,
                        "maximum": 200
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
            "include_file_structure": config.get("include_file_structure", True),
            "include_recent_changes": config.get("include_recent_changes", True),
            "include_git_status": config.get("include_git_status", True),
            "max_summary_length": config.get("max_summary_length", 1000),
            "file_patterns": config.get("file_patterns", ["*.py", "*.yaml", "*.yml", "*.md", "*.txt", "*.json"]),
            "exclude_patterns": config.get("exclude_patterns", ["__pycache__", "*.pyc", ".git", "node_modules"]),
            "max_files": config.get("max_files", 50)
        }
        
        logger.debug("上下文摘要插件初始化完成")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        logger.info("开始生成上下文摘要")
        
        summary_parts = []
        
        try:
            # 文件结构摘要
            if self._config["include_file_structure"]:
                file_structure = self._get_file_structure()
                if file_structure:
                    summary_parts.append(f"## 项目文件结构\n{file_structure}")
            
            # Git状态摘要
            if self._config["include_git_status"]:
                git_status = self._get_git_status()
                if git_status:
                    summary_parts.append(f"## Git状态\n{git_status}")
            
            # 最近变更
            if self._config["include_recent_changes"]:
                recent_changes = self._get_recent_changes()
                if recent_changes:
                    summary_parts.append(f"## 最近变更\n{recent_changes}")
            
            # 项目统计信息
            project_stats = self._get_project_stats()
            if project_stats:
                summary_parts.append(f"## 项目统计\n{project_stats}")
            
            # 生成完整摘要
            summary = "\n\n".join(summary_parts)
            max_length = self._config["max_summary_length"]
            
            if len(summary) > max_length:
                summary = summary[:max_length] + "\n... (摘要已截断)"
            
            # 更新状态
            state["context_summary"] = summary
            state["start_metadata"] = state.get("start_metadata", {})
            state["start_metadata"]["context_summary_generated"] = True
            state["start_metadata"]["context_summary_length"] = len(summary)
            
            logger.info(f"上下文摘要生成完成，长度: {len(summary)} 字符")
            
        except Exception as e:
            logger.error(f"生成上下文摘要失败: {e}")
            state["start_metadata"] = state.get("start_metadata", {})
            state["start_metadata"]["context_summary_error"] = str(e)
        
        return state
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        return True
    
    def _get_file_structure(self) -> str:
        """获取文件结构摘要
        
        Returns:
            str: 文件结构摘要
        """
        try:
            current_dir = Path.cwd()
            file_patterns = self._config["file_patterns"]
            exclude_patterns = self._config["exclude_patterns"]
            max_files = self._config["max_files"]
            
            files = []
            
            # 收集匹配的文件
            for pattern in file_patterns:
                for file_path in current_dir.rglob(pattern):
                    # 检查排除模式
                    if any(exclude in str(file_path) for exclude in exclude_patterns):
                        continue
                    
                    # 转换为相对路径
                    rel_path = file_path.relative_to(current_dir)
                    files.append(str(rel_path))
                    
                    if len(files) >= max_files:
                        break
                
                if len(files) >= max_files:
                    break
            
            if not files:
                return "未找到匹配的文件"
            
            # 按目录层级排序
            files.sort(key=lambda x: (x.count('/'), x))
            
            # 生成树状结构
            tree_lines = []
            current_depth = 0
            
            for file_path in files:
                depth = file_path.count('/')
                parts = file_path.split('/')
                
                # 调整深度
                if depth > current_depth:
                    tree_lines.extend(['│   ' * i + '├── ' + parts[i] for i in range(current_depth, depth)])
                elif depth < current_depth:
                    tree_lines.append('│   ' * depth + '├── ' + parts[-1])
                else:
                    tree_lines.append('│   ' * depth + '├── ' + parts[-1])
                
                current_depth = depth
            
            return '\n'.join(tree_lines[:max_files])
            
        except Exception as e:
            logger.error(f"获取文件结构失败: {e}")
            return f"获取文件结构失败: {e}"
    
    def _get_git_status(self) -> str:
        """获取Git状态
        
        Returns:
            str: Git状态信息
        """
        try:
            # 检查是否是Git仓库
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                return "不是Git仓库"
            
            # 获取Git状态
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                
                # 统计变更类型
                stats = {
                    'modified': 0,
                    'added': 0,
                    'deleted': 0,
                    'untracked': 0,
                    'renamed': 0
                }
                
                for line in lines:
                    if line.startswith(' M'):
                        stats['modified'] += 1
                    elif line.startswith('A '):
                        stats['added'] += 1
                    elif line.startswith('D '):
                        stats['deleted'] += 1
                    elif line.startswith('??'):
                        stats['untracked'] += 1
                    elif line.startswith('R '):
                        stats['renamed'] += 1
                
                status_lines = [f"Git仓库状态:"]
                if stats['modified'] > 0:
                    status_lines.append(f"  修改: {stats['modified']} 个文件")
                if stats['added'] > 0:
                    status_lines.append(f"  新增: {stats['added']} 个文件")
                if stats['deleted'] > 0:
                    status_lines.append(f"  删除: {stats['deleted']} 个文件")
                if stats['untracked'] > 0:
                    status_lines.append(f"  未跟踪: {stats['untracked']} 个文件")
                if stats['renamed'] > 0:
                    status_lines.append(f"  重命名: {stats['renamed']} 个文件")
                
                if sum(stats.values()) == 0:
                    status_lines.append("  工作目录干净")
                
                return '\n'.join(status_lines)
            else:
                return "Git仓库状态: 工作目录干净"
                
        except Exception as e:
            logger.error(f"获取Git状态失败: {e}")
            return f"获取Git状态失败: {e}"
    
    def _get_recent_changes(self) -> str:
        """获取最近变更
        
        Returns:
            str: 最近变更信息
        """
        try:
            # 获取最近5次提交
            result = subprocess.run(
                ['git', 'log', '--oneline', '-5', '--pretty=format:%h %s (%an, %ar)'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('\n')
                return '\n'.join([f"  {commit}" for commit in commits])
            else:
                return "无法获取最近变更"
                
        except Exception as e:
            logger.error(f"获取最近变更失败: {e}")
            return f"获取最近变更失败: {e}"
    
    def _get_project_stats(self) -> str:
        """获取项目统计信息
        
        Returns:
            str: 项目统计信息
        """
        try:
            current_dir = Path.cwd()
            file_patterns = self._config["file_patterns"]
            exclude_patterns = self._config["exclude_patterns"]
            
            stats = {
                'total_files': 0,
                'by_extension': {},
                'total_size': 0
            }
            
            # 统计文件
            for pattern in file_patterns:
                for file_path in current_dir.rglob(pattern):
                    # 检查排除模式
                    if any(exclude in str(file_path) for exclude in exclude_patterns):
                        continue
                    
                    if file_path.is_file():
                        stats['total_files'] += 1
                        
                        # 按扩展名统计
                        ext = file_path.suffix.lower()
                        if ext:
                            stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                        
                        # 统计文件大小
                        try:
                            stats['total_size'] += file_path.stat().st_size
                        except (OSError, PermissionError):
                            pass
            
            # 格式化统计信息
            stats_lines = ["项目统计:"]
            stats_lines.append(f"  总文件数: {stats['total_files']}")
            
            if stats['by_extension']:
                stats_lines.append("  文件类型分布:")
                for ext, count in sorted(stats['by_extension'].items(), key=lambda x: x[1], reverse=True):
                    ext_name = ext if ext else '无扩展名'
                    stats_lines.append(f"    {ext_name}: {count}")
            
            # 格式化文件大小
            size_mb = stats['total_size'] / (1024 * 1024)
            if size_mb < 1:
                size_kb = stats['total_size'] / 1024
                stats_lines.append(f"  总大小: {size_kb:.1f} KB")
            else:
                stats_lines.append(f"  总大小: {size_mb:.1f} MB")
            
            return '\n'.join(stats_lines)
            
        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            return f"获取项目统计失败: {e}"