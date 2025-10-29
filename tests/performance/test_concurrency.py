"""并发测试

测试多线程环境下的稳定性和性能。
"""

import pytest
import threading
import time
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import queue

from src.infrastructure.di_config import DIConfig, create_container
from src.infrastructure.lifecycle_manager import LifecycleManager
from src.infrastructure.container import ServiceLifetime
from src.infrastructure.config_loader import IConfigLoader
from src.application.workflow.manager import IWorkflowManager
from src.application.sessions.manager import ISessionManager


class TestConcurrency:
    """并发测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """配置目录"""
        config_dir = temp_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        
        # 创建基本配置文件
        global_config = config_dir / "global.yaml"
        global_config.write_text("""
logging:
  level: INFO
secrets:
  openai_api_key: "test_key"
        """)
        
        return config_dir
    
    @pytest.fixture
    def container(self, config_dir):
        """创建测试容器"""
        return create_container(
            config_path=str(config_dir),
            environment="test"
        )
    
    def test_concurrent_service_resolution(self, container):
        """测试并发服务解析"""
        num_threads = 20
        num_operations = 100
        results = queue.Queue()
        errors = queue.Queue()
        
        def worker():
            """工作线程函数"""
            try:
                for _ in range(num_operations):
                    # 解析不同服务
                    services = [
                        IConfigLoader,
                        IWorkflowManager,
                        ISessionManager
                    ]
                    
                    for service_type in services:
                        start_time = time.time()
                        service = container.get(service_type)
                        end_time = time.time()
                        
                        assert service is not None
                        results.put({
                            'service': service_type.__name__,
                            'time': end_time - start_time,
                            'thread': threading.current_thread().name
                        })
            except Exception as e:
                errors.put(e)
        
        # 创建并启动线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, name=f"Worker-{i}")
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查错误
        error_list = []
        while not errors.empty():
            error_list.append(errors.get())
        
        assert len(error_list) == 0, f"发生错误: {error_list}"
        
        # 分析结果
        result_list = []
        while not results.empty():
            result_list.append(results.get())
        
        # 验证所有服务都被成功解析
        assert len(result_list) == num_threads * num_operations * 3
        
        # 检查性能
        times = [r['time'] for r in result_list]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"并发解析平均时间: {avg_time * 1000:.3f}ms")
        print(f"并发解析最大时间: {max_time * 1000:.3f}ms")
        
        # 性能要求：并发环境下最大解析时间应小于10ms
        assert max_time < 0.01, f"并发解析时间过长: {max_time * 1000:.3f}ms"
    
    def test_concurrent_container_creation(self, config_dir):
        """测试并发容器创建"""
        num_threads = 10
        containers = queue.Queue()
        errors = queue.Queue()
        
        def worker():
            """工作线程函数"""
            try:
                container = create_container(
                    config_path=str(config_dir),
                    environment="test"
                )
                containers.put(container)
            except Exception as e:
                errors.put(e)
        
        # 创建并启动线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, name=f"Creator-{i}")
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查错误
        error_list = []
        while not errors.empty():
            error_list.append(errors.get())
        
        assert len(error_list) == 0, f"发生错误: {error_list}"
        
        # 验证所有容器都创建成功
        container_list = []
        while not containers.empty():
            container_list.append(containers.get())
        
        assert len(container_list) == num_threads
        
        # 验证每个容器都能正常工作
        for container in container_list:
            assert container.has_service(IConfigLoader)
            service = container.get(IConfigLoader)
            assert service is not None
            
            # 清理容器
            container.clear()
    
    def test_concurrent_lifecycle_management(self, config_dir):
        """测试并发生命周期管理"""
        lifecycle_manager = LifecycleManager()
        
        # 注册多个服务
        services = []
        for i in range(20):
            class TestService:
                def __init__(self):
                    self.initialized = False
                    self.started = False
                    self.stopped = False
                    self.disposed = False
                
                def initialize(self):
                    time.sleep(0.001)  # 模拟耗时操作
                    self.initialized = True
                
                def start(self):
                    self.started = True
                
                def stop(self):
                    self.stopped = True
                
                def dispose(self):
                    self.disposed = True
            
            service = TestService()
            services.append(service)
            lifecycle_manager.register_service(f"service_{i}", service)
        
        # 并发初始化
        def initialize_worker(service_names):
            """初始化工作线程"""
            results = {}
            for name in service_names:
                success = lifecycle_manager.initialize_service(name)
                results[name] = success
            return results
        
        # 分割服务列表
        service_names = [f"service_{i}" for i in range(20)]
        chunk_size = 5
        service_chunks = [service_names[i:i+chunk_size] 
                         for i in range(0, len(service_names), chunk_size)]
        
        # 并发执行初始化
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(initialize_worker, chunk) 
                      for chunk in service_chunks]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # 验证所有服务都已初始化
        all_results = {}
        for result in results:
            all_results.update(result)
        
        assert all(all_results.values())
        assert all(service.initialized for service in services)
        
        # 并发启动
        def start_worker(service_names):
            """启动工作线程"""
            results = {}
            for name in service_names:
                success = lifecycle_manager.start_service(name)
                results[name] = success
            return results
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(start_worker, chunk) 
                      for chunk in service_chunks]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # 验证所有服务都已启动
        all_results = {}
        for result in results:
            all_results.update(result)
        
        assert all(all_results.values())
        
        # 清理
        lifecycle_manager.dispose()
    
    @pytest.mark.asyncio
    async def test_async_session_manager_operations(self, config_dir):
        """测试异步会话管理器操作"""
        # 创建模拟会话管理器
        from src.application.sessions.manager import SessionManager
        
        mock_workflow_manager = Mock()
        mock_session_store = Mock()
        mock_thread_manager = AsyncMock()
        mock_state_manager = Mock()
        
        session_manager = SessionManager(
            workflow_manager=mock_workflow_manager,
            session_store=mock_session_store,
            thread_manager=mock_thread_manager,
            state_manager=mock_state_manager,
            storage_path=config_dir.parent / "sessions"
        )
        
        # 模拟配置文件存在
        with pytest.MonkeyPatch().context() as m:
            m.setattr('pathlib.Path.exists', lambda self: True)
            
            # 并发创建会话
            async def create_session_worker(session_id):
                """创建会话工作协程"""
                workflow_configs = {
                    f"thread_{session_id}": f"config_{session_id}.yaml"
                }
                
                return await session_manager.create_session_with_threads(
                    workflow_configs=workflow_configs
                )
            
            # 并发执行
            tasks = [create_session_worker(i) for i in range(10)]
            session_ids = await asyncio.gather(*tasks)
            
            # 验证所有会话都创建成功
            assert len(session_ids) == 10
            assert all(session_id is not None for session_id in session_ids)
            assert len(set(session_ids)) == 10  # 所有会话ID都不同
    
    def test_thread_safety_of_singleton_services(self, container):
        """测试单例服务的线程安全性"""
        # 注册一个单例服务
        class SingletonService:
            def __init__(self):
                self.value = 0
                self.lock = threading.Lock()
            
            def increment(self):
                with self.lock:
                    self.value += 1
                    return self.value
        
        container.register(
            SingletonService,
            SingletonService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 获取单例服务
        service = container.get(SingletonService)
        
        # 并发递增计数器
        num_threads = 20
        num_operations = 100
        results = queue.Queue()
        
        def worker():
            """工作线程函数"""
            for _ in range(num_operations):
                result = service.increment()
                results.put(result)
        
        # 创建并启动线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, name=f"Counter-{i}")
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        result_list = []
        while not results.empty():
            result_list.append(results.get())
        
        # 验证计数器正确递增
        assert len(result_list) == num_threads * num_operations
        assert max(result_list) == num_threads * num_operations
        assert set(result_list) == set(range(1, num_threads * num_operations + 1))
    
    def test_concurrent_service_registration(self, config_dir):
        """测试并发服务注册"""
        containers = []
        errors = queue.Queue()
        
        def create_and_register_worker(worker_id):
            """创建容器并注册服务的工作线程"""
            try:
                container = create_container(
                    config_path=str(config_dir),
                    environment="test"
                )
                
                # 注册额外服务
                for i in range(10):
                    class_name = f"Worker{worker_id}Service{i}"
                    
                    # 动态创建类
                    service_class = type(class_name, (), {
                        "__init__": lambda self: None
                    })
                    
                    container.register(
                        service_class,
                        service_class,
                        lifetime=ServiceLifetime.SINGLETON
                    )
                
                containers.append(container)
            except Exception as e:
                errors.put(e)
        
        # 创建并启动线程
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=create_and_register_worker,
                args=(i,),
                name=f"Register-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查错误
        error_list = []
        while not errors.empty():
            error_list.append(errors.get())
        
        assert len(error_list) == 0, f"发生错误: {error_list}"
        
        # 验证所有容器都创建成功并注册了服务
        assert len(containers) == 5
        
        for container in containers:
            # 验证核心服务
            assert container.has_service(IConfigLoader)
            
            # 清理容器
            container.clear()
    
    def test_concurrent_environment_switching(self, config_dir):
        """测试并发环境切换"""
        container = create_container(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册环境特定服务
        class TestService:
            def __init__(self):
                self.environment = None
        
        # 注册不同环境的服务
        container.register(TestService, TestService, environment="test")
        container.register(TestService, TestService, environment="development")
        container.register(TestService, TestService, environment="production")
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def environment_worker(environment_name, num_operations):
            """环境切换工作线程"""
            try:
                for _ in range(num_operations):
                    # 切换环境
                    container.set_environment(environment_name)
                    
                    # 获取服务
                    if container.has_service(TestService):
                        service = container.get(TestService)
                        results.put({
                            'environment': environment_name,
                            'service_id': id(service),
                            'thread': threading.current_thread().name
                        })
            except Exception as e:
                errors.put(e)
        
        # 创建并启动线程
        environments = ["test", "development", "production"]
        threads = []
        
        for env in environments:
            thread = threading.Thread(
                target=environment_worker,
                args=(env, 50),
                name=f"Env-{env}"
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查错误
        error_list = []
        while not errors.empty():
            error_list.append(errors.get())
        
        assert len(error_list) == 0, f"发生错误: {error_list}"
        
        # 分析结果
        result_list = []
        while not results.empty():
            result_list.append(results.get())
        
        # 验证每个环境都有服务
        env_results = {}
        for result in result_list:
            env = result['environment']
            if env not in env_results:
                env_results[env] = []
            env_results[env].append(result)
        
        assert len(env_results) == 3
        for env in environments:
            assert env in env_results
            assert len(env_results[env]) == 50
    
    def test_deadlock_prevention(self, config_dir):
        """测试死锁预防"""
        # 创建具有复杂依赖的服务
        di_config = DIConfig()
        container = di_config.configure_core_services(
            config_path=str(config_dir),
            environment="test"
        )
        
        # 注册相互依赖的服务（但通过接口避免循环依赖）
        class ServiceA:
            def __init__(self, service_b: 'IServiceB'):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        class IServiceB:
            pass
        
        # 注册服务
        container.register(ServiceA, ServiceA)
        container.register(IServiceB, ServiceB)
        container.register(ServiceB, ServiceB)
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def worker():
            """工作线程函数"""
            try:
                # 尝试解析服务
                service_a = container.get(ServiceA)
                service_b = container.get(IServiceB)
                
                results.put({
                    'service_a_id': id(service_a),
                    'service_b_id': id(service_b),
                    'thread': threading.current_thread().name
                })
            except Exception as e:
                errors.put(e)
        
        # 创建并启动多个线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, name=f"Worker-{i}")
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查错误
        error_list = []
        while not errors.empty():
            error_list.append(errors.get())
        
        # 应该没有死锁错误
        assert len(error_list) == 0, f"发生错误（可能是死锁）: {error_list}"
        
        # 验证所有线程都成功获取服务
        result_list = []
        while not results.empty():
            result_list.append(results.get())
        
        assert len(result_list) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])