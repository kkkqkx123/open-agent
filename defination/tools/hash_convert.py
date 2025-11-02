"""
Hash转换工具实现

提供将字符串转换为各种哈希值的功能，支持MD5、SHA1、SHA256等算法。
"""

import hashlib
from typing import Dict, Any, Union


def hash_convert(
    text: str, 
    algorithm: str = "sha256"
) -> Dict[str, Any]:
    """将文本转换为指定算法的哈希值
    
    Args:
        text: 要转换的文本
        algorithm: 哈希算法，支持 "md5", "sha1", "sha256", "sha512"
        
    Returns:
        Dict[str, Any]: 包含原文本、算法和哈希值的字典
        
    Raises:
        ValueError: 当算法不支持或参数错误时抛出
    """
    # 验证输入参数
    if not text:
        raise ValueError("Text cannot be empty")
    
    # 支持的算法列表
    supported_algorithms = ["md5", "sha1", "sha256", "sha512"]
    
    if algorithm not in supported_algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}, supported algorithms: {supported_algorithms}")
    
    # 根据算法类型计算哈希值
    try:
        if algorithm == "md5":
            hash_obj = hashlib.md5(text.encode('utf-8'))
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1(text.encode('utf-8'))
        elif algorithm == "sha256":
            hash_obj = hashlib.sha256(text.encode('utf-8'))
        elif algorithm == "sha512":
            hash_obj = hashlib.sha512(text.encode('utf-8'))
        else:
            # 这个分支理论上不会执行，因为前面已经验证了算法
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        hash_value = hash_obj.hexdigest()
        
        return {
            "original_text": text,
            "algorithm": algorithm,
            "hash_value": hash_value,
            "hash_length": len(hash_value)
        }
    except Exception as e:
        raise ValueError(f"Hash calculation failed: {str(e)}")


def md5_convert(text: str) -> Dict[str, Any]:
    """将文本转换为MD5哈希值
    
    Args:
        text: 要转换的文本
        
    Returns:
        Dict[str, Any]: 包含原文本和MD5哈希值的字典
    """
    return hash_convert(text, "md5")


def sha1_convert(text: str) -> Dict[str, Any]:
    """将文本转换为SHA1哈希值
    
    Args:
        text: 要转换的文本
        
    Returns:
        Dict[str, Any]: 包含原文本和SHA1哈希值的字典
    """
    return hash_convert(text, "sha1")


def sha256_convert(text: str) -> Dict[str, Any]:
    """将文本转换为SHA256哈希值
    
    Args:
        text: 要转换的文本
        
    Returns:
        Dict[str, Any]: 包含原文本和SHA256哈希值的字典
    """
    return hash_convert(text, "sha256")


def sha512_convert(text: str) -> Dict[str, Any]:
    """将文本转换为SHA512哈希值
    
    Args:
        text: 要转换的文本
        
    Returns:
        Dict[str, Any]: 包含原文本和SHA512哈希值的字典
    """
    return hash_convert(text, "sha512")


# 示例用法
if __name__ == "__main__":
    # 测试哈希转换工具
    test_text = "Hello, World!"
    
    print("测试哈希转换工具:")
    print(f"原文: {test_text}")
    
    algorithms = ["md5", "sha1", "sha256", "sha512"]
    
    for algo in algorithms:
        try:
            result = hash_convert(test_text, algo)
            print(f"{algo.upper()}: {result['hash_value']}")
        except ValueError as e:
            print(f"错误: {e}")