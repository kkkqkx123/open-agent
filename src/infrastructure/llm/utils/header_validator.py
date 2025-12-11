"""HTTP标头验证和脱敏处理"""

import re
import os
from typing import Dict, List, Optional, Tuple
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class HeaderValidator:
    """HTTP标头验证器"""

    # 白名单标头 - 包含常用的HTTP标头
    ALLOWED_HEADERS = {
        "authorization",      # 认证标头
        "x-api-key",         # API密钥标头
        "x-custom-header",   # 自定义标头
        "user-agent",        # 用户代理标头
        "content-type",      # 内容类型标头
        "content-length",    # 内容长度标头
        "accept",            # 接受类型标头
        "accept-encoding",   # 接受编码标头
        "accept-language",   # 接受语言标头
        "cache-control",     # 缓存控制标头
        "pragma",            # pragma标头
        "x-requested-with",  # 请求来源标头
        "x-forwarded-for",   # 转发IP标头
        "x-forwarded-proto", # 转发协议标头
        "x-forwarded-host",  # 转发主机标头
        "referer",          # 引用页标头
        "origin",           # 来源标头
        "host",             # 主机标头
        "connection",       # 连接标头
        "accept-charset",   # 接受字符集标头
        "accept-datetime",  # 接受日期时间标头
        "x-csrf-token",     # CSRF令牌标头
        "x-http-method-override", # HTTP方法重写标头
    }

    # 敏感标头（需要环境变量引用）- 仅包含真正敏感的标头
    SENSITIVE_HEADERS = {"authorization", "x-api-key"}

    # 环境变量引用模式
    ENV_VAR_PATTERN = re.compile(r"^\$\{([^}:]+)(?::([^}]*))?\}$")

    def __init__(self) -> None:
        """初始化标头验证器"""
        self._validation_errors: List[str] = []

    def validate_headers(self, headers: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        验证HTTP标头

        Args:
            headers: 标头字典

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        self._validation_errors.clear()

        if not headers:
            return True, []

        for header_name, header_value in headers.items():
            # 转换为小写进行比较
            header_lower = header_name.lower()

            # 检查是否在白名单中
            if header_lower not in self.ALLOWED_HEADERS:
                self._validation_errors.append(
                    f"标头 '{header_name}' 不在白名单中。允许的标头: {sorted(self.ALLOWED_HEADERS)}"
                )
                continue

            # 检查敏感标头是否使用环境变量引用
            if header_lower in self.SENSITIVE_HEADERS:
                # Authorization标头特殊处理：允许Bearer格式
                if header_lower == "authorization" and header_value.startswith(
                    "Bearer "
                ):
                    # Bearer格式，检查token是否为环境变量引用
                    token = header_value[7:]  # 移除"Bearer "
                    if not self._is_env_var_reference(token):
                        self._validation_errors.append(
                            f"Authorization标头的token必须使用环境变量引用格式 ${{ENV_VAR}}"
                        )
                    else:
                        # 验证环境变量是否存在
                        env_var_name = self._extract_env_var_name(token)
                        if env_var_name and not os.getenv(env_var_name):
                            logger.warning(f"环境变量 '{env_var_name}' 未设置")
                else:
                    # 其他敏感标头必须使用环境变量引用
                    if not self._is_env_var_reference(header_value):
                        self._validation_errors.append(
                            f"敏感标头 '{header_name}' 必须使用环境变量引用格式 ${{ENV_VAR}}"
                        )
                    else:
                        # 验证环境变量是否存在
                        env_var_name = self._extract_env_var_name(header_value)
                        if env_var_name and not os.getenv(env_var_name):
                            logger.warning(f"环境变量 '{env_var_name}' 未设置")

        return len(self._validation_errors) == 0, self._validation_errors.copy()

    def resolve_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        解析标头中的环境变量引用

        Args:
            headers: 原始标头字典

        Returns:
            Dict[str, str]: 解析后的标头字典
        """
        resolved_headers = {}

        for header_name, header_value in headers.items():
            header_lower = header_name.lower()

            # Authorization标头特殊处理
            if header_lower == "authorization" and header_value.startswith("Bearer "):
                token = header_value[7:]  # 移除"Bearer "
                if self._is_env_var_reference(token):
                    resolved_token = self._resolve_env_var(token)
                    if resolved_token is not None:
                        resolved_headers[header_name] = f"Bearer {resolved_token}"
                    else:
                        logger.warning(
                            f"无法解析Authorization标头的环境变量引用: {token}"
                        )
                else:
                    resolved_headers[header_name] = header_value
            else:
                # 其他标头处理
                if self._is_env_var_reference(header_value):
                    resolved_value = self._resolve_env_var(header_value)
                    if resolved_value is not None:
                        resolved_headers[header_name] = resolved_value
                    else:
                        logger.warning(
                            f"无法解析标头 '{header_name}' 的环境变量引用: {header_value}"
                        )
                else:
                    resolved_headers[header_name] = header_value

        return resolved_headers

    def sanitize_headers_for_logging(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        脱敏标头用于日志记录

        Args:
            headers: 原始标头字典

        Returns:
            Dict[str, str]: 脱敏后的标头字典
        """
        sanitized_headers = {}

        for header_name, header_value in headers.items():
            header_lower = header_name.lower()

            if header_lower in self.SENSITIVE_HEADERS:
                # 敏感标头脱敏
                if header_lower == "authorization" and header_value.startswith(
                    "Bearer "
                ):
                    # Authorization标头完全脱敏
                    sanitized_headers[header_name] = "***"
                else:
                    sanitized_headers[header_name] = "***"
            elif self._is_env_var_reference(header_value):
                # 环境变量引用脱敏
                sanitized_headers[header_name] = "${***}"
            else:
                sanitized_headers[header_name] = header_value

        return sanitized_headers

    def _is_env_var_reference(self, value: str) -> bool:
        """检查是否为环境变量引用"""
        return bool(self.ENV_VAR_PATTERN.match(value.strip()))

    def _extract_env_var_name(self, value: str) -> Optional[str]:
        """提取环境变量名称"""
        match = self.ENV_VAR_PATTERN.match(value.strip())
        if match:
            # 只返回环境变量名称，不包括默认值部分
            return match.group(1)
        return None

    def _resolve_env_var(self, value: str) -> Optional[str]:
        """解析环境变量引用"""
        match = self.ENV_VAR_PATTERN.match(value.strip())
        if not match:
            return value

        env_var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""

        return os.getenv(env_var_name, default_value)

    def validate_authorization_format(self, value: str) -> bool:
        """
        验证Authorization标头格式

        Args:
            value: 标头值

        Returns:
            bool: 是否有效
        """
        if not value:
            return False

        # 检查Bearer格式
        if value.lower().startswith("bearer "):
            # 确保有token，不仅仅是"Bearer "
            parts = value.split(" ", 1)
            return len(parts) > 1 and parts[1].strip() != ""

        # 如果只是"Bearer"而没有token，则无效
        if value.lower() == "bearer":
            return False

        # 检查其他可能的格式
        return len(value) > 0


class HeaderProcessor:
    """HTTP标头处理器"""

    def __init__(self, validator: Optional[HeaderValidator] = None) -> None:
        """
        初始化标头处理器

        Args:
            validator: 标头验证器，如果不提供则创建默认实例
        """
        self.validator = validator or HeaderValidator()

    def process_headers(
        self, headers: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, str], bool, List[str]]:
        """
        处理HTTP标头

        Args:
            headers: 原始标头字典

        Returns:
            Tuple[Dict[str, str], Dict[str, str], bool, List[str]]:
            (解析后的标头, 脱敏后的标头, 是否有效, 错误列表)
        """
        # 验证标头
        is_valid, errors = self.validator.validate_headers(headers)

        # 解析环境变量
        resolved_headers = self.validator.resolve_headers(headers) if is_valid else {}

        # 脱敏处理
        sanitized_headers = self.validator.sanitize_headers_for_logging(headers)

        return resolved_headers, sanitized_headers, is_valid, errors

    def get_allowed_headers(self) -> List[str]:
        """获取允许的标头列表"""
        return sorted(self.validator.ALLOWED_HEADERS)

    def get_sensitive_headers(self) -> List[str]:
        """获取敏感标头列表"""
        return sorted(self.validator.SENSITIVE_HEADERS)
