"""环境检查器单元测试"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

from src.infrastructure.environment import EnvironmentChecker
from src.infrastructure.types import CheckResult


class TestEnvironmentChecker:
    """环境检查器测试"""

    def test_check_python_version_pass(self) -> None:
        """测试Python版本检查通过"""
        checker = EnvironmentChecker(min_python_version=(3, 10, 0))
        result = checker.check_python_version()

        assert result.is_pass()
        assert "Python version" in result.message
        assert "meets requirement" in result.message

    def test_check_python_version_fail(self) -> None:
        """测试Python版本检查失败"""
        # 设置一个不可能满足的高版本要求
        checker = EnvironmentChecker(min_python_version=(99, 0, 0))
        result = checker.check_python_version()

        assert result.is_error()
        assert "is below required" in result.message
        assert "99.0.0" in result.message

    def test_check_required_packages(self) -> None:
        """检查必需包"""
        checker = EnvironmentChecker()
        results = checker.check_required_packages()

        # 应该有每个包的检查结果
        assert len(results) == len(checker.required_packages)

        # 检查结果格式
        for result in results:
            assert result.component.startswith("package_")
            assert "version" in result.details

    def test_check_missing_package(self) -> None:
        """测试缺失包检查"""
        checker = EnvironmentChecker()
        checker.required_packages = ["nonexistent_package_12345"]

        results = checker.check_required_packages()

        assert len(results) == 1
        assert results[0].is_error()
        assert "not installed" in results[0].message

    @patch("importlib.util.find_spec")
    def test_check_package_with_version(self, mock_find_spec: Any) -> None:
        """测试带版本信息的包检查"""
        # 模拟包存在且有版本信息
        mock_module = MagicMock()
        mock_module.__version__ = "1.0.0"
        mock_find_spec.return_value = True

        with patch("importlib.import_module", return_value=mock_module):
            checker = EnvironmentChecker()
            checker.required_packages = ["test_package"]

            results = checker.check_required_packages()

            assert len(results) == 1
            assert results[0].is_pass()
            assert results[0].details["version"] == "1.0.0"

    def test_check_config_files(self) -> None:
        """测试配置文件检查"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试配置文件
            config_dir = Path(temp_dir) / "configs"
            config_dir.mkdir()

            global_config = config_dir / "global.yaml"
            global_config.write_text("log_level: INFO")

            llm_dir = config_dir / "llms"
            llm_dir.mkdir()
            group_config = llm_dir / "_group.yaml"
            group_config.write_text("openai_group: {}")

            # 创建检查器并设置配置路径
            checker = EnvironmentChecker()
            checker.config_files = [
                "configs/global.yaml",
                "configs/llms/_group.yaml",
                "configs/agents/_group.yaml",  # 这个文件不存在
            ]

            # 直接修改checker的config_files属性来测试，而不是模拟Path.exists
            original_config_files = checker.config_files.copy()
            checker.config_files = [
                "configs/global.yaml",  # 存在
                "configs/llms/_group.yaml",  # 存在
                "configs/agents/_group.yaml",  # 不存在，但应该是可选的
            ]

            # 临时创建测试文件来验证逻辑
            with tempfile.TemporaryDirectory() as temp_dir:
                # 创建测试配置目录结构
                config_dir = Path(temp_dir) / "configs"
                config_dir.mkdir()
                (config_dir / "global.yaml").write_text("log_level: INFO")

                llm_dir = config_dir / "llms"
                llm_dir.mkdir()
                (llm_dir / "_group.yaml").write_text("openai_group: {}")

                # 保存原始base_path并临时修改
                import os

                original_cwd = os.getcwd()
                os.chdir(temp_dir)

                try:
                    results = checker.check_config_files()
                finally:
                    os.chdir(original_cwd)
                    checker.config_files = original_config_files

            assert len(results) == 3

            # 检查存在的文件
            global_result = next(r for r in results if "global.yaml" in r.component)
            assert global_result.is_pass()

            # 检查存在的组配置文件
            group_result = next(r for r in results if "llms/_group.yaml" in r.component)
            assert group_result.is_pass()

            # 检查不存在的文件（应该是警告，因为它是可选的）
            missing_result = next(
                r for r in results if "agents/_group.yaml" in r.component
            )
            assert missing_result.is_warning()

    def test_check_system_resources(self) -> None:
        """测试系统资源检查"""
        checker = EnvironmentChecker()
        results = checker.check_system_resources()

        # 应该有操作系统、内存和磁盘空间的检查结果
        assert len(results) >= 3

        # 检查操作系统检查
        os_result = next(r for r in results if r.component == "operating_system")
        assert os_result.is_pass()
        assert "Operating system" in os_result.message

        # 检查内存检查
        memory_result = next(r for r in results if r.component == "memory")
        assert memory_result.component == "memory"

        # 检查磁盘空间检查
        disk_result = next(r for r in results if r.component == "disk_space")
        assert disk_result.component == "disk_space"

    @patch("platform.system")
    def test_check_system_resources_linux(self, mock_system: Any) -> None:
        """测试Linux系统资源检查"""
        mock_system.return_value = "Linux"

        # 模拟/proc/meminfo内容
        meminfo_content = """
MemTotal:        8000000 kB
MemAvailable:    4000000 kB
"""

        # 创建一个模拟的statvfs函数
        mock_statvfs_func = MagicMock()
        mock_stat = MagicMock()
        mock_stat.f_bavail = 1000000  # 可用块数
        mock_stat.f_frsize = 4096  # 块大小
        mock_statvfs_func.return_value = mock_stat

        with patch("builtins.open", mock_open_read_data(meminfo_content)):
            # 直接在os模块上添加statvfs属性，然后进行模拟
            with patch(
                "src.infrastructure.environment.os",
                new=MagicMock(statvfs=mock_statvfs_func),
            ):
                checker = EnvironmentChecker()
                results = checker.check_system_resources()

                memory_result = next(r for r in results if r.component == "memory")
                assert memory_result.is_pass()
                assert memory_result.details["available_gb"] >= 1.0

    @patch("platform.system")
    def test_check_system_resources_memory_warning(self, mock_system: Any) -> None:
        """测试内存不足警告"""
        mock_system.return_value = "Linux"

        # 模拟低内存情况
        meminfo_content = """
MemTotal:        8000000 kB
MemAvailable:    500000 kB
"""

        with patch("builtins.open", mock_open_read_data(meminfo_content)):
            checker = EnvironmentChecker()
            results = checker.check_system_resources()

            memory_result = next(r for r in results if r.component == "memory")
            assert memory_result.is_warning()
            assert "Low available memory" in memory_result.message

    def test_check_environment_variables(self) -> None:
        """测试环境变量检查"""
        # 设置测试环境变量
        os.environ["TEST_VAR"] = "test_value"
        os.environ["SECRET_KEY"] = "secret_value"

        try:
            checker = EnvironmentChecker()
            required_vars = ["TEST_VAR", "SECRET_KEY", "MISSING_VAR"]

            results = checker.check_environment_variables(required_vars)

            assert len(results) == 3

            # 检查存在的变量
            test_var_result = next(r for r in results if "TEST_VAR" in r.component)
            assert test_var_result.is_pass()
            assert test_var_result.details["value"] == "test_value"

            # 检查敏感变量（应该被脱敏）
            secret_result = next(r for r in results if "SECRET_KEY" in r.component)
            assert secret_result.is_pass()
            assert secret_result.details["value"] == "***"

            # 检查缺失的变量
            missing_result = next(r for r in results if "MISSING_VAR" in r.component)
            assert missing_result.is_warning()
            assert "not set" in missing_result.message

        finally:
            # 清理环境变量
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
            if "SECRET_KEY" in os.environ:
                del os.environ["SECRET_KEY"]

    def test_check_dependencies(self) -> None:
        """测试完整依赖检查"""
        checker = EnvironmentChecker()
        results = checker.check_dependencies()

        # 应该包含所有类型的检查
        assert any(r.component == "python_version" for r in results)
        assert any(r.component.startswith("package_") for r in results)
        assert any(r.component.startswith("config_file_") for r in results)
        assert any(
            r.component in ["operating_system", "memory", "disk_space"] for r in results
        )

    def test_generate_report(self) -> None:
        """测试生成环境检查报告"""
        checker = EnvironmentChecker()
        report = checker.generate_report()

        # 检查报告结构
        assert "summary" in report
        assert "details" in report

        # 检查汇总信息
        summary = report["summary"]
        assert "total" in summary
        assert "pass" in summary
        assert "warning" in summary
        assert "error" in summary

        # 检查详细信息
        details = report["details"]
        assert isinstance(details, list)

        if details:
            detail = details[0]
            assert "component" in detail
            assert "status" in detail
            assert "message" in detail
            assert "details" in detail


def mock_open_read_data(data: str) -> Any:
    """模拟open函数返回数据"""
    from unittest.mock import mock_open

    return mock_open(read_data=data)
