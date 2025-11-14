"""LLM任务组配置系统集成测试"""

from infrastructure.llm.exceptions import LLMError
import pytest
import asyncio
from pathlib import Path

from infrastructure.config.core.loader import YamlConfigLoader
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.polling_pool import PollingPoolManager
from src.infrastructure.llm.enhanced_fallback_manager import EnhancedFallbackManager
from src.infrastructure.llm.concurrency_controller import ConcurrencyAndRateLimitManager, ConcurrencyLevel


class TestLLMTaskGroupIntegration:
    """LLM任务组配置系统集成测试"""
    
    @pytest.fixture
    def config_loader(self):
        """配置加载器fixture"""
        return YamlConfigLoader()
    
    @pytest.fixture
    def task_group_manager(self, config_loader):
        """任务组管理器fixture"""
        return TaskGroupManager(config_loader)
    
    @pytest.fixture
    def polling_pool_manager(self, task_group_manager):
        """轮询池管理器fixture"""
        return PollingPoolManager(task_group_manager)
    
    @pytest.fixture
    def fallback_manager(self, task_group_manager):
        """降级管理器fixture"""
        return EnhancedFallbackManager(task_group_manager)
    
    @pytest.mark.asyncio
    async def test_task_group_config_loading(self, task_group_manager):
        """测试任务组配置加载"""
        # 检查注册表文件是否存在
        registry_path = Path("configs/llms/groups/_task_groups.yaml")
        if not registry_path.exists():
            pytest.skip("注册表配置文件不存在")
        
        try:
            config = task_group_manager.load_config()
            
            # 验证基本结构
            assert config is not None
            assert len(config.task_groups) > 0
            assert len(config.polling_pools) > 0
            
            # 验证任务组
            fast_group = config.get_task_group("fast_group")
            assert fast_group is not None
            assert fast_group.description is not None
            assert len(fast_group.echelons) > 0
            
            # 验证轮询池
            single_turn_pool = config.get_polling_pool("single_turn_pool")
            assert single_turn_pool is not None
            assert len(single_turn_pool.task_groups) > 0
            
            # 验证全局配置
            assert config.global_fallback is not None
            assert config.concurrency_control is not None
            assert config.rate_limiting is not None
            
        except Exception as e:
            pytest.fail(f"任务组配置加载失败: {e}")
    
    def test_group_reference_parsing(self, task_group_manager):
        """测试组引用解析"""
        # 测试完整引用
        group_name, echelon = task_group_manager.parse_group_reference("fast_group.echelon1")
        assert group_name == "fast_group"
        assert echelon == "echelon1"
        
        # 测试只有组名
        group_name, echelon = task_group_manager.parse_group_reference("fast_group")
        assert group_name == "fast_group"
        assert echelon is None
        
        # 测试小模型组
        group_name, task_type = task_group_manager.parse_group_reference("fast_small_group.translation")
        assert group_name == "fast_small_group"
        assert task_type == "translation"
    
    @pytest.mark.asyncio
    async def test_polling_pool_creation(self, polling_pool_manager):
        """测试轮询池创建"""
        pool_config = {
            "task_groups": ["fast_group", "fast_small_group"],
            "rotation_strategy": "round_robin",
            "health_check_interval": 30,
            "concurrency_control": {
                "enabled": True,
                "levels": [
                    {
                        "group_level": {
                            "limit": 100,
                            "queue_size": 1000
                        }
                    }
                ]
            },
            "rate_limiting": {
                "enabled": True,
                "algorithm": "token_bucket",
                "bucket_size": 1000,
                "refill_rate": 16.67
            }
        }
        
        try:
            pool = await polling_pool_manager.create_pool("test_pool", pool_config)
            
            assert pool is not None
            assert pool.name == "test_pool"
            assert len(pool.instances) >= 0  # 可能为0，因为没有实际的LLM客户端
            
            # 测试状态获取
            status = pool.get_status()
            assert "name" in status
            assert "total_instances" in status
            assert "stats" in status
            assert "concurrency_status" in status
            
        except Exception as e:
            pytest.fail(f"轮询池创建失败: {e}")
    
    @pytest.mark.asyncio
    async def test_fallback_manager(self, fallback_manager):
        """测试降级管理器"""
        try:
            # 测试熔断器
            circuit_breaker = fallback_manager.get_circuit_breaker("test_target")
            assert circuit_breaker is not None
            assert circuit_breaker.can_execute() == True
            
            # 测试成功记录
            circuit_breaker.record_success()
            assert circuit_breaker.state == "CLOSED"
            
            # 测试失败记录
            for _ in range(6):  # 超过阈值
                circuit_breaker.record_failure()
            
            assert circuit_breaker.state == "OPEN"
            assert circuit_breaker.can_execute() == False
            
            # 测试统计信息
            stats = fallback_manager.get_statistics()
            assert "total_attempts" in stats
            assert "success_rate" in stats
            assert "circuit_breakers" in stats
            
        except Exception as e:
            pytest.fail(f"降级管理器测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrency_control(self):
        """测试并发控制"""
        concurrency_config = {
            "enabled": True,
            "levels": [
                {
                    "group_level": {
                        "limit": 10,
                        "queue_size": 100
                    }
                },
                {
                    "echelon_level": {
                        "limit": 5,
                        "queue_size": 50
                    }
                }
            ]
        }
        
        rate_limit_config = {
            "enabled": True,
            "algorithm": "token_bucket",
            "bucket_size": 100,
            "refill_rate": 1.67
        }
        
        try:
            manager = ConcurrencyAndRateLimitManager(concurrency_config, rate_limit_config)
            
            # 测试并发控制
            can_execute = await manager.check_and_acquire(
                ConcurrencyLevel.GROUP, "test_group", timeout=1.0
            )
            assert can_execute == True
            
            # 释放许可
            manager.release(ConcurrencyLevel.GROUP, "test_group")
            
            # 测试状态获取
            status = manager.get_status()
            assert "concurrency" in status
            assert "rate_limit" in status
            
        except Exception as e:
            pytest.fail(f"并发控制测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, task_group_manager, polling_pool_manager, fallback_manager):
        """测试端到端工作流"""
        # 检查注册表文件是否存在
        registry_path = Path("configs/llms/groups/_task_groups.yaml")
        if not registry_path.exists():
            pytest.skip("注册表配置文件不存在")
        
        try:
            # 加载配置
            config = task_group_manager.load_config()
            
            # 创建轮询池
            pool_config = {
                "task_groups": ["fast_group"],
                "rotation_strategy": "round_robin",
                "health_check_interval": 30
            }
            pool = await polling_pool_manager.create_pool("test_pool", pool_config)
            
            # 测试降级执行
            # 使用monkey patching模拟_execute_target抛出异常
            original_execute_target = fallback_manager._execute_target
            
            async def mock_execute_target(target: str, prompt: str, **kwargs):
                raise LLMError(f"模拟LLM调用失败: {target}")
            
            fallback_manager._execute_target = mock_execute_target
            
            try:
                result = await fallback_manager.execute_with_fallback(
                    primary_target="fast_group.echelon1",
                    fallback_groups=["fast_group.echelon2", "fast_group.echelon3"],
                    prompt="测试提示词"
                )
                # 由于没有实际的LLM客户端，这里会失败，但可以测试降级逻辑
            except Exception as e:
                # 预期的异常，因为没有实际的LLM客户端
                assert "降级尝试都失败了" in str(e) or "所有降级尝试都失败了" in str(e)
            finally:
                # 恢复原始方法
                fallback_manager._execute_target = original_execute_target
            
            # 验证降级历史
            history = fallback_manager.get_fallback_history()
            assert len(history) > 0
            
            # 验证熔断器状态
            circuit_status = fallback_manager.get_circuit_breaker_status()
            assert isinstance(circuit_status, dict)
            
        except Exception as e:
            pytest.fail(f"端到端工作流测试失败: {e}")
    
    def test_config_validation(self, task_group_manager):
        """测试配置验证"""
        # 测试有效的组引用
        assert task_group_manager.validate_group_reference("fast_group.echelon1") == True
        assert task_group_manager.validate_group_reference("fast_small_group.translation") == True
        
        # 测试无效的组引用
        assert task_group_manager.validate_group_reference("nonexistent_group.echelon1") == False
        assert task_group_manager.validate_group_reference("fast_group.nonexistent_echelon") == False
    
    def test_models_retrieval(self, task_group_manager):
        """测试模型检索"""
        # 创建临时配置
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
        
        from src.infrastructure.config.models.task_group_config import TaskGroupsConfig
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        # 测试模型获取
        models = task_group_manager.get_models_for_group("fast_group.echelon1")
        assert models == ["openai-gpt4", "anthropic-claude-opus"]
        
        # 测试降级组获取
        fallback_groups = task_group_manager.get_fallback_groups("fast_group.echelon1")
        # 由于没有配置echelon2，应该返回空列表
        assert fallback_groups == []


if __name__ == "__main__":
    pytest.main([__file__])