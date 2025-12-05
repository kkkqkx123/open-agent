"""环境检查结果数据类"""

from typing import Optional, Dict, Any


class CheckResult:
    """环境检查结果"""

    def __init__(
        self,
        component: str,
        status: str,  # "PASS", "WARNING", "ERROR"
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}

    def is_pass(self) -> bool:
        """检查是否通过"""
        return self.status == "PASS"

    def is_warning(self) -> bool:
        """检查是否为警告"""
        return self.status == "WARNING"

    def is_error(self) -> bool:
        """检查是否为错误"""
        return self.status == "ERROR"
