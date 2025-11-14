"""配置系统重构测试"""

import pytest
import tempfile
import os
from pathlib import Path

from src.infrastructure.config import ConfigFactory
from src.infrastructure.config.interfaces import IConfigSystem


class TestConfigSystem:
    """配置系统测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "configs"
        self.config_path.mkdir(exist_ok=True)
        
        # 创建测试配置文件
        self._create_test_configs()
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_configs(self):
        """创建测试配置文件"""
        # 创建全局配置
        global_config = """
log_level: INFO
env: testing
debug: false
"""
        (self.config_path / "global.yaml").write_text(global_config)
        
        # 创建测试配置
        test_config = """
name: test_config
value: 42
"""
        (self.config_path / "test.yaml").write_text(test_config)
    
    def test_create_config_system(self):
        """测试创建配置系统"""
        config_system = ConfigFactory.create_config_system(str(self.config_path))
        assert isinstance(config_system, IConfigSystem)
    
    def test_load_config(self):
        """测试加载配置"""
        config_system = ConfigFactory.create_config_system(str(self.config_path))
        # 由于我们使用的是完整的配置系统，需要调用特定的加载方法
        # 这里我们测试是否能正确初始化
        global_config = config_system.load_global_config()
        assert global_config is not None
        assert global_config.log_level == "INFO"
        assert global_config.env == "testing"
        assert global_config.debug is False
    
    def test_load_nonexistent_config(self):
        """测试加载不存在的配置"""
        # 这个测试需要根据实际的错误处理机制来调整
        pass