"""配置错误恢复单元测试"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.config.error_recovery import (
    ConfigBackupManager,
    ConfigErrorRecovery,
    ConfigValidatorWithRecovery
)
from src.infrastructure.exceptions import ConfigurationError


class TestConfigBackupManager:
    """配置备份管理器测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def backup_manager(self, temp_dir):
        """创建备份管理器"""
        backup_dir = Path(temp_dir) / "backups"
        return ConfigBackupManager(str(backup_dir), max_backups=3)
    
    @pytest.fixture
    def test_config_file(self, temp_dir):
        """创建测试配置文件"""
        config_path = Path(temp_dir) / "test_config.yaml"
        config_path.write_text("key: value\n")
        return str(config_path)
    
    def test_create_backup(self, backup_manager, test_config_file):
        """测试创建备份"""
        backup_path = backup_manager.create_backup(test_config_file)
        
        # 验证备份文件存在
        assert Path(backup_path).exists()
        
        # 验证备份文件内容
        backup_content = Path(backup_path).read_text()
        original_content = Path(test_config_file).read_text()
        assert backup_content == original_content
    
    def test_create_backup_nonexistent_file(self, backup_manager):
        """测试创建不存在的文件备份"""
        with pytest.raises(ConfigurationError):
            backup_manager.create_backup("nonexistent_file.yaml")
    
    def test_restore_backup(self, backup_manager, test_config_file):
        """测试恢复备份"""
        # 创建备份
        backup_path = backup_manager.create_backup(test_config_file)
        
        # 修改原文件
        Path(test_config_file).write_text("modified: value\n")
        
        # 恢复备份
        success = backup_manager.restore_backup(test_config_file)
        
        assert success is True
        
        # 验证文件已恢复
        content = Path(test_config_file).read_text()
        assert content == "key: value\n"
    
    def test_restore_backup_nonexistent(self, backup_manager):
        """测试恢复不存在的备份"""
        success = backup_manager.restore_backup("nonexistent_file.yaml")
        assert success is False
    
    def test_list_backups(self, backup_manager, test_config_file):
        """测试列出备份"""
        # 创建多个备份
        backup_manager.create_backup(test_config_file)
        backup_manager.create_backup(test_config_file)
        backup_manager.create_backup(test_config_file)
        
        # 列出备份
        backups = backup_manager.list_backups(test_config_file)
        
        assert len(backups) == 3
        
        # 验证备份按时间排序（最新的在前）
        timestamps = [b['timestamp'] for b in backups]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_max_backups_limit(self, backup_manager, test_config_file):
        """测试最大备份数限制"""
        # 创建超过限制的备份
        for _ in range(5):
            backup_manager.create_backup(test_config_file)
        
        # 验证只保留最新的备份
        backups = backup_manager.list_backups(test_config_file)
        assert len(backups) == 3  # max_backups = 3
    
    def test_cleanup_old_backups(self, backup_manager, test_config_file):
        """测试清理旧备份"""
        # 创建多个备份
        backup_manager.create_backup(test_config_file)
        backup_manager.create_backup(test_config_file)
        
        # 验证备份目录存在
        backup_dir = Path(backup_manager.backup_dir)
        assert backup_dir.exists()
        assert len(list(backup_dir.glob("test_config_*"))) == 2


class TestConfigErrorRecovery:
    """配置错误恢复器测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def error_recovery(self, temp_dir):
        """创建错误恢复器"""
        backup_dir = Path(temp_dir) / "backups"
        backup_manager = ConfigBackupManager(str(backup_dir))
        return ConfigErrorRecovery(backup_manager)
    
    @pytest.fixture
    def test_config_file(self, temp_dir):
        """创建测试配置文件"""
        config_path = Path(temp_dir) / "test_config.yaml"
        config_path.write_text("key: value\n")
        return str(config_path)
    
    def test_recover_from_backup(self, error_recovery, test_config_file):
        """测试从备份恢复"""
        # 创建备份
        backup_manager = error_recovery.backup_manager
        backup_manager.create_backup(test_config_file)
        
        # 损坏文件
        Path(test_config_file).write_text("invalid: [")
        
        # 尝试恢复
        error = ConfigurationError("配置文件损坏")
        success = error_recovery.recover_config(test_config_file, error)
        
        assert success is True
        
        # 验证文件已恢复
        content = Path(test_config_file).read_text()
        assert content == "key: value\n"
    
    def test_reset_to_default(self, error_recovery, temp_dir):
        """测试重置为默认配置"""
        # 创建全局配置文件
        global_config_path = Path(temp_dir) / "global.yaml"
        global_config_path.write_text("invalid: [")
        
        # 尝试恢复
        error = ConfigurationError("配置文件损坏")
        success = error_recovery.recover_config(str(global_config_path), error)
        
        assert success is True
        
        # 验证文件已重置为默认配置
        content = global_config_path.read_text()
        assert "log_level: INFO" in content
    
    def test_create_empty_config(self, error_recovery, temp_dir):
        """测试创建空配置文件"""
        # 创建一个不存在的配置文件路径
        config_path = Path(temp_dir) / "new_config.yaml"
        
        # 尝试恢复
        error = ConfigurationError("配置文件不存在")
        success = error_recovery.recover_config(str(config_path), error)
        
        assert success is True
        
        # 验证文件已创建
        assert config_path.exists()
        content = config_path.read_text()
        assert "# 配置文件 - 自动创建" in content
    
    def test_add_recovery_strategy(self, error_recovery, test_config_file):
        """测试添加自定义恢复策略"""
        # 添加自定义策略
        def custom_strategy(config_path, error):
            Path(config_path).write_text("custom: recovery\n")
            return True
        
        error_recovery.add_recovery_strategy(custom_strategy)
        
        # 损坏文件
        Path(test_config_file).write_text("invalid: [")
        
        # 尝试恢复
        error = ConfigurationError("配置文件损坏")
        success = error_recovery.recover_config(test_config_file, error)
        
        assert success is True
        
        # 验证自定义策略生效
        content = Path(test_config_file).read_text()
        assert content == "custom: recovery\n"
    
    def test_can_recover(self, error_recovery, test_config_file):
        """测试检查是否可以恢复"""
        # 有备份的情况
        error_recovery.backup_manager.create_backup(test_config_file)
        assert error_recovery.can_recover(test_config_file) is True
        
        # 删除备份
        backups = error_recovery.backup_manager.list_backups(test_config_file)
        for backup in backups:
            Path(backup['path']).unlink()
        
        # 全局配置文件可以重置为默认
        global_config_path = Path(test_config_file).parent / "global.yaml"
        assert error_recovery.can_recover(str(global_config_path)) is True
        
        # 普通文件可以创建空文件
        assert error_recovery.can_recover(test_config_file) is True


class TestConfigValidatorWithRecovery:
    """带错误恢复的配置验证器测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def validator_with_recovery(self, temp_dir):
        """创建带错误恢复的验证器"""
        backup_dir = Path(temp_dir) / "backups"
        backup_manager = ConfigBackupManager(str(backup_dir))
        error_recovery = ConfigErrorRecovery(backup_manager)
        return ConfigValidatorWithRecovery(error_recovery)
    
    @pytest.fixture
    def test_config_file(self, temp_dir):
        """创建测试配置文件"""
        config_path = Path(temp_dir) / "test_config.yaml"
        config_path.write_text("key: value\n")
        return str(config_path)
    
    def test_validate_with_recovery_success(self, validator_with_recovery, test_config_file):
        """测试验证成功"""
        def validator(config):
            return "key" in config
        
        def loader(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        result = validator_with_recovery.validate_with_recovery(
            test_config_file, validator, loader
        )
        
        assert result == {"key": "value"}
    
    def test_validate_with_recovery_failure_and_recovery(self, validator_with_recovery, test_config_file):
        """测试验证失败并恢复"""
        # 创建备份
        backup_manager = validator_with_recovery.error_recovery.backup_manager
        backup_manager.create_backup(test_config_file)
        
        # 损坏文件
        Path(test_config_file).write_text("invalid: [")
        
        def validator(config):
            return "key" in config
        
        def loader(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # 验证应该成功（因为会恢复）
        result = validator_with_recovery.validate_with_recovery(
            test_config_file, validator, loader
        )
        
        assert result == {"key": "value"}
    
    def test_validate_with_recovery_failure_no_recovery(self, validator_with_recovery, temp_dir):
        """测试验证失败且无法恢复"""
        # 创建无效配置文件
        config_path = Path(temp_dir) / "invalid_config.yaml"
        config_path.write_text("invalid: [")
        
        def validator(config):
            return "key" in config
        
        def loader(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # 验证应该失败
        with pytest.raises(ConfigurationError):
            validator_with_recovery.validate_with_recovery(
                str(config_path), validator, loader
            )