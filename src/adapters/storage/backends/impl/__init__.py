"""存储后端具体实现层

提供按功能组织的具体后端实现。
"""

# 功能化后端
from .session_backend import SessionBackend
from .thread_backend import ThreadBackend

# 按存储技术组合的后端
from .combined_backends import (
    SQLiteSessionBackend,
    SQLiteThreadBackend,
    FileSessionBackend,
    FileThreadBackend
)

__all__ = [
    # 功能化后端
    "SessionBackend",
    "ThreadBackend",
    
    # 按存储技术组合的后端
    "SQLiteSessionBackend",
    "SQLiteThreadBackend",
    "FileSessionBackend", 
    "FileThreadBackend"
]