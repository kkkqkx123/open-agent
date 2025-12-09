"""存储后端具体实现层

提供按功能组织的具体后端实现。
"""

# 功能化后端
from .session_backend import SessionBackend
from .thread_backend import ThreadBackend

__all__ = [
    # 功能化后端
    "SessionBackend",
    "ThreadBackend"
]