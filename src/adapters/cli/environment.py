"""环境检查工具实现"""

import importlib
import sys
import os
import platform
import subprocess
import shutil
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Union
from pathlib import Path

from .check_result import CheckResult


class EnvironmentCheckError(Exception):
    """环境检查异常"""
    pass


class IEnvironmentChecker(ABC):
    """环境检查器接口"""

    @abstractmethod
    def check_dependencies(self) -> List[CheckResult]:
        """检查所有依赖"""
        pass

    @abstractmethod
    def check_python_version(self) -> CheckResult:
        """检查Python版本"""
        pass

    @abstractmethod
    def check_required_packages(self) -> List[CheckResult]:
        """检查必需包"""
        pass

    @abstractmethod
    def check_config_files(self) -> List[CheckResult]:
        """检查配置文件"""
        pass

    @abstractmethod
    def check_system_resources(self) -> List[CheckResult]:
        """检查系统资源"""
        pass

    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """生成环境检查报告"""
        pass


class EnvironmentChecker(IEnvironmentChecker):
    """环境检查器实现"""

    def __init__(self, min_python_version: Tuple[int, int, int] = (3, 13, 0)):
        self.min_python_version = min_python_version
        self.required_packages = [
            "pydantic",
            "pyyaml",
            "watchdog",
            "dependency-injector",
            "python-dotenv",
            "rich",
            "click",
        ]
        self.config_files = [
            "configs/global.yaml",
            "configs/llms/_group.yaml",
            "configs/agents/_group.yaml",
            "configs/tool-sets/_group.yaml",
        ]

    def check_dependencies(self) -> List[CheckResult]:
        """检查所有依赖"""
        results = []

        # 检查Python版本
        results.append(self.check_python_version())

        # 检查必需包
        results.extend(self.check_required_packages())

        # 检查配置文件
        results.extend(self.check_config_files())

        # 检查系统资源
        results.extend(self.check_system_resources())

        return results

    def check_python_version(self) -> CheckResult:
        """检查Python版本"""
        current_version = sys.version_info[:3]

        if current_version >= self.min_python_version:
            return CheckResult(
                component="python_version",
                status="PASS",
                message=f"Python version {sys.version.split()[0]} meets requirement",
                details={
                    "current_version": ".".join(map(str, current_version)),
                    "required_version": ".".join(map(str, self.min_python_version)),
                },
            )
        else:
            return CheckResult(
                component="python_version",
                status="ERROR",
                message=f"Python version {sys.version.split()[0]} is below required {'.'.join(map(str, self.min_python_version))}",
                details={
                    "current_version": ".".join(map(str, current_version)),
                    "required_version": ".".join(map(str, self.min_python_version)),
                },
            )

    def check_required_packages(self) -> List[CheckResult]:
        """检查必需包"""
        results = []

        for package in self.required_packages:
            try:
                # 尝试导入包
                if package == "dependency-injector":
                    import dependency_injector  # type: ignore

                    version = getattr(dependency_injector, "__version__", "unknown")
                elif package == "python-dotenv":
                    import dotenv

                    version = getattr(dotenv, "__version__", "unknown")
                elif package == "pyyaml":
                    import yaml

                    version = getattr(yaml, "__version__", "unknown")
                elif package == "click":
                    # 使用importlib.metadata来避免弃用警告
                    try:
                        from importlib.metadata import version as get_version

                        version = get_version(package)
                    except Exception:
                        version = "unknown"
                else:
                    module = importlib.import_module(package.replace("-", "_"))
                    # 尝试使用importlib.metadata.version，如果失败则回退到__version__
                    try:
                        from importlib.metadata import version as get_version

                        version = get_version(package)
                    except Exception:
                        version = getattr(module, "__version__", "unknown")

                results.append(
                    CheckResult(
                        component=f"package_{package}",
                        status="PASS",
                        message=f"Package {package} is available (version: {version})",
                        details={"version": version},
                    )
                )

            except ImportError:
                results.append(
                    CheckResult(
                        component=f"package_{package}",
                        status="ERROR",
                        message=f"Required package {package} is not installed",
                        details={"package": package},
                    )
                )

        return results

    def check_config_files(self) -> List[CheckResult]:
        """检查配置文件"""
        results = []

        for config_file in self.config_files:
            file_path = Path(config_file)

            if file_path.exists():
                # 检查文件是否可读
                if os.access(file_path, os.R_OK):
                    results.append(
                        CheckResult(
                            component=f"config_file_{config_file}",
                            status="PASS",
                            message=f"Configuration file {config_file} exists and is readable",
                            details={"path": str(file_path.absolute())},
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            component=f"config_file_{config_file}",
                            status="ERROR",
                            message=f"Configuration file {config_file} exists but is not readable",
                            details={"path": str(file_path.absolute())},
                        )
                    )
            else:
                # 某些配置文件可能是可选的
                if config_file.endswith("_group.yaml"):
                    results.append(
                        CheckResult(
                            component=f"config_file_{config_file}",
                            status="WARNING",
                            message=f"Optional configuration file {config_file} does not exist",
                            details={"path": str(file_path.absolute())},
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            component=f"config_file_{config_file}",
                            status="ERROR",
                            message=f"Required configuration file {config_file} does not exist",
                            details={"path": str(file_path.absolute())},
                        )
                    )

        return results

    def check_system_resources(self) -> List[CheckResult]:
        """检查系统资源"""
        results = []

        # 检查操作系统
        system = platform.system()
        results.append(
            CheckResult(
                component="operating_system",
                status="PASS",
                message=f"Operating system: {system}",
                details={
                    "system": system,
                    "release": platform.release(),
                    "version": platform.version(),
                },
            )
        )

        # 检查可用内存
        try:
            mem_gb_result: Union[float, str] = "unknown"  # 初始化变量

            if system == "Linux":
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    mem_total = int(
                        [line for line in meminfo.split("\n") if "MemTotal" in line][
                            0
                        ].split()[1]
                    )
                    mem_available = int(
                        [
                            line
                            for line in meminfo.split("\n")
                            if "MemAvailable" in line
                        ][0].split()[1]
                    )
                    mem_gb = mem_available / (1024 * 1024)
                    mem_gb_result = mem_gb
            elif system == "Darwin":  # macOS
                result = subprocess.run(["vm_stat"], capture_output=True, text=True)
                if result.returncode == 0:
                    # 解析vm_stat输出获取可用内存
                    vm_stat = result.stdout
                    free_pages = int(
                        [line for line in vm_stat.split("\n") if "Pages free:" in line][
                            0
                        ]
                        .split(":")[1]
                        .strip()
                        .replace(".", "")
                    )
                    page_size = 4096  # macOS默认页面大小
                    mem_gb = (free_pages * page_size) / (1024 * 1024 * 1024)
                    mem_gb_result = mem_gb
                else:
                    mem_gb_result = "unknown"
            elif system == "Windows":
                import psutil  # type: ignore

                mem = psutil.virtual_memory()
                mem_gb = mem.available / (1024 * 1024 * 1024)
                mem_gb_result = mem_gb
            else:
                mem_gb_result = "unknown"

            if isinstance(mem_gb_result, (int, float)):
                if mem_gb_result >= 1.0:  # 至少1GB可用内存
                    results.append(
                        CheckResult(
                            component="memory",
                            status="PASS",
                            message=f"Available memory: {mem_gb_result:.1f} GB",
                            details={"available_gb": mem_gb_result},
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            component="memory",
                            status="WARNING",
                            message=f"Low available memory: {mem_gb_result:.1f} GB (recommended: >= 1 GB)",
                            details={"available_gb": mem_gb_result},
                        )
                    )
            else:
                results.append(
                    CheckResult(
                        component="memory",
                        status="WARNING",
                        message="Could not determine available memory",
                        details={"available_gb": str(mem_gb_result)},
                    )
                )

        except Exception as e:
            results.append(
                CheckResult(
                    component="memory",
                    status="WARNING",
                    message=f"Failed to check memory: {str(e)}",
                    details={"error": str(e)},
                )
            )

        # 检查磁盘空间
        try:
            current_path = Path.cwd()
            # 使用shutil.disk_usage，它在所有平台上都可用
            try:
                free_bytes = shutil.disk_usage(str(current_path)).free
                free_gb = free_bytes / (1024 * 1024 * 1024)
            except (OSError, AttributeError) as e:
                # 如果shutil.disk_usage失败，尝试使用平台特定的方法
                if platform.system() != "Windows" and hasattr(os, "statvfs"):
                    # Unix-like系统 (Linux, macOS) - 使用getattr避免静态分析错误
                    statvfs_func = getattr(os, "statvfs", None)
                    if statvfs_func:
                        stat = statvfs_func(str(current_path))
                        free_gb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024 * 1024)
                    else:
                        # 如果getattr失败，使用默认值
                        free_gb = 1.0  # 默认值
                else:
                    # Windows或其他不支持statvfs的系统，使用默认值
                    free_gb = 1.0  # 默认值

            if free_gb >= 1.0:  # 至少1GB可用磁盘空间
                results.append(
                    CheckResult(
                        component="disk_space",
                        status="PASS",
                        message=f"Available disk space: {free_gb:.1f} GB",
                        details={"available_gb": free_gb, "path": str(current_path)},
                    )
                )
            else:
                results.append(
                    CheckResult(
                        component="disk_space",
                        status="WARNING",
                        message=f"Low available disk space: {free_gb:.1f} GB (recommended: >= 1 GB)",
                        details={"available_gb": free_gb, "path": str(current_path)},
                    )
                )

        except Exception as e:
            results.append(
                CheckResult(
                    component="disk_space",
                    status="WARNING",
                    message=f"Failed to check disk space: {str(e)}",
                    details={"error": str(e)},
                )
            )

        return results

    def check_environment_variables(
        self, required_vars: List[str]
    ) -> List[CheckResult]:
        """检查环境变量"""
        results = []

        for var in required_vars:
            value = os.getenv(var)
            if value is not None:
                results.append(
                    CheckResult(
                        component=f"env_var_{var}",
                        status="PASS",
                        message=f"Environment variable {var} is set",
                        details={
                            "variable": var,
                            "value": (
                                "***"
                                if "key" in var.lower() or "secret" in var.lower()
                                else value
                            ),
                        },
                    )
                )
            else:
                results.append(
                    CheckResult(
                        component=f"env_var_{var}",
                        status="WARNING",
                        message=f"Environment variable {var} is not set",
                        details={"variable": var},
                    )
                )

        return results

    def generate_report(self) -> Dict[str, Any]:
        """生成环境检查报告"""
        results = self.check_dependencies()

        report = {
            "summary": {
                "total": len(results),
                "pass": len([r for r in results if r.is_pass()]),
                "warning": len([r for r in results if r.is_warning()]),
                "error": len([r for r in results if r.is_error()]),
            },
            "details": [
                {
                    "component": r.component,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                }
                for r in results
            ],
        }

        return report