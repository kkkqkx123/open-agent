"""BackupManager单元测试"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from src.core.common.utils.backup_manager import BackupManager


class TestBackupManager:
    """BackupManager测试类"""

    def setup_method(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.backup_manager = BackupManager(backup_dir=self.backup_dir, max_backups=3)

    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)

    def test_init_creates_backup_dir(self):
        """测试初始化时创建备份目录"""
        assert os.path.exists(self.backup_dir)

    def test_create_backup_success(self):
        """测试创建备份成功"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建备份
        backup_path = self.backup_manager.create_backup(test_file)

        # 验证备份文件存在
        assert os.path.exists(backup_path)
        assert "test_" in backup_path
        assert backup_path.endswith(".txt")

        # 验证备份内容与原文件相同
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_content = f.read()
        assert backup_content == "test content"

    def test_create_backup_file_not_exists(self):
        """测试文件不存在时创建备份失败"""
        with pytest.raises(RuntimeError, match="文件不存在"):
            self.backup_manager.create_backup("nonexistent.txt")

    def test_restore_backup_success(self):
        """测试恢复备份成功"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("original content")

        # 创建备份
        backup_path = self.backup_manager.create_backup(test_file)

        # 修改原文件内容
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("modified content")

        # 恢复备份
        result = self.backup_manager.restore_backup(test_file)

        # 验证恢复成功
        assert result is True
        with open(test_file, "r", encoding="utf-8") as f:
            restored_content = f.read()
        assert restored_content == "original content"

    def test_restore_backup_with_timestamp(self):
        """测试使用时间戳恢复备份"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("original content")

        # 创建备份
        backup_path = self.backup_manager.create_backup(test_file)
        backup_filename = Path(backup_path).name
        # 提取时间戳部分
        timestamp = backup_filename.split("_")[-1].replace(".txt", "")

        # 修改原文件内容
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("modified content")

        # 使用时间戳恢复备份
        result = self.backup_manager.restore_backup(test_file, timestamp)

        # 验证恢复成功
        assert result is True
        with open(test_file, "r", encoding="utf-8") as f:
            restored_content = f.read()
        assert restored_content == "original content"

    def test_list_backups(self):
        """测试列出备份"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建多个备份
        backup1_path = self.backup_manager.create_backup(test_file)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("modified content")
        backup2_path = self.backup_manager.create_backup(test_file)

        # 列出备份
        backups = self.backup_manager.list_backups(test_file)

        # 验证备份列表
        assert len(backups) == 2
        assert all(isinstance(backup, dict) for backup in backups)
        assert all("path" in backup for backup in backups)
        assert all("timestamp" in backup for backup in backups)
        assert all("size" in backup for backup in backups)
        assert all("created" in backup for backup in backups)

    def test_delete_backup(self):
        """测试删除备份"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建备份
        backup_path = self.backup_manager.create_backup(test_file)
        backup_filename = Path(backup_path).name
        timestamp = backup_filename.split("_")[-1].replace(".txt", "")

        # 验证备份存在
        assert os.path.exists(backup_path)

        # 删除备份
        result = self.backup_manager.delete_backup(test_file, timestamp)

        # 验证删除结果
        assert result is True
        assert not os.path.exists(backup_path)

    def test_delete_all_backups(self):
        """测试删除所有备份"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建多个备份
        self.backup_manager.create_backup(test_file)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("modified content")
        self.backup_manager.create_backup(test_file)

        # 验证备份存在
        backups = self.backup_manager.list_backups(test_file)
        assert len(backups) == 2

        # 删除所有备份
        count = self.backup_manager.delete_all_backups(test_file)

        # 验证删除结果
        assert count == 2
        backups = self.backup_manager.list_backups(test_file)
        assert len(backups) == 0

    def test_cleanup_old_backups(self):
        """测试清理旧备份"""
        # 设置最大备份数为2
        backup_manager = BackupManager(backup_dir=self.backup_dir, max_backups=2)

        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建3个备份
        backup1 = backup_manager.create_backup(test_file)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("content 2")
        backup2 = backup_manager.create_backup(test_file)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("content 3")
        backup3 = backup_manager.create_backup(test_file)

        # 验证只有2个备份保留
        backups = backup_manager.list_backups(test_file)
        assert len(backups) == 2

        # 验证最新的备份仍然存在
        assert os.path.exists(backup2)
        assert os.path.exists(backup3)

    def test_get_backup_stats(self):
        """测试获取备份统计信息"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建备份
        self.backup_manager.create_backup(test_file)

        # 获取统计信息
        stats = self.backup_manager.get_backup_stats()

        # 验证统计信息结构
        assert "total_files" in stats
        assert "total_size" in stats
        assert "backup_dir" in stats
        assert "file_groups" in stats
        assert stats["total_files"] >= 1

    def test_cleanup_all_backups(self):
        """测试清理所有旧备份"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        # 创建备份
        backup_path = self.backup_manager.create_backup(test_file)

        # 验证备份存在
        assert os.path.exists(backup_path)

        # 清理所有备份（即使是新的）
        count = self.backup_manager.cleanup_all_backups(older_than_days=0)

        # 验证备份被删除
        assert count >= 1
        backups = self.backup_manager.list_backups(test_file)
        assert len(backups) == 0