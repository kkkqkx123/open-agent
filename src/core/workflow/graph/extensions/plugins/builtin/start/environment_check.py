"""环境检查插件

检查执行环境，包括依赖、资源和权限。
"""

import os
import sys
import shutil
from src.interfaces.dependency_injection import get_logger
import platform
from typing import Dict, Any, List

from src.interfaces.workflow.plugins import IStartPlugin, PluginMetadata, PluginContext, PluginType


logger = get_logger(__name__)


class EnvironmentCheckPlugin(IStartPlugin):
    """环境检查插件
    
    在工作流开始时检查执行环境，确保满足运行要求。
    """
    
    def __init__(self):
        """初始化环境检查插件"""
        self._config = {}
        self._check_results = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="environment_check",
            version="1.0.0",
            description="检查执行环境，包括依赖、资源和权限",
            author="system",
            plugin_type=PluginType.START,
            config_schema={
                "type": "object",
                "properties": {
                    "check_dependencies": {
                        "type": "boolean",
                        "description": "是否检查依赖",
                        "default": True
                    },
                    "check_resources": {
                        "type": "boolean",
                        "description": "是否检查系统资源",
                        "default": True
                    },
                    "check_permissions": {
                        "type": "boolean",
                        "description": "是否检查权限",
                        "default": True
                    },
                    "fail_on_error": {
                        "type": "boolean",
                        "description": "检查失败时是否失败",
                        "default": False
                    },
                    "required_packages": {
                        "type": "array",
                        "description": "必需的Python包",
                        "default": ["yaml", "pydantic"]
                    },
                    "required_commands": {
                        "type": "array",
                        "description": "必需的系统命令",
                        "default": ["git"]
                    },
                    "min_memory_mb": {
                        "type": "integer",
                        "description": "最小内存要求（MB）",
                        "default": 512,
                        "minimum": 128
                    },
                    "min_disk_space_mb": {
                        "type": "integer",
                        "description": "最小磁盘空间要求（MB）",
                        "default": 1024,
                        "minimum": 100
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
            "check_dependencies": config.get("check_dependencies", True),
            "check_resources": config.get("check_resources", True),
            "check_permissions": config.get("check_permissions", True),
            "fail_on_error": config.get("fail_on_error", False),
            "required_packages": config.get("required_packages", ["yaml", "pydantic"]),
            "required_commands": config.get("required_commands", ["git"]),
            "min_memory_mb": config.get("min_memory_mb", 512),
            "min_disk_space_mb": config.get("min_disk_space_mb", 1024)
        }
        
        self._check_results = {}
        logger.debug("环境检查插件初始化完成")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
            
        Raises:
            RuntimeError: 当检查失败且配置为失败时抛出
        """
        logger.info("开始环境检查")
        
        all_passed = True
        
        try:
            # 检查Python环境
            if self._config["check_dependencies"]:
                python_check = self._check_python_environment()
                self._check_results["python_environment"] = python_check
                if not python_check["passed"]:
                    all_passed = False
            
            # 检查必需的包
            if self._config["check_dependencies"]:
                package_check = self._check_required_packages()
                self._check_results["required_packages"] = package_check
                if not package_check["passed"]:
                    all_passed = False
            
            # 检查必需的命令
            if self._config["check_dependencies"]:
                command_check = self._check_required_commands()
                self._check_results["required_commands"] = command_check
                if not command_check["passed"]:
                    all_passed = False
            
            # 检查系统资源
            if self._config["check_resources"]:
                resource_check = self._check_system_resources()
                self._check_results["system_resources"] = resource_check
                if not resource_check["passed"]:
                    all_passed = False
            
            # 检查权限
            if self._config["check_permissions"]:
                permission_check = self._check_permissions()
                self._check_results["permissions"] = permission_check
                if not permission_check["passed"]:
                    all_passed = False
            
            # 生成检查报告
            check_report = self._generate_check_report()
            
            # 更新状态
            state["environment_check"] = {
                "passed": all_passed,
                "report": check_report,
                "detailed_results": self._check_results,
                "timestamp": context.execution_start_time
            }
            
            state["start_metadata"] = state.get("start_metadata", {})
            state["start_metadata"]["environment_check_completed"] = True
            state["start_metadata"]["environment_check_passed"] = all_passed
            
            logger.info(f"环境检查完成，结果: {'通过' if all_passed else '失败'}")
            
            # 如果检查失败且配置为失败时抛出异常
            if not all_passed and self._config["fail_on_error"]:
                raise RuntimeError(f"环境检查失败: {check_report}")
            
        except Exception as e:
            logger.error(f"环境检查过程中发生错误: {e}")
            state["start_metadata"] = state.get("start_metadata", {})
            state["start_metadata"]["environment_check_error"] = str(e)
            
            if self._config["fail_on_error"]:
                raise
        
        return state
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        self._check_results.clear()
        return True
    
    def _check_python_environment(self) -> Dict[str, Any]:
        """检查Python环境
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        result = {
            "passed": True,
            "details": {},
            "errors": []
        }
        
        try:
            # Python版本
            result["details"]["python_version"] = sys.version
            result["details"]["python_executable"] = sys.executable
            result["details"]["platform"] = platform.platform()
            
            # 检查Python版本（要求3.8+）
            if sys.version_info < (3, 8):
                result["passed"] = False
                result["errors"].append(f"Python版本过低: {sys.version_info}，需要3.8+")
            
            # 检查虚拟环境
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            result["details"]["in_virtual_env"] = in_venv
            
            if not in_venv:
                result["errors"].append("建议在虚拟环境中运行")
            
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"检查Python环境失败: {e}")
        
        return result
    
    def _check_required_packages(self) -> Dict[str, Any]:
        """检查必需的Python包
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        result = {
            "passed": True,
            "details": {},
            "errors": []
        }
        
        required_packages = self._config["required_packages"]
        
        for package in required_packages:
            try:
                __import__(package)
                result["details"][package] = "installed"
            except ImportError:
                result["passed"] = False
                result["details"][package] = "missing"
                result["errors"].append(f"缺少必需的包: {package}")
        
        return result
    
    def _check_required_commands(self) -> Dict[str, Any]:
        """检查必需的系统命令
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        result = {
            "passed": True,
            "details": {},
            "errors": []
        }
        
        required_commands = self._config["required_commands"]
        
        for command in required_commands:
            try:
                command_path = shutil.which(command)
                if command_path:
                    result["details"][command] = {
                        "status": "available",
                        "path": command_path
                    }
                else:
                    result["passed"] = False
                    result["details"][command] = {
                        "status": "missing"
                    }
                    result["errors"].append(f"缺少必需的命令: {command}")
            except Exception as e:
                result["passed"] = False
                result["details"][command] = {
                    "status": "error",
                    "error": str(e)
                }
                result["errors"].append(f"检查命令 {command} 失败: {e}")
        
        return result
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        result = {
            "passed": True,
            "details": {},
            "errors": []
        }
        
        try:
            # 检查内存
            try:
                import psutil
                memory = psutil.virtual_memory()
                available_mb = memory.available / (1024 * 1024)
                total_mb = memory.total / (1024 * 1024)
                
                result["details"]["memory"] = {
                    "total_mb": round(total_mb, 1),
                    "available_mb": round(available_mb, 1),
                    "usage_percent": memory.percent
                }
                
                if available_mb < self._config["min_memory_mb"]:
                    result["passed"] = False
                    result["errors"].append(
                        f"可用内存不足: {available_mb:.1f}MB，需要至少 {self._config['min_memory_mb']}MB"
                    )
                    
            except ImportError:
                result["details"]["memory"] = "psutil未安装，无法检查内存"
                logger.warning("psutil未安装，跳过内存检查")
            
            # 检查磁盘空间
            try:
                disk_usage = shutil.disk_usage(os.getcwd())
                free_mb = disk_usage.free / (1024 * 1024)
                total_mb = disk_usage.total / (1024 * 1024)
                
                result["details"]["disk_space"] = {
                    "total_mb": round(total_mb, 1),
                    "free_mb": round(free_mb, 1),
                    "usage_percent": round((1 - disk_usage.free / disk_usage.total) * 100, 1)
                }
                
                if free_mb < self._config["min_disk_space_mb"]:
                    result["passed"] = False
                    result["errors"].append(
                        f"磁盘空间不足: {free_mb:.1f}MB，需要至少 {self._config['min_disk_space_mb']}MB"
                    )
                    
            except Exception as e:
                result["details"]["disk_space"] = f"检查失败: {e}"
                result["errors"].append(f"检查磁盘空间失败: {e}")
            
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"检查系统资源失败: {e}")
        
        return result
    
    def _check_permissions(self) -> Dict[str, Any]:
        """检查权限
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        result = {
            "passed": True,
            "details": {},
            "errors": []
        }
        
        try:
            current_dir = os.getcwd()
            
            # 检查读权限
            if os.access(current_dir, os.R_OK):
                result["details"]["read_permission"] = "granted"
            else:
                result["passed"] = False
                result["details"]["read_permission"] = "denied"
                result["errors"].append("没有读权限")
            
            # 检查写权限
            if os.access(current_dir, os.W_OK):
                result["details"]["write_permission"] = "granted"
            else:
                result["passed"] = False
                result["details"]["write_permission"] = "denied"
                result["errors"].append("没有写权限")
            
            # 检查执行权限
            if os.access(current_dir, os.X_OK):
                result["details"]["execute_permission"] = "granted"
            else:
                result["passed"] = False
                result["details"]["execute_permission"] = "denied"
                result["errors"].append("没有执行权限")
            
            # 测试创建临时文件
            try:
                test_file = os.path.join(current_dir, ".permission_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                result["details"]["file_creation"] = "success"
            except Exception as e:
                result["passed"] = False
                result["details"]["file_creation"] = f"failed: {e}"
                result["errors"].append(f"无法创建文件: {e}")
            
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"检查权限失败: {e}")
        
        return result
    
    def _generate_check_report(self) -> str:
        """生成检查报告
        
        Returns:
            str: 检查报告
        """
        report_lines = ["环境检查报告:"]
        
        for check_name, check_result in self._check_results.items():
            status = "✓ 通过" if check_result["passed"] else "✗ 失败"
            report_lines.append(f"\n{check_name}: {status}")
            
            # 添加详细信息
            if "details" in check_result:
                for key, value in check_result["details"].items():
                    if isinstance(value, dict):
                        report_lines.append(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            report_lines.append(f"    {sub_key}: {sub_value}")
                    else:
                        report_lines.append(f"  {key}: {value}")
            
            # 添加错误信息
            if "errors" in check_result and check_result["errors"]:
                for error in check_result["errors"]:
                    report_lines.append(f"  错误: {error}")
        
        return '\n'.join(report_lines)