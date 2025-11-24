"""DynamicImporter 模块的单元测试"""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import time

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from core.common.dynamic_importer import (
    DynamicImporter,
    DynamicImportError,
    get_global_importer,
    import_class,
    import_function
)


class TestDynamicImporter:
    """DynamicImporter 类的测试"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.importer = DynamicImporter()

    def test_init(self):
        """测试初始化"""
        assert self.importer._module_cache == {}
        assert self.importer._class_cache == {}
        assert self.importer.max_retries == 3
        assert self.importer.retry_delay == 0.1
        assert self.importer.logger is not None

    def test_import_class_success(self):
        """测试成功导入类"""
        # 测试导入一个真正的类
        cls = self.importer.import_class("pathlib:Path")
        assert cls == Path

    def test_import_class_with_invalid_path(self):
        """测试无效的类路径"""
        with pytest.raises(DynamicImportError) as exc_info:
            self.importer.import_class("invalid_path")
        assert "类路径格式不正确" in str(exc_info.value)

    def test_import_class_nonexistent_module(self):
        """测试导入不存在的模块"""
        with pytest.raises(DynamicImportError):
            self.importer.import_class("nonexistent_module:NonExistentClass")

    def test_import_class_nonexistent_class(self):
        """测试导入模块中不存在的类"""
        with pytest.raises(DynamicImportError):
            self.importer.import_class("os:pathlib.NonExistentClass")

    def test_import_function_success(self):
        """测试成功导入函数"""
        func = self.importer.import_function("os.path:join")
        assert func == os.path.join

    def test_import_function_with_invalid_path(self):
        """测试无效的函数路径"""
        with pytest.raises(DynamicImportError) as exc_info:
            self.importer.import_function("invalid_path")
        assert "函数路径格式不正确" in str(exc_info.value)

    def test_import_function_nonexistent_module(self):
        """测试导入不存在的模块中的函数"""
        with pytest.raises(DynamicImportError):
            self.importer.import_function("nonexistent_module:nonexistent_function")

    def test_import_function_nonexistent_function(self):
        """测试导入模块中不存在的函数"""
        with pytest.raises(DynamicImportError):
            self.importer.import_function("os:nonexistent_function")

    def test_import_function_not_a_function(self):
        """测试导入的不是函数的对象"""
        with pytest.raises(DynamicImportError):
            self.importer.import_function("os:environ")  # environ 是一个对象，不是函数

    def test_import_module_success(self):
        """测试成功导入模块"""
        module = self.importer.import_module("os")
        assert module == os

    def test_import_module_nonexistent(self):
        """测试导入不存在的模块"""
        with pytest.raises(DynamicImportError):
            self.importer.import_module("nonexistent_module_12345")

    def test_is_class_available(self):
        """测试检查类是否可用"""
        # 存在的类
        assert self.importer.is_class_available("pathlib:Path") is True
        # 不存在的类
        assert self.importer.is_class_available("os:NonExistentClass") is False

    def test_is_function_available(self):
        """测试检查函数是否可用"""
        # 存在的函数
        assert self.importer.is_function_available("os.path:join") is True
        # 不存在的函数
        assert self.importer.is_function_available("os:nonexistent_function") is False

    def test_get_class_info_success(self):
        """测试获取类信息成功"""
        info = self.importer.get_class_info("pathlib:Path")
        assert info is not None
        assert info["name"] == "Path"
        assert info["module"] == "pathlib"

    def test_get_class_info_failure(self):
        """测试获取不存在类的信息"""
        info = self.importer.get_class_info("os:NonExistentClass")
        assert info is None

    def test_clear_cache(self):
        """测试清除缓存"""
        # 先导入一些内容以填充缓存
        self.importer.import_class("pathlib:Path")
        assert len(self.importer._class_cache) > 0
        
        # 清除缓存
        self.importer.clear_cache()
        
        # 验证缓存被清空
        assert len(self.importer._module_cache) == 0
        assert len(self.importer._class_cache) == 0

    def test_get_cache_info(self):
        """测试获取缓存信息"""
        # 先导入一些内容以填充缓存
        self.importer.import_class("pathlib:Path")
        
        cache_info = self.importer.get_cache_info()
        assert "module_cache_size" in cache_info
        assert "class_cache_size" in cache_info
        assert "cached_modules" in cache_info
        assert "cached_classes" in cache_info

    @patch('core.common.dynamic_importer.importlib.import_module')
    def test_import_module_with_retry_success(self, mock_import_module):
        """测试导入模块时重试机制成功"""
        # 模拟第一次失败，第二次成功
        mock_import_module.side_effect = [ImportError("First attempt failed"), os]
        
        # 由于模拟的副作用，我们需要特殊处理
        # 实际上，我们要测试重试逻辑
        module = self.importer.import_module("os", retry=True)
        assert module == os

    @patch('time.sleep')
    def test_import_with_retry_failure(self, mock_sleep):
        """测试导入时重试机制失败"""
        with pytest.raises(DynamicImportError):
            self.importer.import_module("nonexistent_module_12345", retry=True)
        # 验证重试了 max_retries 次
        assert mock_sleep.call_count == self.importer.max_retries - 1

    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次导入
        cls1 = self.importer.import_class("pathlib:Path")
        
        # 第二次导入，应该从缓存获取
        cls2 = self.importer.import_class("pathlib:Path")
        
        # 应该是同一个类
        assert cls1 == cls2
        # 验证缓存大小
        assert len(self.importer._class_cache) == 1


class TestGlobalFunctions:
    """测试全局函数"""

    def test_get_global_importer(self):
        """测试获取全局导入器"""
        importer1 = get_global_importer()
        importer2 = get_global_importer()
        
        # 应该返回同一个实例
        assert importer1 is importer2

    def test_import_class_global(self):
        """测试全局导入类函数"""
        cls = import_class("pathlib:Path")
        assert cls == Path

    def test_import_function_global(self):
        """测试全局导入函数函数"""
        func = import_function("os.path:join")
        assert func == os.path.join


if __name__ == "__main__":
    pytest.main([__file__])