"""统一ID生成器"""

import uuid
import hashlib
import time
from typing import Optional


import threading

class IDGenerator:
    """统一ID生成器"""
    
    # 类变量，用于确保ID唯一性
    _sequence = 0
    _sequence_lock = threading.Lock()
    _last_timestamp = 0
    
    @staticmethod
    def generate_id(prefix: str = "", length: int = 8) -> str:
        """生成唯一ID
        
        Args:
            prefix: ID前缀
            length: 随机部分长度
            
        Returns:
            唯一ID
        """
        # 使用时间戳和随机数生成ID
        timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
        random_part = uuid.uuid4().hex[:length]
        
        if prefix:
            return f"{prefix}_{timestamp}_{random_part}"
        else:
            return f"{timestamp}_{random_part}"
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID
        
        Returns:
            UUID字符串
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_uuid(length: int = 8) -> str:
        """生成短UUID
        
        Args:
            length: UUID长度
            
        Returns:
            短UUID字符串
        """
        return uuid.uuid4().hex[:length]
    
    @staticmethod
    def generate_hash(content: str, algorithm: str = "md5") -> str:
        """生成内容哈希
        
        Args:
            content: 要哈希的内容
            algorithm: 哈希算法 ("md5", "sha1", "sha256")
            
        Returns:
            哈希值
        """
        if algorithm == "md5":
            return hashlib.md5(content.encode()).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(content.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    @staticmethod
    def generate_nanoid(length: int = 21) -> str:
        """生成NanoID风格的短ID
        
        Args:
            length: ID长度
            
        Returns:
            短ID字符串
        """
        # 简化版NanoID，使用URL安全的字符集
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        random_bytes = uuid.uuid4().hex
        result = ""
        
        # 生成足够长度的ID
        while len(result) < length:
            random_bytes = uuid.uuid4().hex
            for byte in random_bytes:
                if len(result) >= length:
                    break
                result += alphabet[int(byte, 16) % len(alphabet)]
        
        return result[:length]
    
    @staticmethod
    def generate_time_based_id() -> str:
        """生成基于时间的ID（类似Snowflake）
        
        Returns:
            时间基础ID
        """
        # 简化版Snowflake ID
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        machine_id = 1  # 可以配置为机器标识
        
        # 使用线程安全的序列号确保唯一性
        with IDGenerator._sequence_lock:
            current_timestamp = timestamp
            if current_timestamp == IDGenerator._last_timestamp:
                # 如果时间戳相同，递增序列号
                IDGenerator._sequence = (IDGenerator._sequence + 1) % 4096  # 12位序列号
            else:
                # 如果时间戳不同，重置序列号
                IDGenerator._sequence = 0
                IDGenerator._last_timestamp = current_timestamp
            sequence = IDGenerator._sequence
        
        # 组合时间戳、机器ID和序列号
        snowflake_id = (timestamp << 22) | (machine_id << 12) | (sequence & 0xFFF)
        return str(snowflake_id)
    
    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID
        
        Returns:
            会话ID
        """
        return f"session_{uuid.uuid4().hex}"
    
    @staticmethod
    def generate_thread_id() -> str:
        """生成线程ID
        
        Returns:
            线程ID
        """
        return f"thread_{uuid.uuid4().hex}"
    
    @staticmethod
    def generate_checkpoint_id() -> str:
        """生成检查点ID
        
        Returns:
            检查点ID
        """
        return f"checkpoint_{uuid.uuid4().hex}"
    
    @staticmethod
    def generate_workflow_id() -> str:
        """生成工作流ID
        
        Returns:
            工作流ID
        """
        return f"workflow_{uuid.uuid4().hex}"