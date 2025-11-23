"""FileWatcher单元测试"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

import pytest

from src.core.common.utils.file_watcher import FileWatcher, MultiPathFileWatcher


class TestFileWatcher:
    """FileWatcher测试类"""

    def setup_method(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.yaml")
        with open(self.test_file, "w") as f:
            f.write("initial content")

    def teardown_method(self):
        """测试后清理"""
        # 停止监听器
        if hasattr(self, 'watcher'):
            self.watcher.stop()

        # 删除临时目录
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init(self):
        """测试初始化"""
        watcher = FileWatcher(self.test_dir)
        assert str(watcher.watch_path) == self.test_dir
        assert watcher.patterns == ["*.yaml", "*.yml"]
        assert watcher.callbacks == {}
        assert len(watcher.observers) == 0

        # 测试自定义模式
        watcher_custom = FileWatcher(self.test_dir, ["*.txt", "*.json"])
        assert watcher_custom.patterns == ["*.txt", "*.json"]

    def test_start_and_stop(self):
        """测试开始和停止监听"""
        watcher = FileWatcher(self.test_dir)
        assert not watcher.is_watching()

        watcher.start()
        time.sleep(0.1)  # 等待观察器启动
        assert watcher.is_watching()

        watcher.stop()
        assert not watcher.is_watching()

        # 再次停止不应该出错
        watcher.stop()

    def test_add_and_remove_callback(self):
        """测试添加和移除回调"""
        watcher = FileWatcher(self.test_dir, ["*.yaml"])
        callback = Mock()

        # 添加回调
        watcher.add_callback("*.yaml", callback)
        assert "*.yaml" in watcher.callbacks
        assert callback in watcher.callbacks["*.yaml"]

        # 移除回调
        watcher.remove_callback("*.yaml", callback)
        assert callback not in watcher.callbacks.get("*.yaml", [])

    def test_file_change_callback(self):
        """测试文件变化回调"""
        watcher = FileWatcher(self.test_dir, ["*.yaml"])
        callback = Mock()
        watcher.add_callback("*.yaml", callback)

        watcher.start()
        time.sleep(0.1)  # 等待观察器启动

        # 修改文件
        with open(self.test_file, "w") as f:
            f.write("updated content")

        # 等待回调执行
        time.sleep(0.2)

        # 验证回调被调用
        assert callback.called
        # 由于文件系统事件可能触发多次，我们只验证至少被调用一次
        assert callback.call_count >= 1

        watcher.stop()

    def test_file_change_debounce(self):
        """测试文件变化防抖功能"""
        watcher = FileWatcher(self.test_dir, ["*.yaml"])
        callback = Mock()
        watcher.add_callback("*.yaml", callback)

        watcher.start()
        time.sleep(0.1)  # 等待观察器启动

        # 快速修改文件多次
        for i in range(3):
            with open(self.test_file, "w") as f:
                f.write(f"content {i}")
            time.sleep(0.05)  # 小于防抖时间

        # 等待一段时间以确保处理完成
        time.sleep(0.3)

        # 验证回调被调用（防抖机制会减少调用次数）
        assert callback.called

        watcher.stop()

    def test_is_watching(self):
        """测试监听状态检查"""
        watcher = FileWatcher(self.test_dir)
        assert not watcher.is_watching()

        watcher.start()
        time.sleep(0.1)
        assert watcher.is_watching()

        watcher.stop()
        assert not watcher.is_watching()

    def test_handle_file_change(self):
        """测试处理文件变化"""
        watcher = FileWatcher(self.test_dir, ["*.yaml"])
        callback = Mock()
        watcher.add_callback("*.yaml", callback)

        # 直接调用内部方法测试
        watcher._handle_file_change(self.test_file)

        # 验证回调被调用
        callback.assert_called_once_with(self.test_file)


class TestMultiPathFileWatcher:
    """MultiPathFileWatcher测试类"""

    def setup_method(self):
        """测试前准备"""
        self.test_dir1 = tempfile.mkdtemp()
        self.test_dir2 = tempfile.mkdtemp()
        self.test_file1 = os.path.join(self.test_dir1, "test1.yaml")
        self.test_file2 = os.path.join(self.test_dir2, "test2.yaml")
        
        with open(self.test_file1, "w") as f:
            f.write("content1")
        with open(self.test_file2, "w") as f:
            f.write("content2")

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir1, ignore_errors=True)
        shutil.rmtree(self.test_dir2, ignore_errors=True)

    def test_init(self):
        """测试初始化"""
        multi_watcher = MultiPathFileWatcher()
        assert multi_watcher.watchers == {}

    def test_add_and_remove_watch_path(self):
        """测试添加和移除监听路径"""
        multi_watcher = MultiPathFileWatcher()

        # 添加监听路径
        multi_watcher.add_watch_path(self.test_dir1)
        assert self.test_dir1 in multi_watcher.watchers
        assert multi_watcher.is_watching(self.test_dir1)

        # 移除监听路径
        multi_watcher.remove_watch_path(self.test_dir1)
        assert self.test_dir1 not in multi_watcher.watchers

    def test_add_callback(self):
        """测试添加回调"""
        multi_watcher = MultiPathFileWatcher()
        callback = Mock()

        multi_watcher.add_watch_path(self.test_dir1)
        multi_watcher.add_callback(self.test_dir1, "*.yaml", callback)

        # 验证回调被添加到正确的监听器
        assert "*.yaml" in multi_watcher.watchers[self.test_dir1].callbacks
        assert callback in multi_watcher.watchers[self.test_dir1].callbacks["*.yaml"]

    def test_start_and_stop_all(self):
        """测试开始和停止所有监听"""
        multi_watcher = MultiPathFileWatcher()

        multi_watcher.add_watch_path(self.test_dir1)
        multi_watcher.add_watch_path(self.test_dir2)

        # 开始所有监听
        multi_watcher.start_all()
        time.sleep(0.1)
        assert multi_watcher.is_watching(self.test_dir1)
        assert multi_watcher.is_watching(self.test_dir2)

        # 停止所有监听
        multi_watcher.stop_all()
        assert not multi_watcher.is_watching(self.test_dir1)
        assert not multi_watcher.is_watching(self.test_dir2)

    def test_is_watching_any(self):
        """测试是否正在监听任何路径"""
        multi_watcher = MultiPathFileWatcher()

        # 没有添加任何路径时
        assert not multi_watcher.is_watching()

        # 添加路径但未启动
        multi_watcher.add_watch_path(self.test_dir1)
        assert not multi_watcher.is_watching()

        # 启动后
        multi_watcher.start_all()
        time.sleep(0.1)
        assert multi_watcher.is_watching()