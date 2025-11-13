"""配置迁移工具单元测试"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.infrastructure.llm.migration import ConfigMigrator
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.exceptions import LLMConfigurationError


class TestConfigMigrator:
    """配置迁移器测试"""
    
    @pytest.fixture
    def mock_task_group_manager(self):
        """模拟任务组管理器"""
        manager = Mock(spec=TaskGroupManager)
        manager.list_task_groups.return_value = ["fast_group", "thinking_group"]
        manager.list_polling_pools.return_value = ["fast_pool", "thinking_pool"]
        
        # 模拟任务组配置
        mock_task_group = Mock()
        mock_task_group.echelons = {
            "echelon1": Mock(),
            "echelon2": Mock(),
            "echelon3": Mock()
        }
        manager.get_task_group.return_value = mock_task_group
        
        # 模拟轮询池配置
        mock_polling_pool = Mock()
        mock_polling_pool.fallback_config = None
        manager.get_polling_pool.return_value = mock_polling_pool
        
        return manager
    
    @pytest.fixture
    def temp_config_dir(self):
        """临时配置目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "configs" / "llms"
            config_dir.mkdir(parents=True)
            
            # 创建子目录
            (config_dir / "groups").mkdir()
            (config_dir / "polling_pools").mkdir()
            (config_dir / "backup").mkdir()
            
            yield config_dir
    
    def test_init(self, mock_task_group_manager):
        """测试初始化"""
        migrator = ConfigMigrator(mock_task_group_manager)
        
        assert migrator.task_group_manager == mock_task_group_manager
        assert migrator.config_base_path == Path("configs/llms")
        assert migrator.migration_log == []
    
    def test_load_global_fallback_config_exists(self, mock_task_group_manager, temp_config_dir):
        """测试加载存在的全局降级配置"""
        # 创建全局降级配置文件
        global_fallback_config = {
            "max_attempts": 5,
            "retry_delay": 2.0,
            "circuit_breaker": {
                "failure_threshold": 10,
                "recovery_time": 120
            }
        }
        
        global_fallback_path = temp_config_dir / "global_fallback.yaml"
        with open(global_fallback_path, 'w') as f:
            yaml.dump(global_fallback_config, f)
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        config = migrator._load_global_fallback_config()
        
        assert config == global_fallback_config
    
    def test_load_global_fallback_config_not_exists(self, mock_task_group_manager, temp_config_dir):
        """测试加载不存在的全局降级配置"""
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        config = migrator._load_global_fallback_config()
        
        assert config is None
    
    def test_create_backup(self, mock_task_group_manager, temp_config_dir):
        """测试创建备份"""
        # 创建任务组配置文件
        task_group_config = {
            "name": "fast_group",
            "description": "Fast group",
            "echelon1": {
                "models": ["model1"],
                "concurrency_limit": 10
            }
        }
        
        task_group_path = temp_config_dir / "groups" / "fast_group.yaml"
        with open(task_group_path, 'w') as f:
            yaml.dump(task_group_config, f)
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        migrator._create_backup(["fast_group"])
        
        # 检查备份文件是否存在
        backup_path = temp_config_dir / "backup" / "fast_group.yaml.backup"
        assert backup_path.exists()
        
        # 检查备份内容
        with open(backup_path, 'r') as f:
            backup_config = yaml.safe_load(f)
        
        assert backup_config == task_group_config
    
    def test_migrate_task_group_success(self, mock_task_group_manager, temp_config_dir):
        """测试成功迁移任务组"""
        # 创建任务组配置文件
        task_group_config = {
            "name": "fast_group",
            "description": "Fast group",
            "echelon1": {
                "models": ["model1"],
                "concurrency_limit": 10
            },
            "fallback_strategy": "echelon_down"
        }
        
        task_group_path = temp_config_dir / "groups" / "fast_group.yaml"
        with open(task_group_path, 'w') as f:
            yaml.dump(task_group_config, f)
        
        global_fallback_config = {
            "max_attempts": 5,
            "retry_delay": 2.0,
            "circuit_breaker": {
                "failure_threshold": 10,
                "recovery_time": 120
            }
        }
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator._migrate_task_group("fast_group", global_fallback_config)
        
        assert result == True
        
        # 检查迁移后的配置
        with open(task_group_path, 'r') as f:
            migrated_config = yaml.safe_load(f)
        
        assert "fallback_config" in migrated_config
        assert migrated_config["fallback_config"]["strategy"] == "echelon_down"
        assert migrated_config["fallback_config"]["max_attempts"] == 5
        assert migrated_config["fallback_config"]["retry_delay"] == 2.0
    
    def test_migrate_task_group_already_has_config(self, mock_task_group_manager, temp_config_dir):
        """测试迁移已有降级配置的任务组"""
        # 创建已有降级配置的任务组
        task_group_config = {
            "name": "fast_group",
            "description": "Fast group",
            "echelon1": {
                "models": ["model1"],
                "concurrency_limit": 10
            },
            "fallback_config": {
                "strategy": "echelon_down",
                "max_attempts": 3
            }
        }
        
        task_group_path = temp_config_dir / "groups" / "fast_group.yaml"
        with open(task_group_path, 'w') as f:
            yaml.dump(task_group_config, f)
        
        global_fallback_config = {"max_attempts": 5}
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator._migrate_task_group("fast_group", global_fallback_config)
        
        assert result == True
        
        # 检查配置未更改
        with open(task_group_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config["fallback_config"]["max_attempts"] == 3  # 保持原值
    
    def test_migrate_task_group_file_not_exists(self, mock_task_group_manager, temp_config_dir):
        """测试迁移不存在的任务组文件"""
        global_fallback_config = {"max_attempts": 5}
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator._migrate_task_group("non_existent", global_fallback_config)
        
        assert result == False
    
    def test_get_default_fallback_groups_fast_group(self, mock_task_group_manager):
        """测试获取快速组的默认降级组"""
        migrator = ConfigMigrator(mock_task_group_manager)
        
        fallback_groups = migrator._get_default_fallback_groups("fast_group")
        assert fallback_groups == ["fast_group.echelon2", "fast_group.echelon3"]
    
    def test_get_default_fallback_groups_thinking_group(self, mock_task_group_manager):
        """测试获取思考组的默认降级组"""
        migrator = ConfigMigrator(mock_task_group_manager)
        
        fallback_groups = migrator._get_default_fallback_groups("thinking_group")
        assert fallback_groups == ["thinking_group.echelon2", "thinking_group.echelon3", "fast_group.echelon1"]
    
    def test_get_default_fallback_groups_plan_group(self, mock_task_group_manager):
        """测试获取规划组的默认降级组"""
        migrator = ConfigMigrator(mock_task_group_manager)
        
        fallback_groups = migrator._get_default_fallback_groups("plan_group")
        assert fallback_groups == ["thinking_group.echelon1", "thinking_group.echelon2"]
    
    def test_get_default_fallback_groups_generic(self, mock_task_group_manager):
        """测试获取通用组的默认降级组"""
        migrator = ConfigMigrator(mock_task_group_manager)
        
        fallback_groups = migrator._get_default_fallback_groups("generic_group")
        assert fallback_groups == ["generic_group.echelon2", "generic_group.echelon3"]
    
    def test_migrate_polling_pool_success(self, mock_task_group_manager, temp_config_dir):
        """测试成功迁移轮询池"""
        # 创建轮询池配置文件
        pool_config = {
            "name": "fast_pool",
            "description": "Fast pool",
            "task_groups": ["fast_group"],
            "rotation_strategy": "round_robin"
        }
        
        pool_path = temp_config_dir / "polling_pools" / "fast_pool.yaml"
        with open(pool_path, 'w') as f:
            yaml.dump(pool_config, f)
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator._migrate_polling_pool("fast_pool")
        
        assert result == True
        
        # 检查迁移后的配置
        with open(pool_path, 'r') as f:
            migrated_config = yaml.safe_load(f)
        
        assert "fallback_config" in migrated_config
        assert migrated_config["fallback_config"]["strategy"] == "instance_rotation"
        assert migrated_config["fallback_config"]["max_instance_attempts"] == 2
    
    def test_migrate_polling_pool_already_has_config(self, mock_task_group_manager, temp_config_dir):
        """测试迁移已有降级配置的轮询池"""
        # 创建已有降级配置的轮询池
        pool_config = {
            "name": "fast_pool",
            "description": "Fast pool",
            "task_groups": ["fast_group"],
            "rotation_strategy": "round_robin",
            "fallback_config": {
                "strategy": "instance_rotation",
                "max_instance_attempts": 3
            }
        }
        
        pool_path = temp_config_dir / "polling_pools" / "fast_pool.yaml"
        with open(pool_path, 'w') as f:
            yaml.dump(pool_config, f)
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator._migrate_polling_pool("fast_pool")
        
        assert result == True
        
        # 检查配置未更改
        with open(pool_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config["fallback_config"]["max_instance_attempts"] == 3  # 保持原值
    
    def test_migrate_global_fallback_to_task_groups(self, mock_task_group_manager, temp_config_dir):
        """测试迁移全局降级配置到任务组"""
        # 创建全局降级配置
        global_fallback_config = {
            "max_attempts": 5,
            "retry_delay": 2.0,
            "circuit_breaker": {
                "failure_threshold": 10,
                "recovery_time": 120
            }
        }
        
        global_fallback_path = temp_config_dir / "global_fallback.yaml"
        with open(global_fallback_path, 'w') as f:
            yaml.dump(global_fallback_config, f)
        
        # 创建任务组配置文件
        for group_name in ["fast_group", "thinking_group"]:
            task_group_config = {
                "name": group_name,
                "description": f"{group_name} description",
                "echelon1": {
                    "models": ["model1"],
                    "concurrency_limit": 10
                }
            }
            
            task_group_path = temp_config_dir / "groups" / f"{group_name}.yaml"
            with open(task_group_path, 'w') as f:
                yaml.dump(task_group_config, f)
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator.migrate_global_fallback_to_task_groups(backup=False)
        
        assert result == True
        assert len(migrator.migration_log) == 2
        
        # 检查迁移日志
        for log_entry in migrator.migration_log:
            assert log_entry["status"] == "success"
            assert log_entry["task"] == "migrate_task_group"
    
    def test_migrate_polling_pools(self, mock_task_group_manager, temp_config_dir):
        """测试迁移轮询池"""
        # 创建轮询池配置文件
        for pool_name in ["fast_pool", "thinking_pool"]:
            pool_config = {
                "name": pool_name,
                "description": f"{pool_name} description",
                "task_groups": ["fast_group"],
                "rotation_strategy": "round_robin"
            }
            
            pool_path = temp_config_dir / "polling_pools" / f"{pool_name}.yaml"
            with open(pool_path, 'w') as f:
                yaml.dump(pool_config, f)
        
        migrator = ConfigMigrator(mock_task_group_manager, str(temp_config_dir))
        result = migrator.migrate_polling_pools(backup=False)
        
        assert result == True
        assert len(migrator.migration_log) == 2
        
        # 检查迁移日志
        for log_entry in migrator.migration_log:
            assert log_entry["status"] == "success"
            assert log_entry["task"] == "migrate_polling_pool"
    
    def test_validate_migration(self, mock_task_group_manager):
        """测试验证迁移结果"""
        # 模拟有降级配置的任务组和轮询池
        mock_task_group = Mock()
        mock_task_group.fallback_config = {"strategy": "echelon_down"}
        mock_task_group_manager.get_task_group.return_value = mock_task_group
        
        mock_polling_pool = Mock()
        mock_polling_pool.fallback_config = {"strategy": "instance_rotation"}
        mock_task_group_manager.get_polling_pool.return_value = mock_polling_pool
        
        migrator = ConfigMigrator(mock_task_group_manager)
        result = migrator.validate_migration()
        
        assert result["summary"]["total_task_groups"] == 2
        assert result["summary"]["valid_task_groups"] == 2
        assert result["summary"]["total_polling_pools"] == 2
        assert result["summary"]["valid_polling_pools"] == 2
    
    def test_get_migration_log(self, mock_task_group_manager):
        """测试获取迁移日志"""
        migrator = ConfigMigrator(mock_task_group_manager)
        
        # 添加日志条目
        migrator.migration_log.append({
            "task": "test_task",
            "status": "success"
        })
        
        log = migrator.get_migration_log()
        assert len(log) == 1
        assert log[0]["task"] == "test_task"
        assert log[0]["status"] == "success"