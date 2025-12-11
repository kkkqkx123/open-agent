"""元数据收集插件

收集系统信息、项目信息和用户信息等元数据。
"""

import os
import sys
import platform
import getpass
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any
from datetime import datetime

from src.interfaces.workflow.plugins import IStartPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class MetadataCollectorPlugin(IStartPlugin):
    """元数据收集插件
    
    在工作流开始时收集各种元数据信息。
    """
    
    def __init__(self):
        """初始化元数据收集插件"""
        self._config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="metadata_collector",
            version="1.0.0",
            description="收集系统信息、项目信息和用户信息等元数据",
            author="system",
            plugin_type=PluginType.START,
            config_schema={
                "type": "object",
                "properties": {
                    "collect_system_info": {
                        "type": "boolean",
                        "description": "是否收集系统信息",
                        "default": True
                    },
                    "collect_project_info": {
                        "type": "boolean",
                        "description": "是否收集项目信息",
                        "default": True
                    },
                    "collect_user_info": {
                        "type": "boolean",
                        "description": "是否收集用户信息",
                        "default": False
                    },
                    "collect_environment_info": {
                        "type": "boolean",
                        "description": "是否收集环境变量信息",
                        "default": False
                    },
                    "sensitive_env_patterns": {
                        "type": "array",
                        "description": "敏感环境变量模式",
                        "default": ["PASSWORD", "TOKEN", "SECRET", "KEY", "AUTH"]
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
            "collect_system_info": config.get("collect_system_info", True),
            "collect_project_info": config.get("collect_project_info", True),
            "collect_user_info": config.get("collect_user_info", False),
            "collect_environment_info": config.get("collect_environment_info", False),
            "sensitive_env_patterns": config.get("sensitive_env_patterns", 
                                              ["PASSWORD", "TOKEN", "SECRET", "KEY", "AUTH"])
        }
        
        logger.debug("元数据收集插件初始化完成")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        logger.info("开始收集元数据")
        
        metadata = {
            "collection_timestamp": datetime.now().isoformat(),
            "workflow_id": context.workflow_id,
            "thread_id": context.thread_id,
            "session_id": context.session_id
        }
        
        try:
            # 收集系统信息
            if self._config["collect_system_info"]:
                system_info = self._collect_system_info()
                metadata["system_info"] = system_info
            
            # 收集项目信息
            if self._config["collect_project_info"]:
                project_info = self._collect_project_info()
                metadata["project_info"] = project_info
            
            # 收集用户信息
            if self._config["collect_user_info"]:
                user_info = self._collect_user_info()
                metadata["user_info"] = user_info
            
            # 收集环境信息
            if self._config["collect_environment_info"]:
                environment_info = self._collect_environment_info()
                metadata["environment_info"] = environment_info
            
            # 更新状态
            state["execution_metadata"] = metadata
            state["start_metadata"] = state.get("start_metadata", {})
            state["start_metadata"]["metadata_collected"] = True
            state["start_metadata"]["metadata_collection_time"] = metadata["collection_timestamp"]
            
            logger.info("元数据收集完成")
            
        except Exception as e:
            logger.error(f"收集元数据失败: {e}")
            state["start_metadata"] = state.get("start_metadata", {})
            state["start_metadata"]["metadata_collection_error"] = str(e)
        
        return state
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        return True
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息
        
        Returns:
            Dict[str, Any]: 系统信息
        """
        system_info = {}
        
        try:
            # 基本系统信息
            system_info["platform"] = platform.platform()
            system_info["system"] = platform.system()
            system_info["release"] = platform.release()
            system_info["version"] = platform.version()
            system_info["machine"] = platform.machine()
            system_info["processor"] = platform.processor()
            
            # Python信息
            system_info["python_version"] = sys.version
            system_info["python_executable"] = sys.executable
            system_info["python_implementation"] = platform.python_implementation()
            
            # 虚拟环境信息
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            system_info["in_virtual_env"] = in_venv
            
            if in_venv:
                system_info["virtual_env_prefix"] = sys.prefix
            
            # 环境变量
            system_info["path"] = os.environ.get("PATH", "")
            
            # 工作目录
            system_info["working_directory"] = os.getcwd()
            
            # 尝试获取更多系统信息
            try:
                import psutil
                
                # CPU信息
                cpu_info = {
                    "count": psutil.cpu_count(),
                    "count_logical": psutil.cpu_count(logical=True),
                    "percent": psutil.cpu_percent(interval=1)
                }
                system_info["cpu"] = cpu_info
                
                # 内存信息
                memory = psutil.virtual_memory()
                memory_info = {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent
                }
                system_info["memory"] = memory_info
                
                # 磁盘信息
                disk = psutil.disk_usage(os.getcwd())
                disk_info = {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round((disk.used / disk.total) * 100, 1)
                }
                system_info["disk"] = disk_info
                
            except ImportError:
                system_info["psutil_note"] = "psutil未安装，无法获取详细系统信息"
            except Exception as e:
                system_info["system_info_error"] = str(e)
            
        except Exception as e:
            logger.error(f"收集系统信息失败: {e}")
            system_info["collection_error"] = str(e)
        
        return system_info
    
    def _collect_project_info(self) -> Dict[str, Any]:
        """收集项目信息
        
        Returns:
            Dict[str, Any]: 项目信息
        """
        project_info = {}
        
        try:
            current_dir = os.getcwd()
            project_info["project_path"] = current_dir
            project_info["project_name"] = os.path.basename(current_dir)
            
            # 检查项目类型
            project_info["project_type"] = self._detect_project_type()
            
            # 检查配置文件
            config_files = self._find_config_files()
            project_info["config_files"] = config_files
            
            # 检查依赖文件
            dependency_files = self._find_dependency_files()
            project_info["dependency_files"] = dependency_files
            
            # Git信息
            git_info = self._get_git_info()
            if git_info:
                project_info["git"] = git_info
            
            # 项目统计
            project_stats = self._get_project_stats()
            project_info["stats"] = project_stats
            
        except Exception as e:
            logger.error(f"收集项目信息失败: {e}")
            project_info["collection_error"] = str(e)
        
        return project_info
    
    def _collect_user_info(self) -> Dict[str, Any]:
        """收集用户信息
        
        Returns:
            Dict[str, Any]: 用户信息
        """
        user_info = {}
        
        try:
            # 基本用户信息
            user_info["username"] = getpass.getuser()
            
            # 主目录
            user_info["home_directory"] = os.path.expanduser("~")
            
            # Shell信息（Unix系统）
            if platform.system() != "Windows":
                user_info["shell"] = os.environ.get("SHELL", "unknown")
            
            # 尝试获取更多用户信息
            try:
                import pwd
                if hasattr(pwd, 'getpwuid') and hasattr(os, 'getuid'):
                    pw_entry = pwd.getpwuid(os.getuid())  # type: ignore
                    user_info["full_name"] = pw_entry.pw_gecos
                    user_info["uid"] = pw_entry.pw_uid
                    user_info["gid"] = pw_entry.pw_gid
                    user_info["home"] = pw_entry.pw_dir
            except (ImportError, AttributeError, OSError):
                # Windows系统或权限不足
                pass
            
        except Exception as e:
            logger.error(f"收集用户信息失败: {e}")
            user_info["collection_error"] = str(e)
        
        return user_info
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """收集环境信息
        
        Returns:
            Dict[str, Any]: 环境信息
        """
        env_info = {}
        sensitive_patterns = [pattern.lower() for pattern in self._config["sensitive_env_patterns"]]
        
        try:
            # 收集非敏感的环境变量
            for key, value in os.environ.items():
                key_lower = key.lower()
                
                # 检查是否为敏感变量
                is_sensitive = any(pattern in key_lower for pattern in sensitive_patterns)
                
                if not is_sensitive:
                    # 限制值的长度
                    if len(str(value)) > 200:
                        env_info[key] = f"{str(value)[:200]}... (truncated)"
                    else:
                        env_info[key] = value
                else:
                    env_info[key] = "[REDACTED]"
            
            # 统计信息
            env_info["_stats"] = {
                "total_variables": len(os.environ),
                "collected_variables": len([k for k in os.environ.keys() 
                                          if not any(pattern in k.lower() for pattern in sensitive_patterns)]),
                "redacted_variables": len([k for k in os.environ.keys() 
                                         if any(pattern in k.lower() for pattern in sensitive_patterns)])
            }
            
        except Exception as e:
            logger.error(f"收集环境信息失败: {e}")
            env_info["collection_error"] = str(e)
        
        return env_info
    
    def _detect_project_type(self) -> str:
        """检测项目类型
        
        Returns:
            str: 项目类型
        """
        current_dir = os.getcwd()
        
        # 检查常见的项目标识文件
        project_indicators = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
            "node": ["package.json", "package-lock.json", "yarn.lock"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "go": ["go.mod", "go.sum"],
            "ruby": ["Gemfile", "Gemfile.lock"],
            "php": ["composer.json", "composer.lock"],
            "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
            "kubernetes": ["k8s/", "kubernetes/", "*.yaml", "*.yml"]
        }
        
        for project_type, indicators in project_indicators.items():
            for indicator in indicators:
                if indicator.startswith("*"):
                    # 通配符模式
                    pattern = indicator[1:]
                    for file in os.listdir(current_dir):
                        if file.endswith(pattern):
                            return project_type
                elif os.path.exists(os.path.join(current_dir, indicator)):
                    return project_type
        
        return "unknown"
    
    def _find_config_files(self) -> list:
        """查找配置文件
        
        Returns:
            list: 配置文件列表
        """
        current_dir = os.getcwd()
        config_patterns = [
            "*.yaml", "*.yml", "*.json", "*.toml", "*.ini", "*.cfg",
            "*.conf", "config*", "settings*", ".env*", "Dockerfile*"
        ]
        
        config_files = []
        try:
            import glob
            for pattern in config_patterns:
                files = glob.glob(os.path.join(current_dir, pattern))
                config_files.extend([os.path.basename(f) for f in files])
        except ImportError:
            # 备用方案
            try:
                for file in os.listdir(current_dir):
                    if any(file.endswith(pattern.replace("*", "")) for pattern in config_patterns):
                        config_files.append(file)
            except OSError:
                pass
        
        return sorted(list(set(config_files)))
    
    def _find_dependency_files(self) -> list:
        """查找依赖文件
        
        Returns:
            list: 依赖文件列表
        """
        current_dir = os.getcwd()
        dependency_files = []
        
        common_dependency_files = [
            "requirements.txt", "Pipfile", "pyproject.toml", "setup.py",
            "package.json", "package-lock.json", "yarn.lock",
            "pom.xml", "build.gradle", "Cargo.toml", "go.mod",
            "Gemfile", "composer.json"
        ]
        
        for dep_file in common_dependency_files:
            if os.path.exists(os.path.join(current_dir, dep_file)):
                dependency_files.append(dep_file)
        
        return dependency_files
    
    def _get_git_info(self) -> Dict[str, Any]:
        """获取Git信息
        
        Returns:
            Dict[str, Any]: Git信息
        """
        git_info = {}
        
        try:
            import subprocess
            
            # 检查是否是Git仓库
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                return {}
            
            # 获取当前分支
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
            
            # 获取最新提交
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%s|%an|%ad'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                commit_info = result.stdout.strip().split('|')
                if len(commit_info) >= 4:
                    git_info["latest_commit"] = {
                        "hash": commit_info[0],
                        "message": commit_info[1],
                        "author": commit_info[2],
                        "date": commit_info[3]
                    }
            
            # 获取远程仓库URL
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                git_info["remote_url"] = result.stdout.strip()
            
        except Exception as e:
            logger.debug(f"获取Git信息失败: {e}")
        
        return git_info
    
    def _get_project_stats(self) -> Dict[str, Any]:
        """获取项目统计信息
        
        Returns:
            Dict[str, Any]: 项目统计信息
        """
        stats = {}
        
        try:
            current_dir = os.getcwd()
            
            # 统计文件数量
            file_count = 0
            dir_count = 0
            
            for root, dirs, files in os.walk(current_dir):
                # 跳过隐藏目录和常见的忽略目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target']]
                
                dir_count += len(dirs)
                file_count += len([f for f in files if not f.startswith('.')])
            
            stats["directories"] = dir_count
            stats["files"] = file_count
            
            # 统计不同类型的文件
            file_extensions = {}
            for root, dirs, files in os.walk(current_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target']]
                
                for file in files:
                    if not file.startswith('.'):
                        ext = os.path.splitext(file)[1].lower()
                        if ext:
                            file_extensions[ext] = file_extensions.get(ext, 0) + 1
                        else:
                            file_extensions["no_extension"] = file_extensions.get("no_extension", 0) + 1
            
            # 取前10种文件类型
            top_extensions = sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)[:10]
            stats["file_types"] = dict(top_extensions)
            
        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            stats["collection_error"] = str(e)
        
        return stats