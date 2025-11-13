"""任务组配置系统测试"""

import pytest
from pathlib import Path

from src.infrastructure.config.models.task_group_config import (
    TaskGroupsConfig, TaskGroupConfig, EchelonConfig, 
    FallbackStrategy, RotationStrategy
)
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.config_loader import YamlConfigLoader


class TestTaskGroupConfig:
    """任务组配置测试"""
    
    def test_task_groups_config_from_dict(self):
        """测试从字典创建任务组配置"""
        config_dict = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4", "anthropic-claude-opus"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    "fallback_strategy": "echelon_down"
                }
            },
            "polling_pools": {
                "single_turn_pool": {
                    "description": "单轮对话轮询池",
                    "task_groups": ["fast_group"],
                    "rotation_strategy": "round_robin"
                }
            },
            "global_fallback": {
                "enabled": True,
                "max_attempts": 3
            },
            "concurrency_control": {
                "enabled": True
            },
            "rate_limiting": {
                "enabled": True,
                "algorithm": "token_bucket"
            }
        }
        
        config = TaskGroupsConfig.from_dict(config_dict)
        
        assert config.task_groups["fast_group"].description == "快速响应任务组"
        assert config.task_groups["fast_group"].fallback_strategy == FallbackStrategy.ECHELON_DOWN
        assert config.polling_pools["single_turn_pool"].rotation_strategy == RotationStrategy.ROUND_ROBIN
        assert config.global_fallback.enabled == True
        assert config.concurrency_control.enabled == True
        assert config.rate_limiting.enabled == True
    
    def test_echelon_config_from_dict(self):
        """测试层级配置创建"""
        config_dict = {
            "models": ["openai-gpt4", "anthropic-claude-opus"],
            "concurrency_limit": 10,
            "rpm_limit": 100,
            "priority": 1,
            "timeout": 30,
            "max_retries": 3,
            "temperature": 0.7,
            "max_tokens": 2000,
            "function_calling": "required"
        }
        
        echelon = EchelonConfig.from_dict(config_dict)
        
        assert echelon.models == ["openai-gpt4", "anthropic-claude-opus"]
        assert echelon.concurrency_limit == 10
        assert echelon.rpm_limit == 100
        assert echelon.priority == 1
        assert echelon.timeout == 30
        assert echelon.max_retries == 3
        assert echelon.temperature == 0.7
        assert echelon.max_tokens == 2000
        assert echelon.function_calling == "required"


class TestTaskGroupManager:
    """任务组管理器测试"""
    
    @pytest.fixture
    def config_loader(self):
        """配置加载器fixture"""
        return YamlConfigLoader()
    
    @pytest.fixture
    def task_group_manager(self, config_loader):
        """任务组管理器fixture"""
        return TaskGroupManager(config_loader)
    
    def test_parse_group_reference(self, task_group_manager):
        """测试解析组引用"""
        # 测试完整的组引用
        group_name, echelon = task_group_manager.parse_group_reference("fast_group.echelon1")
        assert group_name == "fast_group"
        assert echelon == "echelon1"
        
        # 测试只有组名
        group_name, echelon = task_group_manager.parse_group_reference("fast_group")
        assert group_name == "fast_group"
        assert echelon is None
        
        # 测试小模型组引用
        group_name, task_type = task_group_manager.parse_group_reference("fast_small_group.translation")
        assert group_name == "fast_small_group"
        assert task_type == "translation"
    
    def test_get_models_for_group(self, task_group_manager):
        """测试获取组模型"""
        # 创建临时配置文件
        config_data = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4", "anthropic-claude-opus"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3
                    }
                }
            }
        }
        
        # 模拟配置加载
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        models = task_group_manager.get_models_for_group("fast_group.echelon1")
        assert models == ["openai-gpt4", "anthropic-claude-opus"]
        
        # 测试不存在的组
        models = task_group_manager.get_models_for_group("nonexistent_group.echelon1")
        assert models == []
    
    def test_validate_group_reference(self, task_group_manager):
        """测试验证组引用"""
        # 创建临时配置
        config_data = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3
                    }
                }
            }
        }
        
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        # 测试有效的组引用
        assert task_group_manager.validate_group_reference("fast_group.echelon1") == True
        assert task_group_manager.validate_group_reference("fast_group") == True
        
        # 测试无效的组引用
        assert task_group_manager.validate_group_reference("nonexistent_group.echelon1") == False
        assert task_group_manager.validate_group_reference("fast_group.nonexistent_echelon") == False
    
    def test_get_fallback_groups(self, task_group_manager):
        """测试获取降级组"""
        config_data = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3
                    },
                    "echelon2": {
                        "models": ["openai-gpt3.5-turbo"],
                        "concurrency_limit": 20,
                        "rpm_limit": 200,
                        "priority": 2,
                        "timeout": 25,
                        "max_retries": 2
                    },
                    "fallback_strategy": "echelon_down"
                }
            }
        }
        
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        # 测试层级降级
        fallback_groups = task_group_manager.get_fallback_groups("fast_group.echelon1")
        assert "fast_group.echelon2" in fallback_groups
        
        # 测试不存在的组
        fallback_groups = task_group_manager.get_fallback_groups("nonexistent_group.echelon1")
        assert fallback_groups == []


class TestTaskGroupConfigIntegration:
    """任务组配置集成测试"""
    
    def test_load_real_config(self):
        """测试加载真实配置文件"""
        config_path = Path("configs/llms/groups/_task_groups.yaml")
        
        if not config_path.exists():
            pytest.skip("配置文件不存在")
        
        config_loader = YamlConfigLoader()
        task_group_manager = TaskGroupManager(config_loader)
        
        try:
            config = task_group_manager.load_config()
            
            # 验证配置结构
            assert len(config.task_groups) > 0
            assert len(config.polling_pools) > 0
            assert config.global_fallback is not None
            assert config.concurrency_control is not None
            assert config.rate_limiting is not None
            
            # 验证任务组
            fast_group = config.get_task_group("fast_group")
            assert fast_group is not None
            assert fast_group.description is not None
            assert len(fast_group.echelons) > 0
            
            # 验证轮询池
            single_turn_pool = config.get_polling_pool("single_turn_pool")
            assert single_turn_pool is not None
            assert len(single_turn_pool.task_groups) > 0
            
        except Exception as e:
            pytest.fail(f"加载配置失败: {e}")
    
    def test_config_status(self):
        """测试配置状态"""
        config_path = Path("configs/llms/groups/_task_groups.yaml")
        
        if not config_path.exists():
            pytest.skip("配置文件不存在")
        
        config_loader = YamlConfigLoader()
        task_group_manager = TaskGroupManager(config_loader)
        
        try:
            status = task_group_manager.get_config_status()
            
            assert "config_loaded" in status
            assert "task_groups_count" in status
            assert "polling_pools_count" in status
            assert "task_groups" in status
            assert "polling_pools" in status
            assert "global_fallback_enabled" in status
            assert "concurrency_control_enabled" in status
            assert "rate_limiting_enabled" in status
            
        except Exception as e:
            pytest.fail(f"获取配置状态失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__])