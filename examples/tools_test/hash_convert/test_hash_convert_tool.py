"""
Hash转换工具测试文件

测试Hash转换工具的功能和正确性。
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到sys.path，以便导入definition.tools.hash_convert
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from definition.tools.hash_convert import hash_convert, md5_convert, sha1_convert, sha256_convert, sha512_convert


class TestHashConvertTool:
    """Hash转换工具测试类"""
    
    def test_hash_convert_with_valid_params(self):
        """测试使用有效参数进行哈希转换"""
        test_text = "Hello, World!"
        
        # 测试SHA256算法
        result = hash_convert(test_text, "sha256")
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha256"
        assert result["hash_value"] == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert result["hash_length"] == 64
    
    def test_hash_convert_with_md5(self):
        """测试MD5算法"""
        test_text = "Hello, World!"
        result = hash_convert(test_text, "md5")
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "md5"
        assert result["hash_value"] == "65a8e27d8879283831b664bd8b7f0ad4"
        assert result["hash_length"] == 32
    
    def test_hash_convert_with_sha1(self):
        """测试SHA1算法"""
        test_text = "Hello, World!"
        result = hash_convert(test_text, "sha1")
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha1"
        assert result["hash_value"] == "0a0a9f2a6772942557ab5355d76af442f8f65e01"
        assert result["hash_length"] == 40
    
    def test_hash_convert_with_sha512(self):
        """测试SHA512算法"""
        test_text = "Hello, World!"
        result = hash_convert(test_text, "sha512")
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha512"
        assert result["hash_length"] == 128
    
    def test_hash_convert_default_algorithm(self):
        """测试默认算法（SHA256）"""
        test_text = "Hello, World!"
        result = hash_convert(test_text)  # 不指定算法，使用默认值
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha256"
        assert result["hash_value"] == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert result["hash_length"] == 64
    
    def test_hash_convert_empty_text(self):
        """测试空文本参数"""
        with pytest.raises(ValueError, match="文本不能为空"):
            hash_convert("")
    
    def test_hash_convert_invalid_algorithm(self):
        """测试无效的算法参数"""
        with pytest.raises(ValueError, match="不支持的算法"):
            hash_convert("Hello, World!", "invalid_algorithm")
    
    def test_md5_convert_function(self):
        """测试MD5转换函数"""
        test_text = "Hello, World!"
        result = md5_convert(test_text)
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "md5"
        assert result["hash_value"] == "65a8e27d8879283831b664bd8b7f0ad4"
        assert result["hash_length"] == 32
    
    def test_sha1_convert_function(self):
        """测试SHA1转换函数"""
        test_text = "Hello, World!"
        result = sha1_convert(test_text)
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha1"
        assert result["hash_value"] == "0a0a9f2a6772942557ab5355d76af442f8f65e01"
        assert result["hash_length"] == 40
    
    def test_sha256_convert_function(self):
        """测试SHA256转换函数"""
        test_text = "Hello, World!"
        result = sha256_convert(test_text)
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha256"
        assert result["hash_value"] == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert result["hash_length"] == 64
    
    def test_sha512_convert_function(self):
        """测试SHA512转换函数"""
        test_text = "Hello, World!"
        result = sha512_convert(test_text)
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha512"
        assert result["hash_length"] == 128
    
    def test_hash_convert_chinese_text(self):
        """测试中文文本的哈希转换"""
        test_text = "你好，世界！"
        result = hash_convert(test_text, "sha256")
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha256"
        assert isinstance(result["hash_value"], str)
        assert len(result["hash_value"]) == 64
    
    def test_hash_convert_special_characters(self):
        """测试特殊字符的哈希转换"""
        test_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = hash_convert(test_text, "sha256")
        
        # 验证结果
        assert result["original_text"] == test_text
        assert result["algorithm"] == "sha256"
        assert isinstance(result["hash_value"], str)
        assert len(result["hash_value"]) == 64


# 运行测试的便捷函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()